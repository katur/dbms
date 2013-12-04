class Variable(object):
	"""
	A variable object at a particular site,
	which has its own multiversion history.
	"""
	def __init__(self, name):
		self.name = name
		self.versions = []
	
	def __str__(self):
		return self.name

	def __repr__(self):
		return str(self.versions)

	def get_committed_versions(self):
		version_list = []
		for version in self.versions:
			if version.is_committed:
				version_list.append(version)
		return version_list
