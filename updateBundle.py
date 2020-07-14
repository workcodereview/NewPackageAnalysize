#coding=utf-8

import os
import sys
import time
import json
import redis
import codecs
import hashlib
import argparse
import multiprocessing
from qb_model import QB
from calc_model import Calc
from analy_model import Analysis
from multiprocessing import Queue
from devide_model import redis_host, redis_password, redis_port, tx_publish_dir


def get_log(redis_client, path, revision, current_path=None, previous_info=None):
    if current_path is None:
        path = path.replace('\\', '/')
        current_path = path
    path_dir_name = os.path.dirname(current_path)
    if current_path == '/':
        if previous_info is not None and previous_info['copyfrom_path']:
            from_path = os.path.join(previous_info['copyfrom_path'],
                                     os.path.relpath(path, previous_info['logfrom_path']))
            from_revision = int(previous_info['copyfrom_rev'])
            return get_log(redis_client, from_path, from_revision)
        return previous_info
    cache_key = hashlib.sha256(bytes(current_path, encoding='utf8')).hexdigest()
    cache_data = redis_client.get(cache_key)
    if cache_data is None:
        return get_log(redis_client, path, revision, path_dir_name, previous_info)
    for info in cache_data.split('\n')[::-1]:
        if info == '':
            continue
        info_json = json.loads(info)
        info_json['logfrom_path'] = current_path
        if revision < info_json['revision']:
            continue
        if path != current_path and info_json['copyfrom_path'] == '':
            continue
        if previous_info is not None and previous_info['revision'] > info_json['revision']:
            return get_log(redis_client, path, revision, path_dir_name, previous_info)
        return get_log(redis_client, path, revision, path_dir_name, info_json)
    return get_log(redis_client, path, revision, path_dir_name, previous_info)


def get_svn(q_write, q_read):
    redis_client = redis.Redis(host=redis_host, password=redis_password, port=redis_port, decode_responses=True)
    while True:
        read_info = q_read.get()
        if read_info is None:
            # 推送给主进程一个None 标志svn数据写完成
            q_write.put(None)
            break
        svn_message = get_log(redis_client, tx_publish_dir + read_info['path']['svn_path'],
                              read_info['path']['revision'])

        if svn_message is None:
            svn_message = {
                'author': 'NULL',
                'msg': 'NULL',
                'date': 'NULL',
                'logfrom_path': 'NULL',
                'revision': 'NULL',
            }
        svn_message['file_path'] = read_info['path']['file_path']
        svn_message['svn_path'] = read_info['path']['svn_path']
        print('[子进程任务]: 文件数量: ' + str(read_info['index']) + ' 文件名: '+read_info['path']['svn_path'])
        q_write.put(svn_message)


# write_file_process 进程 ----> 向q_select队列写数据
def write_file(bundle_info_dict, asset_cache_path, queue_select, process_count):
    file_count = 1
    for bundle, bundle_value in bundle_info_dict.items():
        file_list = bundle_value['fileList']
        for file in file_list:
            file_path = file['f']
            if file_path == 'ABO':
                continue
            if file_path.upper() in asset_cache_path:
                asset_cache_path[file_path.upper()]['file_path'] = file['f']
                queue_select.put({'path': asset_cache_path[file_path.upper()], 'index': file_count})
                file_count += 1

    # put process_count个None 给20个子进程标志数据已推送完毕
    for i in range(process_count):
        queue_select.put(None)


# 保存结果到svn_file
def save_svn_file(queue_result, file):
    while not queue_result.empth():
        info = queue_result.get()
        print('[子进程任务]: 当前向svn_file存入第' + str(i) + '个文件')
        file.write(info['file_path'] + '\t' + info['svn_path'] + '\t' +
                   info['author'] + '\t' + info['date'] + '\t' +
                   info['logfrom_path'] + '\t' + info['msg'].strip().replace('\n', ' ') +
                   '\t' + str(info['revision']) + '\n')


# 单独进程处理资源分析模块
def analysis_calc_worker(arg):
    Analysis(arg.out_path + '/' + 'parseFile.tab')
    Calc(arg.out_path, '')
    print('[子进程任务]: 分析和计算资源完成')


if __name__ == '__main__':

    multiprocessing.freeze_support()
    parser = argparse.ArgumentParser()
    parser.add_argument('-B', '--baseline-buildid', help="baseline buildid", type=int, required=True)
    parser.add_argument('-I', '--input-path', help="input_path", required=True)
    parser.add_argument('-O', '--out-path', help="out_path", required=True)
    args = parser.parse_args()

    status = 1
    if args.input_path.find('\\'):
        args.input_path = args.input_path.replace('\\', '/')

    if args.out_path.find('\\'):
        args.out_path = args.out_path.replace('\\', '/')
    if not os.path.exists(args.out_path):
        os.mkdir(args.out_path)

    process_count = 20
    start_time = time.time()

    Qb_Message = QB(args.baseline_buildid, 'tx_publish', args.input_path, args.out_path)
    analysis_calc_process = multiprocessing.Process(target=analysis_calc_worker, args=(args,))
    analysis_calc_process.start()

    # 查询队列
    q_select = Queue()
    # 结果队列
    q_result = Queue()

    # 子进程负责写文件到队列中 另一子进程从队列拿数据处理 在写入
    write_file_process = multiprocessing.Process(target=write_file, args=(Qb_Message.BUNDLE_INFO_DICT,
                                                                          Qb_Message.ASSET_CACHE_PATH, q_select,
                                                                          process_count,))
    write_file_process.start()

    # 开启20个进程从q_select队列中获取要查询svn信息的文件 并将结果写入q_write队列中
    process_list = []
    for i in range(process_count):
        process_list.append(multiprocessing.Process(target=get_svn, args=(q_result, q_select)))
    for single_process in process_list:
        single_process.start()

    # 从写队列中获取结果存入svn_file.tab中
    f_write = codecs.open(args.out_path + '/svn_file.tab', 'w', 'utf-8')
    f_write.write('fileName\tsvn_file\tauthor\tdate\tfrom_path\tnumber_message\trevision\n')
    count = 0
    file_count = 0
    while True:
        q_info = q_result.get()
        if q_info is None:
            count += 1
            if process_count == count:
                break
            continue
        file_count += 1
        print('[主进程任务]: 当前向svn_file存入第' + str(file_count) + '个文件')
        f_write.write(q_info['file_path'] + '\t' + q_info['svn_path'] + '\t' +
                      q_info['author'] + '\t' + q_info['date'] + '\t' +
                      q_info['logfrom_path']+'\t'+q_info['msg'].strip().replace('\n', ' ') +
                      '\t' + str(q_info['revision']) + '\n')
    f_write.close()
    print('[主进程任务]: 写svn_file文件完成')
    analysis_calc_process.join()
    print('[主进程任务]: join完成')
    end_time = time.time()
    print('共耗时: ' + str(end_time - start_time))

    status = 0
    sys.exit(status)
