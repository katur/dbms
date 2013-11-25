from pprint import pprint
import re
from transaction import Transaction

class TransactionManager(object):
	"""
	A transaction manager object
	"""
	def __init__(self):
		self.directory = {}
		self.transactions = {}

	def print_directory(self):
		print "tm's variable directory:"
		pprint(self.directory)

	def print_transactions(self):
		print "tm's transaction directory:"
		pprint(self.transactions)
		
	# locate next active site for variable var_id
	# returns -1 if no active sites are found
	def locate_read_site(self, var_id):
		site_list = directory[var_id]['site_list']
		site = directory[var_id]['next']
		for loop in range(len(sites)+1):
			directory[var_id]['next'] = site		
			if sites[site].active:
				return site
			site = (sites+1) % len(sites)
		return -1

	def attempt_pending_instructions(self):
		"""
		attempt to execute all pending instructions
		of active transactions
		"""
		ts = self.transactions.values()
		for t in ts:
			if t.status is "active" and t.instruction_buffer:
				i = t.instruction_buffer
				print "attempting old instruction " + i
				self.process_instruction(i)
	
	def process_instruction(self, instruction):
		"""
		process an input instruction
		"""
		# get whatever is between parens
		args = re.search("\((?P<args>.*)\)", instruction)
		if args:
			a = args.group('args')
		else:
			print "Warning: ignoring erroneous instruction (no args)"
			return
		
		# if begin transaction
		if re.match("^begin\((?P<tname>T\d*)\)", instruction):
			if a in self.transactions:
				print "Warning: ignoring input, " + a + " already exists"
			else:
				self.transactions[a] = Transaction(False)
				print "Started " + a
		
		# if begin RO transaction
		elif re.match("^beginRO\(T\d*\)", instruction):
			if a in self.transactions:
				print "Warning: ignoring input, " + a + " already exists"
			else:
				self.transactions[a] = Transaction(True)
				print "Started RO " + a
		
		# if end transaction
		elif re.match("^end\(T\d*\)", instruction):
			if a not in self.transactions:
				print "Warning: ignoring input, " + a + " does not exist"
			else:
				t = self.transactions[a]
				if t.instruction_buffer:
					print "Cannot commit " + a + " due to a pending instruction"
				for site in t.sites_accessed:
					if site.activation_time > t.start_time:
						print "Abort " + a
						break

				print "Commit " + a
		
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
			t,var = a.split(',')
			ro = self.transactions[t].is_read_only
			site = self.locate_read_site(var)
			if site >= 0:
				site = sites[site]
				dm = site.dm
				
		
			
		elif re.match("^W\(.+\,.+\,.+\)", instruction):
			print "Write found: " + a
		
		else:
			print "Warning: ignoring erroneous instruction, " + instruction
		return
