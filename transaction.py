import globalz

class Transaction(object):
	"""
	A transaction object
	"""
	def __init__(self, id, ro):
		self.id = id
		self.status = "active" # otherwise committed, aborted
		self.start_time = globalz.clock
		self.is_read_only = ro
		self.sites_accessed = []
		self.instruction_buffer = ""

	def __repr__(self):
		return self.id
		
	def __str__(self):
		return self.id + '| status:' + self.status