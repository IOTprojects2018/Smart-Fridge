# Authors: Boretto Luca    <luca.boretto@studenti.polito.it>
#          Carta   Loris   <loris.carta@studenti.polito.it>
#          Jarvand Aysan   <aysan.jarvand@studenti.polito.it>
#		   Toscano Alessia <alessia.toscano@studenti.polito.it>

""" This file contains some usefull classes for ThingSpeakAdaptor service
"""
import paho.mqtt.client as MQTT
import urllib
import requests
import time
import json
import datetime

class ThingSpeakAdaptor:
	"""- ThingSpeakAdaptor: MQTT subscriber and REST client"""
	
	def __init__(self,clientID,url_thingspeak,dictionary):	
		self.clientID=clientID
		self.url_thingspeak=url_thingspeak
		self.contacts={}
		self.dictionary=dictionary
		self.calendar={}
		self.jj={}

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
		msg.payload=json.loads(msg.payload)
		# if the resource is a valid resource, it publishes value in the proper field and channel in ThingSpeak
		if msg.payload['e'][0]['n'] in list(self.dictionary.keys()):
			user=msg.payload['e'][0]['user']
			if user not in list(self.calendar.keys()):
				self.calendar[user]={}
			if len(self.calendar[user])==0:
				self.jj[user]=time.time()
			if msg.payload['e'][0]['n'] not in list(self.calendar[user].keys()):
				self.calendar[user][msg.payload['e'][0]['n']]=[]
			n=len(list(self.calendar[user].keys()))
			quad=int(60/n)
			for j,key in enumerate(list(self.calendar[user].keys())):
				self.calendar[user][key]=list(range(j*quad,(j+1)*quad))

			
			try:
				my_dt_ob=datetime.datetime.now()
				date_list = [my_dt_ob.year, my_dt_ob.month, my_dt_ob.day, my_dt_ob.hour, my_dt_ob.minute, my_dt_ob.second]
				second=date_list[-1]
				if second in self.calendar[user][msg.payload['e'][0]['n']]:
					if time.time()-self.jj[user]<15:
						time.sleep(15-(time.time()-self.jj[user]))
					write_key=self.contacts[user]["thingspeak_wkey"]
					p={'api_key':write_key.encode(),self.dictionary[msg.payload['e'][0]['n']].encode():msg.payload['e'][0]['v']}
					r=requests.get(self.url_thingspeak, params=p)
					if r.status_code==200:
						self.jj[user]=time.time()
						print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"- "+"Data received from " + msg.topic + " uploaded on ThingSpeak")
					else:
						print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"- "+"Error while uploading data received from " + msg.topic)
						print ("Status code: " + str(r.status_code) )
			except:
				print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"- "+"Missing thingspeak key for user " + user)
			
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
