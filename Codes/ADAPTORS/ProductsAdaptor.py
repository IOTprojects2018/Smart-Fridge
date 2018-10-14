# Authors: Boretto Luca    <luca.boretto@studenti.polito.it>
#          Carta   Loris   <loris.carta@studenti.polito.it>
#          Jarvand Aysan   <aysan.jarvand@studenti.polito.it>
#		   Toscano Alessia <alessia.toscano@studenti.polito.it>

"""
######################### ProductsAdaptor ############################
This actor:
	- works as mqtt subscriber to obtain data from microservices;
	- works as rest client to obtain data from WebService Catalog and
	  to publish data received from microservices to Products server.
########################################################################
"""

import json
import time
from lib.PAutils import ProductsAdaptor,GetDataFromWSCatalog,ms2topic

# Loading settings from configuration file
f=open('data/ProductsAdaptor_config.json')
config=json.loads(f.read())
f.close()

#- ProductsAdaptor main settings
Name=config["name"]
QoS=config["QoS"]
categories=config["categories"]
topics_update_interval=config["topics_update_interval"]
KEY=config["key4ProductsWS"]


#- ProductsAdaptor settings to access to WebService Catalog
WSC_URL=config["WebServiceCatalog"]["endpoints"]
ADMIN=config["WebServiceCatalog"]["credentials"]["user"]
PASSWORD=config["WebServiceCatalog"]["credentials"]["password"]

# Login to WebService Catalog
client=GetDataFromWSCatalog(WSC_URL,ADMIN,PASSWORD)
client.start()

#- Address to Products service and Barcode2Product service from WebService Catalog
WSname=config["ProductsWS"]["microserviceID"]
url_ProductsWS=client.get_ServerURL(WSname)
WSname=config["Barcode2ProductWS"]["microserviceID"]
barcode2products=client.get_ServerURL(WSname)

print ("ProductWS: "+url_ProductsWS)
print ("Barcode2ProductWS: "+barcode2products)

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

# Init and start ProductsAdaptor
pa=ProductsAdaptor(Name,url_ProductsWS,KEY,categories,barcode2products)
pa.start(msgbrIP,msgbrPORT,sub_topics)

while 1:
	# Update topics	
	time.sleep(topics_update_interval)
	try:
		new_topics=ms2topic(client.get_microservices(),categories)
		new_sub_topics=(new_topics,QoS)
		pa.myUpdate(new_sub_topics,sub_topics)
		sub_topics=new_sub_topics
	except:
		pass
