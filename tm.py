from pprint import pprint
import re
from transaction import Transaction

class TransactionManager(object):
	"""
	A transaction manager object,
	including directory to look up
	where a variable is located.
	"""
	def __init__(self):
		self.directory = {}
		self.transactions = {}

	def print_directory(self):
		print "tm directory:"
		pprint(self.directory)

	def print_transactions(self):
		print "transaction list:"
		pprint(self.transactions)

	def process_instruction(self, instruction):
		# get the args, i.e. whatever is between parens
		args = re.search("\((?P<args>.*)\)", instruction)
		if args:
			a = args.group('args')
		else:
			print "Warning: ignoring erroneous input with no args"
			return
		
		# if begin transaction
		if re.match("^begin\((?P<tname>T\d*)\)", instruction):
			if a in self.transactions:
				print "Warning: ignoring input, transaction " + a + " already exists"
			else:
				self.transactions[a] = Transaction(False)
				print "Started transaction " + a + " with start time " + str(self.transactions[a].start_time)
		
		# if begin RO transaction
		elif re.match("^beginRO\(T\d*\)", instruction):
			if a in self.transactions:
				print "Warning: ignoring input, transaction " + a + " already exists"
			else:
				self.transactions[p] = Transaction(True)
				print "Started RO transaction " + a
		
		# if end transaction
		elif re.match("^end\(T\d*\)", instruction):
			if a not in self.transactions:
				print "Warning: ignoring input, transaction " + a + " does not exist"
			else:
				t = self.transactions[a]
				if t.instruction_buffer:
					print "Cannot commit transaction " + a + " because it has a pending instruction"
				for site in t.sites_accessed:
					if site.activation_time > t.start_time:
						print "Abort transaction " + a
						break

				print "Commit transaction " + a
		
		# if fail site
		elif re.match("^fail\(\d*\)", instruction):
			print "fail site " + a
		
		# if recover site
		elif re.match("^recover\(\d*\)", instruction):
			print "recover site " + a
		
		elif re.match("^dump\(\)", instruction):
			print "dump all copies all var all sites"
		elif re.match("^dump\(\d*\)", instruction):
			print "dump site " + a
		elif re.match("^dump\(x\d*\)", instruction):
			print "dump variable " + a
		
		elif re.match("^R\(.+\,.+\)", instruction):
			print "Read found: " + a
		elif re.match("^W\(.+\,.+\,.+\)", instruction):
			print "Write found: " + a
		
		else:
			print "Warning: ignoring erroneous instruction, " + instruction
		return
