from pprint import pprint
import re
import globalz
from transaction import Transaction

def print_warning(instruction, reason):
				print 'Warning, ignoring instruction "' + instruction + '": ' + reason

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

	def process_instruction(self, i):
		"""
		process an input instruction
		"""
		# get whatever is between parens
		args = re.search("\((?P<args>.*)\)", i)
		if args:
			a = args.group('args')
		else:
			print_warning(i, "erroneous instruction (no args)")
			return

		#####################
		# BEGIN TRANSACTION #
		#####################
		if re.match("^begin\((?P<tname>T\d*)\)", i):
			if a in self.transactions:
				print_warning(i, "transaction already exists")
			else:
				self.transactions[a] = Transaction(False)
				print "Started " + a

		########################
		# BEGIN RO TRANSACTION #
		########################
		elif re.match("^beginRO\(T\d*\)", i):
			if a in self.transactions:
				print_warning(i, "transaction already exists")
			else:
				self.transactions[a] = Transaction(True)
				print "Started RO " + a

		###################
		# END TRANSACTION #
		###################
		elif re.match("^end\(T\d*\)", i):
			if a not in self.transactions:
				print_warning(i, "transaction does not exist")
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
				if t.status is "committed":
					print_warning(i, "transaction previously committed")
				elif t.status is "aborted":
					print_warning(i, "transaction previously aborted")
				elif t.instruction_buffer:
						print_warning(i, "can't commit due to a buffered instruction")
				else:
					# make sure all sites have been up
					for site in t.sites_accessed:
						# if some site hasn't been up, abort
						if site.activation_time > t.start_time:
							t.status = "aborted"
							print "Aborted " + a
							return

					# if all sites have been up, commit
					t.status = "committed"
					print "Committed " + a

		################
		# IF FAIL SITE #
		################
		elif re.match("^fail\(\d*\)", i):
			index = int(a) - 1
			if index<0 or index>=10:
				print_warning(i, "site does not exist")
			else:
				site = globalz.sites[index]
				if not site.active:
					print_warning(i, "site already failed")
				else:
					site.active = False
					print "Site " + a + " failed"

		###################
		# IF RECOVER SITE #
		###################
		elif re.match("^recover\(\d*\)", i):
			index = int(a) - 1
			if index<0 or index>=10:
				print_warning(i, "site does not exist")
			else:
				site = globalz.sites[index]
				if site.active:
					print_warning(i, "site already active")
				else:
					site.active = True
					print "Site " + a + " recovered"

		###########
		# IF DUMP #
		###########
		elif re.match("^dump\(\)", i):
			print "Dump of all copies all var all sites:\n"
			for site in globalz.sites:
				print site.name
				site.print_committed_variables()

		elif re.match("^dump\(\d*\)", i):
			print "Dump of site " + a + ":\n"
			index = int(a) - 1
			site = globalz.sites[index]
			print site.name
			site.print_committed_variables()


		elif re.match("^dump\(x\d*\)", i):
			print "dump variable " + a

		###########
		# IF READ #
		###########
		elif re.match("^R\(.+\,.+\)", i):
			print "Read found: " + a
			t,var = a.split(',')
			ro = self.transactions[t].is_read_only
			site = self.locate_read_site(var)
			if site >= 0:
				site = sites[site]
				dm = site.dm
				
		
			
		elif re.match("^W\(.+\,.+\,.+\)", instruction):

		############
		# IF WRITE #
		############
		elif re.match("^W\(.+\,.+\,.+\)", i):
			print "Write found: " + a

		###############################
		# IF NOT AN INSTRUCTION ABOVE #
		###############################
		else:
			print_warning(i, "instruction not found")

		return
