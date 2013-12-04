from lm import LockManager
from variable_version import VariableVersion
import globalz

class DataManager(object):
	"""
	Data manager object.
	There is one data manager for each site,
	managing the reads and writes for that site.
	Each data manager has its own Lock Manager.
	"""
	def __init__(self,site):
		self.site = site
		self.lm = LockManager(self)
	
	
	def get_read_version(self,t,vid):
		"""
		read the appropriate version of variable vid at this site.
		Args: the transaction wanting to read, the variable to read
		Return value: the value read, or None
			if no appropriate version exists at the site.
		"""
		version_list = self.site.variables[vid].versions
		for v in version_list:
			# if encounter a version not avilable to read,
			#		there must have been a failure, so no
			#		older version will be acceptable for read,
			#		so can stop iterating
			if not v.available_for_read:
				return None
			
			# read-only looks for most recent committed before t began
			if t.is_read_only and v.is_committed and v.time_committed<=t.start_time:
				return v.value

			# read-write looks for most recent committed or written by itself
			if not t.is_read_only and (v.is_committed or v.written_by==t):
				return v.value

		# if applicable version not found, return None
		return None


	def print_read_result(self,t,val,vid):
		print str(t) + " read " + vid + "=" + str(val) + " from " + str(self.site)


	def print_write_result(self,t,val,vid):
		print str(t) + " wrote " + vid + "=" + str(val) + " at " + str(self.site)


	def process_ro_read(self,t,vid):
		"""
		Process a read request from the TM
		for a read-only transaction.
		Arguments: 
			- t: the read-only transaction
			- vid: the variable name to be read
		"""
		read_result = self.get_read_version(t,vid)
		self.print_read_result(t,read_result,vid)
		t.reset_buffer()
		return read_result

	
	def do_read(self,t,vid):
		"""
		Perform the actual read,
		adding it to sites accessed
		and printing the result
		"""
		# add the site to sites_accessed
		t.add_site_access(self.site)

		# get and return the read result
		read_result = self.get_read_version(t,vid)

		# if there was a result, print it
		if read_result:
			self.print_read_result(t,read_result,vid)
			t.reset_buffer()
		
		return read_result # might be None
	

	def process_rw_read(self,t,vid):
		"""
		Process a read request from the TM
		for a read-write transaction.
		Arguments:
			- t: the transaction requesting the read
			- vid: the variable name to be read
		"""
		# try to get the lock
		request_result = self.lm.request_lock(t,vid,'r',None)
		
		if request_result == globalz.Message.Success:
			read_result = self.do_read(t,vid)
			return [request_result, read_result]
		
		else: # read not achieved yet, so let TM know why
			return [request_result, None]
	

	def apply_write(self,t,vid,val):	
		# add the site to sites_accessed
		t.add_site_access(self.site)

		# create new (uncommitted) version 
		#		and insert at the beginning of the list
		new_version = VariableVersion(val,None,t,False)
		version_list = self.site.variables[vid].versions
		version_list.insert(0,new_version)

		# alert console that it was written
		self.print_write_result(t,val,vid)		

		# update t's sites in progress list
		# to show that the lock has been
		# obtained at present site
		t.grant_lock(self.site)

		# reset t's instruction buffer
		# if all writes at all pending sites
		# have completed
		instruction_complete = True
		for s,lock_granted in t.sites_in_progress:
			if not lock_granted:
				instruction_complete = False
		if instruction_complete:
			t.reset_buffer( )
			

	def process_write(self,t,vid,val):
		"""
		Process a write request from the TM.
		Arguments:
			- t: the transaction requesting the write
			- vid: the variable name to be written
			- val: the value to be written
		"""
		request_result = self.lm.request_lock(t,vid,'w',val)
		if request_result == globalz.Message.Success:
			self.apply_write(t,vid,val)			
		return request_result
	
	
	def process_commit(self,t):
		"""
		Process a commit request from the TM
		Argument:
			- t: the transaction to be committed.
		"""
		var_accessed = self.lm.transaction_locks[t]
		#print( str(len(var_accessed)) + " variables accessed at " +
		#	  self.site.name + " to be committed" )
		for vid in var_accessed:
			var = self.site.variables[vid]
			latest_version = var.versions[0] # only need to commit most recent write
			if latest_version.written_by == t:
				latest_version.time_committed = globalz.clock
				latest_version.is_committed = True				
		self.lm.release_locks(t)
		
	
	def process_abort(self,t):
		"""
		Process an abort request from the TM.
		Argument:
			- t: the transaction to be aborted.
		"""
		self.lm.release_locks(t)
