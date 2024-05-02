#coding=utf-8
#Título: Demo MP con agregación. Prueba con datos HVAC del hospital de León.
#
#Autor:
#Fecha:
#Descripción: 

from bokeh.core.templates import AUTOLOAD_TAG
from bokeh.embed import file_html
from bokeh.events import MouseMove, ButtonClick
from bokeh.layouts import row, column, layout,GridBox, Spacer
from bokeh.models import BoxSelectTool,HoverTool, Button, CustomJS, RangeSlider, Div, ColumnDataSource, Slider, RangeSlider
from bokeh.plotting import figure
from bokeh.resources import CDN

import pandas as pd
import numpy as np
import pdb
import matplotlib.pyplot as plt
plt.ion()

from jinja2 import Template
import webbrowser
import ipdb
import sys 


from dcMP import DataCube, refstr, MP, ihist, mediator,scatterMP,timeSeriesMP, SliderFilter
from lib.loadData import loadData 
from lib.encodings import linearEncoding, circularEncoding

DEBUG = True
VARS = ['WHE', 'RSE', 'GRE', 'MHE', 'B1E', 'BME', 'CWE', 'DWE', 'EQE',
       'FRE', 'HPE', 'OFE', 'UTE', 'WOE', 'B2E', 'CDE', 'DNE', 'EBE',
       'FGE', 'HTE', 'OUE', 'TVE', 'UNE']

LABELS = {'WHE': "Whole house (WHE)",
        'RSE': "Rental suite (RSE)",
        'GRE': "Garage (GRE)",
        'MHE': "Main House (MHE)",
        'B1E': "Bedroom 1 (B1E)",
        'BME': "Basement (BME)",
        'CWE': "Clothes washer (CWE)",
        'DWE': "Dishwasher (DWE)",
        'EQE': "Equipment (EQE)",
        'FRE': "Furnance (FRE)",
        'HPE': "Heat pump (HPE)",
        'OFE': "Home office (OFE)",
        'UTE': "Utility (UTE)",
        'WOE': "Wall Oven (WOE)",
        'B2E': "Bedroom 2 (B2E)",
        'CDE': "Clothes dryer (CDE)",
        'DNE': "Dining room (DNE)",
        'EBE': "Work bench (EBE)",
        'FGE': "Fridge (FGE)",
        'HTE': "Hot water (HTE)",
        'OUE': "Outside (OFE)",
        'TVE': "TV (TVE)",
        'UNE': "Unmetered (UNE)"}

# Reading the data and converting the 
DATAPATH = "./data/Electricity_P.csv"
data = loadData(DATAPATH)
data.drop("Time",axis=1,inplace=True)
data = data.resample('60T').bfill()

# Reading t-SNE encodings
z_tsne = pd.read_csv("tsne_enc.csv",index_col=0)
z_tsne = z_tsne.to_dict(orient='index')

if DEBUG:
    data[VARS].hist(bins=30,figsize=(16,9))
# Applying a log transformation in order to enhance the color scale 
#data[VARS] = np.log(data[VARS].values + np.finfo(np.float32).eps)

# Exploration of data
if DEBUG:
    data[VARS].hist(bins=30,figsize=(16,9))

data.rename(columns = LABELS,inplace=True)
data_json = data.to_json(orient='records')

# loading html template
with open('template.html') as f:
    template = Template(f.read())


button = Button(label="Dummy button", button_type="success",css_classes=["dummyButton"],visible=False) 
init_js = refstr('''
    // Empty init js callback    

    ''')



# First of all, we create a mediator that will handle all the interactions
# with the datacube and the morphing projections
med = mediator(init_js); 
# create datacube object
dtCb = DataCube(init_js,data_json,mediator = med)



# # create morphing projections object
m  = MP(init_js,dtCb,mediator = med)




timeSeriesMap = timeSeriesMP(init_js = init_js,                  
                  datacube = dtCb,
                  med=med,
                  y_range = [0,3000],
                  width = 800,
                  height= 800,
                  yAtt = LABELS["WHE"])

for c in data.columns:  
    timeSeriesMap.addAtt(c)
# timeSeriesMap.addAtt(LABELS['B1E'])
# timeSeriesMap.addAtt(LABELS['B2E'])
# timeSeriesMap.addAtt(LABELS['TVE'])
# timeSeriesMap.addAtt(LABELS['FGE'])
# timeSeriesMap.addAtt(LABELS['FRE'])
# timeSeriesMap.addAtt(LABELS['CDE'])
# timeSeriesMap.addAtt(LABELS['EBE'])

# timeSeriesMap.addAtt('Month')
# timeSeriesMap.addAtt('DaysInMonth')
# timeSeriesMap.addAtt('DayOfWeek')
# timeSeriesMap.addAtt('WeekOfYear')
# timeSeriesMap.addAtt('DayOfYear')
timeSeriesMap.set_xAxisAtt("Hour")
timeSeriesMap.addFixedEncoding("DayOfWeek","Enc Dia time",None,"vertical")
timeSeriesMap.addFixedEncoding("Month","Enc mes time",None,"horizontal")
timeSeriesMap.addFixedEncoding("WeekOfYear","Enc week time",None,"horizontal")
timeSeriesMap.addFixedEncoding("DaysInMonth","Enc week time",None,"horizontal")
timeSeriesMap.addFixedCustomEncoding("DayOfYear","t-SNE encoding",z_tsne)
#timeSeriesMap.addFixedEncoding("Year","Enc year time",None,"horizontal")

filtros = [];
filtros.append(SliderFilter(init_js,dtCb,
              name = "Filter1",
              projection = LABELS["WHE"],
              width = 250,
              height = 250,
              nbar = 45,
              alpha = 0.5).getBokehObject())


filtros.append(SliderFilter(init_js,dtCb,
              name = "Filter2",
              projection = LABELS["FGE"],
              width = 250,
              height = 250,
              nbar = 45,
              alpha = 0.5).getBokehObject())



button.js_on_event(ButtonClick,CustomJS(code=init_js.__str__()))


#######################################################
# LAYOUT
#######################################################
etiqueta_sliders = Div(text='<h2>Encodings</h2>')
etiqueta_filtros = Div(text='<h2>Filters</h2>')
etiqueta_config = Div(text='<h2>Configuration</h2>')







timeSeriesCol = column(timeSeriesMap.getScatterBokehObject(),sizing_mode="stretch_both")

filtrosCol    = column( filtros, sizing_mode="stretch_both")
toolsCol      = column([etiqueta_sliders,
                        timeSeriesMap.getEncodingBokehObject(),
                        etiqueta_filtros,
                        filtrosCol,
                        etiqueta_config,
                        timeSeriesMap.getConfigScatterBokehObkject()],
                        width = timeSeriesMap.width_widgetPanel)
html = file_html(column(button,row(Div(margin=(10, 20, 30, 40)),timeSeriesCol,Div(margin=(0, 0, 0, 20)),toolsCol)),
                 CDN,
                 template=template,
                 template_variables={"DataCubePath":"./dcMP/DataCube.js",
                                    "MPPath": "./dcMP/MP.js",
                                    "MediatorPath":"./dcMP/mediator.js"})

f = open('app.html','w')
f.write(html)
f.close()

