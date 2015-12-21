# coding: utf8
import requests
import time
import re
import sys
import os
import getopt
from pyquery import PyQuery as pq
from tornado import gen
from tornado.queues import Queue
from tornado.ioloop import IOLoop
from tornado.process import cpu_count

_domain = 'segmentfault.com'
target_url = 'http://%s' % _domain
login_page_path = '/user/login'
login_api_path = '/api/user/login'
blog_path = '/blog/quietin'
edit_suffix = '/edit'
headers = {'Referer': target_url + '/'}


class PageHtmlChanged(Exception):
    pass


class BlogSavePathError(Exception):
    pass


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

    @staticmethod
    def get_token_from_html(content):
        overall_pat = re.compile(r'SF.token =.*?,\s+_\w+ = [\d,\[\]]+;',
                                 re.DOTALL)
        overall_res = overall_pat.search(content)
        if overall_res:
            overall_content = overall_res.group()
            # remove /* */ type annotation
            filter_res = re.sub(r"(/\*[/a-zA-Z\d' ]+\*/)", '', overall_content)
            str_list = re.findall(r"(?<!//)'([a-zA-Z\d]+)'", filter_res,
                                  re.DOTALL)
            filter_list = re.findall(r'\[(\d+),(\d+)\]', overall_content)
            ret = ''.join(str_list)

            if filter_list:
                for m, n in filter_list:
                    ret = ret[0:int(m)] + ret[int(n):]
            if len(ret) == 32:
                return ret

        raise PageHtmlChanged('website login token has changed')

    def _get_user_cookies(self):
        s = requests.Session()
        s.headers.update(headers)
        rep = s.get(target_url)
        post_url = "%s%s?_=%s" % (target_url, login_api_path,
                                  self.get_token_from_html(rep.text))
        data = {
            'mail': self.username,
            'password': self.passwd,
        }
        s.post(post_url, data=data)
        return s.cookies

    def __init__(self, **conf):
        self.username = conf['username']
        self.passwd = conf['passwd']
        self.save_path = conf.get('save_path')
        self._q = Queue()
        self._cookies = self._get_user_cookies()
        self._parse_save_path()

    @gen.coroutine
    def run(self):
        start_url = target_url + blog_path
        yield self._fetch_blog_list_page(start_url)
        for _ in xrange(cpu_count()):
            self._fetch_essay_content()

        yield self._q.join()

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
                real_file_name = os.path.join(self.save_path, title + '.md')
                logger.info("is backup essay: %s" % title)
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
        's:h:u:p:',
        ['save_path=', 'username=', 'passwd='])

    for opt, value in opts:
        if opt in ['-u', '--username']:
            config['username'] = value
        elif opt in ['-p', '--passwd']:
            config['passwd'] = value
        elif opt in ['-s', '--save_path']:
            config['save_path'] = value
        elif opt in ['-h', '--help']:
            usage()
            sys.exit()

    with TimeCalculate():
        ins = BlogBackup(**config)
        logger.info('Backup start!')
        yield ins.run()
        logger.info('Backup finished!')


class TimeCalculate(object):
    def __enter__(self):
        self.start = time.time()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end = time.time()
        logger.info("Elapsed time: {:.2f}s".format(self.end - self.start))


def usage():
    print '''
    用法：python blogbackup.py -u [USERNAME] -p [PASSWORD]
    -h --help 帮助
    -u --username [USERNAME] 用户名
    -p --passwd [PASSWORD] 密码
    -s --save_path [save path] 博文保存的文件夹路径
    '''


if __name__ == '__main__':
    import logging

    logging.basicConfig(level=logging.WARN, format="%(message)s")
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    IOLoop.current().run_sync(main)
