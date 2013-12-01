class VariableVersion(object):
	"""
	A single version of a variable object,
	including its value, timestamp,
	the transaction that wrote it,
	and whether or not it's committed.
	"""
	def __init__(self, val, ts, wb, comm=False):
		self.value = val
		self.timestamp = ts
		self.written_by = wb
		self.is_committed = comm

	def __repr__(self):
		return '{' + str(self.value) + ", time:" + str(self.timestamp) + \
		", transaction:" + str(self.written_by) + \
		", committed:" + str(self.is_committed) + '}'

	def __str__(self):
		return '{' + str(self.value) + ", time:" + str(self.timestamp) + \
		", transaction:" + str(self.written_by) + \
		", committed:" + str(self.is_committed) + '}'
