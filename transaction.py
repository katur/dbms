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
		self.instruction_buffer = ""
		self.sites_accessed = [] # [ ( site, first_access_time) ]
		self.pending_accesses = []

	def __str__(self):
		return self.id

	def __repr__(self):
		string = self.id + '; ' + self.status + '; started at ' + str(self.start_time)
		if self.is_read_only:
			string += '; is read only'
		if self.instruction_buffer:
			string += '; buffered:' + self.instruction_buffer
		if self.sites_accessed:
			string += '; sites accessed:'
			for site,access_time in self.sites_accessed:
				string += site.name + ' @time' + str(access_time) + '; '
		return string
		
	def add_site_access(self,site):
		if not [i for i in self.sites_accessed if i[0] == site]:
			self.sites_accessed.append((site,globalz.clock))
