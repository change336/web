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
import orm
from coroweb import add_routes,add_static

def init_jinja(app,**kw):
	logging.info('init jinja2...')
	options = dict(
		autoescape = kw.get('autoescape',True),
		block_start_string = kw.get('block_start_string','{%'),
		block_end_string = kw.get('block_end_string','%}'),
		variable_start_string = kw.get('variable_start_string','{{'),
		variable_end_string = kw.get('variable_end_string','}}'),
		auto_reload = kw.get('auto_reload',True)
	)
	path = kw.get('path',None)
	if path is None:
		path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'templates')
		logging.info('set jinja2 template path:%s' % path)
		env = Environment(loader=FileSystemloader(path),**options)
		if filters is not None:
			for name,f in filters.items():
				env.filters[name] = f
		app['__templating__'] = env
		
async def logger_factory(app,handler):
	async def logger(request):
		logging.info('Request: %s %s' % (request.method,request.path))
		#await asyncio.sleep(0.3)
		return (await handler(request))
	return logger
	
async def data_factory(app,handler):
	async def parse_data(request):
		if request.method == 'POST':
			if request.content_type.startswith('application/json'):
				request.__data__=await request.json()
				logging.info('request json:%s' % str(request.__data__))
			elif request.content_type.startwith('application/x-www-form-urlencoded'):
				request.__data__=await request.post()
				logging.info('request form:%s' % str(request.__data__))
		return (await handle(request))
	return parse_data
	
async def response_factory(app,handler):
	async def response(request):
		logging.info('Response handle...')
		r = await handle(request)
		if isinstance(r,web.StreamResponse):
			return r
		if isinstance(r,bytes):
			resp = web.Response(body=r)
			resp.content_type = 'application/octet-stream'
			return resp
		if isinstance(r,str):
			if r.startwith('redirect:'):
				return web.HTTPFound(r[9:])
			resp = web.Response(body=r.encode('utf-8'))
			resp.content_type = 'text/html;charset=utf-8'
			return resp
		if isinstance(r,dict):
			template = r.get('__template__')
			if template is None:
				resp = web.Response(body=json.dumps(r,ensure_ascii=False,default=lambda o:o.__dict__).encode('utf-8'))
				resp.content_type = 'application/json;charset = utf-8'
				return resp
			else:
				resp = web.Response(body=app['__templating__'].get_template(template).render(**r).encode('utf-8'))
				resp.content_type = 'text/html;charset=utf-8'
				return resp
		if isinstance(r,int) and r>=100 and r <600:
			return web.Response(r)
		if isinstance(r,tuple) and len(r) ==2:
			t,m = r
			if isinstance(t,int) and t>=100 and t<600:
				return web.Response(t,str(m))
		#default:
		resp = web.Response(body=str(r).encode('utf-8'))
		resp.content_type = 'text/plain;charset=utf-8'
		return resp
	return response
	
def datetime_filter(t):
	delta = int(time.time() - t)
	if delta<60:
		return u'1分钟前'
	if delta<3600:
		return u'%s分钟前' % (delta//60)
	if delta<86400:
		return u'%小时前' % (delta//3600)
	if delta<608400:
		return u'天前' % (delta//86400)
	dt = datetime.fromtimestamp(t)
	return u'%s年%月%日' % (dt.year,dt.month,dt.day)
	


#def index(request):
	#return web.Response(body=b'<h1>Awesome</h1>')
#定义处理http请求的方法，等号后面的是响应返回的内容

async def init(loop):
#定义一个初始函数，函数作用是返回一个服务器对象
	await orm.creat_pool(loop,host='127.0.0.1',port=3306,user='www',password='www',db='awesome')
	app = web.Application(loop=loop,middlewares=[logger_factory,response_factory
	])
	init_jinja2(app,filters=dict(datetime=datetime_filter))
	app_routes(app,'handlers')
	add_static(app)

	#创建一个循环对象是消息循环的web应用对象
	#app.router.add_route('GET','/',index)
	#将浏览器通过GET方式传过来的对根目录的请求转发给index函数进行处理
	srv = await loop.create_server(app.make_handler(),'127.0.0.1',9000)
	#调用子协程，创建一个TCP服务器，绑定到“127.0.0.1：9000”socket,并返回一个服务器对象，用来监听这个端口
	logging.info('server started at http://127.0.0.1:9000...')
	#打印基本信息
	return srv
	
loop = asyncio.get_event_loop()
#loop是消息循环对象
loop.run_until_complete(init(loop))
#在消息循环中执行协程
loop.run_forever()
#持续监听