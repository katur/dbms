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
		above is list of (site, granted_lock), i.e., the sites that this
			current pending transaction has requested locks at,
			and whether they have been granted the lock.
		If this list is emptied with
			an instruction in progress, then it should
			simply be marked as no longer in progress.
		If all site(s) are granted locks, then 
			the instruction has been completed.
		If any site is not granted a lock, the instruction
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
			for site in self.sites in progress:
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
	
	def add_started_instruction_to_buffer(self,i,site):
		self.instruction_buffer = i
		self.instruction_in_progress = True
		self.sites_in_progress.append(site)

	def add_unstarted_instruction_to_buffer(self,i):
		self.instruction_buffer = i
		self.instruction_in_progress = False
		self.sites_in_progress = []

	def grant_lock(self,site):
		"""
		update a transaction's sites_in_progress
		to reflect a lock being added at a site.
		"""
		for s,granted_lock in t.sites_in_progress:
			if s == site:
				granted_lock = True
