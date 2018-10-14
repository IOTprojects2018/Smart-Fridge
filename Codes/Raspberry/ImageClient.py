#!/usr/bin/env python3

# Authors: Boretto Luca    <luca.boretto@studenti.polito.it>
#          Carta   Loris   <loris.carta@studenti.polito.it>
#          Jarvand Aysan   <aysan.jarvand@studenti.polito.it>
#		   Toscano Alessia <alessia.toscano@studenti.polito.it>

import requests
import json
import base64
import shutil
import time
import os
import datetime

class GetDataFromWSCatalog:
	"""- GetDataFromWSCatalog: REST client for WebService Catalog"""
	
	def __init__(self,Catalog,user,password):
		self.Catalog=Catalog
		self.s=requests.Session()
		self.user=user
		self.password=password
		self.contacts={}
		self.microservices={}
		
	def start(self):
		# login to WebServiceCatalog
		logged=False
		while not logged:
			r=self.s.post(self.Catalog+'/login',data=json.dumps({'user':self.user,'password':self.password}))
			if r.status_code==200:
				logged=True
				print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"- "+"Access to WebService Catalog completed")
			else:
				print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"- "+"Error while login to WebService Catalog")
				time.sleep(10)
				
	def get_msgbroker(self):
		# get message broker from WebServiceCatalog
		r=self.s.get(self.Catalog+'/msgbroker')
		msgbr=json.loads(r.text)['msgbroker']
		return msgbr['IP'],msgbr['PORT']
			
	def get_microservices(self):
		# get microservices list from WebServiceCatalog
		r=self.s.get(self.Catalog+'/microservices')
		self.microservices=json.loads(r.text)['microservices']
		return self.microservices
					
	def get_contacts(self):
		# get users contacts from WebServiceCatalog
		r=self.s.get(self.Catalog+'/contacts')
		self.contacts=json.loads(r.text)['contacts']
		return self.contacts
	
	def get_ServerURL(self,name):
		url=None
		while url is None:
			microservices=self.get_microservices()
			for key in list(microservices.keys()):
				for ms in microservices[key]:
					if ms['microserviceID']==name:
						url=ms['endpoints']
			if url is None:			
				print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"- "+name + " address not found")
			time.sleep(10)
		print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"- "+name + " address found")
		return url

conf="data/config.json"
f=open(conf)
config=json.loads(f.read())
user=config["user"]
password=config["password"]
WSC_url=config["WebServiceCatalog"]


conf="data/cam_config.json"
f=open(conf)
config=json.loads(f.read())

IWS_url=config["ImageWebService"]
KEY=config["KEY"]
source=config["source"]
dims=config["dims"]
deviceID=config["deviceID"]
resource=config["resource"]
protocol=config["protocol"]
endpoints=IWS_url+'/img/'+user+'.png?key='+KEY



s=requests.Session()

OK=False
while not OK:
	try:
		r=s.post(WSC_url+'/login',data=json.dumps({"user":user,"password":password}))
		if r.status_code==200:
			print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"- "+"Access to WebService Catalog completed")
			OK=True
			
		else:
			print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"- "+"Wrong credentials")
	except:
		print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"- "+"WebService Catalog not avaliable at the moment")
	time.sleep(10)
	

while 1:
	
	os.system("fswebcam -r 1280x720 img/tmp.png")

	I=open('img/tmp.png', 'rb').read()
	I=base64.b64encode(I)
	I="".join( chr(x) for x in bytearray(I) )
	data = {'image': I,"user":user}
	
	if KEY=="":
		print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"- "+"Registering "+user+" on ImageWebService")
		r = requests.post(IWS_url+"/register", data=json.dumps(data))
		KEY=json.loads(r.text)["key"]
		config["KEY"]=KEY
		f=open(conf,'w')
		f.write(json.dumps(config))
		f.close()
	else:
		print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"- "+"Uploading "+user+"'s image on ImageWebService")
		r = requests.put(IWS_url+"/upload", params={"key":KEY},data=json.dumps(data))
		endpoints=IWS_url+'/img/'+user+'.png?key='+KEY

	print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"- "+"Putting "+user+"'s "+deviceID+ "information on WebService Catalog")
	s.put(WSC_url+'/newdevice',data=json.dumps({'deviceID':deviceID,'resources':resource,'endpoints':endpoints,'protocol':protocol}))

	time.sleep(10)
