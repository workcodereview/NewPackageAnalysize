# coding: utf8

import os
import json
import time
import codecs
import redis
import hashlib

redis_client = redis.Redis(host='10.11.10.143', password='yourpassword', port=6379, decode_responses=True)


def get_log(path, revision, current_path=None, previous_info=None):
    if current_path is None:
        path = path.replace('\\', '/')
        current_path = path
    path_dirname = os.path.dirname(current_path)
    if current_path == '/':
        if previous_info is not None and previous_info['copyfrom_path']:
            from_path = os.path.join(previous_info['copyfrom_path'], os.path.relpath(path, previous_info['logfrom_path']))
            from_revision = int(previous_info['copyfrom_rev'])
            return get_log(from_path, from_revision)
        return previous_info
    cache_key = hashlib.sha256(bytes(current_path, encoding='utf8')).hexdigest()
    cache_data = redis_client.get(cache_key)
    if cache_data is None:
        return get_log(path, revision, path_dirname, previous_info)
    for info in cache_data.split('\n')[::-1]:
        if info == '':
            continue
        info_json = json.loads(info)
        info_json['logfrom_path'] = current_path
        if revision < info_json['revision']:
            continue
        if previous_info is not None and previous_info['revision'] > info_json['revision']:
            return get_log(path, revision, path_dirname, previous_info)
        return get_log(path, revision, path_dirname, info_json)
    return get_log(path, revision, path_dirname, previous_info)


# begin_time = time.time()
# print(type(get_log('/baanches-rel/tx_publish/JX3Pocket/Assets/JX3Game/Source/Map/SL/SL_HomeTown_boss.unity', 313090)))
# print(time.time() - begin_time)

def compare_file(file1, file2, out_file):
    if not os.path.exists(file1) or not os.path.exists(file2):
        return

    with codecs.open(file1, 'r', 'utf-8') as file_1:
        file_content1 = file_1.read().strip().splitlines()

    with codecs.open(file2, 'r', 'utf-8') as file_2:
        file_content2 = file_2.read().strip().splitlines()

    file_write = codecs.open(out_file, 'w', 'utf-8')
    file_write.write(u'fileName\tnumber\n')
    file_dict1 = {}
    count1 = 0
    for file in file_content1:
        file_info = file.split('\t')
        if file_info[0] != 'fileName':
            count1 = count1 + 1
            file_dict1[file_info[0]] = 1
    print('parseFile 获取到文件数为: '+str(count1))

    count2 = 0
    file_dict2 = {}
    for item in file_content2:
        item_info = item.split('\t')
        if item_info[0] != 'fileName':
            count2 = count2 + 1
            file_dict2[item_info[0]] = 1
    print('svn_file 获取到文件数为: ' + str(count2))

    for key, value in file_dict2.items():
        if key in file_dict1:
            file_dict1[key] = file_dict1[key] + 1

    for key1, value1 in file_dict1.items():
        file_write.write(key1+'\t'+str(value1)+'\n')

    file_write.close()


if __name__ == '__main__':

    file1 = r'E:\NewPackageAnalysize\dist\679477\parseFile.tab'
    file2 = r'E:\NewPackageAnalysize\dist\679477\svn_file.tab'
    out_file = r'E:\NewPackageAnalysize\dist\679477\result.tab'
    compare_file(file1, file2, out_file)