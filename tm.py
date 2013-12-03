from pprint import pprint
import re
import globalz
from transaction import Transaction

def print_warning(instruction, reason):
	print 'ERROR: ignoring instruction "' + instruction + '"; ' + reason

class TransactionManager(object):
	"""
	A transaction manager object
	"""
	def __init__(self):
		# directory keyed on variable name
		# directory[var]['sitelist']: list of sites w/this variable
		# directory[var]['next']: the next site to try
		self.directory = {} 
		
		# transactions keyed on transaction name,
		#		value is the transaction object
		self.transactions = {}
	
	# might lose the following
	def update_waiting_transaction(self,t,site):
		for pa in t.pending_accesses:
			if pa['site'] == site:
				t.pending_accesses.remove(pa)

	def num_active_transactions(self):
		count = 0
		for transaction in self.transactions.values():
			if transaction.status == "active":
				count += 1
		return count
		
	def has_active_transactions(self):
		"""
		returns Boolean of whether there are any 
			active transactions.
		used by program.py to cycle through pending
			instructions at end of program,
			in case we are given any "partial" transactions.
		"""
		for transaction in self.transactions.values( ):
			if transaction.status == "active":
				return True
		return False	

	def locate_read_site(self,t,vid):
		"""
		Locate next active site with applicable read
			for transaction t reading variable var_id.
		Returns None if no active sites are found.
		"""
		site_list = self.directory[vid]['sitelist']
		index = self.directory[vid]['next']
		site = site_list[index]

		# for each possible site, see if it has
		#		a var that is both active and avail to read
		#		depending on if for ro or rw
		for loop in range(len(site_list)+1):
			index = (index+1) % len(site_list)		
			self.directory[vid]['next'] = index
			if site.active and site.dm.get_read_version(t,vid):
				return site
			site = site_list[index]
		return None
	
	def abort_transaction(self,t):
		t.status = "aborted"
		for site,access_time in t.sites_accessed:
			site.dm.process_abort(t)	
	
	def attempt_pending_instructions(self):
		"""
		attempt to execute all unstarted, pending instructions
		of active transactions
		"""
		ts = self.transactions.values()
		for t in ts:
			if t.status is "active" and t.instruction_buffer:
				i = t.instruction_buffer # save instruction
				t.instruction_buffer = "" # reset buffer
				# note: above step okay because if instruction 
				#   still pending, processing will refill the buffer
				print "Attempting buffered '" + i + "' for transaction " + t.id
				self.process_instruction(i)
				
	
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
				print_warning(i,"transaction does not exist")
			else:
				t = self.transactions[a]
				if t.status is "committed":
					print_warning(i,"transaction previously committed")
				elif t.status is "aborted":
					print_warning(i,"transaction previously aborted")
				elif t.instruction_buffer:
					print_warning(i,"can't commit due to a buffered instruction")
				
				# might lose the following
				elif len(t.pending_accesses) > 0:
					print_warning(i,"can't commit due to a buffered instruction")
				
				elif t.is_read_only: # nothing to do for RO on commit!
					t.status = "committed"
					print "Committed RO transaction " + a
				
				else: # t is read-write
					# make sure all sites are up now, and have been up
					for site,access_time in t.sites_accessed:
						# if some site hasn't been up, abort
						if not site.active or site.activation_time > access_time:
							print "Aborting transaction " + t.id + " due to avail copies algo"
							self.abort_transaction(t)
							return

					# otherwise, commit
					for site,access_time in t.sites_accessed:
						site.dm.process_commit(t)
					t.status = "committed"
					print "Committed " + a
		
		###########
		# IF READ #
		###########
		elif re.match("^R\(.+\,.+\)", i):
			tid,vid = [x.strip() for x in a.split(',')]
			t = self.transactions[tid]

			# find a site that is both active and applicable for the read
			#		(i.e., has a committed version avail 
			#		for reading w/approprate timestamp)
			site = self.locate_read_site(t,vid)
			
			if not site: # if no applicable site was found
				print "Must wait: no active site with applicable version found for read"
				t.instruction_buffer = i

			else: # if active site found
				if t.is_read_only: # will succeed regardless in this step
					val = site.dm.process_ro_read(t,vid)
					globalz.print_read_result(val,site,t)
				
				else: # if t is read/write, may need to wait
					flag,val = site.dm.process_rw_read(t,vid)
					
					# if read was successful
					if flag == globalz.Message.success:
						globalz.print_read_result(val,site,t)
					
					# if read is waiting on a lock
					elif flag == globalz.Message.wait:
						t.instruction_buffer = i
						#t.pending_lock_sites.append(site)
						t.pending_accesses.append({ 'site':site, 						
										   'type':'r',
										   'var':vid })
						print "Must wait (lock): " + i
					else: # flag == globalz.Message.Abort
						print "Aborting transaction " + t.id + " due to wait-die"
						self.abort_transaction(t)
				
		############
		# IF WRITE #
		############
		elif re.match("^W\(.+\,.+\,.+\)", i):
			tid,vid,val = [x.strip() for x in a.split(',')]
			val = int(val)
			t = self.transactions[tid]			
			
			site_list = self.directory[vid]['sitelist']
			num_active = len(site_list)
			must_wait = False
			for site in site_list:
				if site.active:
					flag = site.dm.process_write(t,vid,val)
					if flag == globalz.Message.wait:
						t.pending_accesses.append({ 'site':site, 						
										   'type':'w',
										   'var':vid,
										   'value':val })						
						must_wait = True
					elif flag == globalz.Message.abort:
						print "Aborting transaction " + t.id + " due to wait-die"
						self.abort_transaction(t)
						return
					# note, if success, handled within the dm

				else:
					num_active -= 1					
			
			if num_active == 0:
				print "Must wait: no active site found for write"
				t.instruction_buffer = i
			elif must_wait:
				print "Must wait for some locks"
				t.instruction_buffer = i

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
					for variable in site.variables.values():
						if globalz.var_is_replicated(variable.name):
							for version in variable.versions:
								version.available_for_read = False
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
					site.activation_time = globalz.clock 
					print "Site " + a + " recovered"
					# here, have to trigger finding ts in write interim
					# that need more sites?

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

		elif re.match("^querystate\(\)", i):
			print "transactions in tm:"
			self.print_transactions()
			print "state of sites:"
			for site in globalz.sites:
				site.print_site_state()
		
		###############################
		# IF NOT AN INSTRUCTION ABOVE #
		###############################
		else:
			print_warning(i, "instruction not found")
		return
	
	def print_directory(self):
		print "tm's variable directory:"
		pprint(self.directory)

	def print_transactions(self):
		print "tm's transaction directory:"
		pprint(self.transactions)	
