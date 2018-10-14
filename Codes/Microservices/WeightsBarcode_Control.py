#!/usr/bin/python

# Authors: Boretto Luca    <luca.boretto@studenti.polito.it>
#          Carta   Loris   <loris.carta@studenti.polito.it>
#          Jarvand Aysan   <aysan.jarvand@studenti.polito.it>
#		   Toscano Alessia <alessia.toscano@studenti.polito.it>


import time
from lib.utilities import WebServiceClient,MicroServicePubSub
import json

f=open("data/BarcodeWeightService_config.json")
config=json.loads(f.read())
QoS=config["QoS"]
name1=config["name1"]
name2=config["name2"]
resource1=config["resource1"]
endpoints1=config["endpoints1"]
resource2=config["resource2"]
endpoints2=config["endpoints2"]

WSC_URL=config["WSCatalog"]["url"]
ADMIN=config["WSCatalog"]["credentials"]["user"]
PASSWORD=config["WSCatalog"]["credentials"]["password"]


OK=False
while not OK:
	wsc=WebServiceClient(WSC_URL,ADMIN,PASSWORD)
	ans=wsc.start()
	if ans==200:
		OK=True
	else:
		time.sleep(10)

IP_msgbroker, PORT_msgbroker=wsc.get_msgbroker()

OK=False
while not OK:
	try:
		topics1=wsc.get_topics(resource1)
		sub_topics1=[('/'.join(topic.encode().split('/')[1:]),QoS) for topic in topics1]
		topics2=wsc.get_topics(resource2)
		sub_topics2=[('/'.join(topic.encode().split('/')[1:]),QoS) for topic in topics2]
		sub_topics=sub_topics1+sub_topics2
		OK=True
	except:
		pass

name=resource1+resource2+"MicroService"	
test=MicroServicePubSub(name)
test.QoS=QoS
test.start(IP_msgbroker, PORT_msgbroker, sub_topic=sub_topics)

endpoints1=IP_msgbroker+':'+str(PORT_msgbroker)+endpoints1
endpoints2=IP_msgbroker+':'+str(PORT_msgbroker)+endpoints2
data1={'microserviceID':name1,'category':resource1,'endpoints':endpoints1,'protocol':'mqtt'}
data2={'microserviceID':name2,'category':resource2,'endpoints':endpoints1,'protocol':'mqtt'}

while 1:
	time.sleep(5)
	wsc.put_microservice(data1)
	wsc.put_microservice(data2)	
	
	try:
		new_topics1=wsc.get_topics(resource1)
		new_topics2=wsc.get_topics(resource2)
		new_topics=new_topics1+new_topics2
		
		new_sub_topics=[('/'.join(topic.encode().split('/')[1:]),QoS) for topic in new_topics]

		test.myUpdate(new_sub_topics,sub_topics)
		sub_topics=new_sub_topics
	except:
		pass
