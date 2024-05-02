class refstr:
   """
   wrap string in object, so that it can be passed by reference 
   rather than by value to the rest of the objects. 
   """
   def __init__(self,s=""):
      self.s=s
   def __add__(self,s):
      self.s+=s
      return self
   def __str__(self):
      return self.s