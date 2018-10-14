# Authors: Boretto Luca    <luca.boretto@studenti.polito.it>
#          Carta   Loris   <loris.carta@studenti.polito.it>
#          Jarvand Aysan   <aysan.jarvand@studenti.polito.it>
#		   Toscano Alessia <alessia.toscano@studenti.polito.it>


import numpy as np
import zbar

class FIFO:
	""" Buffer FIFO a N bit """
	def __init__(self,nbit=8):
		self.array=[0]*nbit
		self.nbit=nbit
		
	def insert(self,bit):
		""" Insert a value into the lowest bit """
		self.array.pop(0)
		self.array.append(bit)
		
	def check(self):
		""" Check if the buffer is full """
		return sum(self.array)==self.nbit
		
	def reset(self):
		""" Clear the buffer """
		self.array=[0]*self.nbit

class BarCodeReader:
	""" Barcode reader simulator """
	def __init__(self,source=0):
		# create a Processor
		self.proc = zbar.Processor()
		# configure the Processor
		self.proc.parse_config('enable')
		# initialize the Processor
		device = '/dev/video'+str(source)
		self.proc.init(device)

	def start(self):

		# enable the preview window
		self.proc.visible = True
		# read at least one barcode (or until window closed)
		out=self.proc.process_one(timeout=30)
		# hide the preview window
		self.proc.visible = False		
		if out>0:
			# extract results
			for symbol in self.proc.results:
				# do something useful with results
				barcode=symbol.data
				tipo=symbol.type
		else:
			barcode=None
			tipo=None
		return barcode, tipo
