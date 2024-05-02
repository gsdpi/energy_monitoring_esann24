#coding=utf-8
#Título:
#
#Autor: Diego García Pérez
#Fecha:
#Descripción: mediator class 




class mediator(object):
	"""Declarative class for the mediator"""
	def __init__(self, init_js):
		self.init_js = init_js
		self.id = id(self)

		# Instance of the JS mediator that handles all the events from dataCube.js and MP.js
		self.init_js += " \n objects['%s'] = mediator() \n"%self.id


	def getDummyCallback(self):
		return self.init_js

	def getID(self):
		return self.id



