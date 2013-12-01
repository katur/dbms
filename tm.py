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
		t.status = "aborted"
		for site,access_time in t.sites_accessed:
			site.dm.process_abort(t)	
	
	def num_active_transactions(self):
		count = 0
		for transaction in self.transactions.values():
			if transaction.status == "active":
				count += 1
		return count
		
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
				elif t.is_read_only:
					t.status = "committed"
					print "Committed RO transaction " + a
				else:
					# make sure all sites have been up
					for site,access_time in t.sites_accessed:
						# if some site hasn't been up, abort
						if site.activation_time > access_time:
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
			site = self.locate_read_site(vid)
			
			if not site: # if no active site was found
				print "Must wait: no active site found for read"
				t.instruction_buffer = i

			else: # if active site found
				if t.is_read_only: # will succeed regardless
					val = site.dm.process_ro_read(t,vid)
					print str(val) + " read from " + site.name
				
				else: # if t is read/write, may need to wait
					flag,val = site.dm.process_rw_read(t,vid)
					
					# if read was successful
					if flag == globalz.Flag.Success:
						t.add_site_access(site) # add to sites_accessed
						print str(val) + " read from " + site.name
					
					# if read is waiting on a lock
					elif flag == globalz.Flag.Wait:
						t.instruction_buffer = i
						print "Must wait (lock): " + i
					
					else: # flag == globalz.Flag.Abort
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
					if flag == globalz.Flag.Success:
						# add the site to sites_accessed
						t.add_site_access(site)
					elif flag == globalz.Flag.Wait:
						must_wait = True
					elif flag == globalz.Flag.Abort:
						print "Aborting transaction " + t.id + " due to wait-die"
						self.abort_transaction(t)
						return
				else:
					num_active -= 1					
			
			if num_active == 0:
				print "Must wait: no active site found for write"
				t.instruction_buffer = i
			elif must_wait:
				print "Must wait for locks"
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
