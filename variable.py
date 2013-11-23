class Variable(object):
	"""
	A variable object at one site,
	including its own version history.
	"""
	def __init__(self, name):
		self.name = name
		self.versions = []
	
	def __repr__(self):
		return "var name " + self.name + ". versions: " + str(self.versions)

	def __str__(self):
		return "var name " + self.name + ". versions: " + str(self.versions)
