class Variable(object):
	"""
	A variable object at a particular site,
	which has its own multiversion history.
	"""
	def __init__(self, name, replicated):
		self.name = name
		self.replicated = replicated
		self.versions = []
	
	def __str__(self):
		return self.name

	def __repr__(self):
		return str(self.versions)

	def get_committed_version(self):
		for version in self.versions:
			if version.is_committed:
				return version
