#coding=utf-8

import re
import subprocess
import collections
import  time
import xml.etree.ElementTree as ET


class SVN:
    # 只需要传入检查的版本控制路径
    def __init__(self, check_dir, username, password):
        self._check_dir = check_dir
        self._username = username
        self._password = password

    def _p_open_svn(self, cmd):
        if self._username is not None and self._password is not None:
            cmd += ' --username ' + self._username
            cmd += ' --password ' + self._password

        svn_cmd = self._get_cmd_message(cmd)
        # print('svn_cmd: '+svn_cmd)
        out_put_message = subprocess.Popen(svn_cmd, stdout=subprocess.PIPE, shell=True)
        # print('out+put_message: '+str(out_put_message))
        if out_put_message:
            message = out_put_message.stdout.read()
            return message

    # 返回值： tb = {'Revision': '670896', 'LastAuthor': 'a', 'LastDate':'xx-xx-xx'}
    def info(self, rel_path=None, revision=None):
        print('[SVN MODEL]: svn info')
        cmd = ''
        full_url_path = self._check_dir
        if rel_path:
            full_url_path += '/' + '\"' + rel_path + '\"'
            cmd += 'info ' + full_url_path

        if revision:
            cmd += ' -r ' + str(revision)
        result = {'path': '', 'url': '', 'repository root': '', 'relative-url': '', 'repository uuid': '',
                  'last change author': '', 'last change revision': '', 'last change date': ''}

        message = self._p_open_svn(cmd + ' --xml')
        root = ET.fromstring(message)
        for e in root.iter('entry'):
            for x in e.getchildren():
                if x.tag == 'url':
                    result['url'] = x.text
                elif x.tag == 'relative-url':
                    result['relative-url'] = x.text
                elif x.tag == 'commit':
                    result['last change revision'] = x.attrib['revision']
                for c in x.getchildren():
                    if c.tag == 'root':
                        result['repository root'] = c.text
                    if c.tag == 'uuid':
                        result['repository uuid'] = c.text
                    if c.tag == 'author':
                        result['last change author'] = c.text
                    if c.tag == 'date':
                        result['last change date'] = c.text
        return result

    # 返回值 返回当前文件的最后一条提交记录
    def log(self, rel_path=None, revision_from=None, revision_to=None, limit=None,
            stop_on_copy=False, use_merge_history=False):
        # print('[SVN MODEL]: svn log')
        full_url_path = self._check_dir
        if rel_path:
            if '@' in rel_path:
                print('[SVN MODEL]: file path 含有@字符 需要转义处理')
                rel_path = rel_path + '@'
            full_url_path += '/' + '\"' + rel_path + '\"'
            cmd = 'log ' + full_url_path
        if not revision_from:
            revision_from = '1'
        if not revision_to:
            revision_to = 'HEAD'
        cmd += ' -r '+str(revision_from) + ':' + str(revision_to)
        if limit:
            cmd += ' -l ' + str(limit)
        if stop_on_copy:
            cmd += ' --stop-on-copy '
        if use_merge_history:
            cmd += ' --use_merge_history'
        message = self._p_open_svn(cmd + ' --xml')
        result = []
        if 'logentry' in str(message):
            root = ET.fromstring(message)
            for e in root.iter('logentry'):
                entry_info = {x.tag: x.text for x in e.getchildren()}
                d = {'revision': e.attrib['revision'], 'author': entry_info['author'],
                     'date': entry_info['date'], 'msg': entry_info['msg']}
                result.append(d)
        return result

    def list(self, rel_path=None):
        print('[SVN MODEL]: svn list')
        full_url_path = self._check_dir
        if rel_path:
            full_url_path += '/' + '\"' + rel_path + '\"'
        doc = self._p_open_svn('ls ' + full_url_path)
        if doc and doc != '':
            print(doc)

    # 返回值 tb = {'Author': 'a'}
    def delete(self, path, username=None, password=None):
        print('[SVN MODEL]: svn delete')
        result_message = self.log(path, username, password)
        line = None
        tb_message = {}
        if result_message:
            tb_messages = result_message.split('Changed paths:')
            for index, value in enumerate(tb_messages):
                if re.search(r' D', value):
                    line = index
                    break
            print('line: '+str(line))
            tb_message['Author'] = tb_messages[line-1].split('|')[1].strip()
            return tb_message

    def first_submit(self, path):
        print('[SVN MODEL]: svn info first submit')
        result = {'revision':'NULL', 'author: ': 'NULL', 'date': 'NULL', 'number_message': 'NULL'}
        if path:
            doc = self.log(path)
            if doc and doc != '':
                tb_doc = doc.split('\n')
                result['revision'] = tb_doc[0]
                result['author'] = tb_doc[1]

    def last_submit(self, path, revision):
        # print('[SVN MODEL]: svn info last submit')
        doc = self.log(path)
        svn_message = {}
        if doc:
            for key, value in enumerate(doc):
                if int(value['revision']) <= revision:
                    svn_message = value
                else:
                    break
        return svn_message

    @staticmethod
    def _get_cmd_message(cmd):
        svn_cmd = 'svn ' + cmd
        return svn_cmd


















