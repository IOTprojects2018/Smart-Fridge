# Authors: Boretto Luca    <luca.boretto@studenti.polito.it>
#          Carta   Loris   <loris.carta@studenti.polito.it>
#          Jarvand Aysan   <aysan.jarvand@studenti.polito.it>
#		   Toscano Alessia <alessia.toscano@studenti.polito.it>

""" This file contains some usefull classes for ProductsAdaptor service
"""
import paho.mqtt.client as MQTT
import urllib
import requests
import time
import json
import datetime

class ProductsAdaptor:
	"""- ProductsAdaptor: MQTT subscriber and REST client"""
	
	def __init__(self,clientID,url_productsWS,KEY,categories,barcode2products_url):	
		self.clientID=clientID.encode()
		self.url_productsWS=url_productsWS
		self.categories=categories
		if KEY=="":
			r=requests.post(url_productsWS+"/register")
			KEY=json.loads(r.text)["key"]
			f=open('data/'+self.clientID+'_config.json')
			data=json.loads(f.read())
			f.close()
			f=open('data/'+self.clientID+'_config.json','w')
			data["key4ProductsWS"]=KEY
			f.write(json.dumps(data))
			f.close()
		self.KEY=KEY
		self.b2p_url=barcode2products_url


		#create an instance of paho.mqtt.client
		self._paho_mqtt=MQTT.Client(self.clientID,clean_session=True)
		
		#register the callbacks
		self._paho_mqtt.on_connect=self.myOnConnect
		self._paho_mqtt.on_message=self.myOnMessageReceived
		
	def start(self, url, port, sub_topic=None):
		# connection to broker
		self._paho_mqtt.connect(url,port)
		self._paho_mqtt.loop_start()
		
		# if it's also subscriber, subscribe to a topic
		if sub_topic is not None:
			self.mySubscribe(sub_topic)
	
	def stop(self, sub_topic=None):
		
		# if it's also subscriber, subscribe to a topic		
		if sub_topic is not None:
			self.myUnsubscribe(sub_topic)
		
		self._paho_mqtt.loop_stop()
		self._paho_mqtt.disconnect()
	
	def myPublish(self,topic,message,QoS):
		
		# publish a message on a certain topic
		self._paho_mqtt.publish(topic, message, QoS,retain=False)

	def mySubscribe(self,sub_topics):
		
		# subscribe to a topic 
		self._paho_mqtt.subscribe(sub_topics)
	
	def myUnsubscribe(self,sub_topics):
		
		# unsubscribe from a topic
		self._paho_mqtt.unsubscribe(sub_topics)
		
	def myUpdate(self,new_sub_topics,old_sub_topics):
		
		# update topics list
		topics_to_add=[]
		topics_to_remove=[]
		if type(new_sub_topics)==type(list()):
			for topic in new_sub_topics:
				if topic not in old_sub_topics:
					for o in old_sub_topics:
						if o[0] == topic[0] or (o not in new_sub_topics):
							topics_to_remove.append(o[0])
					topics_to_add.append(topic)
			topics_to_remove=self.unique(topics_to_remove)
			self.myUnsubscribe(topics_to_remove)
			self.mySubscribe(topics_to_add)
		else:
			if new_sub_topics!=old_sub_topics:
				self.myUnsubscribe(old_sub_topics[0])
				self.mySubscribe(new_sub_topics)
	
	def unique(self,duplicate):
		
		# unique value in list
		final_list = []
		for num in duplicate:
			if num not in final_list:
				final_list.append(num)
		return final_list
		
	def myOnConnect(self, paho_mqtt, userdata, flags, rc):
		print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"- "+"connected to message broker with rc" + str(rc))
	
	def myOnMessageReceived(self, paho_mqtt, userdata, msg):

		try:
			msg.payload=json.loads(msg.payload)
			# if the resource is a valid resource, it publishes value in the proper field and channel in ThingSpeak
			if msg.payload['e'][0]['n'] in self.categories:
				print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"- "+"Received __ Topic: " + msg.topic) 
				user=msg.payload['e'][0]['user']
				r=requests.get(self.b2p_url+'/product',params={"barcode":msg.payload['e'][0]['v']})
				product=json.loads(r.text)["product"]
				name=product["name"]
				weight=product["weight"]
			
				p={'api_key':self.KEY,'user':user,'name':name,'weight':weight}#'product':product}
				r=requests.put(self.url_productsWS+'/'+msg.payload['e'][0]['action'], params=p)
				if r.status_code==200:
					print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"- "+"Data received from " + msg.topic + " uploaded on ProductsWS")
				else:
					print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"- "+"Error while uploading data received from " + msg.topic)
					print ("Status code: " + str(r.status_code) )
		except:
			pass
			
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

def ms2topic(microservices,categories):
	# Obtain topics from obtained microservices and minimize its number
	# to 1 using wildcards
	topics=[]
	for category in categories:
		if category in list(microservices.keys()):
			for ms in microservices[category]:
				if ms['protocol']=='mqtt':
					topic=ms["endpoints"].split('/')[1:]
					topic='/'.join(topic)
					topics.append(topic.encode())				
	if len(topics)==1:
		topic=topics[0]
	elif len(topics)>1:
		tmp={}
		tot=0
		for i,t in enumerate(topics):
			tmp[str(i)]=t.split('/')
			le=len(tmp[str(i)])
			tot+=le
		assert tot==le*len(tmp)
		topic=[]
		for i in range(le):
			c=False
			item=tmp['0'][i]
			for j in range(len(tmp)):
				if item!=tmp[str(j)][i]:
					c=True
			if c:
				topic.append('+')
			else:
				topic.append(item)
		topic='/'.join(topic)
	else:
		topic=topics
							
	return topic
