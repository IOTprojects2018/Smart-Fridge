#!/usr/bin/env python3

# Authors: Boretto Luca    <luca.boretto@studenti.polito.it>
#          Carta   Loris   <loris.carta@studenti.polito.it>
#          Jarvand Aysan   <aysan.jarvand@studenti.polito.it>
#		   Toscano Alessia <alessia.toscano@studenti.polito.it>


import cherrypy
import json
import time
import os
import io
import socket
import threading
import datetime

class CatalogThread (threading.Thread):
	
	def __init__(self, threadID, name, config=None,age=None):
		threading.Thread.__init__(self)
		self.threadID=threadID
		self.name = name
		self.config=config
		self.age=age

	def run(self):
		print ("Thread#" + self.name + " started")
		if self.name=="CatalogWebService":
			cherrypy.quickstart(CatalogWebService(), '/', config=self.config)
		elif self.name=="refresh":
			self.dm=deviceManager()
			self.jm=JsonManager()			
			while 1:
				print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+" - Refreshing Catalog data")
				self.dm.clean(self.age)
				DB["number_of_devices"]=0
				for u in list(DB["devices"].keys()):
					DB["number_of_devices"]+=len(u[0])
				DB["last_edit"]=time.time()
				self.jm.write(DB,path)
				time.sleep(20)
		else:
			pass
		print ("Thread#" + self.name + " stopped")

def get_ip():
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	try:
		s.connect(('10.255.255.255', 1))
		IP = s.getsockname()[0]
	except:
		IP = '127.0.0.1'
	finally:
		s.close()
	return IP

class Auth(object):
	def __init__(self):
		pass
	def check(self,data):
		return list(data.keys())[0] in list(DB['users_list'].keys())
	def isRoot(self,credentials):
		return credentials['user']==ADMIN and credentials['password']==PSW

class Searcher(object):
	def __init__(self):
		pass

	def all_contacts(self,user):
		if user==ADMIN:
			tmp={}
			for u in list(DB['devices'].keys()):
				tmp[u]=DB['devices'][u][1]
			return tmp
		else:
			return {'contacts':DB['devices'][user][1]}
			
	def all_devices(self,user):
		if user==ADMIN:
			tmp={}
			for u in list(DB['devices'].keys()):
				tmp[u]=DB['devices'][u][0]
			return tmp
		else:
			return {'devices':DB['devices'][user][0]}
		
	def spec_device(self,user,param):
		key=list(param.keys())[0]
		value=list(param.values())[0]
		
		if user==ADMIN:
			output={}
			for u in list(DB['devices'].keys()):
				tmp=[]
				for dev in DB['devices'][u][0]:
					if dev[key]==value:
						tmp.append(dev)
				if len(tmp)>0:
					output[u]=tmp
		else:
			output=[]
			for dev in DB['devices'][user][0]:
				if dev[key]==value:
					output.append(dev)				
		return {'devices':output}
		
	def all_microservices(self):
		return {'microservices':DB['microservices']}
	
	def spec_microservice(self,param):
		key=list(param.keys())[0]
		value=list(param.values())[0]
		
		if key=='microserviceID':
			output=[]
			for c in list(DB['microservices'].keys()):
				for ms in DB['microservices'][c]:
					if ms[key]==value:
						output.append(ms)
		elif key=='category' and value in list(DB['microservices'].keys()):
			output=DB['microservices'][value]
		else:
			output=[]
				
		return {'microservices':output}
		
class deviceManager(object):
	def __init__(self):
		pass

	def add_device(self,user,device):
		DB['devices'][user][0].append(device)

	
	def remove_device(self,user,device):
		ind=None
		for i,dev in enumerate(DB['devices'][user][0]):
			if dev['deviceID']==device['deviceID']:
				ind=i
		if ind is not None:
			DB['devices'][user][0].pop(ind)

		
	def add_contacts(self,user,contacts):
		for key in list(contacts.keys()):				 
			DB['devices'][user][1][key]=contacts[key]
	
	def add_microservice(self,params):
		
		if params['category'] not in DB['microservices']:
			DB['microservices'][params['category']]=[]
		DB['microservices'][params['category']].append(params)
		
	def clean(self,age):
		t=time.time()
		
		for user in list(DB['devices'].keys()):
			ind=[]
			for j,dev in enumerate(DB['devices'][user][0]):
				if t-dev['timestamp']>age:
					ind.append(j)
			for j in sorted(ind, reverse=True):
				DB['devices'][user][0].pop(j)
				
