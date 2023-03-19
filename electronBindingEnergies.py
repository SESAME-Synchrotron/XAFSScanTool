"""
This class returns the electron binding energy of a given 
element in electron volts (eV) in thier natural forms. 
"""
from SEDSS.CLIMessage import CLIMessage
import yaml 
from nob import Nob

electronBindingEngDBPath = "configrations/electronBindingEnergyDB.yaml"

class electronBindingEnergies(): 
	def __init__(self, element): 
		self.energyValue = None
		self.element 	 = element
		"""
		Reading electron binding energy DB file. 
		"""
		with open (electronBindingEngDBPath, "r") as electronBindingDB:
			try: 
				fulldb = yaml.full_load(electronBindingDB)
			except yaml.YAMLError as exc: 
				print(exc)
		"""
		Using Nob package: 
			Instead of working with a standard dictionary 
			we will rely on the Nob package which offers an 
			elegant way to manipulate nested objects.
		"""
		self.nob_tree = Nob(fulldb)
		self.elementKeys = self.nob_tree.keys() # reading elements (dic keys) from the DB 

	def elementExist(self): 
		if self.element in self.elementKeys:
			return True
			CLIMessage("Element is defined in the DB", "I")
		else:
			return False
			CLIMessage("Error: Undefined element", "E")

	def getEdgeEnergy(self, edge):
		self.edge = edge

		# if edge is none, then the default is K 
		if self.edge == "": 
			self.edge == "K"
	
		if self.element in self.elementKeys:
			self.energyValue = self.nob_tree[self.element][self.edge]
			return self.energyValue
		else:
			CLIMessage("Error: Undefined element is chosen", "E")
			CLIMessage("Currently, dict_keys of our DAQ contains \
				these elements {}".format(self.elementKeys), "W")


		