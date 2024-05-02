#coding=utf-8
#Título:
#
#Autor: Diego García Pérez
#Fecha:
#Descripción: Clase para el cubo de datos

from bokeh.models import Button, CustomJS, RangeSlider, Div, ColumnDataSource, Slider,Dropdown
from bokeh.layouts import row, column, layout
from bokeh.plotting import figure
import numpy as np


class DataCube(object):
	"""Declarative class for the datacube"""
	def __init__(self, init_js,datos,**kwargs):
		self.init_js = init_js
		self.id = id(self)
		self.datos = datos
		# Create the instace of the equivalent javascript's object
		self.init_js = init_js + " var dat = %s \n objects['%s'] =  DataCube(dat)"%(self.datos,self.id)
		self.mediator = kwargs.get("mediator",None)
		
		# The mediator that handles the "update" events from datacube is created
		if self.mediator:
			self.init_js += "\n objects['%s'].activeElements(['datacube'],[objects['%s']])"%(self.mediator.getID(),self.id)
			self.medInJS = "objects['%s']"%self.mediator.getID()
		else:
			self.init_js += " \n var med = mediator().activeElements(['datacube'],[objects['%s']])"%self.id
			self.medInJS = "med"
			# Poner aviso!
			


	def getDummyCallback(self):
		return self.init_js

	def getID(self):
		return self.id

	def onUpdate(self,callback):
		"""
			It attaches a callback that will be called after an operation on the datacube.
			This method is useful for updating all the views/plots/graphs that visualize the datacube  
		"""
		self.init_js += f"\n {self.medInJS}.subscribe('datacube.update',{callback})"

		return None

