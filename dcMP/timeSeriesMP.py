
from bokeh.models import Button, CustomJS, RangeSlider, Div, ColumnDataSource, Slider,Dropdown,HoverTool, Select,RadioButtonGroup,Text
from bokeh.layouts import row, column, layout
from bokeh.plotting import figure
import numpy as np
from dcMP import  MP
import ipdb


class timeSeriesMP(object):
	"""
	Declarative class for a timeseriues plot that represents a MP object:
		
		Create the  plot
		Create sliders and comboboxes to interact with the encodings
		Handle the interactions between the sliders and the MP and dtCb objects through mediator's events 

	"""

	def __init__(self, init_js,datacube,**kwargs):


		self.init_js = init_js
		self.name    = kwargs.get("timeSeriesMP",str(id(self)))
		self.id = "timeSeriesMP_" + self.name 
		self.med     = kwargs.get("med",str(id(self)))
		# A new and independent MP object is created o handle MP opetations for time series
		self.MP = MP(init_js,datacube,mediator = self.med )
		self.width   = kwargs.get("width",850)
		self.width_widgetPanel = kwargs.get("widthPanel",400)
		self.height  = kwargs.get("height",850)
		self.y_range = kwargs.get("y_range",[0,500])
		self.scalefactorX = kwargs.get("scalefactorX",0.25)
		self.scalefactorY = kwargs.get("scalefactorY",0.75)
		self.yAtt = kwargs.get("yAtt","PotenciaPF")
		self.xAxisAtt = None;
		self.dtCb  =  datacube
		self.initial_sepRatio = 0.01
		self.select_width     = 200
		self.encodings = []
		self.encodingsSliders = []
		self.typeEncIcons = {"horizontal":"👉", "vertical":"☝","circular":"🔄"}



		init_js += f'''
		    // Empty init js callback 
		    objects['{self.id}'] =new Object();
		    // Initial sclaes for sparklines
		    objects['{self.id}']['scaleFactorX'] = {self.scalefactorX}
		    objects['{self.id}']['scaleFactorY'] = {self.scalefactorY}		   
		    objects['{self.id}']['yAtt'] = '{self.yAtt}'
		    '''

		######################### GRAPHIC OBJECTS #########################
		# Data source (it'll be updated later)
		self.DataSource = ColumnDataSource({
								            'xs':[2*i*np.linspace(-10,10,100) for i in range(5)],
								            'ys':[((i+1)/(i+1))*np.linspace(-10,10,100) for i in range(5)],
								            'ysAll':[((i+1)/(i+1))*np.linspace(-10,10,100) for i in range(5)],
								            },name=self.id)
		# figure
		self.scatterFig = figure(width=self.width,
								height=self.height,
								match_aspect=True,
								x_range=(-10,10),
								y_range=(-10,10),
								title="",
								name ="fig_"+self.id)

		self.scatterFig.axis.visible = False



		self.scatterFig.xgrid.grid_line_color = None
		self.scatterFig.ygrid.grid_line_color = None
		self.scatterFig.background_fill_color = "#FFFFFF"
		# Lines
		self.lines = self.scatterFig.multi_line(xs='xs',ys='ys', line_width=3,alpha=0.5,line_color= "#313234",source=self.DataSource)
		self.linesAll = self.scatterFig.multi_line(xs='xs',ys='ysAll', line_width=3,alpha=0.3,line_color= "#808183",source=self.DataSource)
			

		# Hover tooltips
  
		# Text with the tooltips
		self.text_source = ColumnDataSource(dict(x=[-5], y=[-5], text=["hola caracola"]))
		self.text_annotation = Text(x='x', y='y', text="text", angle=0, text_color="#B3B6B7")		
		#self.scatterFig.add_glyph(self.text_source, self.text_annotation)

		self.divToolTip = Div(text= "",style={"color": "#bfbfbf","font-size": "12px","line-height": "1"},width=200)

  		# add a hover tool that sets the link data for a hovered circle
		# https://docs.bokeh.org/en/latest/docs/user_guide/interaction/js_callbacks.html 
		code = """
			groupPosVals = objects[id_MP].getGroup().Values
			tipAtts = objects[id_MP].getGroup().Meta.Attribute
			tipAtts = tipAtts.slice(-(tipAtts.length-1))
			idx = cb_data.index.indices 
			if (idx>0){
				//debugger
				selIdx = src_fig.data.IDX[idx[0]][0]
				vals  = groupPosVals[selIdx].value
				tooltip = ""
				tipAtts.forEach(d => tooltip = tooltip + "<p>" + d + ":   "+ String(vals["all_avg"+d]) +"</p>")
				text.text= tooltip 
			}
			else{
				text.text= ""
			}
			
		""" 


		
		callback = CustomJS(args=dict(text=self.divToolTip,src_fig=self.DataSource,id_MP=self.MP.getID()),code=code)


		self.scatterFig.add_tools(HoverTool(tooltips=None, callback=callback, renderers=[self.linesAll]))



		# self.hover = HoverTool()
		# self.hover.tooltips = [
		#     ('DayOfMonth',"@{DayOfMonth}"),
		#     ('Month',"@{Month}"),
		#     ('WeekOfYear',"@{WeekOfYear}"),
		#     ('DayOfWeek',"@{DayOfWeek}"),
		#     ]



		#self.scatterFig.tools.append(self.hover)


		# #----- Sliders for selecting the alphas  -----
		self.slider_sepX = Slider(start=0, end=5, value=self.scalefactorX, step=0.01, title="Size X",name = self.id+"_sliderSepX")
		self.slider_sepX.js_on_change("value",CustomJS(args=dict(
                                          s = self.slider_sepX,
                                          dtCbID = self.dtCb.getID(),
                                          ID= self.id),
                        code  = """objects[ID]['scaleFactorX'] = s.value;
                                   objects[dtCbID].update()

                                """))

		self.slider_sepY = Slider(start=0, end=5, value=self.scalefactorY, step=0.01, title="Size Y",name = self.id+"_sliderSepX")
		self.slider_sepY.js_on_change("value",CustomJS(args=dict(
                                          s = self.slider_sepY,
                                          dtCbID = self.dtCb.getID(),
                                          ID= self.id),
                        code  = """objects[ID]['scaleFactorY'] = s.value;
                                   objects[dtCbID].update()

                                """))
		# #----- Selection of the att plotted as sparklines  -----
		self.SelectYatt_menu= ["Item2","item2"] # dumy opts
		self.SelectYatt = Select(title = " ",options = self.SelectYatt_menu,max_width= self.select_width,name = "SelYatt_"+self.id)
		self.init_js += " \n Bokeh.documents[0].get_model_by_name('%s').options = objects['%s'].availableAtt()"%(self.SelectYatt.name,self.dtCb.getID())
		self.init_js += " \n Bokeh.documents[0].get_model_by_name('%s').value = objects['%s']['yAtt']"%(self.SelectYatt.name,self.id)

		self.SelectYatt_callbck = CustomJS( args= dict(id_group  = self.id, dtCbID = self.dtCb.getID() ),										    
											code="""
													// Update yAtt
													objects[id_group]['yAtt'] =  this.value
													objects[dtCbID].update()
											""")
		
		self.SelectYatt.js_on_change("value", self.SelectYatt_callbck)






		######################## INITIAL CONDITIONS ########################
		# self.init_js += """ 
		# Bokeh.documents[0].get_model_by_name('%s').value = 0.4
		# """%(self.id +"_slider2")

	def addFixedCustomEncoding(self,att,title,lookup=None):
		
		self.encodings.append(att)
		self.MP.addEncoding(att,title,lookup,"custom")

		#self.MP.changeEnc(att,0.9)

		newSlider = Slider(start=0, end=1, value=0, step=.001, title=title,default_size=50,name= self.id +"_slider{}".format(len(self.encodings)))
		newSlider.js_on_change("value",CustomJS( args=dict(s = newSlider,name  = att), 
									              	 code  = """
									              	 		var id = %s
									              	 		var v = s.value;
                  											var n = name;
                  											objects[id].changeEnc(n,v)
									              	 """%self.MP.getID()))

		# typeEncRadioButton = RadioButtonGroup(labels=list(self.typeEncIcons.values()), active=list(self.typeEncIcons.keys()).index(typeEnc),width=50)
		# typeEncRadioButton.js_on_click(CustomJS(args = dict(MPID = self.MP.getID(), att = att, availableTypes = list(self.typeEncIcons.keys())),code="""
		# 										    	var newType = availableTypes[this.active]
		# 										    	objects[MPID].changeTypeEnc(att,newType)
												
		# 										"""))


		self.encodingsSliders.append(row(newSlider,width=self.width_widgetPanel,sizing_mode="stretch_width"))


		return None	
	
	
	def addFixedEncoding(self,att,title,lookup=None,typeEnc = None):
		
		self.encodings.append(att)
		self.MP.addEncoding(att,title,lookup,typeEnc)

		#self.MP.changeEnc(att,0.9)

		newSlider = Slider(start=0, end=1, value=0, step=.001, title=att,default_size=50,name= self.id +"_slider{}".format(len(self.encodings)))
		newSlider.js_on_change("value",CustomJS( args=dict(s = newSlider,name  = att), 
									              	 code  = """
									              	 		var id = %s
									              	 		var v = s.value;
                  											var n = name;
                  											objects[id].changeEnc(n,v)
									              	 """%self.MP.getID()))

		typeEncRadioButton = RadioButtonGroup(labels=list(self.typeEncIcons.values()), active=list(self.typeEncIcons.keys()).index(typeEnc),width=50)
		typeEncRadioButton.js_on_click(CustomJS(args = dict(MPID = self.MP.getID(), att = att, availableTypes = list(self.typeEncIcons.keys())),code="""
												    	var newType = availableTypes[this.active]
												    	objects[MPID].changeTypeEnc(att,newType)
												
												"""))


		self.encodingsSliders.append(row(typeEncRadioButton,newSlider,width=self.width_widgetPanel,sizing_mode="stretch_width"))


		return None

	def getBokehObject(self):
		if len(self.encodings) >1:
			row_scale_yatt = row([self.divToolTip,Div(text="",width=250),column([self.SelectYatt,self.slider_sepX,self.slider_sepY])],width=self.width_widgetPanel)
			return column(self.scatterFig,column([row_scale_yatt]+self.encodingsSliders,width=self.width_widgetPanel),width=self.width)
		else:
			return column(self.scatterFig);

	def getScatterBokehObject(self):
		tooltipsObj = row([self.divToolTip],width=self.width_widgetPanel)
		return column(self.scatterFig,tooltipsObj,width=self.width_widgetPanel)


	def getEncodingBokehObject(self):
		if len(self.encodings)>1:
			return column(self.encodingsSliders,width=self.width_widgetPanel)
		
	def getConfigScatterBokehObkject(self):
			return column([self.SelectYatt,self.slider_sepX,self.slider_sepY],width=self.width_widgetPanel)
		
	def onUpdatePoints(self):
		return None
	def set_xAxisAtt(self,att):
		self.xAxisAtt = att;
		self.MP.addEncoding(att,"Enc base",None,"horizontal")
		self.MP.changeEnc(att,0.9)
		self.encodings.append(att);

		self.MP.excludeEnc(att);


		######################### CALLBACKS #########################


		# Update lines callback

		self.updateLinesCllbck = """function(){
							   	var id_plot = '%s'
							   	var id = '%s'
							   	dtCb = objects[%s]
							   	var scaleFactorX = objects[id_plot]['scaleFactorX']
							   	var scaleFactorY = objects[id_plot]['scaleFactorY']
							   	

							    var source = Bokeh.documents[0].get_model_by_name(id_plot)
							    var Vpos = objects[id].getGroup().Values
							    var meta = objects[id].getGroup().Meta
							    
								var Epos = objects[id].getPos()
								
								

							    var y_axisAtt = objects[id_plot]['yAtt']
							    var x_axisAtt  = '%s'
							    
							    
							    
							    if (Vpos){
							    	

							    	y_axisValues = Vpos.map(function(d){
							    		const v = d['value']['avg'+y_axisAtt];
							    		
							    		// Los bins sin datos (o con pocos datos) hacemos que no se muestres 
							    		// igualando su a visualizar a NaN
							    		if(d['value']['count']>0)
							    			return v;
							    		else
							    			return NaN; 
							    	})
							    	
							    	y_axisValuesAll = Vpos.map(function(d){
							    		const v = d['value']['all_avg'+y_axisAtt];
							    		
							    		
							    		return v;

							    	})
							    	
							    	
							    	x_axisValues = Vpos.map(d=>d['key'][0])		
									// Idx to access data from tooltip hover
									idx = new math.range(0,math.size(x_axisValues)[0],1).toArray()
			    								 
							    	M  = dtCb.getDataInfo()[x_axisAtt]['n_unique']
							    	X_max = dtCb.getDataInfo()[x_axisAtt]['max']
							    	Y_max = dtCb.getDataInfo()[y_axisAtt]['max']
									
							    	posX = Epos.map(d=>d[0])
							    	posY = Epos.map(d=>d[1])
							    	posYall  = Epos.map(d=>d[1])

								    //console.log(Vpos)
							    	posX = math.reshape(posX,[M,-1])
							    	posY = math.reshape(posY,[M,-1])
							    	posYall = math.reshape(posYall,[M,-1])


							    	X = math.reshape(x_axisValues,[M,-1])
							    	Y = math.reshape(y_axisValues,[M,-1])
									IDX = math.reshape(idx,[M,-1])
							    	Yall = math.reshape(y_axisValuesAll,[M,-1])
							    
							  		oldIdx = X.map(d=>d[0])
							    	_ = JSON.parse(JSON.stringify(oldIdx))
							    	newIdx = math.sort(_)
							    	
							    	orderedX = newIdx.map(d=>(X[oldIdx.lastIndexOf(d)]))
							    	orderedY = newIdx.map(d=>(Y[oldIdx.lastIndexOf(d)]))
							    	orderedYall = newIdx.map(d=>(Yall[oldIdx.lastIndexOf(d)]))
							    	orderedPosX = newIdx.map(d=>(posX[oldIdx.lastIndexOf(d)]))
							    	orderedPosY = newIdx.map(d=>(posY[oldIdx.lastIndexOf(d)]))
							    	orderedPosYall = newIdx.map(d=>(posYall[oldIdx.lastIndexOf(d)]))
									orderedIDX = newIdx.map(d=>(IDX[oldIdx.lastIndexOf(d)]))

							    	orderedX = math.transpose(orderedX)
							    	orderedY = math.transpose(orderedY)
							    	orderedYall = math.transpose(orderedYall)
									orderedIDX  = math.transpose(orderedIDX)

							    	orderedPosX = math.transpose(orderedPosX)
							    	orderedPosY = math.transpose(orderedPosY)
							    	orderedPosYall = math.transpose(orderedPosYall)

							    	orderedX = math.divide(orderedX, X_max*(1/scaleFactorX))
							    	orderedY = math.divide(orderedY,Y_max*(1/scaleFactorY))
							    	orderedYall = math.divide(orderedYall,Y_max*(1/scaleFactorY))

							    	if ((math.size(orderedX)[0]!=math.size(orderedPosX)[0]) || (math.size(orderedX)[0]!=math.size(orderedPosX)[0])){
							        	source.data['xs']  = orderedX
							        	source.data['ys']  = orderedY
							        	source.data['ysAll']  = orderedYall

							        	source.data['IDX'] = orderedIDX

							        	source.change.emit()
							        	return -1

							    	} 

						    		source.data['xs']  = math.add(orderedX,orderedPosX)
						        	source.data['ys']  = math.add(orderedY,orderedPosY)
						        	source.data['ysAll']  = math.add(orderedYall,orderedPosYall)
									source.data['IDX'] = orderedIDX
						        	
									
							        source.change.emit()
							    }
							  }

							"""%(self.id,self.MP.getID(),self.dtCb.getID(),self.xAxisAtt)


		

		# Adding a callback within MP object in order to update the position of the points after a change in the encodings,
		# the creation of new grouping or after adding/removing/modifying a filter.

		# Change of any alpha in the encodings
		self.MP.onUpdatePoints(self.updateLinesCllbck)

		# Change of grouping
		self.MP.onUpdateMPGroups(self.updateLinesCllbck)

		# Change in the filters
		self.dtCb.onUpdate(self.updateLinesCllbck)

		return None

	def getMP(self):
		return self.MP;
	def addAtt(self,att):
		self.MP.addAtt(att);

	def getID(self):
		return self.id