import paho.mqtt.client as MQTT
import requests
import telepot
import time
import json
import os
import datetime


class DoSomething(object):
	
	def __init__(self):
		#self.clientID=None
		#self.msg=None
		self.fifo=None
		self.timer=None
		self.weights_vector=None
		self.products=None
		self.remove_product=None
		self.add_product=None
		self.current_product=None
		self.received_products=None 
		self.weights_vector=None
		self.last=None
		self.answers=None
		self.last_barcode_msg={}
		self.add_product_w={}
		self.t_w={}
		self.scalechecker=ScaleChecker(50,0.9)
		self.last_stab={}
			 
	def temperature(self,clientID,msg,flags):
		# Obtain user and payload
		user,payload=self.user_payload(msg)
		
		# Check if 15 s are passed from the last temperature sample.
		# If it is, it sets flags['timer']=True and timer is updated
		flags,self.timer,msg=self.common(clientID,flags,msg)
		
		# If current user's FIFO is not in FIFOs create a FIFO for this user	
		if user not in list(self.fifo.keys()):
			self.fifo[user]=FIFO(8)
		
		# Check if temperature is over threshold insert 1 to user's FIFO
		if payload['e'][0]['v']>payload['e'][0]['tr']:
			self.fifo[user].insert(1)
		else:
			self.fifo[user].insert(0)
			
		# If FIFO is full set flags['allarm']=True	
		if self.fifo[user].check():
			flags['allarm']=True
		
		return msg,flags
		
	def humidity(self,clientID,msg,flags):
		# Check if 15 s are passed from the last humidity sample.
		# If it is, it sets flags['timer']=True and timer is updated
		flags,self.timer,msg=self.common(clientID,flags,msg)
		return msg,flags
		
	def motion(self,clientID,msg,flags):
		# Check if 15 s are passed from the last motion sample.
		# If it is, it sets flags['timer']=True and timer is updated
		flags,self.timer,msg=self.common(clientID,flags,msg)
		return msg,flags
		
	def barcode(self,clientID,msg,flags):
		# Obtain user and payload
		user,payload=self.user_payload(msg)
		
		resource=payload['e'][0]['n']
		topic_l=msg.topic.split('/')
		topic_l[0]='MicroServices/'+resource+'/BarcodeService'
		msg.topic='/'.join(topic_l)
		
		# If current user's list of product isn't in the product archive
		# create an empty product list for the current user
		if user not in list(self.products.keys()):
			self.products[user]=[]
			self.received_products[user]=[]
			self.remove_product[user]=False
			self.add_product[user]=False
			self.add_product_w[user]=False
			self.last[user]=0
			self.weights_vector[user]=[]
		
		#Backup message	
		self.last_barcode_msg[user]=msg
		
		# Add received product to proper user's received product list
		self.received_products[user].append([payload['e'][0]['v'].encode(),payload['e'][0]['t']])
		
		# Add/Remove received product to/from proper user's product list
		#try:
		
		if not self.remove_product[user]:
			self.add_product[user]=True
		
		if self.remove_product[user]:
			msg.payload=json.loads(msg.payload)
			try:
				out=[i for i,p in enumerate(self.products[user]) if self.received_products[user][-1][0]==p[0]]
				self.products[user].pop(out[0])
			except:
				pass
			msg.payload['e'][0]['v']=self.received_products[user][-1][0]
			msg.payload['e'][0]['action']='remove'
			msg.payload['e'][0]['t']=time.strftime("%a %d %b %Y %H:%M:%S GMT",  time.gmtime(self.received_products[user][-1][1]))
			msg.payload['e'][0]['user']=user
			msg.payload['bn']=msg.topic
			msg.payload=json.dumps(msg.payload)
			flags["bc"]=msg
			self.remove_product[user]=False

		return msg,flags
		
	def weight(self,clientID,msg,flags):
		# Obtain user and payload
		user,payload=self.user_payload(msg)
		flags,self.timer,msg=self.common(clientID,flags,msg)
		
		# If current user's list of product isn't in the product archive
		# create an empty weights vector for the current user
		if user not in list(self.products.keys()):
			self.last[user]=0
			self.weights_vector[user]=[]
			self.remove_product[user]=False
			self.add_product[user]=False
			self.add_product_w[user]=False
			self.products[user]=[]
			self.received_products[user]=[]
			self.t_w[user]=0
			self.last_stab[user]=0
			
		# Add received weight sample to current user's weights vector
		if payload['e'][0]['t']>self.t_w[user]:
			
			self.weights_vector[user].append(payload['e'][0]['v'])
			self.t_w[user]=payload['e'][0]['t']
		
		# Check if the current sample is a positive/negative step
		self.answers[user],self.last_stab[user]=self.scalechecker.check(self.weights_vector[user][self.last[user]:],self.last_stab[user])
		

		
		# If it is a positive step (answer=1) --> set add product flag to True
		# else if it is a negative step (answer=-1) --> set remove product flag to True
		# else if it is not a step (answer=0) --> do nothing
		if self.answers[user]==1:
			self.add_product_w[user]=True
			self.last[user]=len(self.weights_vector[user])-1
			print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"- "+user+': a barcode was detected before the removal of a product')
			
		elif self.answers[user]==-1:
			if self.products[user]!=[]:
				self.remove_product[user]=True
				self.last[user]=len(self.weights_vector[user])-1
				print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"- "+user+': a barcode was detected after the removal of a product')

		else:
			pass
		


		if self.add_product[user] and self.add_product_w[user]:
			last_barcode_msg=self.last_barcode_msg[user]
			last_barcode_msg.payload=json.loads(last_barcode_msg.payload)
			timestamp=time.strftime("%a %d %b %Y %H:%M:%S GMT", time.gmtime(self.received_products[user][-1][1]))
			self.products[user].append([self.received_products[user][-1][0],timestamp])
			last_barcode_msg.payload['e'][0]['v']=self.received_products[user][-1][0]
			last_barcode_msg.payload['e'][0]['action']='add'
			last_barcode_msg.payload['e'][0]['t']=time.strftime("%a %d %b %Y %H:%M:%S GMT",  time.gmtime(self.received_products[user][-1][1]))
			last_barcode_msg.payload['e'][0]['user']=user
			last_barcode_msg.payload['bn']=msg.topic
			last_barcode_msg.payload=json.dumps(last_barcode_msg.payload)
			flags["bc"]=last_barcode_msg
			self.add_product[user]=False
			self.add_product_w[user]=False
			
		return msg,flags
	
	def user_payload(self,msg):
		user=msg.topic.split('/')[1].encode() #ricontrolla per temp e hum e moti
		payload=json.loads(msg.payload)
		return user,payload
		
	def common(self,clientID,flags,msg):
		user,payload=self.user_payload(msg)
		resource=payload['e'][0]['n']
		if user not in list(self.timer.keys()):
			self.timer[user]={}
			if resource not in list(self.timer[user].keys()):
				self.timer[user][resource]=time.time()
		if time.time()-self.timer[user][resource]>15: # thingspeak maximum number of data points for hour is 240
			self.timer[user][resource]=time.time()
			topic_l=msg.topic.split('/')
			topic_l[0]='MicroServices/'+resource+'/'+clientID
			if resource == 'barcode' or 'weight':
				topic_l[0]='MicroServices/'+resource+'/'+resource.capitalize()+'Service'
				
			msg.topic='/'.join(topic_l)
			payload['e'][0]['user']=user
			payload['bn']=msg.topic
			msg.payload=json.dumps(payload)
			flags["timer"]=True			
		else:
			flags["timer"]=False
		return flags,self.timer,msg
		

