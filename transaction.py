from pprint import pprint
import config

class Transaction(object):
	"""
	A transaction object
	"""
	def __init__(self, ro):
		self.start_time = config.clock
		self.is_read_only = ro
		self.sites_accessed = []
		self.instruction_buffer = ""
