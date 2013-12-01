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

	def __str__(self):
		return self.name

	def __repr__(self):
		return self.name

	def print_site_state(self):
		string = str(self)
		if self.active:
			string += ', active since ' + str(self.activation_time)
		else:
			string += ', failed'
		string += ": "
		print string
		pprint(self.variables)

	def print_committed_variables(self):
		for variable in self.variables.values():
			print(variable.name + ":"),
			for version in variable.versions:
				if version.is_committed:
					print(version.value),
					break
			print(";"),
		print "\n"
