#coding=utf-8

import os
import codecs
import logging
from devide_model import AllSource_Item, AllSource_APK, AllSource_IPA, APK_IPA_Filter, Bundle_Name


# 计算结果
# 构造函数 out_path package_path package_flag(apk/ipa)
# result: _total_module_size  ---> Bundle_File_Total.tab apk_total.tab/ipa_total.tab
#         _total_download_bundle ---> DownLoad.txt
# package_flag:  self._divide = APK_PATH IPA_PATH

class Calc:
    def __init__(self, out_path, package_divide):
        self.out_path = out_path
        self.divide = {}
        if package_divide:
            if package_divide == 'apk':
                print('[Calc_Model]：匹配到apk包')
                self.title1 = 'Apk'
                self.title2 = '/apk_total.tab'
                self.divide = AllSource_APK
            elif package_divide == 'ipa':
                print('[Calc_Model]：匹配到ipa包')
                self.title1 = 'Ipa'
                self.title2 = '/ipa_total.tab'
                self.divide = AllSource_IPA
            self._total_module_package_size()
            self._total_download_bundle()
        else:
            self._total_module_update_size()

    # bundle 去除重复
    def _total_module_package_size(self):
        print('[Calc_Model]：获取全包Bundle_File_Total.tab and apk_total.tab or ipa_total.tab')
        w_file = codecs.open(self.out_path + '/Bundle_File_Total.tab', 'w', 'utf-8')
        w_file.write(Bundle_Name[0] + '\t' + self.title1 + Bundle_Name[1] + '\t' + self.title1 + Bundle_Name[2] +
                     '\t' + Bundle_Name[4] + '\t' + Bundle_Name[5] +
                     '\t' + Bundle_Name[6] + '\t' + Bundle_Name[7] +
                     '\t' + Bundle_Name[8] + '\t' + Bundle_Name[9] +
                     '\t' + Bundle_Name[10] + '\t' + Bundle_Name[11] +
                     '\t' + Bundle_Name[12] + '\t' + Bundle_Name[13] + '\n')
        bundle_list = []
        for k, v in AllSource_Item.items():
            file_path = self.out_path + '/' + v + '.tab'
            print('[Calc_Model]：正在计算的文件'+file_path)
            if not os.path.exists(file_path):
                logging.error(file_path+'Not Exist!!!')
                continue
            with codecs.open(file_path, 'r', 'utf-8') as f:
                file_content = f.read().strip().splitlines()
            file_count = 0
            file_size = 0
            bundle_count = 0
            bundle_size = 0
            bundle_name = ''
            apk_count = 0
            apk_size = 0
            first_count = 0
            first_size = 0
            dlc_count = 0
            dlc_size = 0
            other_count = 0
            other_size = 0

            for index, file_item in enumerate(file_content):
                if index == 0:
                    continue
                file_info = file_item.split('\t')
                file_count = file_count + 1
                if file_info[2] != '文件大小(在bundle中的大小)':
                    file_size = file_size + int(file_info[2])
                if bundle_name != file_info[3]:
                    bundle_name = file_info[3]
                    if bundle_name not in bundle_list:
                        bundle_list.append(bundle_name)
                        if file_info[4] == 'bundle大小':
                            continue
                        bundle_size = bundle_size + int(file_info[4])
                        bundle_count = bundle_count + 1
                if file_info[5] == 'Apk':
                    apk_count = apk_count + 1
                    apk_size = apk_size + int(file_info[2])
                elif file_info[5] == 'Dlc':
                    dlc_count = dlc_count + 1
                    dlc_size = dlc_size + + int(file_info[2])
                elif file_info[5] == 'Unused':
                    other_count = other_count + 1
                    other_size = other_size + int(file_info[2])
                elif file_info[5] == 'First':
                    first_count = first_count + 1
                    first_size = first_size + int(file_info[2])

            w_file.write(k + '\t' + str(apk_count) + '\t' + str(round(apk_size/1024/1024, 2)) +
                         '\t' + str(first_count) + '\t' + str(round(first_size/1024/1024, 2)) +
                         '\t' + str(dlc_count) + '\t' + str(round(dlc_size/1024/1024, 2)) +
                         '\t' + str(other_count) + '\t' + str(round(other_size/1024/1024, 2)) +
                         '\t' + str(bundle_count) + '\t' + str(round(bundle_size/1024/1024, 2)) +
                         '\t' + str(file_count) + '\t' + str(round(file_size/1024/1024, 2)) + '\n')

        # 匹配分析
        if self.divide:
            z_file = codecs.open(self.out_path + self.title2, 'w', 'utf-8')
            z_file.write(u'模块\t文件数\t文件大小(未解压)\t文件大小(解压后)\n')
            for k, v in self.divide.items():
                file_path = self.out_path+'/'+v+'.tab'
                print('[Calc_Model]：正在计算的文件' + file_path)
                if not os.path.exists(file_path):
                    logging.error(file_path+' Not Exist!!!')
                    continue
                with codecs.open(file_path, 'r', 'utf-8') as f:
                    file_content = f.read().strip().splitlines()

                file_compress_size = 0
                file_count = 0
                for index, file_item in enumerate(file_content):
                    if index == 0:
                        continue
                    file_info = file_item.split('\t')
                    file_count = file_count + 1
                    if file_info[1] != '文件大小(未解压)':
                        file_compress_size = file_compress_size + int(file_info[1])
                    if file_info[2] != '文件大小(解压后)':
                        file_size = file_size + int(file_info[2])
                z_file.write(k + '\t' + str(file_count) + '\t' + str(round(file_compress_size/1024/1024, 2)) + '\t' +
                             str(round(file_size/1024/1024, 2)) + '\n')
                if k not in APK_IPA_Filter:
                    w_file.write(
                        k + '\t' + str(file_count) + '\t' + str(round(file_compress_size/1024/1024, 2)) + '\t' +str(0) +
                        '\t' + str(0) + '\t' + str(0) + '\t' + str(0) + '\t' + str(0) + '\t' + str(0) +
                        '\t' + str(0) + '\t' + str(0) + '\t' + str(0) + '\t' + str(0) + '\n')
            z_file.close()
        w_file.close()
        logging.info('[Calc_Model]: Total Success!!!')

    def _total_module_update_size(self):
        print('[Calc_Model]：获取更新包Bundle_File_Total.tab file')
        w_file = codecs.open(self.out_path+'/Bundle_File_Total.tab', 'w', 'utf-8')
        w_file.write(u'模块名\tbundle数\tbundle大小(MB)\t文件数\t文件总大小(MB)\n')
        bundle_list = []

        for k, v in AllSource_Item.items():
            file_path = self.out_path + '/' + v + '.tab'
            if os.path.exists(file_path):
                with codecs.open(file_path, 'r', 'utf-8') as f:
                    file_content = f.read().strip().splitlines()
                file_count = 0
                file_size = 0
                bundle_count = 0
                bundle_size = 0
                bundle_name = ''
                count = 0

                for file_item in file_content:
                    count = count + 1
                    if count == 1:
                        continue
                    file_count = file_count + 1
                    file_info = file_item.split('\t')
                    if file_info[2] != '文件大小(在bundle中的大小)':
                        file_size = file_size + int(file_info[2])
                    if len(file_info) > 2:
                        if file_info[3] != bundle_name:
                            bundle_name = file_info[3]
                            if bundle_name not in bundle_list:
                                bundle_list.append(bundle_name)
                                if file_info[4] == 'bundle大小':
                                    continue
                                bundle_size = bundle_size + int(file_info[4])
                                bundle_count = bundle_count + 1
                                bundle_name = file_info[3]

                w_file.write(k + '\t' + str(bundle_count) + '\t' + str(round(bundle_size/1024/1024, 2)) +
                             '\t'+str(file_count) + '\t' + str(round(file_size/1024/1024, 2)) + '\n')
        print('[Calc_Model]: 获取Bundle_File_Total.tab Success')
        w_file.close()

    def _total_download_bundle(self):
        logging.info('[Calc_Model]：D.txt')
        file_path = self.out_path+'/parseBundle.tab'
        w_file = codecs.open(self.out_path+'/DownLoad.txt', 'w', 'utf-8')
        if not os.path.exists(file_path):
            logging.error(file_path+' Not Exist!!!')
            w_file.close()
            return
        with codecs.open(file_path, 'r', 'utf-8') as f:
            file_content = f.read().strip().splitlines()
        apk_size = 0
        apk_count = 0
        dlc_size = 0
        dlc_count = 0
        first_size = 0
        first_count = 0
        other_size = 0
        other_count = 0
        for file_item in file_content:
            file_info = file_item.split('\t')
            if file_info[4] == 'Apk':
                apk_size = apk_size + int(file_info[1])
                apk_count = apk_count + 1
            elif file_info[4] == 'Dlc':
                dlc_size = dlc_size + int(file_info[1])
                dlc_count = dlc_count + 1
            elif file_info[4] == 'Unused':
                other_size = other_size + int(file_info[1])
                other_count = other_count + 1
            elif file_info[4] == 'First':
                first_size = first_size + int(file_info[1])
                first_count = first_count + 1
        w_file.write(
            u'apk下载大小(bundle下载量):' + str(round(apk_size / 1024 / 1024, 2)) + 'MB,bundle数目为: ' + str(apk_count) + '\n')
        w_file.write(u'首次更新下载大小(bundle下载量): ' + str(round(first_size / 1024 / 1024, 2)) + 'MB,bundle数目为: ' + str(
            first_count) + '\n')
        w_file.write(
            u'Dlc下载大小(bundle下载量): ' + str(round(dlc_size / 1024 / 1024, 2)) + 'MB,bundle数目为: ' + str(dlc_count) + '\n')
        w_file.write(u'Other下载大小(bundle下载量): ' + str(round(other_size / 1024 / 1024, 2)) + 'MB,bundle数目为: ' + str(
            other_count) + '\n')
        w_file.close()
        logging.info('[Calc_Model]: Total Success!!!')