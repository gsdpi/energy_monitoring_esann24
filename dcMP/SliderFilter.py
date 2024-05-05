#coding=utf-8
#Título: Slider-based filter 
#
#Author: Diego García Pérez
#Fecha: 02/05/23
#Descripción: Slider able to filter the datacube

from bokeh.models import  CustomJS, Div,Slider, ColumnDataSource, Select,BoxSelectTool, RangeTool,CustomAction,RangeSlider
from bokeh.models.ranges import Range1d
from bokeh.layouts import row, column, layout
from bokeh.plotting import figure
import numpy as np
import pandas as pd
from os import path 
import ipdb


class SliderFilter(object):
	"""
	Declarative class for the SliderFilter:
		
		- It creates a group within our datacube object in order to project available data into it (It doesnt show the aggregation)
		
		- It is able to filter the datacube by filtering on the created group

	PARAMETERS:

		init_js (string):      				Required for initializing JS objects
		
		datacube (datacube object): 		Datacube python object by which the data to be represented will be extracted
		
		name (string): 						Slider identifier. The configuration of this ihist will be placed in objects[name] and the group
											associated to the hist will have the same name.
		
		projection (string): 				X axis and the attribute by which the data will be projected by means of the datacube
		
		width: 								Width of the resulting bokeh figure

		nbar: 								Maximum number of bars in the histogram

	METHODS



	"""



	def __init__(self, init_js,datacube,**kwargs):

		self.init_js = init_js
		self.name    = kwargs.get("name",id(self))
		self.prjAtt  = kwargs.get("projection",None)
		self.AggFn   = kwargs.get("aggregation","count")
		self.mea     = kwargs.get("measure",None)
		self.width   = kwargs.get("width",300)
		self.height  = kwargs.get("height",300)
		self.nbar    = kwargs.get("nbar",90)
		self.alpha   = kwargs.get("alpha",0.8)


		self.select_width = int(self.width/2)
		self.id = "SliderFilter_" + self.name 
		self.datacube = datacube 
		self.eps    = 1e-5

		######## INITIAL CONFIGURATION OF THE iHIST  IN JS ##########
		# Field in objects that host the iHist configuration
		self.init_js +=  " \n objects['%s'] = Object()"%self.id

		# Projection att
		if self.prjAtt:
			self.init_js +=  " \n objects['%s']['Prj'] = '%s' \n "%(self.id,self.prjAtt)
		else:
			self.init_js +=  " \n objects['%s']['Prj'] = objects['%s'].availableAtt()[0] \n "%(self.id,self.datacube.getID())

		# Measure
		self.init_js +=  " \n objects['%s']['Mea'] = objects['%s'].availableAtt()[0] \n "%(self.id,self.datacube.getID())

		# Number of bins,
		self.init_js  += " \n objects['%s']['nbar']= %s"%(self.id,self.nbar)
		self.init_js  += " \n objects['%s']['alpha']= %s"%(self.id,self.alpha)

		self.init_js  += f"""\n
							objects['{self.id}'].getReso = function(att){{ 
							var reso;

							if(objects['{self.datacube.getID()}'].getDataInfo()[att].n_unique > objects['{self.id}']['nbar'])
							 	reso = (1/objects['{self.id}']['nbar'])*(objects['{self.datacube.getID()}'].getDataInfo()[att].max - objects['{self.datacube.getID()}'].getDataInfo()[att].min)
							else
								reso = undefined

							return reso;
							}}
							 """

		self.init_js += f"objects['{self.id}']['reso'] = objects['{self.id}'].getReso(objects['{self.id}']['Prj'])"; 
		######### DATACUBE CONFIGURATION ####¡################
		# New datacube group
		self.init_js += f"""
		\n
		 var config = objects['{self.id}']
		 objects['{self.datacube.getID()}'].group('{self.id}',config['Prj'],config['reso'], config['Mea'])
		 \n

		 """


		# Bokeh objects

		############### SLIDER  ###############   
	
		self.SliderFilter_tool = RangeSlider(start=-9, end=9, value=(-9,9), step=.1, title="Filter",name = "SliderFilterG_"+self.id)
		self.init_js += f" \n Bokeh.documents[0].get_model_by_name('{self.SliderFilter_tool.name}').start = objects['{self.datacube.getID()}'].getDataInfo()['{self.prjAtt}'].min"
		self.init_js += f" \n Bokeh.documents[0].get_model_by_name('{self.SliderFilter_tool.name}').end = objects['{self.datacube.getID()}'].getDataInfo()['{self.prjAtt}'].max"
		#self.init_js += f" \n Bokeh.documents[0].get_model_by_name('{self.SliderFilter_tool.name}').value = (objects['{self.datacube.getID()}'].getDataInfo()['{self.prjAtt}'].min,objects['{self.datacube.getID()}'].getDataInfo()['{self.prjAtt}'].max)"

		################ FILTER CALLBACK  ################
    	# 1) filter the datacube according to the start end valores of the rangeTool 
		self.sliderFilterCllbck = CustomJS(args = dict(dtCb_id = self.datacube.getID(),
												   gName   = self.id),
									  code = 
											"""											
												var min_v = this.value[0]
												var max_v = this.value[1]
												
												objects[dtCb_id].filter(gName,[min_v,max_v])
											""")


		self.SliderFilter_tool.js_on_change("value", self.sliderFilterCllbck)


		############### COMBOBOXES  ###############

		# Projection
		self.SelectPrj_menu = ["Item2","item2"] # dumy opts
		self.SelectPrj = Select(title = " ",options = self.SelectPrj_menu,max_width= self.select_width,name = "SelPrj_"+self.id)
		self.init_js += " \n Bokeh.documents[0].get_model_by_name('%s').options = objects['%s'].availableAtt()"%(self.SelectPrj.name,self.datacube.getID())
		self.init_js += " \n Bokeh.documents[0].get_model_by_name('%s').value = objects['%s']['Prj']"%(self.SelectPrj.name,self.id)

		############   PROJECTION CALLBACK   ############
		# 1) Redefine the datacube projection. 
		# 2) Update of the resolution of the new group
		# 3) Update the range of the slider



		self.SelectPrj_callbck = CustomJS( args      = dict(dtCbID = self.datacube.getID(),
										   					id_group  = self.id,
										   					eps       = self.eps,
										   					slider	  = self.SliderFilter_tool),
										    code="""

													// Update datacube
													objects[id_group]['Prj'] =  this.value
													objects[id_group]['reso'] =  objects[id_group].getReso(objects[id_group]['Prj']);
													objects[dtCbID].filter(id_group,null)
													
													objects[dtCbID].group(id_group,objects[id_group]['Prj'],objects[id_group]['reso'], config['Mea'] )

													//update slider range
													slider.start = objects[dtCbID].getDataInfo()[this.value].min-1
													slider.end = objects[dtCbID].getDataInfo()[this.value].max+1
													
													slider.value = [slider.start,slider.end]
											""")
		
		self.SelectPrj.js_on_change("value", self.SelectPrj_callbck)




		


		############### DATACUBE CHANGES ###############
		# When the datacube is modified the bars (number, width, position and height) and the labels are updated.  


	def getBokehObject(self):
			return column(row(self.SelectPrj,self.SliderFilter_tool));

	def getDummyCallback(self):
	# Get dummy callback or init.js used to create the MP.js object in JS side.
		return self.init_js

	def getID(self):
		return self.id
