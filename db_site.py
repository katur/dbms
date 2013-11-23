from pprint import pprint
from dm import DataManager

class Site(object):
	"""
	A site (server) in the database,
	including variables present at the site,
	a data manager (DM) for the site.
	"""
	def __init__(self, number):
		self.name = "site" + str(number)
		active = True
		site_activation_time = 0
		self.variables = {}
		self.dm = DataManager()
	
	def print_site_state(self):
		print self.name + ":"
		pprint(self.variables)
