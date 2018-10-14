#!/usr/bin/env python3

# Authors: Boretto Luca    <luca.boretto@studenti.polito.it>
#          Carta   Loris   <loris.carta@studenti.polito.it>
#          Jarvand Aysan   <aysan.jarvand@studenti.polito.it>
#		   Toscano Alessia <alessia.toscano@studenti.polito.it>

import threading
import json
from lib.SenseSend import SenseSend
import time

 
class RaspThread (threading.Thread):
	
	def __init__(self, threadID, name, p):
		threading.Thread.__init__(self)
		self.threadID=threadID
		self.name = name
		self.params= dict(p)

	def run(self):
		print ("Thread#" + self.name + " started")
		sensor=SenseSend(**self.params)
		sensor.start()
		print ("Thread#" + self.name + " stopped")

if __name__=="__main__":
	
	# init
	global USER_PATH
	USER_PATH='data/config.json'

	f=open(USER_PATH)	
	global WSC_URL  
	WSC_URL=json.loads(f.read())["WebServiceCatalog"]
	f.close()

	f=open('data/sensors_config.json')
	config=json.loads(f.read())
	f.close()

	kinds=config.keys()
	threads=[]
	k=0
	for kind in kinds:
		for i in range(len(config[kind])):
			i_config=config[kind][i]
			i_config["WSC_URL"]=WSC_URL
			i_config["USER_PATH"]=USER_PATH
			i_thread=RaspThread(k,i_config["deviceID"], dict(i_config))
			threads.append(i_thread)
			k+=1
			i_thread.start()
			time.sleep(2)
