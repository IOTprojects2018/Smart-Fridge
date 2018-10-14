# Authors: Boretto Luca    <luca.boretto@studenti.polito.it>
#          Carta   Loris   <loris.carta@studenti.polito.it>
#          Jarvand Aysan   <aysan.jarvand@studenti.polito.it>
#		   Toscano Alessia <alessia.toscano@studenti.polito.it>


import cherrypy
import time
import json
import socket
import os
import random
import string
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
	
	def generate(self,KEYS,size=8, chars=string.ascii_uppercase + string.digits):
		r=True
		while r:
			key=''.join(random.choice(chars) for _ in range(size))
			r=self.check(key,KEYS)	
		return key
			
	def check(self,key,KEYS):
		return key in KEYS
		
		
		
		
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
		try:
			f=open(path,'r')
		except:
			f=open(path,'w')
			f.write('{}')
			f.close()
			f=open(path,'r')
		data=json.loads(f.read())
		f.close()
		semafor=True
		return data
		
@cherrypy.expose
class ProductsWebService(object):
	def __init__(self):
		
		self.jm=JsonManager()
		self.rkj=RandomKeyGenerator()
	
	def POST(self,*uri,**params):

		if len(uri)==1 and uri[0].lower()=='register' and params=={}:
				if "KEYS" not in DATA.keys():
					DATA["KEYS"]=[]
				if "USERS" not in DATA.keys():
					DATA["USERS"]={}
				key=self.rkj.generate(DATA["KEYS"])
				DATA["KEYS"].append(key)
				DATA["USERS"][key]=[]
				if "PRODUCTS" not in DATA.keys():
					DATA["PRODUCTS"]={}
				self.jm.write(DATA,path)
				return json.dumps({"key":key})
		else:
			raise cherrypy.HTTPError(404)

	def GET(self, *uri, **params):
		
		if len(uri)==1 and uri[0].lower()=='products' and params.keys()==['user']:
			user=params['user'].encode()
			if user in DATA['PRODUCTS'].keys():
				return json.dumps({'products':DATA['PRODUCTS'][user]})	
			else:
				raise cherrypy.HTTPError(404)
		else:
			raise cherrypy.HTTPError(400)
			
	def PUT(self,*uri,**params):

		if len(uri)==1 and uri[0].lower()=='add' and sorted(params.keys())==['api_key','name','user','weight']:#['api_key','product','user']:	
			if params['api_key'] not in DATA['KEYS']:
				raise cherrypy.HTTPError(401)
							
			user=params['user'].encode() 
			api_key=params['api_key'].encode()
			#product=params['product'].encode()
			name=params['name'].encode()
			weight=params['weight'].encode()
			
			if user not in DATA["PRODUCTS"].keys():
				DATA["PRODUCTS"][user]=[]
				DATA["USERS"][api_key].append(user)
				DATA["PRODUCTS"][user].append([name,weight,time.strftime("%D %H:%M", time.localtime(int(time.time())))])
				self.jm.write(DATA,path)
				print "Adding "+name+" to "+user+"'s product list"
				print "Product list for "+user+"was updated as follow:"			
			else:
				if user not in DATA["USERS"][api_key]:
					raise cherrypy.HTTPError(401)
				else:
					DATA["PRODUCTS"][user].append([name,weight,time.strftime("%D %H:%M", time.localtime(int(time.time())))])
					self.jm.write(DATA,path)
				
		elif len(uri)==1 and uri[0].lower()=='remove' and sorted(params.keys())==['api_key','name','user','weight']:#['api_key','product','user']:
			if params['api_key'] not in DATA['KEYS']:
				raise cherrypy.HTTPError(401)
			
			user=params['user'].encode() 
			api_key=params['api_key'].encode()
			name=params['name'].encode()
			weight=params['weight'].encode()
			 
			if user in DATA["PRODUCTS"].keys():
				if user in DATA["USERS"][api_key]:
					i=-1
					for j,prod in enumerate(DATA['PRODUCTS'][user]):
						if name==prod[0] and weight==prod[1]:
							i=j
					if i!=-1:
						DATA['PRODUCTS'][user].pop(i)
						self.jm.write(DATA,path)
						print "Removing "+name+" to "+user+"'s product list"
						print "Product list for "+user+"was updated as follow:"		
				else: 
					raise cherrypy.HTTPError(401)
			else:
				raise cherrypy.HTTPError(404)
		
		else:
			raise cherrypy.HTTPError(400)

@cherrypy.expose
class Barcode2Product(object):
	def __init__(self,barcodes_path):
		f=open(barcodes_path)
		self.barcodes=json.loads(f.read())
		f.close()

	def GET(self, *uri, **params):
		
		if len(uri)==1 and uri[0].lower()=='product' and params.keys()==['barcode']:
			barcode=params['barcode'].encode()
			if barcode in self.barcodes.keys():
				return json.dumps({'product':self.barcodes[barcode]})	
			else:
				raise cherrypy.HTTPError(404)
		else:
			raise cherrypy.HTTPError(400)
			
		
		

if __name__=="__main__":

	f=open("data/config.json")
	conf=json.loads(f.read())
	
	# init database path
	global path
	path=conf["ProductsWS"]["database"]
	
	barcodes_path=conf["Barcode2ProductWS"]["database"]

	# init semafor for access to database file
	global semafor
	semafor=True

	# init database variable
	jm=JsonManager()
	global DATA
	DATA=jm.read(path)

	user=conf["ProductsWS"]["WSCatalog"]["credentials"]["user"]
	password=conf["ProductsWS"]["WSCatalog"]["credentials"]["password"]
	WSC=conf["ProductsWS"]["WSCatalog"]["url"]
	

	# Web Service configuration
	config = {
		'global': {
			'server.socket_host': get_ip(),
			'server.socket_port': 9090,
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
	


	s=requests.Session()
	r=s.post(WSC+"/login",data=json.dumps({"user":user,"password":password}))
	
	endpoints="http://"+get_ip()+":9090/products"
	name=conf["ProductsWS"]["name"]
	resource=conf["ProductsWS"]["resource"]
	data={'microserviceID':name,'category':resource,'endpoints':endpoints,'protocol':'rest'}
	r=s.put(WSC+"/newmicroservice",data=json.dumps(data))
	
	endpoints="http://"+get_ip()+":9090/barcode2product"
	name=conf["Barcode2ProductWS"]["name"]
	resource=conf["Barcode2ProductWS"]["resource"]
	data={'microserviceID':name,'category':resource,'endpoints':endpoints,'protocol':'rest'}
	r=s.put(WSC+"/newmicroservice",data=json.dumps(data))
	
	# Start Web Service
	cherrypy.tree.mount(ProductsWebService(), '/products', config)
	cherrypy.tree.mount(Barcode2Product(barcodes_path), '/barcode2product', config)
	cherrypy.config.update({'server.socket_host': get_ip()})
	cherrypy.config.update({'server.socket_port': 9090})
	cherrypy.engine.start()
	cherrypy.engine.block()
