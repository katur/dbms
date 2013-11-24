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
		if re.match("^begin\((?P<tname>T\d*)\)", instruction):
			m = re.match("^begin\((?P<tname>T\d*)\)", instruction)
			print "start transaction:" + m.group('tname')
		elif re.match("^beginRO\(T\d*\)", instruction):
			print "start RO T"
		elif re.match("^end\(T\d*\)", instruction):
			print "end T"
		
		elif re.match("^fail\(\d*\)", instruction):
			print "fail site"
		elif re.match("^recover\(\d*\)", instruction):
			print "recover site"
		
		elif re.match("^dump\(\)", instruction):
			print "dump all copies all var all sites"
		elif re.match("^dump\(\d*\)", instruction):
			print "dump a particular site"
		elif re.match("^dump\(x\d*\)", instruction):
			print "dump a particular variable"
		
		elif re.match("^R\(.+\,.+\)", instruction):
			print "Read found"
		elif re.match("^W\(.+\,.+\,.+\)", instruction):
			print "Write found"
		
		else:
			print "erroneous instruction:" + instruction
		return
