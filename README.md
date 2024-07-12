[中文版](https://github.com/quietin/seg_backup_script/blob/master/README_CN.md)

# seg_backup_script
**Blog Backup Program**  

A blog backup script for the [SegmentFault](http://segmentfault.com) website, written in Tornado and PhantomJS.  
PhantomJS simulates login, and Tornado's coroutines are used for concurrency.

There are two versions of the code: `backup_simple.py` uses only `requests` for login, while `backup_with_phantomjs` additionally utilizes PhantomJS. The latter is more suitable for websites with dynamically generated content (such as Weibo) after further extension.


# Usage:
To see usage:
```bash
python worker.py -h
