from lm import LockManager
from variable_version import VariableVersion
import globalz

class DataManager(object):
	"""
	Data manager object.
	There is one data manager for every distributed site,
	the data manager managing the reads and writes
	for that site.
	Each data manager has its own Lock Manager.
	"""
	def __init__(self,site):
		self.site = site
		self.lm = LockManager()
	
	def process_ro_read(self,t,vid):
		"""
		Process a read request from the TM
		for a read-only transaction.
		Arguments: 
			- t: the read-only transaction
			- vid: the variable name to be read
		"""
		version_list = self.site.variables[vid].versions
		for version in version_list:
			if version.timestamp<=t.start_time and version.is_committed:
				return version.value

	def process_rw_read(self,t,vid):
		"""
		Process a read request from the TM
		for a read-write transaction.
		Arguments:
			- t: the transaction requesting the read
			- vid: the variable name to be read
		"""
		request_result = self.lm.request_lock(t,vid,'r')
		
		if request_result == globalz.Flag.Success:
			version_list = self.site.variables[vid].versions
			for version in version_list:
				if version.is_committed:
					return [request_result, version.value]
				# impossible for no committed versions	
		
		else: # read not completed yet
			return [request_result,None]
	
	def process_write(self,t,vid,val):
		"""
		Process a write request from the TM.
		Arguments:
			- t: the transaction requesting the write
			- vid: the variable name to be written
			- val: the value to be written
		"""
		request_result = self.lm.request_lock(t,vid,'w')
		
		if request_result == globalz.Flag.Success:
			version_list = self.site.variables[vid].versions
			
			# create new version and insert at the beginning of the list
			new_version = VariableVersion(val,globalz.clock,t,False)
			version_list.insert(0,new_version)
		return request_result
	
	def process_commit(self,t):
		"""
		Process a commit request from the TM
		Argument:
			- t: the transaction to be committed.
		"""
		variables_accessed = self.lm.transaction_locks[t]
		for vid in variables_accessed:
			var = self.site.variables[vid]
			latest_version = var.versions[0]
			latest_version.timestamp = globalz.clock
			latest_version.is_committed = True
		self.lm.release_locks(t)
		
	def process_abort(self,t):
		"""
		Process an abort request from the TM.
		Argument:
			- t: the transaction to be aborted.
		"""
		self.lm.release_locks(t)	
