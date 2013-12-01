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
		
	def abort_transaction(self,t):
		print "Aborting transaction " + t.id
		t.status = "aborted"
		for site in t.sites_accessed:
			site.dm.process_abort(t)	
		
	def locate_read_site(self, var_id):
		"""
		locate next active site for variable var_id.
		returns None if no active sites are found.
		"""
		site_list = self.directory[var_id]['sitelist']
		index = self.directory[var_id]['next']
		site = site_list[index]	
		for loop in range(len(site_list)+1):
			index = (index+1) % len(site_list)		
			self.directory[var_id]['next'] = index
			if site.active:
				return site
			site = site_list[index]
		return None

	def attempt_pending_instructions(self):
		"""
		attempt to execute all pending instructions
		of active transactions
		"""
		ts = self.transactions.values()
		for t in ts:
			if t.status is "active" and t.instruction_buffer:
				i = t.instruction_buffer
				print "attempting buffered '" + i + "' for transaction " + t.id
				result = self.process_instruction(i)
				if result == globalz.Flag.Success:
					print "success!"
					t.instruction_buffer = ""

				elif result == globalz.Flag.Wait:
					print "no dice. try again later."

	def process_instruction(self, i):
		"""
		Process an input instruction
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
				self.transactions[a] = Transaction(a,False)
				print "Started " + a

		########################
		# BEGIN RO TRANSACTION #
		########################
		elif re.match("^beginRO\(T\d*\)", i):
			if a in self.transactions:
				print_warning(i, "transaction already exists")
			else:
				self.transactions[a] = Transaction(a,True)
				print "Started RO " + a

		###################
		# END TRANSACTION #
		###################
		elif re.match("^end\(T\d*\)", i):
			if a not in self.transactions:
				print_warning(i, "transaction does not exist")
			else:
				print 'Request to commit ' + a
				t = self.transactions[a]
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
							self.abort_transaction(t)
							return

					# if all sites have been up, commit
					for site in t.sites_accessed:
						site.dm.process_commit(t)	
					t.status = "committed"
					
					print "Successfully committed " + a
					return globalz.Flag.Success
		
		###########
		# IF READ #
		###########
		elif re.match("^R\(.+\,.+\)", i):
			tid,vid = a.split(',')
			tid = tid.strip()
			vid = vid.strip()
			t = self.transactions[tid]
			site = self.locate_read_site(vid)
			
			if not site: # if no active site was found
				print "No active site found for read"
				t.instruction_buffer = i

			else: # if active site found
				if t.is_read_only:
					val = site.dm.process_ro_read(t,vid)
					print str(val) + " read from " + site.name
				
				else: # t is a read/write transaction
					flag,val = site.dm.process_rw_read(t,vid)
				
					if flag == globalz.Flag.Success:
						if not site in t.sites_accessed:				
							t.sites_accessed.append(site)
						print str(val) + " read from " + site.name
					
					elif flag == globalz.Flag.Wait:
						t.instruction_buffer = i
						print "Instruction pending: " + i
					
					else: # flag == globalz.Flag.Abort
						self.abort_transaction(t)
				return flag
				
		############
		# IF WRITE #
		############
		elif re.match("^W\(.+\,.+\,.+\)", i):
			tid,vid,val = a.split(',')
			tid = tid.strip()
			vid = vid.strip()
			val = int(val.strip())
			t = self.transactions[tid]			
			site_list = self.directory[vid]['sitelist']
			num_active = len(site_list)
			must_wait = False
			for site in site_list:
				if site.active:
					flag = site.dm.process_write(t,vid,val)
					if flag == globalz.Flag.Wait:
						must_wait = True
					elif flag == globalz.Flag.Abort:
						self.abort_transaction(t)
				else:
					num_active -= 1					
			if num_active == 0 or must_wait:
				t.instruction_buffer = i
			else:
				return globalz.Flag.Success

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
			print "Dump of all copies all var all sites:"
			for site in globalz.sites:
				print site.name
				site.print_committed_variables()

		elif re.match("^dump\(\d*\)", i):
			print "Dump of site " + a + ":"
			index = int(a) - 1
			site = globalz.sites[index]
			print site.name
			site.print_committed_variables()

		elif re.match("^dump\(x\d*\)", i):
			print "Dump of variable " + a + ":"
			for site in self.directory[a]['sitelist']:
				print site.name + ":" + str(site.variables[a].get_committed_version().value)

		###############################
		# IF NOT AN INSTRUCTION ABOVE #
		###############################
		else:
			print_warning(i, "instruction not found")

		return
