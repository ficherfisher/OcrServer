## flask

- 简介

Flask是一个使用Python编写的轻量级Web应用框架。基于Werkzeug WSGI(*PythonWeb服务器[网关](https://link.jianshu.com?t=http://baike.baidu.com/view/807.htm)接口（Python Web Server Gateway Interface，缩写为WSGI*)是Python应用程序或框架和Web服务器之间的一种接口，已经被广泛接受, 它已基本达成它的可移植性方面的目标)工具箱和Jinja2 模板引擎。 Flask使用BSD授权。 Flask也被称为“microframework”，因为它使用简单的核心，用extension增加其他功能。Flask没有默认使用的数据库、窗体验证工具。然而，Flask保留了扩增的弹性，可以用Flask-extension加入这些功能：ORM、窗体验证工具、文件上传、各种开放式身份验证技术。

- 搭建服务器API，设置post请求方式(合适传送json信息)

```python
@app.route('/ocr', methods=['GET', 'POST'])
def get_request():
    if request.method == "GET":
        return b"please use post method to access!"
    else:
        request_data = json.loads(request.get_data(as_text=True))
        result, status_code = authenticate.check_information(request_data)
        send_back_dicts["status_code"] = status_code
        send_back_dicts["result"] = result
        send_back_dicts["tips"] = config_tips[status_code]
        # print(json.dumps(send_back_dicts, indent=1))
        return json.dumps(send_back_dicts).encode()
```

- flask与authenticate模块API接口

```python
    def check_information(self, data_dict):
        check_label_tag = self.check_label(data_dict)
        if check_label_tag != "True":
            return "None", check_label_tag
        check_sign_tag = self.check_sign(data_dict)
        if check_sign_tag != "True":
            return "None", check_sign_tag
        ocr_result_dicts = self.__ocr_system.usage_text_sys(data_dict["picture_url"])
        import uuid
        nonce_redis = str(uuid.uuid4())
        insert_dicts = {
            "nonce": data_dict["nonce"], "access_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "picture_url": data_dict["picture_url"], "status": ocr_result_dicts['status'], 
            "ocr_result": ocr_result_dicts["text"]
            }
        self.__insert_database(user_name=data_dict["username"], insert_dicts=insert_dicts, nonce_redis=nonce_redis)
        return ocr_result_dicts["text"], ocr_result_dicts["status"]

```

## nginx

- 简介

**Nginx （engine x）是一个开源、高性能的 HTTP 和反向代理 Web 服务器，同时也提供了 IMAP/POP3/SMTP 服务”。**

首先，对 Web 服务器做一个简要说明：

Web 服务器一般指网站服务器，是指驻留于因特网上某种类型计算机的程序，可以向浏览器等 Web 客户端提供文档，也可以放置网站文件，让全世界浏览。可以放置数据文件，让全世界下载。

常见的 Web 服务器有: Apache、Nginx、微软的 IIS 和 Tomcat。比如当我启动 Nginx 服务后，服务监听服务器上的端口，当从外面访问这个 ip+ 端口 的地址时，我们能对应访问服务器上的某些静态文件，或者动态服务响应，对相应的 http 请求进行处理并返回某个结果。这样就是通过浏览器和 Web 服务器（也就是 Nginx ）进行交互。

Nginx 是由俄罗斯的工程师 Igor Sysoev 在 Rambler 集团任职系统管理员时利用业余时间所开发高性能 web 服务，官方测试 Nginx 能够支撑 5 万并发链接，并且 cpu、内存等资源消耗却非常低，运行非常稳定，所以现在很多知名的公司都在使用 Nginx 或者在此基础上进行了二次开发，包括淘宝、新浪、百度等。对于中小型企业而言，开源免费而又性能强大的 Nginx 必然也是首选，后续我们将看到一组统计数据来说明 Nginx 的应用之广泛。

- nginx 配置

```shell
worker_processes  1;
events {
    worker_connections  1024;
}
http {
    include       mime.types;
    default_type  application/octet-stream;

    sendfile        on;
    keepalive_timeout  65;
    upstream ocr{
        server localhost:8081;
    }
    upstream slt{
        server localhost:8082;
    }
    upstream fc{
        server localhost:8083;
    }
    server {
        listen       80;
        server_name  localhost;
        location /ocr {
            proxy_pass http://ocr;
	    proxy_set_header Host $host;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
        location /slt {
            proxy_pass http://slt;
	    proxy_set_header Host $host;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
        location /fc {
            proxy_pass http://fc;
            proxy_set_header Host $host;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
        error_page   500 502 503 504  /50x.html;
        location = /50x.html {
            root   html;
        }
    }
}

```

## gunicorn

- 简介

Gunicorn是一个unix上被广泛使用的高性能的Python WSGI UNIX HTTP Server。
和大多数的web框架兼容，并具有实现简单，轻量级，高性能等特点。

- 启动配置文件解析

```python

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
```

- 启动命令

```shell
gunicorn --config="gunicorn.py" run_ocr_flask:app

gunicorn --config="gunicorn.py" run_ocr_flask:app
```

>以gunicorn命令启动待配置的*.py文件，参数会全部传入argparse模块中。需要将argparse设置解析参数信息为模糊操作，自动忽略没有key的参数值。

- [联系作者]()