# Authors: Boretto Luca    <luca.boretto@studenti.polito.it>
#          Carta   Loris   <loris.carta@studenti.polito.it>
#          Jarvand Aysan   <aysan.jarvand@studenti.polito.it>
#		   Toscano Alessia <alessia.toscano@studenti.polito.it>

import Adafruit_DHT
import RPi.GPIO as GPIO
from lib.hx711 import HX711
from lib.barcode_utils import BarCodeReader, FIFO

class SensorManager(object):
	""" This object lets to manage different sensors"""
	def __init__(self):
		pass
		
	def Temperature(self,pin=11,name=17):
		""" Temperature sensor """
		_, temperature = Adafruit_DHT.read_retry(pin,name)
		return temperature
	
	def Humidity(self,pin=11,name=17):
		""" Humidity sensor """
		humidity, _ = Adafruit_DHT.read_retry(pin,name)
		return humidity
	
	def Motion(self,pin=13):
		""" Motion sensor """
		GPIO.setwarnings(False)
		GPIO.setmode(GPIO.BOARD)
		GPIO.setup(pin,GPIO.IN)
		out=GPIO.input(pin)
		return out
	
	def Weight(self, DT=29, SCK=31, reference_unit=-105, n_samples_avg=5, dev=None):
		""" Weight sensor """
		if dev is None:
			dev = HX711(DT, SCK)
			dev.set_reading_format("LSB", "MSB")
			dev.set_reference_unit(reference_unit)
			dev.reset()
			dev.tare()
			return dev
		else:
			weight = max(0, int(dev.get_weight(n_samples_avg)))
			return weight
	
	def Barcode(self, source=0, dev=None):
		""" Webcam used as barcode reader """		
		if dev is None:
			dev=BarCodeReader(source)
			return dev
		else:
			barcode, tipo=dev.start()
			return barcode
		

		
	
