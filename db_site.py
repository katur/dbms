from pprint import pprint
from dm import DataManager

class Site(object):
	"""
	A site (server) in the database,
	including variables present at the site,
	a data manager (DM), and a transaction manager
	(TM) for the site.
	"""
	def __init__(self, number, tm):
		self.name = "site" + str(number)
		self.active = True # False means failed
		self.activation_time = 0
		self.variables = {}
		self.dm = DataManager(self)
		self.tm = tm

	def __repr__(self):
		return self.name

	def print_site_state(self):
		print self.name + "; active:" + str(self.active) + "; activation time:" + str(self.activation_time) + "; variables:"
		pprint(self.variables)

	def print_committed_variables(self):
		for variable in self.variables.values():
			print variable.name
			for version in variable.versions:
				if version.committed:
					print version.value
					break
