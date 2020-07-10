import os
import codecs
import json


class Compare:
    def __init__(self, file_1, file_2, out_path, flag):
        self.path1 = file_1
        self.path2 = file_2
        self.out_path = out_path
        self.flag = flag

    def reload(self):
        self.download_hot_list = self._load_download_hot_list()
        self.asset_hot_list = self._load_asset_hot_list()

    def _load_download_hot_list(self):
        download_hot_list = {}
        if os.path.exists(self.path1):
            file = codecs.open(self.path1, 'r', 'utf-8')
            data = json.load(file)

            for key, values in data.items():
                if key == self.flag:
                    for index, bundle in enumerate(values):
                        download_hot_list[bundle+'.assetBundle'] = {'bundle_count': 0, ''bundle_load': self.flag}
        return download_hot_list

    def _load_asset_hot_list(self):
        asset_hot_list = {}
        if os.path.exists(self.path2):
            with codecs.open(self.path2, 'r', 'utf-8') as file:
                file_content = file.read().strip().splitlines()
            for file in file_content:
                file_info = file.split('\t')
                if file_info[4] == self.flag:
                    asset_hot_list[file_info[0]] = {'bundle_size': file_info[1], 'bundle_count': 0, 'bundle_load': self.flag}
        return asset_hot_list

    def _compare_file(self):
        for key, value in self.download_hot_list.items():
            if key in self.asset_hot_list:
                self.asset_hot_list[key] = self.asset_hot_list[key]['bundle_count'] + 1

    def save_result_file(self):
        file = codecs.open(self.out_path+'/bundle.tab', 'w', 'utf-8')
        file.write(u'bundle_name\tbundle_size\tbundle_count\n')

        for bundle, bundle_info in self.asset_hot_list.items():
            file.write(bundle+'\t'+bundle_info['bundle_size']+'\t'+bundle_info['bundle_count']+'\n')

        file.close()


if __name__ == '__main__':
    file1 = ''
    file2 = ''
    out_path = ''

    compare = Compare(file1, file2)
