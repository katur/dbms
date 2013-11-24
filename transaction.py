from pprint import pprint
import globalz

class Transaction(object):
	"""
	A transaction object
	"""
	def __init__(self, ro):
		self.status = "active" # otherwise committed, aborted
		self.start_time = globalz.clock
		self.is_read_only = ro
		self.sites_accessed = []
		self.instruction_buffer = ""
