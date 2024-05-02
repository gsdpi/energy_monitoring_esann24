#coding=utf-8
#Título:
#
#Autor:
#Fecha:
#Descripción: 

import numpy as np
import pandas as pd

def circularEncoding(N):
  """
  E = circularEncoding(N)
    
    N: Number of classes in the encoding (ej. 7, to represent weekdays)
    E: dataframe with N positions of a circular encoding of radius=1

    Example
      circular encoding for 7 groups (e.g. weekdays):

      circularEncoding(7)

                  x         y
        0  1.000000  0.000000
        1  0.623490  0.781831
        2 -0.222521  0.974928
        3 -0.900969  0.433884
        4 -0.900969 -0.433884
        5 -0.222521 -0.974928
        6  0.623490 -0.781831

  """

  x = np.arange(N)
  pos = np.vstack((np.cos(2*np.pi*x/N),np.sin(2*np.pi*x/N))).T
  E   = pd.DataFrame(pos,x,columns=['x','y'])
  return E



def linearEncoding(N,direction):
    """
    E = linearEncoding(N,direction)

      N: Number of classes in the encoding (ej. 7, to represent weekdays)
      E: dataframe with N positions of a linear encoding in range [-0.5,0.5]

      Example
        horizontal encoding for 5 groups (e.g. buildings)

        linearEncoding(5,'hor')

               x    y
          0 -1.0  0.0
          1 -0.6  0.0
          2 -0.2  0.0
          3  0.2  0.0
          4  0.6  0.0
    
    """
    x = np.arange(N)
    if direction=='hor':
      posx = 2*x/float(N)-1
      posy = 0.*x
    else:
      posx = 0.*x
      posy = 2*x/float(N)-1

    E   = pd.DataFrame(np.vstack((posx,posy)).T,x,columns=['x','y'])
    return E
		