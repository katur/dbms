from pprint import pprint
import re
import globalz
from transaction import Transaction

def print_warning(instruction, reason):
	"""
	generic printing message to print a warning to console
		in case of unexpected input (typo, an impossible
		instruction according to spec, etc)
	Arguments: the faulting instruction, and the reason it is being ignored
	Side effects: printing to console
	"""
	print 'INPUT ERROR: ignoring instruction "' + instruction + \
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


	def locate_read_site(self,t,vid):
		"""
		Locate next active site with applicable read
			for transaction t reading variable var_id.
		Arguments
			- the transaction t requesting the read
			- the id of the var it wants to read.
		Return val
			- a site it one is found, 
			- or None if no active sites are found.
		Side effects
			- update t.next such that no single site
				becomes a hotspot for replicated vars
			- RO transaction might get aborted if it
				realizes here that all 10 sites impossible
				to read from
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
						self.abort_transaction(t,"MVRC situation where all sites deemed impossible to read from (versions too old)")
						return None
			
			# increment to next index
			site = site_list[index]
		return None


	def abort_transaction(self,t,reason):
		"""
		Abort a transaction.
		Args: the transaction and the reason
		Side effects: the transaction is aborted,
			and some locks may be released
		"""
		t.status = "aborted"

		# alert to console
		print "Aborting transaction " + \
			t.id + " due to " + reason

		# if read-write, must process the abort
		#		at all accessed sites to release t's locks
		if not t.is_read_only:
			for site,access_time in t.sites_accessed:
				site.dm.process_abort(t)


	def commit_transaction(self,t):
		"""
		Commit a transaction.
		Args: the transaction
		Side effect: the transaction is committed,
			and some writes may be marked as committed
		"""
		t.status = "committed"
		
		if t.is_read_only: # if read only, not much to do!
			print "Committed RO transaction " + str(t)
		else: # if read-write
			print "Committed transaction " + str(t)

			# call dm to mark writes as committed
			for site,access_time in t.sites_accessed:
				site.dm.process_commit(t)


	def attempt_unstarted_buffered_instructions(self):
		"""
		attempt to execute all unstarted, pending instructions
		of active transactions
		"""
		ts = self.transactions.values()
		for t in ts:
			if t.status is "active" and t.instruction_buffer and not t.instruction_in_progress:
				i = t.instruction_buffer # save instruction
				t.reset_buffer()
				# NOTE: buffer will get re-filled if instruction
					# still can't start
				
				print "Attempting buffered '" + i + "' for transaction " + t.id
				self.process_instruction(i)


	def process_instruction(self, i):
		"""
		Process an input instruction
		Argument: an instruction (parsed from an input line)
		Return value: none
		Side effects: numerous! the instruction gets processed,
			changing many data structures and calling many other
			modules to perform work along the way
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
				if t.instruction_buffer:
					print_warning(i,"can't commit due to a buffered instruction")
					
				elif t.status is "committed":
					print_warning(i,"transaction previously committed")
				elif t.status is "aborted":
					print_warning(i,"transaction previously aborted")
				
				elif t.is_read_only and t.status=="active": 
					# not much to do for RO on commit!
					self.commit_transaction(t)
				
				else: # t is read-write
					# make sure all sites are up now, 
					#		and have been up
					for site,access_time in t.sites_accessed:
						# if some site hasn't been up, abort
						if (not site.active) or site.activation_time > access_time:
							self.abort_transaction(t,"available copies algorithm")
							return

					# otherwise, commit
					self.commit_transaction(t)
		
		###########
		# IF READ #
		###########
		elif re.match("^R\(.+\,.+\)", i):
			tid,vid = [x.strip() for x in a.split(',')]
			t = self.transactions[tid]
			if t.instruction_buffer:
				print_warning(i,"new instruction received while one pending")
				return

			# find a site that is both active and applicable for the read
			#		(i.e., has a committed version avail 
			#		for reading w/approprate timestamp)
			site = self.locate_read_site(t,vid)
			
			if not site:
				if t.status=="active": # if no ready site found
					print str(t) + " must wait: no active site with applicable " + \
						"version found for read"				
					t.add_unstarted_instruction_to_buffer(i)
				elif t.status=="aborted":
					pass # abortion was handled in locate_read_site

			else: # if active+applicable site found
				if t.is_read_only: # will succeed regardless in this step
					site.dm.process_ro_read(t,vid)
					# NOTE: printing handled by the dm
				
				else: # if t is read/write, may need to wait
					flag,val = site.dm.process_rw_read(t,vid)
					
					# if read is waiting on a lock
					if flag == globalz.Message.Wait:
						print str(t) + " must wait for a lock at " + str(site)
						t.add_started_instruction_to_buffer(i,site)

					# if die due to wait die
					elif flag == globalz.Message.Abort:
						self.abort_transaction(t,"wait-die")

					# note: success case handled by the dm
					#		(the print occurs there)
				
		############
		# IF WRITE #
		############
		elif re.match("^W\(.+\,.+\,.+\)", i):
			tid,vid,val = [x.strip() for x in a.split(',')]
			val = int(val)
			t = self.transactions[tid]			
			if t.instruction_buffer:
				print_warning(i,"new instruction received while one pending")
		
			# get all sites where this var is present
			#		keeping track of how many are active,
			#		and also relaying write command to the dm
			#		at any active site
			site_list = self.directory[vid]['sitelist']
			num_active = len(site_list)

			# add all active as started access sites
			for site in site_list:
				if site.active:
					t.add_started_instruction_to_buffer(i,site)
			
			# for all active sites, relay the write to dm
			#		and possibly take wait-die actions
			for site in site_list:
				if site.active:				
					flag = site.dm.process_write(t,vid,val)
					
					# if write at this site queued 
					if flag == globalz.Message.Wait:
						print str(t) + " waiting for lock at " + \
							str(site)
					
					elif flag == globalz.Message.Abort:
						self.abort_transaction(t,"wait-die")
						return
					# NOTE: success handled within dm

				else:
					num_active -= 1					
			
			# if no sites are active
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
					
					# update any transactions with in-progress reads/writes
					#		on this site in response to the failure
					for t in self.transactions.values():
						# if a pending instruction
						if t.instruction_buffer and t.instruction_in_progress:
							i = t.instruction_buffer
							
							# if read
							if re.match("^R\(.+\,.+\)", i):
								
								# site length should always be 1
								if len(t.sites_in_progress) != 1:
									print "warning: a read with " + \
										"sites_in_progress not len 1"

								# if this site present in sites_in_progress,
								#		simply mark it to restart on next clock tick
								for site_entry in t.sites_in_progress: # should just be 1
									if site_entry[0] == site:
										t.add_unstarted_instruction_to_buffer(i)	
							
							# if write
							elif re.match("^W\(.+\,.+\,.+\)", i):
								
								# iterate through all sites, keeping track
								#		of how many have been written to already,
								#		and also removing any matching this site
								#		if they haven't been written to
								#	NOTE: if they have been written to,
								#		the transaction will abort at commit time due to avail copies
								num_written = 0
								for site_entry in t.sites_in_progress:
									if site_entry[1] == True:
										num_written += 1
									if site_entry[0]==site and site_entry[1]==False:
										t.sites_in_progress.remove(site)
							
								# if list is now empty, 
								if not t.sites_in_progress:
									t.add_unstarted_instruction_to_buffer(i)
								
								# if list is now filled with written values,
								#		the instruction is done and the transaction can move on
								# NOTE: this step is so that if a site fails while a
								#		transaction is waiting to write to it but hasn't
								#		yet written to it, it need not abort.
								if len(t.sites_in_progress) == num_written:
									t.reset_buffer()
								

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
					
					# find all transactions that are in the middle of writing variables
					#		(i.e. waiting on locks), and see if the newly
					#		recovered site should be added to their list of sites to 
					#		write to
					for t in self.transactions.values():
						if t.instruction_buffer and t.instruction_buffer[0] == 'W':
							args = re.search("\((?P<args>.*)\)", t.instruction_buffer)
							if args:
								a = args.group('args')
								tid,vid,val = [x.strip() for x in a.split(',')]
								val = int(val)
							if site in self.directory[vid]['sitelist']:
								t.add_started_instruction_to_buffer(i,site)
								message = site.dm.process_write(t,vid,val)
								if message == globalz.Message.Wait:
									print "Waiting on lock at site " + \
										  str(site)
						
								elif message == globalz.Message.Abort:
									self.abort_transaction(t,"wait-die")			
											

		###########
		#  DUMPS  #
		###########
		elif re.match("^dump\(\)", i):
			print "Dump of all committed versions of all " + \
				"variables at all sites"
			for site in globalz.sites:
				print site.name
				site.print_committed_variable_versions()

		elif re.match("^dump\(\d*\)", i):
			print "Dump of site " + a + ":"
			index = int(a) - 1
			site = globalz.sites[index]
			print site.name
			site.print_committed_variable_versions()

		elif re.match("^dump\(x\d*\)", i):
			print "Dump of variable " + a + ":"
			for site in self.directory[a]['sitelist']:
				print site.name + ": " + \
					str(site.variables[a].get_committed_versions())

		elif re.match("^querystate\(\)", i):
			print "TM'S TRANSACTIONS:"
			self.print_transactions()
			print "SITE STATES AND LOCKS:"
			for site in globalz.sites:
				site.print_site_state()
				site.dm.lm.print_lock_table()
		
		elif re.match("^transactions\(\)", i):
			print "TM'S TRANSACTIONS:"
			self.print_transactions()

		
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
