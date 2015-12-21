# coding: utf8
import requests
import time
import sys
import os
import getopt
from selenium import webdriver
from selenium.common.exceptions import (
    WebDriverException, NoSuchElementException, TimeoutException)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import staleness_of
from pyquery import PyQuery as pq
from tornado import gen
from tornado.queues import Queue
from tornado.ioloop import IOLoop
from tornado.process import cpu_count

_domain = 'segmentfault.com'
target_url = 'http://%s' % _domain
login_page_path = '/user/login'
blog_path = '/blog/quietin'
edit_suffix = '/edit'


class PageHtmlChanged(Exception):
    pass


class BlogSavePathError(Exception):
    pass


class PhantomjsPathError(Exception):
    pass


def has_page_load(driver):
    return driver.execute_script("return document.readyState") == 'complete'


class BlogBackup(object):
    _default_dir_name = 'seg_blog_backup'

    def _generate_save_dir(self):
        cur_dir = os.path.dirname(__file__)
        self.save_path = os.path.join(cur_dir, self._default_dir_name)
        if not os.path.isdir(self.save_path):
            os.mkdir(self.save_path)

    def _parse_save_path(self):
        if self.save_path:
            if os.path.exists(self.save_path) and \
                    os.path.isdir(self.save_path):
                return
            else:
                raise BlogSavePathError(
                    "'%s' not exists or is not dir!" % self.save_path)
        else:
            self._generate_save_dir()

    def _get_user_cookies(self):
        url = target_url + login_page_path
        self.driver.get(url)
        try:
            user_input = self.driver.find_element_by_name('mail')
            passwd_input = self.driver.find_element_by_name('password')
            submit_btn = self.driver.find_element_by_class_name('pr20')
        except NoSuchElementException:
            raise PageHtmlChanged(
                "%s login page structure have changed!" % _domain)

        user_input.send_keys(self.username)
        passwd_input.send_keys(self.passwd)
        submit_btn.click()
        try:
            WebDriverWait(self.driver, 3).until(staleness_of(submit_btn))
        except TimeoutException:
            raise Exception("Wrong username or password!")

        WebDriverWait(self.driver, timeout=10).until(has_page_load)
        try_times = 0
        while True:
            time.sleep(1)
            if url != self.driver.current_url:
                return self.driver.get_cookies()

            try_times += 1
            if try_times > 10:
                raise Exception("Getting cookie info failed!")

    def _get_driver(self):
        if self.phantomjs_path:
            try:
                return webdriver.PhantomJS(
                    executable_path=self.phantomjs_path,
                    service_log_path=os.path.devnull)
            except WebDriverException:
                raise PhantomjsPathError("Phantomjs locate path invalid!")
        else:
            return webdriver.PhantomJS(service_log_path=os.path.devnull)

    def __init__(self, **conf):
        self.username = conf['username']
        self.passwd = conf['passwd']
        self.phantomjs_path = conf.get('phantomjs_path')
        self.save_path = conf.get('save_path')
        self._q = Queue()

        self._parse_save_path()
        self.driver = self._get_driver()
        self._cookies = self._get_user_cookies()

    @gen.coroutine
    def run(self):
        self.__filter_cookies()

        start_url = target_url + blog_path
        yield self._fetch_blog_list_page(start_url)
        for _ in xrange(cpu_count()):
            self._fetch_essay_content()

        yield self._q.join()

    def __filter_cookies(self):
        self._cookies = {k['name']: k['value'] for k in self._cookies if
                         k['domain'] == _domain}

    @gen.coroutine
    def _fetch_blog_list_page(self, page_link):
        ret = requests.get(page_link, cookies=self._cookies)
        d = pq(ret.text)
        link_elements = d('.stream-list__item > .summary > h2 > a')
        for link in link_elements:
            yield self._q.put(d(link).attr('href'))

        next_ele = d('.pagination li.next a')
        if next_ele:
            next_page_url = target_url + next_ele.attr('href')
            self._fetch_blog_list_page(next_page_url)

    @gen.coroutine
    def _fetch_essay_content(self):
        while True:
            try:
                essay_path = yield self._q.get(timeout=1)
                essay_url = target_url + essay_path + edit_suffix
                ret = requests.get(essay_url, cookies=self._cookies)
                d = pq(ret.text)
                title = d("#myTitle").val()
                content = d("#myEditor").text()
                file_name = title + '.md'
                real_file_name = os.path.join(self.save_path, file_name)
                with open(real_file_name, 'w') as f:
                    f.writelines(content.encode('utf8'))
            except gen.TimeoutError:
                raise gen.Return()
            finally:
                self._q.task_done()


@gen.coroutine
def main():
    config = {}
    opts, args = getopt.getopt(
        sys.argv[1:],
        'hs:u:p:',
        ['phantomjs_path=', 'save_path=', 'username=', 'passwd='])

    for opt, value in opts:
        if opt in ['-u', '--username']:
            config['username'] = value
        elif opt in ['-p', '--passwd']:
            config['passwd'] = value
        elif opt == '--phantomjs_path':
            config['phantomjs_path'] = value
        elif opt in ['-s', '--save_path']:
            config['save_path'] = value
        elif opt in ['-h', '--help']:
            usage()
            sys.exit()

    ins = BlogBackup(**config)
    yield ins.run()
    print 'finished!'


def usage():
    print '''
用法：python blogbackup.py -u [USERNAME] -p [PASSWORD] --phantomjs_path \
[phantomjs locate path]
-h --help 帮助
-u --username [USERNAME] 用户名
-p --passwd [PASSWORD] 密码
-s --save_path [save path] 博文保存的文件夹路径, 默认为本文件所在路径下的\
seg_blog_backup文件夹
--phantomjs_path  [phantomjs locate path] phantomjs所在路径, 如果其在PATH下可以\
找到则不必填
    '''


if __name__ == '__main__':
    IOLoop.current().run_sync(main)
