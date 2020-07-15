#coding=utf-8

import os
import re
import json
import codecs
import requests
import logging
import xml.etree.ElementTree as ET
from devide_model import AllSource_Item, AllSource_APK, AllSource_IPA

# BundleData.txt BundleDownLoad.txt build id 获取
# aba_bundle.json 从StreamingAssets获取

# 构造函数 BundleData.txt BundleDownLoad.txt aba_bundle.json out_path

# load BundleData.txt ---> _load_bundle_data ---> self.APK_DLC_OTHER

# load BundleDownLoad.txt ---> _load_bundle_download  ---> self.DOWNLOAD_FIRST

# load aba_bundle.json   ---> _load_aba_bundle --->  self.BUNDLE_INFO_DICT

# load installpacksize.txt ---> _load_package_file ---> self.PACKAGE_FILE_DICT

# installpacksize.txt 内容来自于 ---> http://10.11.10.86/download/resource_package/1591419425778/original/installpacksize.txt

# result: _save_file ---> parseFile.tab

# result: _save_bundle_file  --->  parseBundle.tab dlc.tab

# result: _save_scene_away ---> dlc.tab
QB_URL = 'http://j3m.rdev.kingsoft.net:8810'
QB_USERNAME = 'foranalyse'
QB_PASSWORD = 'anRes0756'
QB_REQUESTS = requests.Session()
QB_REQUESTS.auth = (QB_USERNAME, QB_PASSWORD)
RESOURCE_URL = 'http://10.11.10.86/download/resource_package'


