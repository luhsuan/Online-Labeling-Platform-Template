# -*-coding:utf-8 -*-

# from django.template.loader import get_template
# from django import template
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render_to_response
from django.template.loader import get_template
from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from pprint import pprint
from bs4 import BeautifulSoup as bs
from PlatformApp.models import dbconfig

import xml.parsers.expat
import datetime
import requests
import os.path
import MySQLdb
import string
import socket
import time
import json
import sys
import re
import os 


# 登入頁面 

def stop_word_setting(request):
	 #   抓projectID
	if 'projectID' not in request.session:
		return HttpResponseRedirect('/newproject/')
	
	if 'Userid' not in request.session:
		return HttpResponseRedirect('/login/')

	project_id = request.session['projectID']
	urid = request.session['Userid']

	return render_to_response('stop_word_setting.html', locals())

@csrf_exempt
def all_stop_word(request):

	project_id = request.session['projectID']

	conn = MySQLdb.connect(**dbconfig)
	x = conn.cursor()
	x.execute("""
			SELECT text 
			FROM stop_word 
			WHERE project_id = '%s' 
			AND delete_time is NULL """ % (project_id))
	allword = x.fetchall()
	# print(allword)
	conn.commit()

	
	return JsonResponse({"allword":allword})

@csrf_exempt
def search_stop_word(request):
	
	Word = request.POST.get("Word")
	Status = request.POST.get("Status")

	project_id = request.session['projectID']

	conn = MySQLdb.connect(**dbconfig)
	x = conn.cursor()
	
	print("使用者: ",Word)
	if Word != None and Status != None:

		
		Exist=False

		
		datetime=time.strftime("%Y-%m-%d %H:%M:%S")
		x.execute("""SELECT id FROM stop_word WHERE text='%s' 
			AND project_id='%s' AND delete_time is NULL """ 
			% (Word,project_id))
		allid=x.fetchall()
		l=len(allid)
		if l > 0 :
			Exist=True
		if l == 0:
			Exist=False
		
		conn.commit()

		return JsonResponse({"Exist":Exist})

@csrf_exempt
def add_stop_word(request):

	Word = request.POST.get("Word")
	Orig_Word = request.POST.get("Orig_Word")
	Status = request.POST.get("Status")

	if Word != None :

		project_id = request.session['projectID']

		conn = MySQLdb.connect(**dbconfig)
		x = conn.cursor()

		Exist=False
		datetime=time.strftime("%Y-%m-%d %H:%M:%S")
		print(Status)
		if Status=='modify' :
			print(Word)
			x.execute("""SELECT id FROM stop_word WHERE text='%s' 
				AND project_id='%s' AND delete_time is NULL """ 
				% (Word,project_id))
			alltime=x.fetchall()
			l=len(alltime)
	
			if l > 0 :
				Exist=True
		#若曾經存於db 新增word 	
			if l == 0 :
				Exist=False 
		#不存在db 刪除原word
				x.execute("""UPDATE stop_word 
						 SET delete_time='%s'
						 WHERE text='%s' 
						 AND project_id='%s' 
						 AND delete_time is NULL
		 				""" % (datetime, Orig_Word,project_id))
				conn.commit()
		#不存在db 新增word 	
				x.execute("""INSERT INTO stop_word (create_time,project_id,text)
						 VALUES ( '%s', '%s', '%s')
						""" % ( datetime,project_id, Word))
				conn.commit()
				x.execute("""UPDATE project 
						 SET status_id='6'
						 WHERE id='%s'
						""" % (project_id))
				conn.commit()
		#若不存在則新增 
		if Status=='add' :
			print(Word)
			x.execute("""SELECT create_time,delete_time FROM stop_word 
				WHERE text='%s' AND project_id='%s' 
				AND delete_time is NULL""" 
				% (Word,project_id))
			alltime=x.fetchall()
			l=len(alltime)
			if l > 0 :
				Exist=True
				Exist=Word+'已存在'

			if l == 0 :
				Exist=False
				x.execute("""INSERT INTO stop_word (create_time,project_id,text)
						 VALUES ( '%s', '%s', '%s')
						""" % ( datetime,project_id, Word))
				conn.commit()
				x.execute("""UPDATE project 
						 SET status_id='6'
						 WHERE id='%s'
						""" % (project_id))
				conn.commit()
				Exist=Word+' 新增成功'	


		conn.commit()

		return JsonResponse({"Exist":Exist})

@csrf_exempt
def delete_stop_word(request):

	Word = request.POST.get("Word")
	if Word != None :

		project_id = request.session['projectID']
		
		conn = MySQLdb.connect(**dbconfig)
		x = conn.cursor()

		a=0
		b=0
		Exist=False
		x.execute("""SELECT id FROM stop_word WHERE text='%s' 
			AND project_id='%s' AND delete_time is NULL """ 
			% (Word,project_id))
		alltime=x.fetchall()
		l=len(alltime)
		if l > 0 :
			Exist=True
			datetime=time.strftime("%Y-%m-%d %H:%M:%S")
			x.execute("""UPDATE stop_word 
						 SET delete_time='%s'
						 WHERE text='%s' 
						 AND project_id='%s' 
						 AND delete_time is NULL
		 				""" % (datetime, Word,project_id))

		else:
			Exist=False



		conn.commit()

		return JsonResponse({"Exist":Exist})