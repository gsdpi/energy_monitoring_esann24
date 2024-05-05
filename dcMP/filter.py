#coding=utf-8
#Título: Slider-based filter 
#
#Author: Diego García Pérez
#Fecha: 02/05/23
#Descripción: Slider able to filter the datacube

from bokeh.models import  CustomJS, Div, ColumnDataSource, Select,BoxSelectTool, RangeTool,CustomAction
from bokeh.models.ranges import Range1d
from bokeh.layouts import row, column, layout
from bokeh.plotting import figure
import numpy as np
import pandas as pd
from os import path 
import ipdb


class SliderFilter(object):
	"""
	Declarative class for the ihist:
		
		- It creates a group within our datacube object in order to project available data into it and show the resulting aggregated data in the hist
		
		- Dimension(s) of the group, resolution, dimension by which the outcome aggregated values will be computed.

	PARAMETERS:

		init_js (string):      				Required for initializing JS objects
		
		datacube (datacube object): 		Datacube python object by which the data to be represented will be extracted
		
		name (string): 						iHist identifier. The configuration of this ihist will be placed in objects[name] and the group
											associated to the hist will have the same name.
		
		projection (string): 				X axis and the attribute by which the data will be projected by means of the datacube
		
		measure (string): 					Y axis when the aggregation function is different from count.

		aggregarion (string): 				Aggregation function among 'count', 'sum', 'avg'

		width: 								Width of the resulting bokeh figure

		height: 							Height of the resulting bokeh figure

		nbar: 								Maximum number of bars in the histogram

		alpha: 								Bar width ratio [0,1]. With alpha = 1, there will be no space between bars.



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
		self.color   = kwargs.get("color","#0669BC")


		self.select_width = int(self.width/2)
		self.id = "hist_" + self.name 
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

		# Agg function
		self.init_js +=  " \n objects['%s']['Agg'] = '%s' \n "%(self.id,self.AggFn)

		# Measure of the agg
		if self.mea:
			self.init_js +=  " \n objects['%s']['Mea'] = '%s' \n "%(self.id,self.mea)
		else:
			self.init_js +=  " \n objects['%s']['Mea'] = objects['%s'].availableAtt()[0] \n "%(self.id,self.datacube.getID())

		# Number of bars, bars width and width ratio (alpha)
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

		############### HISTOGRAM  ###############   
		# Dummy datasource
		self.DataSource = ColumnDataSource({ 'x':[0,0],
											  'y': [0,0],
											  'right': [0,0],
											  'left': [0,0]},name = "%s"%self.id);

		# Figure
		self.histFig = figure( plot_width = self.width, 
		                  plot_height = self.height,
		                  title = "",
		                  x_axis_label = self.prjAtt,
		                  y_axis_label = self.AggFn,
		                  name = "fig_"+self.id)
		# Bars
		self.histFig.quad(bottom=0, 
		           top='y', 
		           left='left', 
		           right='right', 
		           source=self.DataSource,
		           fill_color=self.color,
		           hover_fill_alpha=0.7,
		           hover_fill_color=self.color,
		           line_color=self.color)

		# Add the range tool to the graph
		self.histFig.tools = []

		self.range_tool = RangeTool(x_range=Range1d(0,10),name= "range_"+self.id) # 1d range is initially defined with dummy min/max values
    	
    	################ FILTER CALLBACK  ################
    	# 1) filter the datacube according to the start end valores of the rangeTool 
		self.range_toolCllb = CustomJS(args = dict(dtCb_id = self.datacube.getID(),
												   gName   = self.id),
									  code = 
											"""
												console.log(cb_obj.attributes.start,cb_obj.attributes.end)
												var min_v = cb_obj.attributes.start
												var max_v = cb_obj.attributes.end
												objects[dtCb_id].filter(gName,[min_v,max_v])
											""")

		self.range_tool.x_range.js_on_change('start',self.range_toolCllb)
		self.range_tool.x_range.js_on_change('end',self.range_toolCllb)


		############### RESET FILTER CALLBACK  ####################
		# 1) hide rangeTool
		# 2) reset active filter
		# 3) deactivate the rangetool

		self.resetFilter_callback = CustomJS(args = dict(dtCb_id   = self.datacube.getID(),
														 gName     = self.id,
														 rangeTool = self.range_tool,
														 eps       = self.eps),


											code = """
														var filterState = rangeTool.active
														var start       = 0
														var end         = 0

														if(filterState){
															objects[dtCb_id].filter(gName,null)
														}
														
														else{

															start = objects[dtCb_id].getDataInfo()[objects[gName]['Prj']].min - eps
															end = objects[dtCb_id].getDataInfo()[objects[gName]['Prj']].max + eps
															
															rangeTool.x_range.start = start
															rangeTool.x_range.end = end

														}
														
														rangeTool.overlay.visible = !rangeTool.overlay.visible 
														rangeTool.active = !rangeTool.active



													""")


		self.resetFilter_tool = CustomAction(icon=path.join(path.split(__file__)[0], "reset.png"),
                    						 callback=self.resetFilter_callback,
                    						 action_tooltip = "ON/OFF filter")


		self.histFig.add_tools(self.resetFilter_tool)
		self.histFig.add_tools(self.range_tool)

		#self.histFig.toolbar.autohide = True
		self.histFig.toolbar.logo = None
		############### COMBOBOXES  ###############

		# Projection
		self.SelectPrj_menu = ["Item2","item2"] # dumy opts
		self.SelectPrj = Select(title = "Projection",options = self.SelectPrj_menu,max_width= self.select_width,name = "SelPrj_"+self.id)
		self.init_js += " \n Bokeh.documents[0].get_model_by_name('%s').options = objects['%s'].availableAtt()"%(self.SelectPrj.name,self.datacube.getID())
		self.init_js += " \n Bokeh.documents[0].get_model_by_name('%s').value = objects['%s']['Prj']"%(self.SelectPrj.name,self.id)

		# Aggregation
		self.SelectAggFn_menu = ["count","sum","avg"]
		self.SelectAggFn = Select(title = "Aggregation",options = self.SelectAggFn_menu,max_width= self.select_width)
		

		# Measure
		self.SelectAggMea_menu = ["Var1","Var2","Var3"] # dumy opts
		self.SelectAggMea = Select(title = "Measure",options = self.SelectAggMea_menu,max_width= self.select_width,name = "SelMea_"+self.id)
		self.init_js += " \n Bokeh.documents[0].get_model_by_name('%s').options = objects['%s'].availableAtt()"%(self.SelectAggMea.name,self.datacube.getID())


		############   PROJECTION CALLBACK   ############
		# 1)Redefine the datacube projection. 
		# 2) Update of the resolution of the new group
		# 2) update objects with the new config
		# 3) update the range in RangeTool
		# 4) update labels of the figure
		# 5) Hide the rangetool object

		self.SelectPrj_callbck = CustomJS( args      = dict(dtCbID = self.datacube.getID(),
										   xAxis     = self.histFig.xaxis[0],
										   title     = self.histFig.title,
										   id_group  = self.id,
										   rangeTool = self.range_tool,
										   eps       = self.eps),
										    code="""

													// Update datacube
													objects[id_group]['Prj'] =  this.value
													objects[id_group]['reso'] =  objects[id_group].getReso(objects[id_group]['Prj']);
													objects[dtCbID].filter(id_group,null)
													
													objects[dtCbID].group(id_group,objects[id_group]['Prj'],objects[id_group]['reso'], objects[id_group]['Mea'])
													
													// Update rangetool ranges
													rangeTool.x_range.start = objects[dtCbID].getDataInfo()[objects[id_group]['Prj']].min - eps
													rangeTool.x_range.end = objects[dtCbID].getDataInfo()[objects[id_group]['Prj']].max + eps

													// Hide the range tool
													rangeTool.overlay.visible = false
													rangeTool.active = false

													// Update labels
													xAxis.axis_label = objects[id_group]['Prj']
													title.text = objects[id_group]['Agg'] + '_' + objects[id_group]['Mea'] + "@"+  objects[id_group]['Prj'];



											""")
		
		self.SelectPrj.js_on_change("value", self.SelectPrj_callbck)


		############   AGG CALLBACK   ############
		# 1) Update title and labels
		# 2) Change agg configuration
		# 3) Update figure
		self.SelectAggFN_callbck = CustomJS(  args = dict(dtCbID   = self.datacube.getID(),
											 			  yAxis    = self.histFig.yaxis[0],
											 			  title    = self.histFig.title,
											 			  id_group = self.id),
											code="""

											// Actualizar el cubo de datos
											objects[id_group]['Agg'] =  this.value
											yAxis.axis_label = objects[id_group]['Agg']+'@'+objects[id_group]['Mea']

											title.text = objects[id_group]['Agg'] + '_' + objects[id_group]['Mea'] + "@"+  objects[id_group]['Prj']


											objects[dtCbID].update()
											""")
		
		self.SelectAggFn.js_on_change("value", self.SelectAggFN_callbck)


		############   MEASURE CALLBACK   ############
		# 1) Update title and labels
		# 2) Change Mea config
		# 3) Update the measure in the datacube object
		self.SelectAggMea_callbck = CustomJS(  args = dict(dtCbID = self.datacube.getID(), yAxis = self.histFig.yaxis[0], title = self.histFig.title, id_group = self.id),
											code="""

											objects[id_group]['Mea'] =  this.value
											yAxis.axis_label = objects[id_group]['Agg']+'@'+objects[id_group]['Mea']

											objects[dtCbID].measure(id_group,objects[id_group]['Mea']);
											
											

											title.text = objects[id_group]['Agg'] + '_' + objects[id_group]['Mea'] + "@"+  objects[id_group]['Prj']
											""")
		
		self.SelectAggMea.js_on_change("value", self.SelectAggMea_callbck)




		


		############### DATACUBE CHANGES ###############
		# When the datacube is modified the bars (number, width, position and height) and the labels are updated.  

		self.datacube.onUpdate(
				"""
				  function(){
				  		var id_fig   = '%s'
				  		var id_group = '%s'
				  		var id_dtCb  = '%s'
				  		var id_source = '%s'
				  		var barWidth = 0.4
				  		var AggFn   = objects[id_group]['Agg']
				  		
				  		if(objects[id_group]['reso'])
				  			barWidth = 0.5*objects[id_group]['alpha']* objects[id_group]['reso']
				  		else
				  			barWidth = 0.5*objects[id_group]['alpha']*(objects[id_dtCb].group(id_group).Values[1].key - objects[id_dtCb].group(id_group).Values[0].key)

				  		var fig    = Bokeh.documents[0].get_model_by_name(id_fig)
				  		var source = Bokeh.documents[0].get_model_by_name(id_source)

				  		source.data['x'] = objects[id_dtCb].group(id_group).Values.map(d => d.key)
				  		source.data['right'] = objects[id_dtCb].group(id_group).Values.map(d => d.key+barWidth)
				  		source.data['left'] = objects[id_dtCb].group(id_group).Values.map(d => d.key-barWidth)
				  		source.data['y'] = objects[id_dtCb].group(id_group).Values.map(d => d.value[AggFn])

				  		source.change.emit()
				  }

				"""%(self.histFig.name, self.id,self.datacube.getID(),self.DataSource.name)
			)











	def getBokehObject(self):
			return column(row(self.SelectPrj,self.SelectAggFn),
						 self.SelectAggMea,
						 self.histFig);

	def getFigure(self):
		return self.histFig;

	def getDummyCallback(self):
	# Get dummy callback or init.js used to create the MP.js object in JS side.
		return self.init_js

	def getID(self):
		return self.id
