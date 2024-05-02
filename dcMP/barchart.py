#coding=utf-8
#Título: Interactive barchart in bokeh
#
#Autor: Diego García Pérez
#Fecha:
#Descripción: 

from bokeh.models import Button, CustomJS, RangeSlider, Div, ColumnDataSource, Slider,Dropdown
from bokeh.layouts import row, column, layout
from bokeh.plotting import figure
import numpy as np


class barchart(object):
	"""
	Declarative class for defining an interactive barchart capable of interacte with
	a crossfilter-based datacube 
	"""
	def __init__(self, init_js, datacube,att,lims,name):
		self.init_js = init_js
		self.id = id(self)
		self.att = att
		self.datacube = datacube
		# Create the instance of the equivalent javascript's object
		self.init_js = init_js + " \n objects['%s'].group('%s','%s',undefined,'%s')"%(self.datacube.getID(),"BC_"+str(self.id),self.att,self.att)
		slider = Slider(start=lims[0], end=lims[1], value=lims[1], step=1, title=name)

		self.layout = [slider]
		callback = CustomJS(args=dict(s=slider, group = "BC_"+str(self.id)),
                    code="""
                    		objects['%s'].filter(group, [0,s.value])
				"""%self.datacube.getID())
		slider.js_on_change("value",callback)
	def getLayout(self):
		return self.layout
		