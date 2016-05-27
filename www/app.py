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

def index(request):
	return web.Response(body=b'<h1>Awesome</h1>')
#定义处理http请求的方法，等号后面的是响应返回的内容

async def init(loop):
#定义一个初始函数，函数作用是返回一个服务器对象
	app = web.Application(loop=loop)
	#创建一个循环对象是消息循环的web应用对象
	app.router.add_route('GET','/',index)
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