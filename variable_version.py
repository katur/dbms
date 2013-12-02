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
		self.available_for_read = True

	def __str__(self):
		str(self.value)
	
	def __repr__(self):
		string = '{' + str(self.value) + ' @ time ' + str(self.timestamp) + ' by ' + str(self.written_by)
		if self.is_committed:
			string += ", committed"
		else:
			string += ", not committed, "
		if not self.available_for_read:
			string += "un"
		string += "available for read}"
		return string
		