class VariableVersion(object):
	"""
	A single version of a variable object,
	including its value and whether or not it is committed.
	"""
	def __init__(self, val, comm=False):
		self.value = val
		self.committed = comm
	
	def __repr__(self):
		return str(self.value)

	def __str__(self):
		return str(self.value)
