# segmentfault_blog_backup

用tornado和phantomjs写的[segmentfault](http://segmentfault.com)网站的博客备份脚本


用法：
```bash
python worker.py -u username -p passwd
```
第一版，还需要完善，自己使用请改一下`save_path`，也就是保存博文内容的目录，默认以**.md**后缀保存

查看用法：
```bash
python worker.py -h
```
