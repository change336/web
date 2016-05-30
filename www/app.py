#!/usr/bin/env python3
# -*- coding:utf-8 -*-

__author__='Michaelmakun'

'''
async web application
'''
#学习内容来自寥雪峰的博客
#http://www.liaoxuefeng.com/wiki/0014316089557264a6b348958f449949df42a6d3a2e542c000/00143217133614028a244ea855b40a586b551c616d3b2c9000


import logging;logging.basicConfig(level=logging.INFO)
#默认情况下，logging将日志打印到屏幕，日志级别为WARNING；
#日志级别大小关系为：CRITICAL > ERROR > WARNING > INFO > DEBUG > NOTSET，当然也可以自己定义日志级别
#简单说，logging的作用就是输出一些信息
#logging.basicConfig是一个函数，主要作用是对输出的信息及方式进行相关配置，这函数有很多参数，INFO指的是普通信息，INFO以及INFO以上的比如说WARNING警告信息也会被输出
#logging输出的信息可以帮助我们理解程序执行的流程，对后期除错也非常有帮助，下面是logging.basicConfig的一些参数，可以查阅
# logging.basicConfig(level=logging.INFO, 
                    # format='levelname:%(levelname)s filename: %(filename)s '
                           # 'outputNumber: [%(lineno)d]  thread: %(threadName)s output msg:  %(message)s'
                           # ' - %(asctime)s', datefmt='[%d/%b/%Y %H:%M:%S]',
                    # filename='./loggmsg.log')
 
# logging.info("hi,leon")
# logging.basicConfig函数各参数:
# filename: 指定日志文件名
# filemode: 和file函数意义相同，指定日志文件的打开模式，'w'或'a'
# format: 指定输出的格式和内容，format可以输出很多有用信息，如上例所示:
 # %(levelno)s: 打印日志级别的数值
 # %(levelname)s: 打印日志级别名称
 # %(pathname)s: 打印当前执行程序的路径，其实就是sys.argv[0]
 # %(filename)s: 打印当前执行程序名
 # %(funcName)s: 打印日志的当前函数
 # %(lineno)d: 打印日志的当前行号
 # %(asctime)s: 打印日志的时间
 # %(thread)d: 打印线程ID
 # %(threadName)s: 打印线程名称
 # %(process)d: 打印进程ID
 # %(message)s: 打印日志信息
# datefmt: 指定时间格式，同time.strftime()
# level: 设置日志级别，默认为logging.WARNING
# stream: 指定将日志的输出流，可以指定输出到sys.stderr,sys.stdout或者文件，默认输出到sys.stderr，当stream和filename同时指定时，stream被忽略

import asyncio,os,json,time
#asyncio内置了对异步IO的支持，os是操作系统模块，json是不同编程语言传递对象的标准格式，datetime是python处理日期和时间的标准库
from datetime import datetime

from aiohttp import web
#aiohttp是基于asyncio实现的HTTP框架,同时支持HTTP客户端和服务端,导入web函数
from jinja2 import Environment,FileSystemLoader
#Environment应该指的是jinja2模板的环境配置，FileSystemloader是文件加载器，用来加载模板路径
import orm
from coroweb import add_routes, add_static
#这个函数功能是初始化jinia2模板，配置jinja2的环境

def init_jinja2(app, **kw):
    logging.info('init jinja2...')
	#打印初始化jinja2的基本信息
	#设置解析模板需要用到的环境变量
    options = dict(
        autoescape = kw.get('autoescape', True),#不明所以，看别人说是自动转义xml/html的特殊字符（这是别的同学的注释，我不太明白具体指的是什么）
        block_start_string = kw.get('block_start_string', '{%'),#设置代码块起始字符串，下面那是结束字符串
        block_end_string = kw.get('block_end_string', '%}'),#意思就是{%和%}中间是python代码，而不是html，不明白，代码块是做什么用的
        variable_start_string = kw.get('variable_start_string', '{{'),#变量起始和结束字符串
        variable_end_string = kw.get('variable_end_string', '}}'),#就是说{{和}}中间是变量，看过templates目录下的test.html文件就很好理解了
        auto_reload = kw.get('auto_reload', True)#当模板文件被修改后，下次请求加载该模板文件的时候会自动重新加载修改后的模板文件
    )
    path = kw.get('path', None)   #从**kw中获取模板路径，如果没有拷入这个参数，默认为None
    if path is None:   #如果path为None，则将当前目录下的templates目录设置为模板文件的目录
		#下面这句代码其实就是三个步骤，先取当前文件所在目录文件，也就是app.py的绝对路径，然后取这个绝对路径的目录部分，最后在这个目录后面加上templates子目录
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    logging.info('set jinja2 template path: %s' % path)
	#loader=FileSystemLoader(path)指的是到哪个目录下加载模板文件，**options就是前面提到的option，用法和kw类似
    env = Environment(loader=FileSystemLoader(path), **options)
    filters = kw.get('filters', None)#过滤器？？？
    if filters is not None:
        for name, f in filters.items():
            env.filters[name] = f
    app['__templating__'] = env #前面已经把jinja2的环境配置都赋值给env，这里把env存入app的dict中，这样app就知道去哪找模板，怎么解析模板

#这个函数的作用就是当有http请求的时候，通过logging.info输出请求的信息，其中包括请求的方法和路径
async def logger_factory(app, handler):
    async def logger(request):
        logging.info('Request: %s %s' % (request.method, request.path))
        # await asyncio.sleep(0.3)
        return (await handler(request))
    return logger

