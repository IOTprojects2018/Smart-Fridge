#!/usr/bin/env python3

# Authors: Boretto Luca    <luca.boretto@studenti.polito.it>
#          Carta   Loris   <loris.carta@studenti.polito.it>
#          Jarvand Aysan   <aysan.jarvand@studenti.polito.it>
#		   Toscano Alessia <alessia.toscano@studenti.polito.it>

import cherrypy
import requests
import json
import os
import socket

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
	
class RaspberryWebService(object):
	def __init__(self,WSC):
		self.WSCatalog=WSC

	@cherrypy.expose
	def index(self):
		return open("templates/homepage.html").read()
	
	@cherrypy.expose
	def registration(self):
		return open("templates/registration.html").read()

	@cherrypy.expose
	def join(self):
		return open("templates/join.html").read()
	
	@cherrypy.expose
	def settings(self):
		return open("templates/settings.html").read()
		
	@cherrypy.expose
	def thingspeak(self):
		return open("templates/thingspeak.html").read()


	@cherrypy.expose
	def post_join(self, user,password,key):
		ans=open("templates/ans.html").read()
		f=open('data/config.json')
		data=json.loads(f.read())
		f.close()
		if data["key"]==key:
			r=requests.post(self.WSCatalog+"/login",data=json.dumps({"user":user,"password":password}))
			if r.status_code==200:
				f=open('data/config.json',"w")
				data["user"]=user
				data["password"]=password
				f.write(json.dumps(data))
				f.close()
				out=ans % "Coupling completed"
				return out
			else:
				out=ans % "Invalid user or password"
				return out
		else:
			out=ans % "Invalid key"
			return out			

	@cherrypy.expose
	def post_registration(self, user,password):
		ans=open("templates/ans.html").read()
		r=requests.post(self.WSCatalog+"/register",data=json.dumps({"user":user,"password":password}))
		if r.status_code==200:
			out=ans % "Registered"
			return out
		elif r.status_code==409:
			out=ans % "User already registered"
			return out
		else:
			out=ans % "An error occurred. Try again later"
			return out
	@cherrypy.expose		
	def post_settings(self,temperature):
		ans=open("templates/ans.html").read()
		try:
			temperature=float(temperature)
			f=open("data/sensors_config.json")
			data=json.loads(f.read())
			data["Temperature"][0]["threshold"]=temperature
			f.close()
			f=open("data/sensors_config.json","w")
			f.write(json.dumps(data))
			f.close()
			out=ans % "Temperature threshold properly setted"
			return out
		except:
			out=ans % "Invalid value"
			return out
			
	@cherrypy.expose		
	def post_thingspeak(self,channelID,wkey,rkey):
		ans=open("templates/ans.html").read()
		f=open("data/config.json")
		data=json.loads(f.read())
		f.close()
		s=requests.Session()
		r=s.post(self.WSCatalog+"/login",data=json.dumps({"user":data["user"],"password":data["password"]}))
		if r.status_code==200:
			r=s.put(self.WSCatalog+"/newcontact",data=json.dumps({'thingspeak_chID':channelID,'thingspeak_rkey':rkey,'thingspeak_wkey':wkey}))
			if r.status_code==200:
				out=ans % "ThingSpeak keys properly setted"
				return out
			else:
				out=ans % "An error occurred"
				return out		
		else:
			out=ans % "You need to join your device or create an account before"
			return out

if __name__ == '__main__':
	conf = {'global': {
			'server.socket_host': get_ip(),
			'server.socket_port':5000,
		},"/img": {"tools.staticdir.on": True,"tools.staticdir.dir": os.path.join(os.path.dirname(os.path.abspath(__file__)), "img")}}
	f=open("data/config.json")
	WSC=json.loads(f.read())["WebServiceCatalog"]
	f.close()
	cherrypy.quickstart(RaspberryWebService(WSC), '/', conf)

