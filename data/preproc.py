#coding=utf-8
#Título:
#
#Autor:
#Fecha:
#Descripción: 

import matplotlib.pyplot as plt
plt.ion()
import pandas as pd

# Lectura del conjunto de los datos
data = pd.read_csv('Electricity_P.csv',index_col=0)
data.index = pd.to_datetime(data.index, unit ='s')

# El dataframe contiene muchos consumos en tipo (int) muestreados a minuto
# Los códigos de los consumos vienen en el artículo:
#  "Electricity, water, and natural gas consumption of a residential house in Canada from 2012 to 2014"

# Preparar los datos con las helper columns: hora del días, año, día de la semana, etc.
# Cargar todos los datos inicialmente.
# Reproducir el mismo bokeh que tengo para HVAC.

