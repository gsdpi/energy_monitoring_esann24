#coding=utf-8
#Título: Read and proccess the HVAC data
#
#Autor: Diego García Pérez
#Fecha: 05/05/23
#Descripción: Adaptado para AMPds 


import pandas as pd
import numpy as np
from pandas.tseries.offsets import *
import ipdb
DATAPATH = "../data/MaqPotUTC.csv"

		
# función de procesamiento de los datos
def loadData(DATAPATH):

	# Reading the data
	data = pd.read_csv(DATAPATH,index_col = 'UNIX_TS')
	data.index = pd.to_datetime(data.index,unit ='s',utc=True)
	#Setting the time zone to Vancouver (where the dataset was created) vancouver: GMT-7
	#data.index = data.index.tz_convert('America/Vancouver')
	data.index = data.index - pd.DateOffset(hours = 7)

	indexMin = pd.date_range(start=min(data.index), end = (max(data.index) - DateOffset(minutes=1)), freq='1min')
	data = data.reindex(index = indexMin,method = None)
	data = data.loc['2012-04-02 00:00:00+00:00 ':'2013-04-01 23:59:00+00:00']


	# Adding some helper columns
	data['DayOfYear'] = data.index.dayofyear
	data['Hour'] = data.index.hour
	data['Time'] = data.index.time
	data['Month'] = data.index.month - 1
	data['DaysInMonth'] = data.index.day
	data['WeekOfYear'] = data.index.weekofyear
	data['Minute'] = data.index.minute
	data['DayOfWeek'] = data.index.dayofweek 
	data['Year'] = data.index.year 

	return data

# unit testing 
if __name__ == "__main__":

	DATAPATH = "../../data/MaqPotUTC.csv"	
	data = loadData(DATAPATH)
	