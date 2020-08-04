import os
import re
import codecs
from svn_model import SVN


trunk_dir = 'svn://xsjreposvr3.rdev.kingsoft.net/JX3M/trunk/JX3Pocket'
username = 'zhangyin'
password = 'ZyZd97.zdd'


# svn_path_dict = {file.upper(): svn_file}
def sve_svn_path(svn_file):
    svn_path_dict = {}
    file_count = 0
    if os.path.exists(svn_file):
        with codecs.open(svn_file, 'r', 'utf-8') as svn:
            svn_content = svn.read().strip().splitlines()
        for file_item in svn_content:
            file_count += 1
            if file_count == 1:
                continue
            file_info = file_item.split('\t')
            if file_info[0].endswith('.anim'):
                svn_path_dict[file_info[0].upper()] = file_info[1]
    return svn_path_dict


def find_not_fbx(export_path, out_result, out_path, svn_path_dict):
    svn = SVN(trunk_dir, username, password)
    w_file = codecs.open(out_result, 'w', 'utf-8')
    w_file.write(u'fbx\tanim_File\tanim_Size(Byte)\tanim_MomerySize(Byte)\tanim_last_author\n')
    file_count = 0
    not_count = 0
    if os.path.exists(export_path):
        with codecs.open(export_path, 'r', 'utf-8') as export:
            file_content = export.read().strip().splitlines()
        for file_item in file_content:
            file_count += 1
            if file_count <= 1:
                continue
            if file_count > 502:
                break
            file_info = file_item.split('\t')
            print('文件：'+str(file_info[0]))
            svn_file_anim = svn_path_dict[file_info[0].upper()]
            anim_author = svn.last_submit(svn_file_anim)['author']
            fbx_path = out_path + svn_path_dict[file_info[0].upper()].replace('Assets/JX3Game', '')
            fbx_split = fbx_path.split('/')
            fbx_name = '@'+fbx_split[len(fbx_split) - 1].replace('.anim', '.fbx')
            fbx = ''
            for i in range(len(fbx_split) - 1):
                fbx = fbx + fbx_split[i] + '/'
            fbx_path = fbx + fbx_name

            # print('fbx_path: ' + fbx_path)
            if not os.path.exists(fbx_path):
                not_count += 1
                print('当前找到数量: '+str(not_count)+' 文件为: '+fbx_path)
                fbx_file = re.findall('/(.*)', fbx_path)
                # print('fbx_file: '+str(fbx_file[0]))
                w_file.write(str(fbx_file[0])+'\t'+file_info[0]+'\t'+file_info[1]+'\t'+file_info[2]+'\t'+
                             anim_author+'\n')
    w_file.close()


def find_md5_apk(md5_path):
    if not os.path.exists(md5_path):
        print(md5_path+' is not exist !!!')
    with codecs.open(md5_path, 'r', 'utf-8') as md_file:
        md5_content = md_file.read().strip().splitlines()

   #  dict = {}
    dict2 = {}

    file_count = 0
    for md5_item in md5_content:
        file_count += 1
        if file_count <= 1:
            continue
        file_info = md5_item.split('\t')
        file_split = file_info[1].split('; ')
        dict2[file_info[0]] = {'file_list': [], 'file_size': file_info[2]}
        for index, key in enumerate(file_split):
            if key != '':
                file_path = key.replace('../../', '')
                # dict[file_path.upper()] = {'file_path': file_path.strip(), 'md5': file_info[0], 'file_size': file_info[2], 'download': ''}
                dict2[file_info[0]]['file_list'].append(file_path.strip())
    return dict2


def save_parse_dict(parse_path):
    file_dict = {}
    if os.path.exists(parse_path):
        parse_content = codecs.open(parse_path, 'r', 'utf-8')
        for file_item in parse_content:
            file_info = file_item.split('\t')
            file_dict[file_info[0].upper()] = {'file_path': file_info[0].strip(), 'download': file_info[5].strip()}
    return file_dict


def save_result(md5_dict, file_dict, result_path):
    w_file = codecs.open(result_path, 'w', 'utf-8')
    w_file.write(u'md5值\t文件名\t大小\t下载方式\n')

    for md5, value in md5_dict.items():
        for index, file in enumerate(md5_dict[md5]['file_list']):
           # if file != '':
            if file.upper() in file_dict:
                w_file.write(md5+'\t'+file+'\t'+value['file_size']+'\t'+file_dict[file.upper()]['download']+'\n')
            w_file.write(md5+'\t'+file+'\t'+value['file_size']+'\n')

    w_file.close()


if __name__ == '__main__':
    path = r'D:\Users\Desktop\work_file\work\confgcheck\CaseMD51.tab'
    parse_path = r'D:\Users\Desktop\work_file\work\confgcheck\parseFile.tab'
    result_path = r'D:\Users\Desktop\work_file\work\confgcheck\CaseMD52.tab'
    md5_dict = find_md5_apk(path)
    file_dict = save_parse_dict(parse_path)
    for key, value in md5_dict.items():
        print(str(key) + ' '+str(value))
    save_result(md5_dict, file_dict, result_path)
   #  compare_parse(dict, parse_path, result_path)

    # svn_file = r'E:\NewPackageAnalysize\svn_file.tab'
    # export_path = r'E:\NewPackageAnalysize\export.tab'
    # out_path = 'E:/jx3m/AnimationFBX'
    # out_result = r'E:\NewPackageAnalysize\fbx.tab'
    # svn_path_dict = sve_svn_path(svn_file)
    #
    # find_not_fbx(export_path, out_result, out_path, svn_path_dict)