#只有当请求方法是POST时这个函数才起作用，这会没用到，请求方法包括多种么？   
async def data_factory(app, handler):
    async def parse_data(request):
        if request.method == 'POST':
            if request.content_type.startswith('application/json'):
                request.__data__ = await request.json()
                logging.info('request json: %s' % str(request.__data__))
            elif request.content_type.startswith('application/x-www-form-urlencoded'):
                request.__data__ = await request.post()
                logging.info('request form: %s' % str(request.__data__))
        return (await handler(request))
    return parse_data

async def response_factory(app, handler):
    async def response(request):
        logging.info('Response handler...')
		#调用handler来处理url请求，并返回响应结果
        r = await handler(request)
        if isinstance(r,web.StreamResponse):
		#若响应结果为streamResponse，直接返回
		#StreamResponse是aiohttp定义response的基类，即所有响应类型都继承该类
		#StreamResponse主要为流式数据而设计，不懂
            return r
        # # 若响应结果为字节流,则将其作为应答的body部分,并设置响应类型为流型
        if isinstance(r,bytes):
            resp = web.Response(body=r)
            resp.content_type = 'application/octet-stream'
            return resp
         # 若响应结果为字符串
        if isinstance(r, str):
			# 判断响应结果是否为重定向.若是,则返回重定向的地址
            if r.startswith('redirect:'):
                return web.HTTPFound(r[9:])
			 # 响应结果不是重定向,则以utf-8对字符串进行编码,作为body.设置相应的响应类型
            resp = web.Response(body=r.encode('utf-8'))
            resp.content_type = 'text/html;charset=utf-8'
            return resp
		# 若响应结果为字典,则获取它的模板属性,此处为jinja2.env(见init_jinja2)
        if isinstance(r, dict):
            template = r.get('__template__')
			# 若不存在对应模板,则将字典调整为json格式返回,并设置响应类型为json
            if template is None:
                resp = web.Response(body=json.dumps(r, ensure_ascii=False, default=lambda o: o.__dict__).encode('utf-8'))
                resp.content_type = 'application/json;charset=utf-8'
                return resp
            # 存在对应模板的,则将套用模板,用request handler的结果进行渲染
            else:
                resp = web.Response(body=app['__templating__'].get_template(template).render(**r).encode('utf-8'))
                resp.content_type = 'text/html;charset=utf-8'
                return resp
		# 若响应结果为整型的
        # 此时r为状态码,即404,500等
        if isinstance(r, int) and r >= 100 and r < 600:
            return web.Response(r)
		# 若响应结果为元组,并且长度为2
        if isinstance(r, tuple) and len(r) == 2:
            t, m = r
			 # t为http状态码,m为错误描述
            # 判断t是否满足100~600的条件
            if isinstance(t, int) and t >= 100 and t < 600:
                return web.Response(t, str(m))
        # default:
		# 默认以字符串形式返回响应结果,设置类型为普通文本
        resp = web.Response(body=str(r).encode('utf-8'))
        resp.content_type = 'text/plain;charset=utf-8'
        return resp
    return response

def datetime_filter(t):
    delta = int(time.time() - t)
    if delta < 60:
        return u'1分钟前'
    if delta < 3600:
        return u'%s分钟前' % (delta // 60)
    if delta < 86400:
        return u'%s小时前' % (delta // 3600)
    if delta < 604800:
        return u'%s天前' % (delta // 86400)
    dt = datetime.fromtimestamp(t)
    return u'%s年%s月%s日' % (dt.year, dt.month, dt.day)


#def index(request):
#	return web.Response(body=b'<h1>Awesome</h1>')
#定义处理http请求的方法，等号后面的是响应返回的内容

# async def init(loop):
# #定义一个初始函数，函数作用是返回一个服务器对象
	# app = web.Application(loop=loop)
	# #创建一个循环对象是消息循环的web应用对象
	# app.router.add_route('GET','/',index)
	# #将浏览器通过GET方式传过来的对根目录的请求转发给index函数进行处理
	# srv = await loop.create_server(app.make_handler(),'127.0.0.1',9000)
	# #调用子协程，创建一个TCP服务器，绑定到“127.0.0.1：9000”socket,并返回一个服务器对象，用来监听这个端口
	# logging.info('server started at http://127.0.0.1:9000...')
	# #打印基本信息
	# return srv
	
#看到init记住就是初始化的意思，至于初始化什么玩意儿，我也说不太清楚
async def init(loop):
    #创建数据库连接池
    await orm.create_pool(loop=loop, host='127.0.0.1', port=3306, user='www-data', password='www-data', db='awesome')
    #middlewares翻译过来是中间件，factory是工厂，把request和response送进厂里改造一番再出来。好吧，是我瞎猜的，就当没看见。
    app = web.Application(loop=loop, middlewares=[
        logger_factory, response_factory
    ])
    #初始化jinja2模板，并传入时间过滤器
    init_jinja2(app, filters=dict(datetime=datetime_filter))
    #下面这两个函数在coroweb模块中，这里我就不注释了
    add_routes(app, 'handlers')#handlers指的是handlers模块也就是handlers.py
    add_static(app)
    #监听127.0.0.1这个IP的9000端口的访问请求
    srv = await loop.create_server(app.make_handler(), '127.0.0.1', 9000)
    logging.info('server started at http://127.0.0.1:9000...')
    return srv
	
loop = asyncio.get_event_loop()
#loop是消息循环对象
loop.run_until_complete(init(loop))
#在消息循环中执行协程
loop.run_forever()
#持续监听