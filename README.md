# seg_backup_script
**Blog Backup Program**  

A blog backup script for the [segmentfault](http://segmentfault.com) website, written with Tornado and PhantomJS.  
PhantomJS simulates login, and Tornado's coroutines are used for concurrency.

There are two version codes: `backup_simple.py` uses only `requests` for login, while `backup_with_phantomjs` additionally utilizes `phantomjs`. After further extension, the latter is more suitable for websites with dynamically generated content (such as Weibo).



# Usage:
To see usage:
```bash
python worker.py -h
