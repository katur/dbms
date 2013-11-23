from pprint import pprint

class TransactionManager(object):
	"""
	A transaction manager object,
	including directory to look up
	where a variable is located.
	"""
	def __init__(self):
		self.directory = {}
		t_pending_instructions = []

	def print_directory(self):
		print "tm directory:"
		pprint(self.directory)
