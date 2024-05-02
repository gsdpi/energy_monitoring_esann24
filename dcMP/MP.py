#coding=utf-8
#Título:
#
#Autor:
#Fecha:
#Descripción: 

from bokeh.models import Button, CustomJS, RangeSlider, Div, ColumnDataSource, Slider,Dropdown
from bokeh.layouts import row, column, layout
from bokeh.plotting import figure
import numpy as np



class MP(object):
	"""
	Declarative class for the MP:
		
		Create the MP.js object
		Add the encodings to MP.js
		Indicate the att by which the resulting aggregation will be computed  

	"""
	def __init__(self, init_js,datacube,softGrouping=False,**kwargs):
		self.init_js = init_js
		self.id = id(self)
		self.datacube = datacube
		self.mediator = kwargs.get("mediator",None)

		if softGrouping:
			softG = "true"
		else:
			softG = "false"
		# Create the instace of the equivalent javascript's object
		self.init_js = init_js + " \n objects['%s'] = MP('%s', objects['%s'],%s)"%(self.id,self.id, self.datacube.getID(),softG)

		# If a mediator object is passed, the MP.js object is included in the mediator as an active element
		if(self.mediator):
			self.init_js += f"\n objects['{self.mediator.getID()}'].activeElements(['MP_{self.id}'],[objects['{self.id}']])"


	def addEncoding(self,att,title,lookup=None,typeEnc = None):
		# Add the callback for that encoding
		if typeEnc == "custom":
			self.init_js = self.init_js + " \n objects['%s'].addEncoding('%s',%s,'%s')"%(self.id,att,lookup,typeEnc)
			
		else:
			self.init_js = self.init_js + " \n objects['%s'].addEncoding('%s',undefined,'%s')"%(self.id,att,typeEnc)
			

	def addAtt(self,att):
		# Add an att by which the elements of each group's bin will be aggregated 
		self.init_js = self.init_js + "\n objects['%s'].addAtt('%s')"%(self.id,att)

	def getDummyCallback(self):
		# Get dummy callback or init.js used to create the MP.js object in JS side.
		return self.init_js

	def getID(self):
		return self.id

	def onUpdatePoints(self,callback):
		"""
			It attaches a callback that will be called after updating the position of the points.
			This method is useful for updating all the views/plots/graphs that visualize the MP points
		"""
		if self.mediator:
			self.init_js +=  f"\n objects['{self.mediator.getID()}'].subscribe('MP_{self.id}.updatePoints',{callback});"
		else:
			raise AttributeError("There is no mediator associated to this object");

		return None

	def changeEnc(self,att,v):
		self.init_js = self.init_js + "\n objects['%s'].changeEnc('%s',%f)"%(self.id,att,v)

	def excludeEnc(self,att):
		self.init_js = self.init_js + "\n objects['%s'].excludeEnc('%s')"%(self.id,att)		

	def onUpdateMPGroups(self,callback):
		"""
			It attaches a callback that will be called after updating the position of the points.
			This method is useful for updating all the views/plots/graphs that visualize the MP points
		"""
		if self.mediator:
			self.init_js +=  f"\n objects['{self.mediator.getID()}'].subscribe('MP_{self.id}.updateMPGroups',{callback});"
		else:
			raise AttributeError("There is no mediator associated to this object");

		return None