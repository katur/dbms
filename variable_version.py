class VariableVersion(object):
	"""
	A single version of a variable object,
	including its value, timestamp,
	the transaction that wrote it,
	and whether or not it's committed.
	"""
	def __init__(self, val, ts, wb, comm=False):
		self.value = val
		self.written_by = wb
		self.is_committed = comm
		self.time_committed = ts
		self.available_for_read = True

	def __str__(self):
		return str(self.value)
	
	def __repr__(self):
		string = '{' + str(self.value) + '; time' + \
			str(self.time_committed) + '; '
		if not self.available_for_read:
			string += "UN"
		string += "avail to read}"
		return string
		
		"""
		# more elaborate version:
		string = '{' + str(self.value) + ' written by ' + \
			str(self.written_by) + ' @ time ' + \
			str(self.time_committed)
		if self.is_committed:
			string += ", committed, "
		else:
			string += ", NOT committed, "
		if not self.available_for_read:
			string += "un"
		string += "available to read} "
		return string
		"""
