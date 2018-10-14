# Authors: Boretto Luca    <luca.boretto@studenti.polito.it>
#          Carta   Loris   <loris.carta@studenti.polito.it>
#          Jarvand Aysan   <aysan.jarvand@studenti.polito.it>
#		   Toscano Alessia <alessia.toscano@studenti.polito.it>


import paho.mqtt.client as MQTT

class PubSub:
	def __init__(self,clientID):
		
		self.clientID=clientID

		#create an instance of paho.mqtt.client
		self._paho_mqtt=MQTT.Client(self.clientID,clean_session=True)
		
		#register the callbacks
		self._paho_mqtt.on_connect=self.myOnConnect
		self._paho_mqtt.on_message=self.myOnMessageReceived
		
		# initalize Data in SenML Dataformat
		self.DATA={}
		
	def start(self, url, port, sub_topic=None):
		# connection to broker
		self._paho_mqtt.connect(url,port)
		self._paho_mqtt.loop_start()
		
		# if it's also subscriber, subscribe to a topic
		if sub_topic is not None:
			self._paho_mqtt.subscribe(sub_topic)
	
	def stop(self, sub_topic=None):

		# if it's also subscriber, subscribe to a topic		
		if sub_topic is not None:
			self._paho_mqtt.unsubscribe(sub_topic)
		
		self._paho_mqtt.loop_stop()
		self._paho_mqtt.disconnect()
	
	def myPublish(self,topic,message,QoS):
		
		# publish a message on a certain topic
		self._paho_mqtt.publish(topic, message, QoS,retain=False)
		
	def myOnConnect(self, paho_mqtt, userdata, flags, rc):
		print ("connected to message broker with rc" + str(rc))
	
	def myOnMessageReceived(self, paho_mqtt, userdata, msg):
		print ("Received __ Topic: " + msg.topic + " QoS: "+ str(msg.qos) +"Message: "+msg.payload)
		# update Data
		self.DATA[msg.topic]=msg.payload
