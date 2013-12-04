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
		"""
		Returns a list of all the committed
			versions of this variable (whether
			or not available to read)
		No side effects or args.
		Used in the dump() input functions.
		"""
		version_list = []
		for version in self.versions:
			if version.is_committed:
				version_list.append(version)
		return version_list
