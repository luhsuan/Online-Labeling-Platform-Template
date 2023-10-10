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
from CKIP_python import CKIP_client
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

def seed_modify(request):

	#   抓projectID
	if 'projectID' in request.session:
		project_id = request.session['projectID']
	else:
		return HttpResponseRedirect('/newproject/')

	if 'Userid' in request.session:
		urid = request.session['Userid']
	else:
		return HttpResponseRedirect('/login/')

	return render_to_response('seed_modify.html', locals())

@csrf_exempt
def existed_seed(request):

	project_id = request.session['projectID']

	conn = MySQLdb.connect(**dbconfig)
	x = conn.cursor()

	x.execute("""
			SELECT text 
			FROM term 
			WHERE project_id = '%s' 
			AND delete_time is NULL """ % (project_id))
	allseed = x.fetchall()
	print(allseed)

	conn.commit()
	conn.close()

	return JsonResponse({"allseed":allseed})

@csrf_exempt
def show_seed_result2(request):
		
	Seed = request.POST.get("Seed")
	Status = request.POST.get("Status")
	project_id = request.session['projectID']
	
		
	if Seed != None:

		print("輸入:", Seed)
		conn = MySQLdb.connect(**dbconfig)
		x = conn.cursor()
# seed是否存在於資料表中
		l=0
		con_id=0
		ex_sent=''
		final_conid=''
		final_exsent=''	
		final_seed=[]
		may_seed=''
		exist=False
		state=''
# 尋找seed是否存在於資料表中
		x.execute("""
			SELECT concept_id, sentence 
			FROM term 
			WHERE text = '%s' AND project_id = '%s' AND delete_time is NULL """ % (Seed, project_id))
		allterm = x.fetchall()
		l = len(allterm)
		print("allterm = ", allterm)
# seed存在
		if l > 0 :
			exist = True
			con_id = allterm[0][0]	# concept_id
			final_exsent = allterm[0][1]	# sentence(舉例)
			print("是否存在db:是")
			x.execute("""
				SELECT Concept FROM concepttab 
				WHERE ConID = '%s' AND project_id='%s' 
				AND  delete_time is NULL
				""" % (con_id,project_id))
			final_conid = x.fetchall()
			print("是否存在db:是", final_conid,final_exsent)
		if l == 0 :
			exist = False
			print("是否存在db:否")
			

# seed存在 並要被刪除
		if l > 0 and Status == "delete" :
			datetime = time.strftime("%Y-%m-%d %H:%M:%S")
			x.execute("""
				UPDATE term
				SET delete_time='%s' WHERE text='%s' AND project_id='%s' 
				""" % (datetime,Seed,project_id))
			print("刪除成功")


# 搜尋資料表中有可能的seed
		# 表示term table中沒有輸入要查詢的seed 
		if l == 0 :
			state ="mayexist"

			maySeed="%"+Seed+"%"
			x.execute("""
				SELECT text 
				FROM term  WHERE text LIKE '%s' AND project_id='%s' 
				AND delete_time is NULL
				""" % (maySeed,project_id))
			eachseed = x.fetchall()	
			final_seed=eachseed

			print("最終seed:", final_seed)
	
		
		print("最終存在:", exist, " 狀態:", state)
		conn.commit()
		conn.close()

		return JsonResponse({
			"Exist": exist,
			"State": state,
			"MaySeed": final_seed,
			"Seed": Seed,
			"Concept": final_conid,
			"Sentence": final_exsent
			})


@csrf_exempt
def into_ckip(request):

	if 'projectID' in request.session:
		projectID = request.session['projectID']
		

	Seed = request.POST.get("Seed")
	Status = request.POST.get("Status")
	Concept = request.POST.get("Concept")
	Modify_orig = request.POST.get("Modify_orig")
	Sentence = request.POST.get("Sentence")
		


# 查找seedlog資料表是否已存在 
	text = Seed
	print("輸入:",text)
	conn = MySQLdb.connect(**dbconfig)
	x = conn.cursor()
# 先搜尋是否曾經有新增 修正 存在於資料表中
	allconcept=''
	conID=0
	concept_id=0
	sentence=''
	exist=False
	addseed=''
	delseed=''
	addnum=0
	delnum=0
	orignum=0
	orig_test=''
	test=''
	test_sent=''