class MicroServicePubSub:
	def __init__(self,clientID,TOKEN=None,WSC_URL=None,ADMIN=None,PASSWORD=None):
		
		self.clientID=clientID
		#self.resource=resource
		if TOKEN is not None:
			self.bot = telepot.Bot(token=TOKEN)
		if None not in [WSC_URL,ADMIN,PASSWORD]:	
			self.clientSession=WebServiceClient(WSC_URL,ADMIN,PASSWORD)
			self.clientSession.start()
		else:
			self.clientSession=None
		self.doSomething=DoSomething()

		#create an instance of paho.mqtt.client
		self._paho_mqtt=MQTT.Client(self.clientID,clean_session=True)
		
		#register the callbacks
		self._paho_mqtt.on_connect=self.myOnConnect
		self._paho_mqtt.on_message=self.myOnMessageReceived
		
		# initalize Data 

		self.doSomething.timer={}
		self.doSomething.fifo={}
		self.doSomething.weights_vector={}
		self.doSomething.products={}
		self.doSomething.remove_product={}
		self.doSomething.add_product={}
		self.doSomething.current_product={}
		self.doSomething.received_products={}
		self.doSomething.weights_vector={}
		self.doSomething.last={}
		self.doSomething.answers={}
		self.QoS=2

		
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
			self.myUnsubscribe(sub_topics)
		
		self._paho_mqtt.loop_stop()
		self._paho_mqtt.disconnect()
	
	def myPublish(self,topic,message,QoS):
		
		# publish a message on a certain topic
		self._paho_mqtt.publish(topic, message, QoS,retain=False)

	def mySubscribe(self,sub_topics):
		self._paho_mqtt.subscribe(sub_topics)
	
	def myUnsubscribe(self,sub_topics):
		self._paho_mqtt.unsubscribe(sub_topics)
		
	def myUpdate(self,new_sub_topics,old_sub_topics):
		topics_to_add=[]
		topics_to_remove=[]
		for topic in new_sub_topics:
			if topic not in old_sub_topics:
				for o in old_sub_topics:
					if o[0] == topic[0] or (o not in new_sub_topics):
						topics_to_remove.append(o[0])
				topics_to_add.append(topic)
		topics_to_remove=self.unique(topics_to_remove)
		
		if topics_to_remove!=[]:
			self.myUnsubscribe(topics_to_remove)
		if topics_to_add!=[]:
			self.mySubscribe(topics_to_add)
		
	def unique(self,duplicate):
		final_list = []
		for num in duplicate:
			if num not in final_list:
				final_list.append(num)
		return final_list
		
	def myOnConnect(self, paho_mqtt, userdata, flags, rc):
		print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"- "+"connected to message broker with rc" + str(rc))
	
	def myOnMessageReceived(self, paho_mqtt, userdata, msg):
		print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"- "+"Received from Topic: " + msg.topic + " QoS: "+ str(msg.qos))
		
		# initialize timer and allarm flags
		flags={"timer":False,"allarm":False,"bc":False}
		
		# get the type of resource
		resource=json.loads(msg.payload)['e'][0]['n']
		
		# update doSomething object attributes
		#self.doSomething.clientID=self.clientID
		#self.doSomething.msg=msg
		user=msg.topic.split('/')[1]
		action=getattr(self.doSomething,resource)	
		msg,flags=action(self.clientID,msg,flags)

		
		if flags['timer']:
			self.myPublish(msg.topic,msg.payload,self.QoS)
			print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"- "+"Publishing subsampled data to Topic: " + msg.topic + " QoS: "+ str(self.QoS))
		
		if flags['bc']:
			msg=flags['bc']
			self.myPublish(msg.topic,msg.payload,self.QoS)
			print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"- "+"Publishing received Barcode to Topic: " + msg.topic + " QoS: "+ str(self.QoS))
		
		if flags['allarm']:	
			contacts=self.clientSession.get_contacts()
			print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"- "+user+": sending allarm to user by RefrigeratorAllarm_bot")
			try:
				chat_id=contacts[user]['telegramID']
				tmsg='WARNING: '+resource+' is over threshold!!!'
				self.bot.sendMessage(chat_id=chat_id, text=tmsg)
			except:
				print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"- "+"Missing telegram contact for "+user)
			
