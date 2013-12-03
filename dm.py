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
					val = read_version_for_rw(self,t,vid)
					if val:
						globalz.print_read_result(val,site,t)
					globalz.tm.update_waiting_transaction(t,self.site)							
			
			# some pending transaction(s) has obtained an exclusive lock
			elif updates:
				transaction = updates['ts'][0]
				val = updates['write_value']
				print vid + "=" + str(val) + " written at " + self.site.name + " (uncommitted)"							
				globalz.tm.update_waiting_transaction(transaction,self.site)


	def read_version_for_ro(self,t,vid):
		"""
		read the appropriate version of variable vid at this site
			for RO transaction t
		"""
		version_list = self.site.variables[vid].versions
		for version in version_list:
			# if encounter a version not avilable to read,
			# there must have been a failure, so no
			# further version will be acceptable for read
			if not version.available_for_read:
				return None

			if version.is_committed and version.time_committed<=t.start_time:
				return version.value
		return None


	def read_version_for_rw(self,t,vid):
		"""
		read the appropriate version of variable vid at this site
			for RW transaction t
		"""
		version_list = self.site.variables[vid].versions
		for version in version_list:
			if not version.available_for_read:
				return None

			if version.is_committed or version.written_by==t:
				return version.value
		return None


	def process_ro_read(self,t,vid):
		"""
		Process a read request from the TM
		for a read-only transaction.
		Arguments: 
			- t: the read-only transaction
			- vid: the variable name to be read
		"""
		read_version_for_ro(self,t,vid)


	def process_rw_read(self,t,vid):
		"""
		Process a read request from the TM
		for a read-write transaction.
		Arguments:
			- t: the transaction requesting the read
			- vid: the variable name to be read
		"""
		request_result = self.lm.request_lock(t,vid,'r',None)
		
		if request_result == globalz.Message.success:
			read_result = read_version_for_rw(self,t,vid)
			return [request_result, version.value]
		
		else: # read not achieved
			return [request_result,None]
	

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
			version_list = self.site.variables[vid].versions
			
			# create new (uncommitted) version 
			#		and insert at the beginning of the list
			new_version = VariableVersion(val,None,t,False)
			version_list.insert(0,new_version)
			print vid + "=" + str(val) + " written at " + self.site.name + " (uncommitted)"
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
