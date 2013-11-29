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
		
		returns True if some instructions remain pending after 
		execution
		"""
		num_pending = 0
		ts = self.transactions.values()
		for t in ts:
			if t.status is "active" and t.instruction_buffer:
				num_pending += 1
				i = t.instruction_buffer
				print "attempting old instruction " + i
				result = self.process_instruction(i)
				if result == globalz.Flag.Success:
					t.instruction_buffer = ""
					num_pending -= 1
		return num_pending > 0

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
				t = self.transactions[a]
				if t.status is "committed":
					print_warning(i, "transaction previously committed")
				elif t.status is "aborted":
					print_warning(i, "transaction previously aborted")
				elif t.instruction_buffer:
					#print_warning(i, "can't commit due to a buffered instruction")
					t.instruction_buffer = i	
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
					#for site in t.sites_accessed:
						
					
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
			tstr,vid = a.split(',')
			t = self.transactions[tstr]
			ro = t.is_read_only
			site = self.locate_read_site(vid)
			# active site found
			if site: 
				dm = site.dm
				flag,val = dm.process_request(t,vid,'r',None)
				t.sites_accessed.append(site)
				print "Value " + str(val) + " read from site " + site.name
				return flag
				
		############
		# IF WRITE #
		############
		elif re.match("^W\(.+\,.+\,.+\)", i):
			print "Write found: " + a	
			tstr,vid,val = a.split(',')				
			t = self.transactions[tstr]			
			site_list = self.directory[vid]['sitelist']
			num_active = len(site_list)
			must_wait = False
			for site in site_list:
				if site.active:
					dm = site.dm
					flag,trash = dm.process_request(t,vid,'w',val)
					if flag == globalz.Flag.Wait:
						must_wait = True
					elif flag == globalz.Flag.Abort:
						print 'must abort transaction'
				else:
					num_active -= 1					
			if num_active == 0 or must_wait:
				t.instruction_buffer = i
			else:
				return globalz.Flag.Success
			

		###############################
		# IF NOT AN INSTRUCTION ABOVE #
		###############################
		else:
			print_warning(i, "instruction not found")

		return