class QB:
    def __init__(self, build_id, tree_flag, input_path, out_path):
        self.build_id = build_id
        self.input_path = input_path
        self.tree_flag = tree_flag
        # AssetsCageData
        self.ASSET_CACHE_PATH = {}
        # 用来转化文件路径为svn路径
        self.out_path = out_path
        self._reload()
        self._save_bundle_file()
        self._save_module_file()
        self._save_file()
        self._save_scene_away()

    def _reload(self):
        self.build_svn, self.build_time = self._load_build_info()
        self._load_asset_cache()
        self.APK_DLC_OTHER = self._load_bundle_data()
        self.BUNDLE_INFO_DICT = self._load_aba_bundle()
        if self.tree_flag == 'trunk':
            print('[QB_MODEL]: 全包资源分析')
            self.DOWNLOAD_FIRST_DLC = self._load_bundle_download()
            self._set_apk_dlc_other()
            # self.PACKAGE_FILE_DICT = self._load_package_file()
            self.PACKAGE_FILE_DICT = self._load_package_file1()
            self._save_package_file()
        elif self.tree_flag == 'tx_publish':
            print('[QB_MODEL]: 更新包资源分析')

    def _load_build_info(self):
        print('[QB_MODEL]：获取build_svn build_time')
        build_svn, build_time = None, None
        url = QB_URL + '/rest/builds/%d' % self.build_id
        print(url)
        req = QB_REQUESTS.get(url)
        if req.status_code != 200:
            logging.error(u'builds获取失败\nstatus_code=%d\n%s' % (req.status_code, url))
            return build_svn, build_time

        root = ET.fromstring(req.content)
        for item in root.iterfind('version'):
            build_svn = int(item.text)
        for item in root.iterfind('secretAwareVariableValues/entry'):
            if 'var_BuildInfo_UnixTimestampMillis' == item.findtext('string'):
                build_time = int(item.findtext('com.pmease.quickbuild.SecretAwareString/string'))
        return build_svn, build_time

    def _load_package_file(self):
        print('[QB_MODEL]：从installpacksize.txt文件获取数据--->package_file_dict')
        package_file_dict = {}
        file_message = self._load_file_message(self.input_path+'/installpacksize.txt')
        if file_message == '':
            logging.error('[QB_MODEL]：从installpacksize.txt文件获取失败!!!')
            return package_file_dict

        dir_path = ''
        for line_str in file_message.split('\n'):
            if not line_str:
                continue
            if re.match('^\.', line_str):
                dir_path = line_str.strip('./').split(':')[0]
            if re.match('^\-rw', line_str):
                line_data = re.split(r' +', line_str)
                length = len(line_data)
                if dir_path == '':
                    file_path = line_data[length - 1]
                else:
                    file_path = dir_path + '/' + line_data[length - 1]
                package_file_dict[file_path] = {'file_path': file_path, 'file_size': line_data[4]}

        return package_file_dict

    def _load_package_file1(self):
        print('[QB_MODEL]：ziplistfiles.txt文件获取数据--->package_file_dict')
        package_file_dict = {}
        file_message = self._load_file_message(self.input_path + '/ziplistfiles.txt')
        if file_message == '':
            logging.error('[QB_MODEL]：从installpacksize.txt文件获取失败!!!')
            return package_file_dict

        file_count = 0
        for file_item in file_message.splitlines():
            file_count += 1
            if file_count <= 3:
                continue
            if re.match(r'^-', file_item):
                # print(str(file_item))
                break
            file_info = re.sub(' +', '\t', file_item.strip())
            file_split = file_info.split('\t')
            file_length = len(file_split)
            if not file_split[file_length - 1].endswith('/'):
                package_file_dict[file_split[file_length - 1]] = {'file_size': file_split[0],
                                                                  'file_compress_size': file_split[2]}
        return package_file_dict

    # self.ASSET_CACHE_PATH = {'svn_path': file, 'file_lists': [file], 'revision': self.build_svn}
    def _load_asset_cache(self):
        print('[QB_MODEL]：从AssetCacheData.txt文件获取数据--->asset_cache_dict')
        asset_cache_dict = {}
        file_message = self._load_file_message(self.input_path+'/AssetCacheData.txt')

        if file_message == '':
            logging.error('[QB_MODEL]：AssetCacheData.txt文件获取失败!!!')
            return asset_cache_dict

        data = json.loads(file_message)
        for key, values in enumerate(data):
            if data[values]['productFileList']:
                for index, file in enumerate(data[values]['productFileList']):
                    self.ASSET_CACHE_PATH[file.upper()] = {'svn_path': data[values]['assetPath'],
                                                           'revision': self.build_svn}

    def _load_bundle_data(self):
        print('[QB_MODEL]：从BundleData.txt文件获取数据--->apk_dlc_other')
        apk_dlc_other = {}
        file_message = self._load_file_message(self.input_path+'/BundleData.txt')
        if file_message == '':
            logging.error('[QB_MODEL]：BundleData.txt文件获取失败!!!')
            return apk_dlc_other

        data = json.loads(file_message)
        count = 0
        download_type = ''

        for key, values in enumerate(data):
            count = count + 1
            if count < 2:
                continue
            key = values['name'] + '.assetBundle'
            load_from = values['downloadForm']
            if load_from == 0:
                download_type = 'Apk'
            elif load_from == 1:
                download_type = 'Dlc'
            elif load_from == 2:
                download_type = 'Unused'
            if values['includs']:
                for index, file in enumerate(values['includs']):
                    if file.upper() not in self.ASSET_CACHE_PATH:
                        self.ASSET_CACHE_PATH[file.upper()] = {'svn_path': file,
                                                               'revision': self.build_svn}
            apk_dlc_other[key] = download_type
        logging.info('Save APK_DLC_OTHER success!!!')
        return apk_dlc_other

    def _load_bundle_download(self):
        print('[QB_MODEL]：从BundleDownloadInfo.txt文件获取数据--->download_first_dlc')
        download_first_dlc = {}
        file_message = self._load_file_message(self.input_path+'/BundleDownloadInfo.txt')
        if not file_message:
            logging.error('[QB_MODEL]：BundleDownloadInfo.txt文件获取失败!!!')
            return download_first_dlc

        data = json.loads(file_message)
        for key, values in data.items():
            if key == 'HotUpdateList':
                for k, v in enumerate(values):
                    download_first_dlc[v+'.assetBundle'] = 'First'
            if key == 'DlcChapter':
                for k1, v1 in enumerate(values):
                    i = 0
                    for k2, v2 in v1.items():
                        if k2 == 'bundls':
                            while i < len(v1[k2]):
                                download_first_dlc[v2[i] + '.assetBundle'] = 'Dlc'
                                i = i + 1
        return download_first_dlc

    def _load_aba_bundle(self):
        print('[QB_MODEL]：从aba_bundle.json文件获取数据--->bundle_info_dict')
        bundle_info_dict = {}
        file_message = self._load_file_message(self.input_path+'/aba_bundle.json')
        if file_message == '':
            logging.error('[QB_MODEL]：aba_bundle.json文件获取失败!!!')
            return bundle_info_dict

        bundle_count = 0
        for bundle_item in file_message.split('\n'):
            bundle_count = bundle_count + 1
            bundle_item = bundle_item.strip()
            if bundle_item == '':
                break
            bundle_data = json.loads(bundle_item)

            if bundle_data['bundle'].find('\\') > 0:
                bundle_info = bundle_data['bundle'].split('\\')
                key = bundle_info[1]
            else:
                key = bundle_data['bundle']
            bundle_info_dict[key] = {'bundlesize': bundle_data['bundleSize'], 'compress': bundle_data['compress'],
                                     'fileCount': bundle_data['fileCount'], 'fileList': bundle_data['fileList']}
        return bundle_info_dict

    def _set_apk_dlc_other(self):
        print('[QB_MODEL]：获取重新set的APK_DLC_OTHER')
        for bundle, load_from in self.DOWNLOAD_FIRST_DLC.items():
            self.APK_DLC_OTHER[bundle] = load_from

    def _save_bundle_file(self):
        print('[QB_MODEL]：获取parseBundle.tab file')
        f_write = codecs.open(self.out_path+'/parseBundle.tab', 'w', 'utf-8')
        f_write.write('bundleName\tbundleSize\tbundleCompress\tfileCount\tLoadFrom\n')
        bundle_name = ''
        for bundle, bundle_message in self.BUNDLE_INFO_DICT.items():
            if bundle_name == bundle:
                continue
            f_write.write(
                str(bundle) + '\t' +
                str(bundle_message['bundlesize']) + '\t' +
                str(bundle_message['compress']) + '\t' +
                str(bundle_message['fileCount']) + '\t' +
                ('NULL' if bundle not in self.APK_DLC_OTHER else str(
                    self.APK_DLC_OTHER[bundle])) + '\n'
            )
            bundle_name = bundle
        logging.info('Save Bundle File Success!!!')

    def _save_file(self):
        print('[QB_MODEL]：获取parseFile.tab file')
        f_write = codecs.open(self.out_path + '/parseFile.tab', 'w', 'utf-8')
        f_write.write('fileName\tfileSize\tfile_mSize\tbundleName\tbundleSize\tLoadFrom\n')
        with codecs.open(self.out_path + '/parseBundle.tab', 'r', 'utf-8') as f:
            bundle_content = f.read().strip().splitlines()
        load_from = ''
        file_count = 0
        bundle_count = 0

        for bundle, bundle_message in self.BUNDLE_INFO_DICT.items():
            bundle_count = bundle_count + 1
            file_list = bundle_message['fileList']
            for file_info in file_list:
                key = file_info['f']
                if key != 'ABO':
                    file_count = file_count + 1
                    for line in bundle_content:
                        lineinfo = line.split('\t')
                        if lineinfo[0] == bundle:
                            load_from = lineinfo[4]
                    # print('write success count = ' + str(file_count))
                    f_write.write(file_info['f'] + '\t' + str(file_info['s']) + '\t' + str(file_info['ds']) + '\t'
                                  + bundle + '\t' + str(bundle_message['bundlesize']) + '\t'
                                  + load_from + '\t' + '\n')
        f_write.close()
        print('[QB_MODEL]：Save parseFile.tab Success')

    def _save_package_file(self):
        print('[QB_MODEL]：获取parsePackageFile.tab file')
        file_path = self.out_path + '/parsePackageFile.tab'
        p_file = codecs.open(file_path, 'w', 'utf-8')
        p_file.write('文件名\t文件大小(未解压)\t文件大小(解压后)\n')
        for file_path, file_list in self.PACKAGE_FILE_DICT.items():
            p_file.write(file_path.strip()+'\t'+file_list['file_compress_size']+'\t'+file_list['file_size']+'\n')
        p_file.close()

    def _save_scene_away(self):
        print('[QB_MODEL]：获取dlc.tab file')
        file_path = self.out_path+'/parseFile.tab'
        message = u'下载方式\t场景名\t文件大小(KB)\tbundle名\tbundle大小(KB)\n'
        d_file = codecs.open(self.out_path + '/dlc.tab', 'w', 'utf-8')
        d_file.write(message)
        if not os.path.exists(file_path):
            logging.error(file_path+' Not Exist!!!')
        with codecs.open(file_path, 'r', 'utf-8') as f:
            file_content = f.read().strip().splitlines()

        for index, file_item in enumerate(file_content):
            if index == 0:
                continue
            file_info = file_item.split('\t')
            if not file_info[0].endswith('.unity'):
                continue
            d_file.write(file_info[5]+'\t'+file_info[0]+'\t'+str(round(int(file_info[1])/1024, 4)) +
                         '\t' + file_info[3] + '\t' + str(round(int(file_info[4])/1024, 2))+'\n')
        d_file.close()

    def _save_module_file(self):
        print('[QB_MODEL]：获取module.tab file')
        file_path = self.out_path + '/module.tab'
        file = codecs.open(file_path, 'w', 'utf-8')
        file.write(u'模块\t类型\t文件名\n')
        for bundle_module, bundle_file_name in AllSource_Item.items():
            file.write(bundle_module + '\t' + 'bundle' +'\t' + bundle_file_name + '\n')
        for apk_module, apk_file_name in AllSource_APK.items():
            file.write(apk_module + '\t' + 'apk' + '\t' + apk_file_name + '\n')
        for ios_module, ios_file_name in AllSource_IPA.items():
            file.write(ios_module + '\t' + 'ios' + '\t' + ios_file_name + '\n')
        file.close()
        print('[QB_MODEL]：获取module.tab file success')

    @staticmethod
    def _load_file_message(file_path):
        if os.path.exists(file_path):
            with codecs.open(file_path, 'r', 'utf-8') as file:
                file_content = file.read().strip()
            return file_content
        else:
            return ''
