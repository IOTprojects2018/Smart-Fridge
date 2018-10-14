# Authors: Boretto Luca    <luca.boretto@studenti.polito.it>
#          Carta   Loris   <loris.carta@studenti.polito.it>
#          Jarvand Aysan   <aysan.jarvand@studenti.polito.it>
#		   Toscano Alessia <alessia.toscano@studenti.polito.it>

"""
######################### ThingSpeakAdaptor ############################
This actor:
	- works as mqtt subscriber to obtain data from microservices;
	- works as rest client to obtain data from WebService Catalog and
	  to publish data received from microservices to ThingSpeak.
########################################################################
"""

import json
import time
from lib.TSAutils import GetDataFromWSCatalog,ThingSpeakAdaptor,ms2topic

# Loading settings from configuration file
f=open('data/ThingSpeakAdaptor_config.json')
config=json.loads(f.read())
f.close()

#- ThingSpeakAdaptor main settings
Name=config["name"]
QoS=config["QoS"]
categories=config["categories"]
dictionary=config["vocabulary"]
topics_update_interval=config["topics_update_interval"]

#- ThingSpeakAdaptor settings to access to WebService Catalog
WSC_URL=config["WebServiceCatalog"]["endpoints"]
ADMIN=config["WebServiceCatalog"]["credentials"]["user"]
PASSWORD=config["WebServiceCatalog"]["credentials"]["password"]

#- Address to ThingSpeak
url_thingspeak=config["ThingSpeak"]["url"]

# Login to WebService Catalog
client=GetDataFromWSCatalog(WSC_URL,ADMIN,PASSWORD)
client.start()
# Get message broker's address from WebService Catalog
msgbrIP,msgbrPORT=client.get_msgbroker()

# Get avaiable microservices from WebService Catalog and obtain topics
OK=False
while not OK:
	try:
		microservices=client.get_microservices()
		sub_topics=ms2topic(microservices,categories)
		sub_topics=(sub_topics,QoS)
		OK=True
	except:
		pass
# Init and start ThingSpeakAdaptor
tsa=ThingSpeakAdaptor(Name,url_thingspeak,dictionary)
tsa.start(msgbrIP,msgbrPORT,sub_topics)

while 1:
	# Get ThingSpeak proper write key from WebService Catalog
	tsa.contacts=client.get_contacts()

	# Update topics	
	time.sleep(topics_update_interval)
	try:
		new_topics=ms2topic(client.get_microservices(),categories)
		new_sub_topics=(new_topics,QoS)
		tsa.myUpdate(new_sub_topics,sub_topics)
		sub_topics=new_sub_topics
	except:
		pass
