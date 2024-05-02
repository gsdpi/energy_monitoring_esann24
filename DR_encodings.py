import pandas as pd
import numpy as np
import pdb
import matplotlib.pyplot as plt
plt.ion()

from lib.loadData import loadData 
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
DEBUG = True
RANDOM_SEED = 42

# Reading the data and converting the 
DATAPATH = "./data/Electricity_P.csv"
data = loadData(DATAPATH)
data.drop("Time",axis=1,inplace=True)
data = data.resample('60T').mean()

# windowing
P_daily = data["WHE"].values.reshape((-1,24));# P_daily= P_daily/np.nanmax(P_daily)

#P_weekly = data["WHE"].values.reshape((-1,144*7)); P_weekly= P_weekly/np.nanmax(P_weekly)

if DEBUG:   
    rdn_N = 25
    rdn_samples = np.random.permutation(P_daily)[:25]
    plt.close("raw active power")
    plt.figure("raw active power")
    plt.plot(data["WHE"].values)

    plt.close("samples")
    plt.figure("samples")
    for i,sample in enumerate(rdn_samples):
        plt.subplot(5,5,i+1)
        plt.plot(sample)
        plt.ylim(0,5000)
        


from sklearn.manifold import TSNE
import umap

#reducer = umap.UMAP(n_components = 2, n_neighbors=5,min_dist=0.2)

reducer = TSNE(n_components=2,n_iter=2000, perplexity=15,verbose=3,random_state=RANDOM_SEED)

z = reducer.fit_transform(P_daily)

plt.close("LT daily profiles")
plt.figure("LT daily profiles")
plt.scatter(z[:,0],z[:,1],c="blue",alpha=0.6)
plt.axis('equal')

ATTS = ["WHE","Month","DayOfWeek","CDE","HPE","FGE","TVE","CWE","EBE"]
plt.close(" atts")
plt.figure(" atts",figsize=(16,9))
for i,att in enumerate(ATTS):
    att_data = data[att].values.reshape((-1,24))
    att_data = np.mean(att_data,axis=-1)
    plt.subplot(3,3,i+1)
    plt.scatter(z[:,0],z[:,1],c=att_data,cmap="viridis")
    plt.title(f"LT by {LABELS[att] if att in LABELS else att} ")
    plt.axis('equal')
plt.tight_layout()

# Normalizing z [-5,5]
z = 10*(z - np.min(z,axis=0))/(np.max(z,axis=0)-np.min(z,axis=0)) -5
tsne_enc = pd.DataFrame(z,columns= ["x","y"])
tsne_enc.index  = data["DayOfYear"].values.reshape((-1,24)).mean(axis=-1) 
tsne_enc.to_csv("tsne_enc.csv",index="DayOfYear")

