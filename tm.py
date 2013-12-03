from pprint import pprint
import re
import globalz
from transaction import Transaction

def print_warning(instruction, reason):
	print 'ERROR: ignoring instruction "' + instruction + \
		'"; ' + reason

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
		# start with "next" position (stored in dir)
		site_list = self.directory[vid]['sitelist']
		index = self.directory[vid]['next']
		site = site_list[index]

		# for each possible site, see if it has
		#		a var that is both active and capable
		#		of being read by the transaction
		for loop in range(len(site_list)+1):
			# get next index and reset "next" field
			index = (index+1) % len(site_list)
			self.directory[vid]['next'] = index

			# try to get a read version
			read_result = site.dm.get_read_version(t,vid)

			# if site active with a read, return it
			if site.active and read_result:
				return site
			
			# if site active w/o a read and RO transaction,
			#		then update the t.impossible_sites
			#		and if this makes all sites impossible,
			#		abort the transaction
			elif t.is_read_only and not read_result:
				if site.name not in t.impossible_sites:
					t.impossible_sites.append(site.name)
					if len(t.impossible_sites) == 10:
						self.abort_transaction(t)
						print "Aborted Read-Only " + str(t) + \
							" since all sites deemed impossible to read from" + \
							"(all versions are too old)"
						return None
			
			# increment to next index
			site = site_list[index]
		return None


	def abort_transaction(self,t):
		t.status = "aborted"
		if not t.is_read_only:
			for site,access_time in t.sites_accessed:
				site.dm.process_abort(t)

	def attempt_unstarted_buffered_instructions(self):
		"""
		attempt to execute all unstarted, pending instructions
		of active transactions
		"""
		ts = self.transactions.values()
		for t in ts:
			if t.status is "active" and t.instruction_buffer and not t.instruction_in_progress:
				i = t.instruction_buffer # save instruction
				t.instruction_buffer = "" # reset buffer
				# NOTE: buffer will get re-filled if instruction
					# still can't start
				
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
				
				elif t.is_read_only and t.status=="active": 
					# not much to do for RO on commit!
					t.status = "committed"
					print "Committed RO transaction " + a
				
				else: # t is read-write
					# make sure all sites are up now, 
					#		and have been up
					for site,access_time in t.sites_accessed:
						# if some site hasn't been up, abort
						if not site.active or site.activation_time > access_time:
							print "Aborting transaction " + t.id + \
								" due to avail copies algo"
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
			
			if not site:
				if t.status=="active": # if no ready site found
					print "Must wait: no active site with applicable " + \
						"version found for read"
					t.add_unstarted_transaction_to_buffer(i)
				elif t.status=="aborted":
					pass

			else: # if active+applicable site found
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
						print "Must wait (lock): " + i
						t.add_started_instruction_to_buffer(i,site)

					# if die due to wait die
					else: # (flag == globalz.Message.Abort)
						print "Aborting transaction " + \
							t.id + " due to wait-die"
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
						print "waiting on lock at site " + \
							str(site)
						t.add_started_instruction_to_buffer(i,site)
					
					elif flag == globalz.Message.abort:
						print "Aborting transaction " + \
							t.id + " due to wait-die"
						self.abort_transaction(t)
						return
					# NOTE: success handled within dm

				else:
					num_active -= 1					
			
			if num_active == 0:
				print "Must wait: no active site for write"
				t.add_unstarted_instruction_to_buffer(i)


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
					# set site to failed
					site.active = False

					# mark all replicated vars 
					#		unavailable for read
					for variable in site.variables.values():
						if globalz.var_is_replicated(variable.name):
							for version in variable.versions:
								version.available_for_read = False
					
					# reset the lock table
					site.dm.lm.reset_lock_table()
					print "Site " + a + " failed"
					
					# ~~~~~~~~~~~~~~~~~~~~~~~~
					# here, need to remove the site
					# from transactions with in-progress
					# read or write at the site,
					# possibly setting to no longer in
					# progress / to be started over
					# at clock tick, or for replicated writes,
					# seeing if the site list is empty
					# ~~~~~~~~~~~~~~~~~~~~~~~~

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
					#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
					# here, have to add to recovered,
					# pending site to replicated,
					# in-progress writes
					#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
				print site.name + ":" + \
					str(site.variables[a].get_committed_version().value)

		elif re.match("^querystate\(\)", i):
			print "TM'S TRANSACTIONS:"
			self.print_transactions()
			print "SITE STATES AND LOCKS:"
			for site in globalz.sites:
				site.print_site_state()
				site.dm.lm.print_lock_table()
		
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
