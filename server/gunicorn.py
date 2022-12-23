
import os
import gevent.monkey
gevent.monkey.patch_all()
import multiprocessing
 
 
#开发环境可以打开，生产环境可以
#debug = True  
 
#用于控制errorlog的信息级别，可以设置为debug、info、warning、error、critical
loglevel = 'debug'
 
#监听地址+端口
bind = "localhost:8081"
 
#定义日志存储
if not os.path.exists('log/'):
    os.makedirs('log/')
pidfile = "log/gunicorn.pid"
#访问日志
accesslog = "log/access.log"
#错误日志
errorlog = "log/debug.log"
 
#开启后台运行，默认值为False
daemon = True
 
#启动的进程数，推荐值为：CPU核数*2+1
workers = multiprocessing.cpu_count() // 2 
 
#指开启的每个工作进程的模式类型，默认为sync模式，也可使用gevent模式
worker_class = 'gevent'
