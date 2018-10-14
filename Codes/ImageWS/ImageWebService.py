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
from PIL import Image
import base64
import string
import random
import requests

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


class RandomKeyGenerator(object):
	def __init__(self):
		pass
	
	def generate(self,size=16, chars=string.ascii_uppercase + string.digits+string.ascii_lowercase):
		key=''.join(random.choice(chars) for _ in range(size))
		while self.check(key,database["registered"].values()):
			key=''.join(random.choice(chars) for _ in range(size))	
		return key
	def check(self,key,key_list):
		return key in key_list
		
class ImageSaver(object):
	def __init__(self,formato,img_path):
		self.formato=formato
		self.path=img_path
	def save(self,image,user):					
		image=image.encode("utf-8")
		image=base64.b64decode(image)
		image = Image.open(io.BytesIO(image))
		image.save(self.path+user+self.formato)
		
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
class ImageWebService(object):
	def __init__(self):
		
		self.rkg=RandomKeyGenerator()
		self.jm=JsonManager()
		self.ims=ImageSaver(formato='.png',img_path='img/')
	
	def POST(self,*uri,**params):
		if len(uri)==1 and uri[0]=="register":
			data=json.loads(cherrypy.request.body.read())
			if "user" not in data.keys() or "image" not in data.keys():
				raise cherrypy.HTTPError(400)
			user=data["user"]
			image=data["image"]
			if user not in database["registered"].keys():
				database["registered"][user]=self.rkg.generate()
				database["number_of_user"]+=1
				database["last_edit"]=time.time()
				self.jm.write(database,path)
				image=data["image"]
				self.ims.save(image,user)
				return json.dumps({"key":database["registered"][user]})
			else:
				raise cherrypy.HTTPError(409)
		else:
			raise cherrypy.HTTPError(400)
		
	def PUT(self,*uri,**params):

		if len(uri)==1 and uri[0]=="upload" and list(params.keys())==["key"]:
			data=json.loads(cherrypy.request.body.read())
			key=params["key"]
			if "user" not in data.keys() or "image" not in data.keys():
				raise cherrypy.HTTPError(400)
			user=data["user"]
			if user in database["registered"].keys():
				if database["registered"][user]==key:
					image=data["image"]
					self.ims.save(image,user)
					return "Image successfully uploaded"
				else:
					raise cherrypy.HTTPError(401)
			else:
				raise cherrypy.HTTPError(401)
		else:
			raise cherrypy.HTTPError(400)
			
	def GET(self,*uri,**params):
		if list(params.keys())==["key"]:
			
			if params["key"] in list(database["registered"].values()):
				key=params["key"]
				for u in list(database["registered"].keys()):
					if database["registered"][u]==key:
						user=u
						break
							
				out=open("templates/image.html").read()
				p='img/'+user+'.png'
				out = out % (json.dumps(p))
				return out
			else:
				raise cherrypy.HTTPError(401)
		else:
			raise cherrypy.HTTPError(400)
							

if __name__=="__main__":
	global semafor
	semafor=True


	f=open("data/config.json")
	conf=json.loads(f.read())
	
	global path
	path=conf["ImageWS"]["database"]
	
	global database
	try:
		f=open(path)
	except:
		f=open(path,'w')
		f.write(json.dumps({"registered":{},"number_of_user":0,"last_edit":0}))
		f.close()
		f=open(path)
	database=json.loads(f.read())
	f.close()
	
	user=conf["ImageWS"]["WSCatalog"]["credentials"]["user"]
	password=conf["ImageWS"]["WSCatalog"]["credentials"]["password"]
	WSC=conf["ImageWS"]["WSCatalog"]["url"]
	
	
	config = {
		'global': {
			'server.socket_host': get_ip(),
			'server.socket_port': 5000,
		},
		'/': {
				'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
				'tools.sessions.on': True,
				'tools.response_headers.on': True,
				'tools.staticdir.root': os.path.dirname(os.path.abspath(__file__)),
				'tools.staticdir.on': True,
				'tools.staticdir.dir': '/',
			},
		'/img': {
				'tools.staticdir.on': True,
				'tools.staticdir.dir': os.path.join(os.path.dirname(os.path.abspath(__file__)), "img")
				}
		}


	s=requests.Session()
	r=s.post(WSC+"/login",data=json.dumps({"user":user,"password":password}))
	
	endpoints="http://"+get_ip()+":5000"
	name=conf["ImageWS"]["name"]
	resource=conf["ImageWS"]["resource"]
	data={'microserviceID':name,'category':resource,'endpoints':endpoints,'protocol':'rest'}
	r=s.put(WSC+"/newmicroservice",data=json.dumps(data))
		
	# Start Web Service
	cherrypy.quickstart(ImageWebService(), '/', config=config)
