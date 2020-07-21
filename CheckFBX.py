import os
import re
import codecs


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

    w_file = codecs.open(out_result, 'w', 'utf-8')
    w_file.write(u'fbx\tanim_File\tanim_Size(Byte)\tanim_MomerySize(Byte)\n')
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
            # print('文件svn_file: '+svn_path_dict[file_info[0].upper()])
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
                w_file.write(str(fbx_file[0])+'\t'+file_info[0]+'\t'+file_info[1]+'\t'+file_info[2]+'\n')
    w_file.close()


if __name__ == '__main__':
    svn_file = r'E:\NewPackageAnalysize\svn_file.tab'
    export_path = r'E:\NewPackageAnalysize\export.tab'
    out_path = 'E:/jx3m/AnimationFBX'
    out_result = r'E:\NewPackageAnalysize\fbx.tab'
    svn_path_dict = sve_svn_path(svn_file)

    find_not_fbx(export_path, out_result, out_path, svn_path_dict)





