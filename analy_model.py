#coding=utf-8

import re
import os
import codecs
import logging
from devide_model import MODULE_PATH, APK_PATH, IPA_PATH, AllSource_Item, AllSource_APK, AllSource_IPA


# 构造函数: file_path ----> parseFile.tab
#          package_path ---->

# analysis bundle parseFile.tab ----> Bundle_xxx_Data.tab
# parseFile.tab: fileName fileSize file_mSize bundleName bundleSize LoadFrom
# analysis package parsePackageFile.tab ----> Apk_xxx_Data.tab Ipa_xxx_Data.tab
# parsePackageFile.tab: fileName fileSize

class Analysis:
    def __init__(self, file_path, package_path=None):
        self.file_path = file_path
        self.package_path = package_path
        if self.package_path is not None:
            # 用在_analysis_divide_package函数中
            self._get_package_type()
            self._analysis_divide_bundle()
            self._analysis_divide_package()
        else:
            self._analysis_divide_bundle()

    def _analysis_divide_bundle(self):
        parent_path = os.path.dirname(self.file_path)
        print('[Analysis_Model]: 分析bundle资源')
        with codecs.open(self.file_path, 'r', 'utf-8') as f:
            file_content = f.read().strip().splitlines()
        values_exist = {}
        for index, fileItem in enumerate(file_content):
            if index < 1:
                continue
            file_info = fileItem.split('\t')
            # print('Current File count: ' + str(index - 1))
            ret = self.is_match(MODULE_PATH, file_info[0], 'bundle')
            for key, values in AllSource_Item.items():
                module_name = ret['module_name']
                if key != module_name:
                    continue
                f_write = codecs.open(parent_path + '/' + values + '.tab', 'a+', 'utf-8')
                if values not in values_exist:
                    values_exist[values] = True
                    f_write.write(u'文件名\t文件大小\t文件大小(在bundle中的大小)\tbundle名\tbundle大小\t下载方式\n')
                f_write.write(
                    file_info[0] + '\t' + str(file_info[1]) + '\t' + str(file_info[2]) + '\t' + file_info[
                        3] + '\t' + str(file_info[4]) + '\t' + file_info[5] + '\n')
                f_write.close()

        logging.info('Match Bundle File Info Success !!!')

    def _analysis_divide_package(self):
        parent_path = os.path.dirname(self.package_path)
        print('[Analysis_Model]: 分析package资源')
        with codecs.open(self.package_path, 'r', 'utf-8') as f:
            file_content = f.read().strip().splitlines()
        values_exist = {}
        for index, file_item in enumerate(file_content):
            if index == 0:
                continue
            file_info = file_item.split('\t')
            # print('Current File index: ' + str(index - 1))
            ret = self.is_match(self.divide, file_info[0], 'package')
            if file_info[0] == 'AndroidManifest.xml':
                print('AndroidManifest.xml'+ret['module_name'])
            for key, values in self._result_divide.items():
                module_name = ret['module_name']
                if key != module_name:
                    continue
                f_write = codecs.open(parent_path + '/' + values + '.tab', 'a+', 'utf-8')
                if values not in values_exist:
                    values_exist[values] = True
                    f_write.write(u'文件名\t文件大小(未解压)\n')
                f_write.write(file_info[0]+'\t'+str(file_info[1]+'\n'))
                f_write.close()
        logging.info('Match Package File Info Success !!!')

    def _get_package_type(self):
        print('[Analysis_Model]: 获取安装包类型信息')
        with codecs.open(self.package_path, 'r', 'utf-8') as f:
            file_content = f.read().strip().splitlines()

        for index, file_item in enumerate(file_content):
            if index == 0:
                continue
            file_info = file_item.split('\t')
            if file_info[0].strip() == 'AndroidManifest.xml':
                print('[Analysis_Model]: apk文件')
                self.divide = APK_PATH
                self._result_divide = AllSource_APK
                self.flag = 'apk'
            elif file_info[0].strip() == 'appsize_list.txt':
                print('[Analysis_Model]: IPA文件')
                self.divide = IPA_PATH
                self._result_divide = AllSource_IPA
                self.flag = 'ipa'

    @staticmethod
    def is_match(module_path, file_path, package_flag):
        ret_result = {'is_match': 0, 'module_name': ''}
        for module_name, file_item in module_path.items():
            for file_regex in file_item:
                if re.match(file_regex.upper(), file_path.upper()):
                    if module_name == u'lua文件':
                        if file_path.endswith('.lua'):
                            ret_result['is_match'] = 1
                            ret_result['module_name'] = module_name
                    elif module_name == u'shader文件':
                        if file_path.endswith('.shader'):
                            ret_result['is_match'] = 1
                            ret_result['module_name'] = module_name
                    elif module_name == u'cs文件':
                        if file_path.endswith('.cs'):
                            ret_result['is_match'] = 1
                            ret_result['module_name'] = module_name
                    elif module_name == u'bundle文件':
                        if file_path.endswith('.assetBundle'):
                            ret_result['is_match'] = 1
                            ret_result['module_name'] = module_name
                    else:
                        ret_result['is_match'] = 1
                        ret_result['module_name'] = module_name
                    break
        if ret_result['is_match'] == 0 and package_flag == 'bundle':
            ret_result['module_name'] = u'其他/Others(bundle)'
        elif ret_result['is_match'] == 0 and package_flag == 'package':
            ret_result['module_name'] = u'其他/Others(package)'
        return ret_result