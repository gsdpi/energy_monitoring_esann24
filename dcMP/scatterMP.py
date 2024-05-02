
from bokeh.models import Button, CustomJS, RangeSlider, Div, ColumnDataSource, Slider,Dropdown,HoverTool, Select,RadioButtonGroup
from bokeh.layouts import row, column, layout
from bokeh.plotting import figure
import numpy as np
import ipdb


class scatterMP(object):
	"""
	Declarative class for a scatter plot that represents a MP object:
		
		Create the scatter plot
		Create sliders and comboboxes to interact with the encodings
		Handle the interactions between the sliders and the MP and dtCb objects through mediator's events 

	"""

	def __init__(self, init_js,MP,datacube,**kwargs):


		self.init_js = init_js
		self.name    = kwargs.get("name",str(id(self)))
		self.MP = MP
		self.width   = kwargs.get("width",850)
		self.width_widgetPanel = kwargs.get("widthPanel",400)
		self.background_fill_color = kwargs.get("background_fill_color","#0B132B")
		self.height  = kwargs.get("height",850)
		self.dtCb  =  datacube
		self.id = "scatterMP_" + self.name 
		self.initial_sepRatio = 0.0001
		self.select_width     = 200
		self.encodings = []
		self.encodingsSliders = []
		self.typeEncIcons = {"horizontal":"👉", "vertical":"☝","circular":"🔄","custom":"custom"}


		# Creamos las escalas de color y tamaño en un objecto global para luego poder acceder desde las callbacks
		# Las escalas son escalas de D3
		# Este objecto se va actualizando en las callbacks de los comboboxes donde el usuario selecciona el atributo de color y tamaño
		init_js += f'''
		    // Empty init js callback 
		    objects['{self.id}'] =new Object();   		   
		    objects['{self.id}']['sepRatio'] = {self.initial_sepRatio};
		    objects['{self.id}']['colorAtt']  = Object.keys(objects['{self.dtCb.getID()}'].getDataInfo())[0]
		    objects['{self.id}']['sizeAtt']  = Object.keys(objects['{self.dtCb.getID()}'].getDataInfo())[0]
		    objects['{self.id}']['escalaColor_min'] = objects['{self.dtCb.getID()}'].getDataInfo()[objects['{self.id}']['colorAtt']]['min']
		    objects['{self.id}']['escalaColor_max'] = objects['{self.dtCb.getID()}'].getDataInfo()[objects['{self.id}']['colorAtt']]['max']
			objects['{self.id}']['escalaColor'] = d3.scaleSequential().domain([objects['{self.id}']['escalaColor_min'],objects['{self.id}']['escalaColor_max']]).range([0,1]).interpolator(d3.interpolateTurbo)
		    objects['{self.id}']['escalaSize_min'] = objects['{self.dtCb.getID()}'].getDataInfo()[objects['{self.id}']['sizeAtt']]['min']
		    objects['{self.id}']['escalaSize_max'] = objects['{self.dtCb.getID()}'].getDataInfo()[objects['{self.id}']['sizeAtt']]['max']
		    objects['{self.id}']['escalaSize'] = d3.scaleSequential().domain([objects['{self.id}']['escalaSize_min'],objects['{self.id}']['escalaSize_max']]).range([0,300]).clamp(true)
		    '''

		######################### GRAPHIC OBJECTS #########################
		# Data source (it'll be updated later)
		self.DataSource = ColumnDataSource({
								            'Ex':np.linspace(-10,10,100),
								            'Ey':np.linspace(-10,10,100),
								            'tam':5*np.ones(100),
								            'all_tam':5*np.ones(100),			            
								            'color': ['#00ff00']*100,
								            'all_color': ['#F2F3F4']*100,
								            },name=self.id)
		# figure
		self.scatterFig = figure(width=self.width,
								height=self.height,
								x_range=(-6,6),
								y_range=(-6,6),
								match_aspect=False,
								title="",
								name ="fig_"+self.id)

		self.scatterFig.axis.visible = False
		self.scatterFig.xgrid.grid_line_color = None
		self.scatterFig.ygrid.grid_line_color = None
		self.scatterFig.background_fill_color = self.background_fill_color
		# Points
		self.points = self.scatterFig.circle(x='Ex',y='Ey',radius='tam',color='color',source=self.DataSource,alpha=0.5)
		self.points_all = self.scatterFig.circle(x='Ex',y='Ey',radius='all_tam',color='all_color',source=self.DataSource,alpha=0.2)
		
		# Hover tool tips
		self.hover = HoverTool()
		self.hover.tooltips = [
		    ('key del grupo',"@{keys}"),
		    ('Temperatura',"@{Temperature}")
		    ]

		self.scatterFig.tools.append(self.hover)
		
		#----- Combobox for selecting the color of the points   -----
		self.SelectColor_menu = ["Item1","item2"] # dumy opts
		self.SelectColor = Select(title = "Color",options = self.SelectColor_menu,max_width= self.select_width,name = self.id+"_SelColor")
		self.init_js += f"\n Bokeh.documents[0].get_model_by_name('{self.SelectColor.name}').options = Object.keys(objects['{self.dtCb.getID()}'].getDataInfo())"
		self.init_js += f"\n Bokeh.documents[0].get_model_by_name('{self.SelectColor.name}').value = objects['{self.id}']['colorAtt']"


		#----- Combobox for selecting the size of the points   -----
		# Esto está deshabilitado porque:
		# 		Cuando los valores agregados se obtienen con pocos puntos el valor de la media filtrada supera al valor del promedio sin filtrar


		# self.SelectSize_menu = ["Item1","item2"] # dumy opts
		# self.SelectSize = Select(title = "Size att.",options = self.SelectColor_menu,max_width= self.select_width,name = self.id+"_SelSize")
		# self.init_js += f"\n Bokeh.documents[0].get_model_by_name('{self.SelectSize.name}').options = Object.keys(objects['{self.dtCb.getID()}'].getDataInfo())"
		# self.init_js += f"\n Bokeh.documents[0].get_model_by_name('{self.SelectSize.name}').value = objects['{self.id}']['sizeAtt']"




		# #----- Sliders for selecting the alphas  -----
		self.slider_sep = Slider(start=0, end=0.001, value=self.initial_sepRatio, step=.00001, title="Size ratio",name = self.id+"_sliderSep")
		self.slider_sep.js_on_change("value",CustomJS(args=dict(
                                          s = self.slider_sep,
                                          dtCbID = self.dtCb.getID(),
                                          ID= self.id),
                        code  = """objects[ID]['sepRatio'] = s.value;
                                   objects[dtCbID].update()

                                """))

		
		######################### CALLBACKS #########################


		# Update points callback
		#
		# Size of points is fixed to the count
		# The color of the points is an user-defined option. It is defined by avg value computed for a selected att


		self.updateScttCllbck = """function(){
							   	var id_scatter = '%s'
							   	var id = '%s'

							    var source = Bokeh.documents[0].get_model_by_name(id_scatter)
							    var Epos = objects[id].getPos()
							    if (Epos){
							        source.data['Ex']  = Epos.map(d=>d[0])
							        source.data['Ey']  = Epos.map(d=>d[1])
							        source.data['tam'] = objects[id].getAtt(objects[id_scatter]['sizeAtt'],'count').map(d=>d*objects[id_scatter]['sepRatio'])
							        //source.data['tam'] = objects[id].getAtt('PotenciaPF','count').map(d=>d*objects[id_scatter]['sepRatio'])
							        source.data['color'] = objects[id].getAtt(objects[id_scatter]['colorAtt'],'avg').map(d => d3.color(objects[id_scatter]['escalaColor'](d)).formatHex())

							        source.data['all_tam'] = objects[id].getGroup()['Values'].map(d=>d['value']['all_count']*objects[id_scatter]['sepRatio'])
							        //source.data['all_tam'] = objects[id].getGroup()['Values'].map(d=>objects[id_scatter]['escalaSize'](d['value']['all_avg'+objects[id_scatter]['sizeAtt']])*objects[id_scatter]['sepRatio'])
							        source.data['all_color'] = new Array(source.data['Ex'].length).fill('#A3A4A6')

							        
							        //source.data['keys'] = objects[id].getGroup().Values.map(d=>d.key)
							        //source.data['Temperature'] = objects[id].getAtt('Temperature','avg') 
							        
							        source.change.emit()
							    }
							  }

							"""%(self.id,self.MP.getID())


		# Callback for color select
		self.SelectColor.js_on_change("value", CustomJS( args=dict(s = self.SelectColor, id = self.id, dtCbID = self.dtCb.getID(),MPID=self.MP.getID()), # Aquí debería ir el nombre elegido en el combobox
									              	 code  = """
									              	 		// Change in color att
									              	 		objects[id]['colorAtt'] = this.value
														    
														    // Change in the color scale
														    objects[id]['escalaColor_min'] = objects[dtCbID].getDataInfo()[s.value]['min']
														    objects[id]['escalaColor_max'] = objects[dtCbID].getDataInfo()[s.value]['max']
														    objects[id]['escalaColor'].domain([objects[id]['escalaColor_min'],objects[id]['escalaColor_max']])

														    // Updating the points
														    objects[MPID].updateEvent()


													              	 """))



		#Calback for size select
		# Deshabilitado por lo de arriba
		# self.SelectSize.js_on_change("value", CustomJS( args=dict(s = self.SelectSize, id = self.id, dtCbID = self.dtCb.getID(),MPID=self.MP.getID()), # Aquí debería ir el nombre elegido en el combobox
		# 							             	 code  = """
		# 							              	 		// Change in size att
		# 							              	 		objects[id]['sizeAtt'] = this.value
														    
		# 												    // Change in the color scale
		# 												    objects[id]['escalaSize_min'] = objects[dtCbID].getDataInfo()[s.value]['min']
		# 												    objects[id]['escalaSize_max'] = objects[dtCbID].getDataInfo()[s.value]['max']
		# 												    objects[id]['escalaSize'].domain([objects[id]['escalaSize_min'],objects[id]['escalaSize_max']])

		# 												    // Updating the points
		# 												    objects[MPID].updateEvent()


		# 											              	 """))

		
		self.encodingsSliders.append(row(self.SelectColor,self.slider_sep,width=self.width_widgetPanel))

		


		# Adding a callback within MP object in order to update the position of the points after a change in the encodings,
		# the creation of new grouping or after adding/removing/modifying a filter.

		# Change of any alpha in the encodings
		self.MP.onUpdatePoints(self.updateScttCllbck)

		# Change of grouping
		self.MP.onUpdateMPGroups(self.updateScttCllbck)

		# Change in the filters
		self.dtCb.onUpdate(self.updateScttCllbck)


		######################## INITIAL CONDITIONS ########################
		# self.init_js += """ 
		# Bokeh.documents[0].get_model_by_name('%s').value = 0.4
		# """%(self.id +"_slider2")

	def addFixedEncoding(self,att,title,lookup=None,typeEnc = None):
		
		self.encodings.append(att)
		self.MP.addEncoding(att,title,lookup,typeEnc)

		newSlider = Slider(start=0, end=1, value=0, step=.001, title=att,default_size=50,name= self.id +"_slider{}".format(len(self.encodings)))
		newSlider.js_on_change("value",CustomJS( args=dict(s = newSlider,name  = att), 
									              	 code  = """
									              	 		var id = %s
									              	 		var v = s.value;
                  											var n = name;
                  											objects[id].changeEnc(n,v)
									              	 """%self.MP.getID()))

		typeEncRadioButton = RadioButtonGroup(labels=list(self.typeEncIcons.values())[:-1], active=list(self.typeEncIcons.keys()).index(typeEnc),width=50)
		typeEncRadioButton.js_on_click(CustomJS(args = dict(MPID = self.MP.getID(), att = att, availableTypes = list(self.typeEncIcons.keys())),code="""
												    	var newType = availableTypes[this.active]
												    	objects[MPID].changeTypeEnc(att,newType)
												
												"""))


		self.encodingsSliders.append(row(typeEncRadioButton,newSlider,width=self.width_widgetPanel,sizing_mode="stretch_width"))


		return None

	def getBokehObject(self):
		return column(column(self.scatterFig,column(self.encodingsSliders,width=self.width_widgetPanel)),width=self.width);

	def onUpdatePoints(self):
		return None

	def addAtt(self,att):
		self.MP.addAtt(att);

	def getID(self):
		return self.id