class JsonManager(object):
	def __init__(self):
		pass
	def write(self,database,path):
		global semafor
		while not semafor:
			pass
		semafor=False
		f=open(path,'w')
		f.write(json.dumps(database))
		f.close()
		semafor=True
	def read(self,path):
		global semafor
		while not semafor:
			pass
		semafor=False
		f=open(path,'r')
		data=json.loads(f.read())
		f.close()
		semafor=True
		return data
		
@cherrypy.expose
class CatalogWebService(object):
	def __init__(self):
		
		self.auth=Auth()
		self.jm=JsonManager()
		self.s=Searcher()
		self.dm=deviceManager()
	
	def POST(self,*uri,**params):
		data=cherrypy.request.body.read()

		try:
			data=json.loads(data)
			if self.auth.isRoot(data):
				root=True
			else:
				root=False
			if len(data["user"])==0 or len(data['password'])==0:
				raise cherrypy.HTTPError(400)
			data={data['user']:data['password']}
		except:
			raise cherrypy.HTTPError(404)
		if len(uri)==1 and uri[0].lower()=='login' and params=={}:
			if not root:
				status=self.auth.check(data)
				if status and DB['users_list'][list(data.keys())[0]]==data[list(data.keys())[0]]:
					cherrypy.session['data']=data
					return 'Access Completed'
				else:
					cherrypy.session['data']=False
					raise cherrypy.HTTPError(401) # Access denied
			else:
				cherrypy.session['data']=data
				return 'Access Completed'	
		
		elif len(uri)==1 and uri[0].lower()=='register' and params=={}:

			status=self.auth.check(data)
			if status:
				raise cherrypy.HTTPError(409) # username already used (conflict)
			else:
				DB['users_list'][list(data.keys())[0]]=data[list(data.keys())[0]]
				DB['devices'][list(data.keys())[0]]=[[],{"telegramID": "","thingspeak_chID":"","thingspeak_rkey":"","thingspeak_wkey":""}]
				DB["last_edit"]=time.time()
				DB["number_of_users"]+=1
				self.jm.write(DB,path)
				return 'Registration Completed'
		else:
			raise cherrypy.HTTPError(404)

	def GET(self, *uri, **params):

		if 'data' not in list(cherrypy.session.keys()):
			raise cherrypy.HTTPError(401)
		
		if cherrypy.session['data'] and len(uri)==1 and uri[0].lower()=='devices':
			user=list(cherrypy.session['data'].keys())[0] 
			devices=self.s.all_devices(user)
			if params=={}:
				return json.dumps({"devices":devices})

			elif len(params)==1 and (list(params.keys())[0] in ['deviceID','resources']):
				devices=self.s.spec_device(user,params)
				if len(devices['devices'])>0:
					return json.dumps(devices)
				else:
					raise cherrypy.HTTPError(404)	# not found			
			else:
				raise cherrypy.HTTPError(400)
		
		elif cherrypy.session['data'] and len(uri)==1 and uri[0].lower()=='microservices':
			user=list(cherrypy.session['data'].keys())[0]
			if user!=ADMIN:
				raise cherrypy.HTTPError(401)
				
			microservices=self.s.all_microservices()
			if params=={}:
				return json.dumps(microservices)

			elif len(params)==1 and (list(params.keys())[0] in ['microserviceID','category']):
				microservices=self.s.spec_microservice(params)
				if len(microservices['microservices'])>0:
					return json.dumps(microservices)
				else:
					raise cherrypy.HTTPError(404)	# not found			
			else:
				raise cherrypy.HTTPError(400)

		elif cherrypy.session['data'] and len(uri)==1 and uri[0].lower()=='contacts' and params=={}:		
			user=list(cherrypy.session['data'].keys())[0]		
			contacts=self.s.all_contacts(user)
			return json.dumps({"contacts":contacts})			
					
		elif cherrypy.session['data'] and len(uri)==1 and uri[0].lower()=='msgbroker' and params=={}:
			return json.dumps({'msgbroker':DB['msgbroker']})
		else:
			raise cherrypy.HTTPError(401)
			
	def PUT(self,*uri,**params):
		if 'data' not in list(cherrypy.session.keys()):
			raise cherrypy.HTTPError(401)

		if cherrypy.session['data'] and len(uri)==1 and uri[0].lower()=='newdevice':
			data=json.loads(cherrypy.request.body.read())
			print(sorted(list(data.keys())))
			if sorted(list(data.keys()))==['deviceID','endpoints','protocol','resources']:	
			
				user=list(cherrypy.session['data'].keys())[0]	
				devices=self.s.all_devices(user)['devices']
			
				i=None
				for j,dev in enumerate(devices):
					if dev['deviceID']==data['deviceID']:
						i=j
				if i is not None:
					DB['devices'][user][0].pop(i)
					DB["number_of_devices"]-=1
					
				data['timestamp']=time.time()
				self.dm.add_device(user,data)
				DB["last_edit"]=time.time()
				DB["number_of_devices"]+=1
				self.jm.write(DB,path)
				return 'New device Added'
			else:
				raise cherrypy.HTTPError(400)				

		elif cherrypy.session['data'] and len(uri)==1 and uri[0].lower()=='newcontact':
			data=json.loads(cherrypy.request.body.read())
			if (False not in [i in ['telegramID','thingspeak_chID','thingspeak_rkey','thingspeak_wkey'] for i in list(data.keys())]):	 
				user=list(cherrypy.session['data'].keys())[0]						
				self.dm.add_contacts(user,data)
				DB["last_edit"]=time.time()				 
				self.jm.write(DB,path)
				return 'Conctact Added'
			else:
				raise cherrypy.HTTPError(400)
		
		elif cherrypy.session['data'] and len(uri)==1 and uri[0].lower()=='newmicroservice':
			data=json.loads(cherrypy.request.body.read()) 
			if sorted(list(data.keys()))==['category','endpoints','microserviceID','protocol']:
				
				user=list(cherrypy.session['data'].keys())[0]
				if user==ADMIN:
					microservices=self.s.all_microservices()['microservices']
					if data['category'] in list(microservices.keys()):
						check= [data['microserviceID']==ms['microserviceID'] for ms in microservices[data['category']]]
					else:
						check=[False]
				else:
					raise cherrypy.HTTPError(401)
					
				if True in check:
					for cat in list(microservices.keys()):
						i=None
						for j,ms in enumerate(microservices[cat]):
							if ms['microserviceID']==data['microserviceID']:
								i=j
						if i is not None:
							DB['microservices'][cat].pop(i)

				data['timestamp']=time.time()
				self.dm.add_microservice(data)
				DB["last_edit"]=time.time()
				self.jm.write(DB,path)
				return 'New microservice Added'				
		else:
			raise cherrypy.HTTPError(400)

			
	def DELETE(self,*uri,**params):
		if 'data' not in list(cherrypy.session.keys()):
			raise cherrypy.HTTPError(401)
			
		if cherrypy.session['data'] and len(uri)==1 and uri[0].lower()=='delete' and len(params)==1 and list(params.keys())[0]=='deviceID':	
			user=list(cherrypy.session['data'].keys())[0]	
			devices=self.s.all_devices(user)['devices']

			check= [params['deviceID']==dev['deviceID'] for dev in devices]

			if True in check:
				self.dm.remove_device(user,params)
				DB["last_edit"]=time.time()
				self.jm.write(DB,path)
			else:
				raise cherrypy.HTTPError(404)
				
		elif cherrypy.session['data'] and len(uri)==1 and uri[0].lower()=='clean' and len(params)==1 and list(params.keys())[0]=='age':
			user=list(cherrypy.session['data'].keys())[0]	
			if user==ADMIN:
				try:
					params['age']=float(params['age'])
				except:
					raise cherrypy.HTTPError(400)
					
				self.dm.clean(params['age'])
				DB["number_of_devices"]=0
				for u in list(DB["devices"].keys()):
					DB["number_of_devices"]+=len(u[0])
				DB["last_edit"]=time.time()
				self.jm.write(DB,path)
			else:
				raise cherrypy.HTTPError(401)
		else:
			raise cherrypy.HTTPError(400)					

if __name__=="__main__":
	
	f=open("data/WSCatalog_config.json")
	conf=json.loads(f.read())
	f.close()
	
	# init root
	global ADMIN
	ADMIN=conf["administrator"]["user"]
	global PSW
	PSW=conf["administrator"]["password"]

	# init database path
	global path
	path=conf["CatalogPath"]

	# init semafor for access to database file
	global semafor
	semafor=True

	# init database variable
	jm=JsonManager()
	global DB
	DB=jm.read(path)

	# Web Service configuration
	config = {
		'global': {
			'server.socket_host': get_ip(),
			'server.socket_port': 8080,
		},
		'/': {
				'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
				'tools.sessions.on': True,
				'tools.response_headers.on': True,
				'tools.staticdir.root': os.path.dirname(os.path.abspath(__file__)),
				'tools.staticdir.on': True,
				'tools.staticdir.dir': '/',
			}
		}
	
	# Start Web Service
	#cherrypy.quickstart(CatalogWebService(), '/', config=config)
	
	thread1=CatalogThread(1,"CatalogWebService", config=config)
	thread2=CatalogThread(2,"refresh", age=120)
	thread1.start()
	thread2.start()
