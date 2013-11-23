from pprint import pprint
import re

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

	def process_instruction(self, instruction):
		if re.match("^begin\(.+\)", instruction):
			print "start T found"
		elif re.match("^beginRO\(.+\)", instruction):
			print "start RO T found"
		elif re.match("^R\(.+\,.+\)", instruction):
			print "Read found"
		elif re.match("^W\(.+\,.+\,.+\)", instruction):
			print "Write found"
		else:
			print "other found:" + instruction
		return
