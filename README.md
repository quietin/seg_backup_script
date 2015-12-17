# segmentfault_blog_backup

用tornado和phantomjs写的[segmentfault](http://segmentfault.com)网站的博客备份脚本.  
phantomjs模拟登录，tornado的coroutine做并发.


# Usage：
查看用法：
```bash
python worker.py -h
```

文章默认保存在`worker.py`所在文件夹下的seg_blog_backup文件夹中，以**.md**后缀保存
```bash
python worker.py -u username -p passwd
```
  
非必选参数
- -s 保存文章的文件夹
- --phantomjs_path phantomjs的路径

