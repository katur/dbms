import globalz

class Transaction(object):
	"""
	A transaction object
	"""
	def __init__(self, id, ro):
		self.id = id
		self.status = "active" # otherwise committed, aborted
		self.start_time = globalz.clock
		self.is_read_only = ro

		self.instruction_buffer = "" # any instruction not completed

		self.instruction_in_progress = False
		"""
		if the instruction is not in progress, 
			we will simply re-send instruction on every clock tick
		if in progress, the instruction's progress will instead
			be event driven (i.e., changes occur in response
			to lock release, site failure, or site recovery)
		"""

		self.sites_in_progress = []
		"""
		above is list of (site, written), i.e., the sites that this
			current pending transaction has requested locks at,
			and whether they have been granted the lock.
		If empty, signifies the instruction is no longer in progress
		If all entries are written=True, then 
			the instruction has been completed.
		If any entry is written=False, the instruction
			is still in progress.
		"""

		if self.is_read_only:
			self.impossible_sites = []
			"""
			Impossible_sites is a list of sites attempted
				and deemed impossible to read from (while active)
				for a RO transaction to perform its current read.
				This is to cover corner sites that ALL sites
				have failed since RO started, so no version exists
				and the transaction should abort.
			Note: must clear impossible sites every RO read.
			"""
		else: # if read-write
			self.sites_accessed = [] # [ ( site,first_access_time ) ], for avail copies

	def __str__(self):
		return self.id

	def __repr__(self):
		string = self.id + '; ' + self.status + \
			'; started at ' + str(self.start_time)
		if self.is_read_only:
			string += '; is read only'
		if self.instruction_buffer:
			string += '; buffered:' + self.instruction_buffer
		if self.instruction_in_progress:
			string += " in progress at sites "
			for site in self.sites_in_progress:
				string += str(site) + " "
		
		if self.sites_accessed:
			string += '; sites accessed:'
			for site,access_time in self.sites_accessed:
				string += site.name + ' @time' + \
					str(access_time) + '; '
		return string
		
	def add_site_access(self,site):
		if not [i for i in self.sites_accessed if i[0]==site]:
			self.sites_accessed.append((site,globalz.clock))

	"""
	The following three functions update the instruction
		buffer and related fields (instruction_in_progress
		and sites_in_progress) due to the following:
	reset_buffer: if the instruction finished.
	add_started_instruction_to_buffer: when an 
		instruction first is enqueued at a new site
		and is therefore in progress. 
	add_unstarted_instruction_buffer: whenever an instruction
		is deemed unstarted (either initially or from 
		being demoted from started after site failure)
	"""
	def reset_buffer(self):
		"""
		No args or return value. Side effects explained above.
		"""
		self.instruction_buffer = ""
		self.instruction_in_progress = False
		self.sites_in_progress = []

	def add_started_instruction_to_buffer(self,i,site):
		"""
		Arguments: the instruction and site to add
		No return value. Side effects explained above.
		"""
		self.instruction_buffer = i
		self.instruction_in_progress = True
		self.sites_in_progress.append([site,False])

	def add_unstarted_instruction_to_buffer(self,i):
		"""
		Arguments: the instruction to be buffered
		No return value. Side effects explained above.
		"""
		self.instruction_buffer = i
		self.instruction_in_progress = False
		self.sites_in_progress = []

	def grant_lock(self,site):
		"""
		update a transaction's sites_in_progress
		to reflect a lock being granted at a site.
		Argument: the site
		No return value
		Side effect: for all sites_in_progress matching
			the argument, marked as written
		"""
		for i in range(len(self.sites_in_progress)):
			if self.sites_in_progress[i][0] == site:
				self.sites_in_progress[i][1] = True
