# Authors: Boretto Luca    <luca.boretto@studenti.polito.it>
#          Carta   Loris   <loris.carta@studenti.polito.it>
#          Jarvand Aysan   <aysan.jarvand@studenti.polito.it>
#		   Toscano Alessia <alessia.toscano@studenti.polito.it>

import time
import json
import requests
from lib.MySensors import SensorManager
from lib.MyMQTT import PubSub
from lib.barcode_utils import FIFO
import datetime


class SenseSend:
	def __init__(self, WSC_URL, USER_PATH, deviceID, resource, unit='', 
				 QoS=2, dt=1, pin=None,name=None, DT=None, SCK=None, 
				 reference_unit=None, n_samples_avg=None, source=None, threshold=None):
		
		# General parameters
		self.WSC_URL=WSC_URL
		self.USER_PATH=USER_PATH
		self.deviceID=deviceID
		self.resource=resource
		self.unit=unit
		self.QoS=QoS
		self.dt=dt
		self.user=None
		self.typeOfDevice="Raspberry"
		
		# Init sensor manager object
		self.sensor=SensorManager()
		
		# Particular parameters
		self.sensor_config={}
		if pin is not None:
			self.sensor_config["pin"]=pin
		if name is not None:
			self.sensor_config["name"]=name
		if DT is not None:
			self.sensor_config["DT"]=DT
		if SCK is not None:
			self.sensor_config["SCK"]=SCK
		if reference_unit is not None:
			self.sensor_config["reference_unit"]=reference_unit
		if n_samples_avg is not None:
			self.sensor_config["n_samples_avg"]=n_samples_avg
		if source is not None:
			self.sensor_config["source"]=source
		if threshold is not None:
			self.threshold=threshold
		self.jj={}
		

			
	def start(self):
		""" Start PubSub"""
		# Get coupled user's credentials
		self.get_credentials()
		
		# Start a new session and Login to Web Service Catalog
		r=self.login()
		# If access is completed start next steps
		if r.status_code==200:
			
			# Get info about message broker
			self.get_msgBroker()
			# Initialize an MQTT Publisher/Subscriber
			self.clientID=self.user+"_"+self.deviceID
			self.test = PubSub(self.clientID)
			# Start it
			if self.resource=="barcode":
				# Define topics to follow
				pr=self.typeOfDevice+'/'+self.user
				pr=pr.encode()
				self.sub_Topics=[(pr+'/motion/Motion1',2)]#,(pr+'/weight/Weight1',2)]
				self.test.start(self.IPmsgBroker,self.PORTmsgBroker,self.sub_Topics)
				# init an 8 bit FIFO buffer to monitor the motion
				self.fifo=FIFO(8)
			else:
				self.test.start(self.IPmsgBroker,self.PORTmsgBroker)
			
			print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"- "+self.clientID+' Publisher/Subscriber started')
			
			# Define a topic for publishing
			self.pub_Topic=self.typeOfDevice+'/'+self.user+'/'+self.resource+'/'+self.deviceID
			# Generate endpoints
			self.endpoints=self.IPmsgBroker+':'+str(self.PORTmsgBroker)+'/'+self.pub_Topic
			
			# Get the proper function for the selected sensor
			self.function=getattr(self.sensor,self.resource.capitalize())
			
			# Barcode reader and Scale need to be initialized
			if self.resource == "barcode" or self.resource == "weight":
				self.sensor_config["dev"]=self.function(**self.sensor_config)
			
			if self.resource not in self.jj.keys():
				self.jj[self.resource]=0
			
			try:
				while 1:
					# Get value from sensor, convert data to SenML and 
					# publish to topic
					self.get_value()
					# Add a new device in user devices
					if self.resource not in ["barcode","motion"] or (self.resource in ["barcode","motion"] and self.jj[self.resource]%10==0):
						self.put_device()
					# Wait
					self.jj[self.resource]+=1
					time.sleep(self.dt)
			except KeyboardInterrupt:
				self.stop()
				
	def stop(self):
		""" Stop PubSub"""
		self.test.stop()
		print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"- "+self.ClientID+' Publisher/Subscriber stopped')
		
	def get_credentials(self):
		""" Get credentials of the coupled user from a specific file """
		while self.user is None:
			try:
				# Read authentication parameters	
				f=open(self.USER_PATH,'r')
				self.credentials=json.loads(f.read())
				self.user=self.credentials['user']
				f.close()
			except:
				time.sleep(10)
				
	def login(self):
		""" Login to Web Service Catalog"""
		# Start a new session
		self.s=requests.Session()
		# Login to Web Service Catalog
		r=self.s.post(self.WSC_URL+'/login',data=json.dumps(self.credentials))
		return r
		
	def get_msgBroker(self):
		""" Get message broker info"""
		r=self.s.get(self.WSC_URL+'/msgbroker')
		msgBroker=json.loads(r.text)['msgbroker']
		self.IPmsgBroker=msgBroker['IP']
		self.PORTmsgBroker=msgBroker['PORT']
		return r
		
	def get_value(self):
		""" Get a value from the sensor and send it"""
		OK=True
		if self.resource == "barcode":
			OK=self.barcodemotion_check() 
		if OK:
			self.value=self.function(**self.sensor_config)
			# Convert data to SenML and publish to topic
			if self.value is not None:
				self.send_message()
	
	def barcodemotion_check(self):
		""" Check that motion buffer is full before starting a new
			barcode acquisition """

		try:
			pr=self.typeOfDevice+'/'+self.user
			pr=pr.encode()
			self.fifo.insert(json.loads(self.test.DATA[pr+'/motion/Motion1'])['e'][0]['v'])
			return self.fifo.check()
		except:
			print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"- "+'Barcode: < Motion data not found >')	
			return False
	
	def send_message(self):
		""" Convert data to SenML format and publish message to topic"""
		message = {"bn":self.endpoints,"e":[{ "n": self.resource, "u":self.unit, "t": time.time(), "v":self.value }]}
		if self.resource=='temperature':
			message["e"][0]["tr"]=self.threshold
		message=json.dumps(message)
		self.test.myPublish (self.pub_Topic, message,self.QoS)
		print("")
		print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"- "+'PUBLISHING: '+self.resource+' ' +str(self.value)+' '+ self.unit)
		print ('on '+self.pub_Topic)
		print ('current message: ') 
		print (message)
		print("")
		if self.resource=="barcode":
			time.sleep(5)

	def put_device(self):
		""" Update devices list with sensor"""
		print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"- "+"Putting "+self.user+"'s "+self.deviceID+ " information on WebService Catalog")
		self.s.put(self.WSC_URL+'/newdevice',data=json.dumps({'deviceID':self.deviceID,'resources':self.resource,'endpoints':self.endpoints,"protocol":"MQTT"}))