class ScaleChecker:
	def __init__(self,noise,perc):
		self.noise=noise
		self.perc=perc
	
	def check(self,v,last_stab):
		if max(self.diff(v[-3:]))>=self.noise:
			return 0,last_stab
		if self.added(v):
			last_stab=self.mode(v)[0]
			return 1,last_stab
		elif self.removed(v):
			last_stab=self.mode(v)[0]
			return -1,last_stab
		else:
			if  float(sum(v))/len(v)>last_stab+self.noise:
				last_stab=self.mode(v)[0]
				return 1,last_stab
			elif float(sum(v))/len(v)<last_stab-self.noise:
				last_stab=self.mode(v)[0]
				return -1,last_stab
			else:
				return 0,last_stab
		
	def added(self,v):
		c=0
		for i in range(len(v)-1):
			if v[-1]>(v[i]+self.noise):
				c+=1
		return c>len(v)*self.perc

	def removed(self,v):
		c=0
		for i in range(len(v)-1):
			if v[-1]<(v[i]-self.noise):
				c+=1
		return c>len(v)*self.perc
	
	def diff(self,v):
		out=[]
		for j in range(len(v)):
			for i in range(len(v)):
				out.append(abs(v[i]-v[j]))
		return out
		
	def mode(self,array):
		most = max(list(map(array.count, array)))
		return list(set(filter(lambda x: array.count(x) == most, array)))
			
class WebServiceClient(object):
	def __init__(self,urlWebService,user,password):
		self.url=urlWebService
		self.user=user
		self.password=password
		self.loggedin=False
	
	def start(self):
		r=self.login()
		if r.status_code==200:
			self.loggedin=True
		else:
			print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"- "+"Authentication Error")
		return r.status_code
	
	def login(self):
		self.s=requests.Session()
		r=self.s.post(self.url+'/login',data=json.dumps({'user':self.user,'password':self.password}))
		return r
			
	def get_msgbroker(self):
		IP_msgbroker=None
		PORT_msgbroker=None
		if self.loggedin:
			r=self.s.get(self.url+'/msgbroker')
			msgbroker=json.loads(r.text)['msgbroker']
			IP_msgbroker=msgbroker["IP"]
			PORT_msgbroker=msgbroker["PORT"]
		return IP_msgbroker,PORT_msgbroker
	
	def get_topics(self,resource):
		if self.loggedin:
			r=self.s.get(self.url+'/devices',params={'resources':resource})
			topics=[]
			devices=json.loads(r.text)['devices']
			users=list(devices.keys())
			for user in users:
				for dev in devices[user]:
					if dev["resources"]==resource:
						topics.append(dev['endpoints'])
			return topics
		else:
			return None
		
	def get_contacts(self):
		contacts=None
		if self.loggedin:
			r=self.s.get(self.url+'/contacts')
			contacts=json.loads(r.text)['contacts']
		return contacts
	
	def put_microservice(self,data):
		if self.loggedin:
			r=self.s.put(self.url+'/newmicroservice',data=json.dumps(data))
			return r.status_code
		else:
			return 401



	
class FIFO:
	def __init__(self,nbit=8):
		self.array=[0]*nbit
		self.nbit=nbit
		
	def insert(self,bit):
		self.array.pop(0)
		self.array.append(bit)
		
	def check(self):
		return sum(self.array)==self.nbit
		
	def reset(self):
		self.array=[0]*self.nbit


		
		
		
		


