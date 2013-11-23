from pprint import pprint

class Site(object):
	"""
	A site in the database,
	including variables present at the site
	"""
	def __init__(self, number):
		self.variables = {}
		self.name = "site" + str(number)
	
	def print_site_state(self):
		print self.name + ":"
		pprint(self.variables)
