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
		self.lm = LockManager()
	
	
	def try_pending(self):
		"""
		Cycles through each variable in the site, distributing new locks
		where available. Transactions receiving locks are updated
		by the transaction manager via @tm.update_waiting_transaction.
		"""
		for vid in self.site.variables:
			updates = self.lm.update_queue(vid)
			# some pending transaction(s) has obtained a shared lock
			if updates and updates['lock_type'] == 'r':
				for t in updates['ts']:
					val = self.read_version_for_rw(t,vid)
					if val:
						globalz.print_read_result(val,site,t)
					globalz.tm.update_waiting_transaction(t,self.site)							
			
			# some pending transaction(s) has obtained an exclusive lock
			elif updates:
				transaction = updates['ts'][0]
				val = updates['write_value']
				print vid + "=" + str(val) + " written at " + self.site.name + " (uncommitted)"							
				globalz.tm.update_waiting_transaction(transaction,self.site)


	def get_read_version(self,t,vid):
		"""
		read the appropriate version of variable vid at this site.
		returns None if no appropriate version exists at the site.
		"""
		version_list = self.site.variables[vid].versions
		for v in version_list:
			# if encounter a version not avilable to read,
			#		there must have been a failure, so no
			#		older version will be acceptable for read,
			#		so can stop iterating
			if not v.available_for_read:
				return None
			
			if t.is_read_only and v.is_committed and v.time_committed<=t.start_time:
				return v.value
			if not t.is_read_only and (v.is_committed or v.written_by==t):
				return v.value
		# if applicable version not found, return None
		return None


	def process_ro_read(self,t,vid):
		"""
		Process a read request from the TM
		for a read-only transaction.
		Arguments: 
			- t: the read-only transaction
			- vid: the variable name to be read
		"""
		return self.get_read_version(t,vid)


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
		
		if request_result == globalz.Message.success:
			# add the site to sites_accessed
			t.add_site_access(self.site)

			# get and return the read result to the tm
			read_result = self.get_read_version(t,vid)
			return [request_result, read_result]
		
		else: # read not achieved yet, so let TM know why
			return [request_result, None]
	

	def process_write(self,t,vid,val):
		"""
		Process a write request from the TM.
		Arguments:
			- t: the transaction requesting the write
			- vid: the variable name to be written
			- val: the value to be written
		"""
		request_result = self.lm.request_lock(t,vid,'w',val)
		if request_result == globalz.Message.success:
			# add the site to sites_accessed
			t.add_site_access(self.site)

			# create new (uncommitted) version 
			#		and insert at the beginning of the list
			new_version = VariableVersion(val,None,t,False)
			version_list = self.site.variables[vid].versions
			version_list.insert(0,new_version)

			# alert console that it was written
			globalz.print_write_result(vid,val,self.site,t)
		return request_result
	
	
	def process_commit(self,t):
		"""
		Process a commit request from the TM
		Argument:
			- t: the transaction to be committed.
		"""
		var_accessed = self.lm.transaction_locks[t]
		print( str(len(var_accessed)) + " variables accessed at " +
			  self.site.name + " to be committed" )
		for vid in var_accessed:
			var = self.site.variables[vid]
			# ??? is below necessarily from a write ? if a read, could be committing crap
			latest_version = var.versions[0] # only need to commit most recent write
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