# 是否存在於資料表中
	project_id = request.session['projectID']
	x.execute("""SELECT concept_id,sentence FROM term 
		WHERE text='%s' AND project_id='%s' 
		AND delete_time is NULL """ % (text,project_id))
	allseed = x.fetchall()
	l=len(allseed)
	if l > 0 :
		exist=True
		concept_id=allseed[0][0]
		sentence=allseed[0][1]
		print("存在:",concept_id,sentence)
	if l == 0 :
		exist=False
		print("不存在")
#新增 若不存在則丟進斷詞再新增 
	if exist == False and Status=='add':
		test="不存在 進入新增"
		x.execute("""SELECT Concept FROM concepttab 
			WHERE project_id='%s' AND  delete_time is NULL """ 
			% (project_id))
		allconcept=x.fetchall()
		# print(test)
		conn.commit()
		conn.close()
	if exist == False and Status == None :
	# seed 斷詞
		ckip_seed = CKIP_client.raw2ckip(text)
		l=len(ckip_seed[0])
		a=0
		while a < l :
			if a == l :
				break
			test+=ckip_seed[0][a]+' ('+ckip_seed[1][a]+') '
			a+=1
	# 例句斷詞
		ckip_sent = CKIP_client.raw2ckip(Sentence)
		l=len(ckip_sent[0])
		a=0
		while a < l :
			if a == l :
				break
			test_sent+=ckip_sent[0][a]+' ('+ckip_sent[1][a]+') '
			a+=1

		datetime=time.strftime("%Y-%m-%d %H:%M:%S")
		x.execute("""SELECT ConID FROM concepttab WHERE Concept='%s' 
			AND project_id='%s' AND  delete_time is NULL """ 
			% (Concept,project_id))
		conID=x.fetchall()
		
		x.execute("""
			INSERT INTO term(create_time, `text`, segment_text, concept_id, sentence, segmented_sentence, project_id)
			VALUES ('%s', '%s', '%s', '%d', '%s', '%s', '%s')
			""" % (datetime, text, test, conID[0][0], Sentence, test_sent, projectID))
		test=test+' ,Concept: '+Concept+' ,例句:'+Sentence+"--新增成功"
		conn.commit()
		conn.rollback()
		conn.close()

	if exist==True:
		test="Seed已存在 無法新增"
		# print(test)

	if Status=='modify' :
		x.execute("""SELECT Concept FROM concepttab WHERE project_id='%s' 
			AND  delete_time is NULL """ % (project_id))
		allconcept=x.fetchall()
		x.execute("""SELECT Concept FROM concepttab WHERE ConID='%s'
		    AND project_id='%s' AND  delete_time is NULL """ 
		    % (concept_id,project_id))
		con=x.fetchall()
		print(con)
		test=''
		test=text+" ,Concept為 ["+con[0][0]+"] ,例句為 <"+sentence+">--可修正"
		# print(test)

#修正 若存在且按鈕狀態為修正 丟進斷詞
	if exist == False and Status == 'modified' :
	# seed 斷詞
		ckip_seed = CKIP_client.raw2ckip(text)
		l=len(ckip_seed[0])
		a=0
		while a < l :
			if a == l :
				break
			test+=ckip_seed[0][a]+' ('+ckip_seed[1][a]+') '
			a+=1
	# 例句斷詞
		ckip_sent = CKIP_client.raw2ckip(Sentence)
		l=len(ckip_sent[0])
		a=0
		while a < l :
			if a == l :
				break
			test_sent+=ckip_sent[0][a]+' ('+ckip_sent[1][a]+') '
			a+=1
		conn = MySQLdb.connect(**dbconfig)
		x = conn.cursor()
		datetime=time.strftime("%Y-%m-%d %H:%M:%S")

		x.execute("""SELECT ConID FROM concepttab WHERE Concept='%s' 
			AND project_id='%s' AND  delete_time is NULL """ 
			% (Concept,project_id))
		conID=x.fetchall()
		x.execute("""
				UPDATE term
				SET delete_time='%s' WHERE text='%s' AND project_id='%s' 
				""" % (datetime,Modify_orig,project_id))
		print("刪除成功")
		conn.commit()
		x.execute("""
			INSERT INTO term(create_time, `text`, segment_text, concept_id, sentence, segmented_sentence, project_id)
			VALUES ('%s', '%s','%s', '%d', '%s', '%s','%s')
			""" % (datetime, text,test,conID[0][0],Sentence,test_sent,project_id))
		test=test+' ,Concept: '+Concept+' ,例句:'+Sentence+"--修正成功"
		conn.commit()
		conn.close()
	
	return JsonResponse({"Exist":exist,"Text":test,"Concept":allconcept})