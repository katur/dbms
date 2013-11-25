from pprint import pprint
from dm import DataManager

class Site(object):
	"""
	A site (server) in the database,
	including variables present at the site,
	a data manager (DM) for the site.
	"""
	def __init__(self, number, time):
		self.name = "site" + str(number)
		self.active = True # False means failed
		self.activation_time = time
		self.variables = {}
		self.dm = DataManager(self)

	def print_site_state(self):
		print self.name + "; active:" + str(self.active) + "; activation time:" + str(self.activation_time) + "; variables:"
		pprint(self.variables)

	def print_committed_variables(self):
		for variable in self.variables.values():
			print variable.name
			for version in reversed(variable.versions):
				if version.committed:
					print version.value
					break
