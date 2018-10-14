#!/usr/bin python

# Authors: Boretto Luca    <luca.boretto@studenti.polito.it>
#          Carta   Loris   <loris.carta@studenti.polito.it>
#          Jarvand Aysan   <aysan.jarvand@studenti.polito.it>
#		   Toscano Alessia <alessia.toscano@studenti.polito.it>

import json
import logging
import sys
import time
import telepot
import requests
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
import json
import shutil
import os
import datetime


class RefrigeratorBOT(object):
	def __init__(self,TOKEN,img_TOKEN,CATALOG,WS_products_url):
		self.TOKEN=TOKEN
		self.bot = telepot.Bot(TOKEN)
		self.img_TOKEN=img_TOKEN.encode()
		self.CATALOG=CATALOG
		self.PRODUCTS=WS_products_url

		self.keyboard = InlineKeyboardMarkup(inline_keyboard=[
					   [InlineKeyboardButton(text='Register', callback_data='/register')],
					   [InlineKeyboardButton(text='Login', callback_data='/login')]
				   ])
		self.keyboard2 = InlineKeyboardMarkup(inline_keyboard=[
					   [InlineKeyboardButton(text='Photo', callback_data='/photo')],
					   [InlineKeyboardButton(text='Temperature', callback_data='/temperature')],
					   [InlineKeyboardButton(text='Humidity', callback_data='/humidity')],
					   [InlineKeyboardButton(text='Motion', callback_data='/motion')],
					   [InlineKeyboardButton(text='Weight', callback_data='/weight')],
					   [InlineKeyboardButton(text='List of products', callback_data='/products')],
					   [InlineKeyboardButton(text='Enable Tempeature Allarm', callback_data='/enable_allarm')],
					   [InlineKeyboardButton(text='Disable Temperature Allarm', callback_data='/disable_allarm')]
				   ])
		self.data={}
		self.s={}
		
	def start(self):
		MessageLoop(self.bot, {'chat': self.on_chat_message,
				  'callback_query': self.on_callback_query}).run_as_thread()
		print('Listening ...')
		
	def on_chat_message(self,msg):
		content_type, chat_type, chat_id = telepot.glance(msg)

		if chat_id in list(self.data.keys()):
			if '/register' in list(self.data[chat_id].keys()):
				if self.data[chat_id]['/register']['username']==None and self.data[chat_id]['/register']['password']==None:
					self.data[chat_id]['/register']['username']=msg['text']
					self.bot.sendMessage(chat_id, text='password:')
					
				elif self.data[chat_id]['/register']['username']!=None and self.data[chat_id]['/register']['password']==None:
					self.data[chat_id]['/register']['password']=msg['text']
					self.s[chat_id]=requests.Session()
					r=self.s[chat_id].post(self.CATALOG+'/register',data=json.dumps({'user':self.data[chat_id]['/register']['username'],'password':self.data[chat_id]['/register']['password']}))
					if r.status_code == 200:
						r=self.s[chat_id].post(self.CATALOG+'/login',data=json.dumps({'user':self.data[chat_id]['/register']['username'],'password':self.data[chat_id]['/register']['password']}))
						r=self.s[chat_id].put(self.CATALOG+'/newcontact',data=json.dumps({'telegramID':chat_id}))
						if r.status_code == 200:
							self.bot.sendMessage(chat_id, text='Registration completed')
						else:
							self.bot.sendMessage(chat_id, text='Registration denied')
					else:
						self.bot.sendMessage(chat_id, text='Registration denied')
					del self.data[chat_id]['/register']
					
			if '/login' in list(self.data[chat_id].keys()):
				if self.data[chat_id]['/login']['username']==None and self.data[chat_id]['/login']['password']==None:
					self.data[chat_id]['/login']['username']=msg['text']
					self.bot.sendMessage(chat_id, text='password:')
					
				elif self.data[chat_id]['/login']['username']!=None and self.data[chat_id]['/login']['password']==None:
					self.data[chat_id]['/login']['password']=msg['text']
					self.s[chat_id]=requests.Session()
					r=self.s[chat_id].post(self.CATALOG+'/login',data=json.dumps({'user':self.data[chat_id]['/login']['username'],'password':self.data[chat_id]['/login']['password']}))
					if r.status_code == 200:
						self.bot.sendMessage(chat_id, "Logged as "+ self.data[chat_id]['/login']['username'], reply_markup=self.keyboard2)
					else:
						self.bot.sendMessage(chat_id, "Login failed")
				else:
					self.bot.sendMessage(chat_id, "", reply_markup=self.keyboard2)
		else:
			self.bot.sendMessage(chat_id, "SmarRefrigerator: use the menu' to do what you want", reply_markup=self.keyboard)

	def on_callback_query(self,msg):

		query_id, chat_id, query_data = telepot.glance(msg, flavor='callback_query')

		print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"- "+'Callback Query:', query_id, chat_id, query_data)

		if(query_data == '/register' or query_data == '/login'):
			self.data[chat_id]={}
			self.data[chat_id][query_data]={}
			self.data[chat_id][query_data]['username']=None
			self.data[chat_id][query_data]['password']=None
			self.data[chat_id][query_data]['status']=None
			self.bot.sendMessage(chat_id, text='username:')
			
		elif(query_data == '/photo'):
			r=self.s[chat_id].get(self.CATALOG+'/devices')
			devices=json.loads(r.text)['devices']["devices"]
			user=self.data[chat_id]['/login']['username']
			url=None
			for dev in devices:
				if dev["resources"]=="image" and dev["protocol"]=="REST":
					url=dev["endpoints"]
			print(url)
			r = requests.get(url, stream=True)
			address='img/'+user+'.png'
			with open(address, 'wb') as out_file:
				shutil.copyfileobj(r.raw, out_file)
			#del r
			foto=open(address, 'rb')
			bot2=telepot.Bot(self.img_TOKEN)
			bot2.sendPhoto(chat_id=chat_id, photo=foto)

		
		elif(query_data == '/temperature'):
			field='1'
			r=self.s[chat_id].get(self.CATALOG+'/contacts')
			thingspeak=json.loads(r.text)['contacts']['contacts']
			chID=thingspeak["thingspeak_chID"].encode()
			n_samples='100'
			p={'api_key':thingspeak["thingspeak_rkey"],'results':n_samples}
			r=self.s[chat_id].get('https://api.thingspeak.com/channels/'+chID+'/fields/'+field+'.json?',params=p)
			try:
				feeds=json.loads(r.text)['feeds']
				ind=-1
				for j,sample in enumerate(feeds):
					if sample["field"+field] is not None:
						ind=j
				if ind==-1:
					n_samples=str(json.loads(r.text)["channel"]["last_entry_id"])
					p={'api_key':thingspeak["thingspeak_rkey"],'results':n_samples}
					r=self.s[chat_id].get('https://api.thingspeak.com/channels/'+chID+'/fields/'+field+'.json?',params=p)
					feeds=json.loads(r.text)['feeds']
					ind=-1
					for j,sample in enumerate(feeds):
						if sample["field"+field] is not None:
							ind=j
				Temperature=str(json.loads(r.text)['feeds'][ind]['field'+field].encode('utf-8'))
				self.bot.sendMessage(chat_id, text='Temperature is: ' + Temperature + ' C')
				self.bot.sendMessage(chat_id, text="https://thingspeak.com/channels/"+chID+"/charts/"+field)
			except:
				self.bot.sendMessage(chat_id, text="Data not avaliable")
		elif(query_data == '/humidity'):
			field='2'
			r=self.s[chat_id].get(self.CATALOG+'/contacts')
			thingspeak=json.loads(r.text)['contacts']['contacts']
			chID=thingspeak["thingspeak_chID"].encode()
			n_samples='100'
			p={'api_key':thingspeak["thingspeak_rkey"],'results':n_samples}
			r=self.s[chat_id].get('https://api.thingspeak.com/channels/'+chID+'/fields/'+field+'.json?',params=p)
			try:
				feeds=json.loads(r.text)['feeds']
				ind=-1
				for j,sample in enumerate(feeds):
					if sample["field"+field] is not None:
						ind=j
				if ind==-1:
					n_samples=str(json.loads(r.text)["channel"]["last_entry_id"])
					p={'api_key':thingspeak["thingspeak_rkey"],'results':n_samples}
					r=self.s[chat_id].get('https://api.thingspeak.com/channels/'+chID+'/fields/'+field+'.json?',params=p)
					feeds=json.loads(r.text)['feeds']
					ind=-1
					for j,sample in enumerate(feeds):
						if sample["field"+field] is not None:
							ind=j

				Humidity=str(json.loads(r.text)['feeds'][ind]['field'+field].encode('utf-8'))
				self.bot.sendMessage(chat_id, text="Humidity is: " + Humidity + '%')
				self.bot.sendMessage(chat_id, text="https://thingspeak.com/channels/"+chID+"/charts/"+field)
			except:
				self.bot.sendMessage(chat_id, text="Data not avaliable")
		elif(query_data == '/motion'):
			field='3'
			r=self.s[chat_id].get(self.CATALOG+'/contacts')
			thingspeak=json.loads(r.text)['contacts']['contacts']
			chID=thingspeak["thingspeak_chID"].encode()
			n_samples='100'
			p={'api_key':thingspeak["thingspeak_rkey"],'results':n_samples}
			r=self.s[chat_id].get('https://api.thingspeak.com/channels/'+chID+'/fields/'+field+'.json?',params=p)
			try:
				feeds=json.loads(r.text)['feeds']
				ind=-1
				for j,sample in enumerate(feeds):
					if sample["field"+field] is not None:
						ind=j
				if ind==-1:
					n_samples=str(json.loads(r.text)["channel"]["last_entry_id"])
					p={'api_key':thingspeak["thingspeak_rkey"],'results':n_samples}
					r=self.s[chat_id].get('https://api.thingspeak.com/channels/'+chID+'/fields/'+field+'.json?',params=p)
					feeds=json.loads(r.text)['feeds']
					ind=-1
					for j,sample in enumerate(feeds):
						if sample["field"+field] is not None:
							ind=j
				Motion=str(json.loads(r.text)['feeds'][ind]['field'+field].encode('utf-8'))
				self.bot.sendMessage(chat_id, text="Motion is: " + Motion)
				self.bot.sendMessage(chat_id, text="https://thingspeak.com/channels/"+chID+"/charts/"+field)
			except:
				self.bot.sendMessage(chat_id, text="Data not avaliable")
		elif(query_data == '/weight'):
			field='4'
			r=self.s[chat_id].get(self.CATALOG+'/contacts')
			thingspeak=json.loads(r.text)['contacts']['contacts']
			chID=thingspeak["thingspeak_chID"].encode()
			n_samples='100'
			p={'api_key':thingspeak["thingspeak_rkey"],'results':n_samples}
			r=self.s[chat_id].get('https://api.thingspeak.com/channels/'+chID+'/fields/'+field+'.json?',params=p)
			try:
				feeds=json.loads(r.text)['feeds']
				ind=-1
				for j,sample in enumerate(feeds):
					if sample["field"+field] is not None:
						ind=j
				if ind==-1:
					n_samples=str(json.loads(r.text)["channel"]["last_entry_id"])
					p={'api_key':thingspeak["thingspeak_rkey"],'results':n_samples}
					r=self.s[chat_id].get('https://api.thingspeak.com/channels/'+chID+'/fields/'+field+'.json?',params=p)
					feeds=json.loads(r.text)['feeds']
					ind=-1
					for j,sample in enumerate(feeds):
						if sample["field"+field] is not None:
							ind=j

				Weight=str(json.loads(r.text)['feeds'][ind]['field'+field].encode('utf-8'))
				self.bot.sendMessage(chat_id, text="Weight is: " + Weight +' g')
				self.bot.sendMessage(chat_id, text="https://thingspeak.com/channels/"+chID+"/charts/"+field)
			except:
				self.bot.sendMessage(chat_id, text="Data not avaliable")
				
		elif(query_data == '/products'):
			r=requests.get(self.PRODUCTS+'/products',params={'user':self.data[chat_id]['/login']['username']})
			self.bot.sendMessage(chat_id, text='List of product is:')
			products=json.loads(r.text)['products']
			for product in products:
				self.bot.sendMessage(chat_id, text=json.dumps(product))
			
		elif(query_data == '/enable_allarm'):
			r=self.s[chat_id].put(self.CATALOG+'/newcontact',data=json.dumps({'telegramID':chat_id}))		
			if r.status_code == 200:
				self.bot.sendMessage(chat_id, text="Allarm enabled - However you could need to start @RefrigeratorAllarm_bot to receive allarm")
			else:
				self.bot.sendMessage(chat_id, text="Error enabling allarm")
			
		elif(query_data == '/disable_allarm'):
			r=self.s[chat_id].put(self.CATALOG+'/newcontact',data=json.dumps({'telegramID':""}))		
			if r.status_code == 200:
				self.bot.sendMessage(chat_id, text="Allarm disabled")
			else:
				self.bot.sendMessage(chat_id, text="Error disabling allarm")

			


if __name__=='__main__':

	f=open('data/BOT_config.json')
	config=json.loads(f.read())
	
	TOKEN = config["TOKEN"]
	img_TOKEN=config["img_TOKEN"]
	CATALOG=config["WS_catalog"]["url"]
	catalog_user=config["WS_catalog"]["credentials"]["user"]
	catalog_password=config["WS_catalog"]["credentials"]["password"]
	WS_products_name=config["WS_products"]["name"]
	WS_products_url=None
	
	s=requests.Session()
	r=s.post(CATALOG+'/login',data=json.dumps({"user":catalog_user,"password":catalog_password}))
	while WS_products_url is None:
		r=s.get(CATALOG+'/microservices')
		microservices=json.loads(r.text)['microservices']["products"]
		for ms in microservices:
			if ms['microserviceID']==WS_products_name:
				WS_products_url=ms['endpoints']
		time.sleep(10)
	
	rbot=RefrigeratorBOT(TOKEN,img_TOKEN,CATALOG,WS_products_url)

	rbot.start()

	while 1:
		time.sleep(1)




