# coding:utf-8
"""
create on Jan 22, 2021 By Wenyan YU
Email: ieeflsyu@outlook.com

Function:

因为搞自治域网络地理位置定位算法，涉及到大量数据爬取，数据太慢，需要借助异步非阻塞技术
调研了一圈，Tornado相当优秀，值得研究

Tornado有两种异步模式
1)add_callback。基于asyncio，资源消耗较少，性能还不错
2)run_in_executor。基于线程池/进程池，性能很好，但是资源消耗要高于add_callback的方案

"""
from tornado.ioloop import IOLoop, PeriodicCallback
import requests
import time
from concurrent.futures import ThreadPoolExecutor
import asyncio


HEADERS = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
   'Accept-Language': 'zh-CN,zh;q=0.8',
   'Accept-Encoding': 'gzip, deflate',}

URLS = ['http://www.cnblogs.com/moodlxs/p/3248890.html', 
        'https://www.zhihu.com/topic/19804387/newest',
        'http://blog.csdn.net/yueguanghaidao/article/details/24281751',
        'https://my.oschina.net/visualgui823/blog/36987',
        'http://blog.chinaunix.net/uid-9162199-id-4738168.html',
        'http://www.tuicool.com/articles/u67Bz26',
        'http://rfyiamcool.blog.51cto.com/1030776/1538367/',
        'http://itindex.net/detail/26512-flask-tornado-gevent',
        'http://www.cnblogs.com/moodlxs/p/3248890.html', 
        'https://www.zhihu.com/topic/19804387/newest',
        'http://blog.csdn.net/yueguanghaidao/article/details/24281751',
        'https://my.oschina.net/visualgui823/blog/36987',
        'http://blog.chinaunix.net/uid-9162199-id-4738168.html',
        'http://www.tuicool.com/articles/u67Bz26',
        'http://rfyiamcool.blog.51cto.com/1030776/1538367/',
        'http://itindex.net/detail/26512-flask-tornado-gevent',
        'http://www.cnblogs.com/moodlxs/p/3248890.html', 
        'https://www.zhihu.com/topic/19804387/newest',
        'http://blog.csdn.net/yueguanghaidao/article/details/24281751',
        'https://my.oschina.net/visualgui823/blog/36987',
        'http://blog.chinaunix.net/uid-9162199-id-4738168.html',
        'http://www.tuicool.com/articles/u67Bz26',
        'http://rfyiamcool.blog.51cto.com/1030776/1538367/',
        'http://itindex.net/detail/26512-flask-tornado-gevent',
        'http://www.cnblogs.com/moodlxs/p/3248890.html', 
        'https://www.zhihu.com/topic/19804387/newest',
        'http://blog.csdn.net/yueguanghaidao/article/details/24281751',
        'https://my.oschina.net/visualgui823/blog/36987']


# 业务逻辑操作
def job(id):
    """
    定义要干的事
    """
    # url = 'https://www.baidu.com/'
    # resp = requests.get(url)
    # print(resp.text)
    # file_write = 'D:/Code/Crawler4Caida/060Tornado/write_txt.txt'
    # with open(file_write, 'a', encoding="utf-8") as f:
    #     f.write(resp.text)
    time.sleep(3)
    print("job:", id, ", finish!")


def job_spider(url):
    headers = HEADERS
    headers['user-agent'] = "Mozilla/5.0+(Windows+NT+6.2;+WOW64)+AppleWebKit/537.36+(KHTML,+like+Gecko)+Chrome/45.0.2454.101+Safari/537.36"
    try:
        r = requests.get(url, allow_redirects=False, timeout=2.0, headers=headers)
    except:
        pass
    else:
        print(r.status_code, r.url)


# async def runner():
#     """
#     任务分发到异步非阻塞模型（Tornado）中
#     """
#     loop = IOLoop.current()
#     exctutor = ThreadPoolExecutor(1000)
#     tasks = []
#     # 此处开始任务分派
#     for job_id in range(1000):
#         task = loop.run_in_executor(exctutor, job, job_id)
#         tasks.append(task)

#     print('This will be excuted before loop finished.') 

if __name__ == '__main__':
    time_start = time.time()
    # IOLoop.current().run_sync(runner)
    loop = asyncio.get_event_loop()
    executor = ThreadPoolExecutor(1000)
    tasks = []
    for url in URLS:
        task = loop.run_in_executor(executor, job_spider, url)
        tasks.append(task)
    loop.run_until_complete(asyncio.wait(tasks))
    time_end = time.time()
    print("=>Scripts Finish, Time Consuming:", (time_end - time_start), "S")



