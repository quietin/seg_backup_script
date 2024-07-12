# seg_backup_script
**Blog Backup Program**  

There are two versions: `backup_simple.py` uses only `requests` for login, while `backup_with_phantomjs` additionally utilizes `phantomjs`. The latter is more suitable for websites with dynamically generated content (such as Weibo) after further extension.

A blog backup script for the [segmentfault](http://segmentfault.com) website, written with Tornado and PhantomJS.  
PhantomJS simulates login, and Tornado's coroutine is used for concurrency.

# Usage:
To see usage:
```bash
python worker.py -h
