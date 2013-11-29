from lm import LockManager
from variable_version import VariableVersion
import globalz

class DataManager(object):
	"""
	Data manager object
	"""
	def __init__(self,site):
		self.site = site
		self.lm = LockManager()
		
	def process_request(self,transaction,vid,r_type,val):
		#####################
		# IF READ-ONLY READ #
		#####################		
		if r_type == 'r' and transaction.is_read_only:
			t_start_time = transaction.start_time
			version_list = self.site.variables[vid].versions
			for version in version_list:
				if version.timestamp <= t_start_time and version.committed:
					return version.value
					
		###################
		# IF READ / WRITE #
		###################							
		elif r_type == 'r' or r_type == 'w':
			request_result = self.lm.request_lock(transaction,vid,r_type)
			if request_result == globalz.Flag.Success:
				version_list = self.site.variables[vid].versions
				if r_type == 'w':
					version = VariableVersion(val,globalz.clock,transaction,False)
					version_list.insert(0,version)
					return [request_result,val]
				else:
					return [request_result,version_list[0].value]								
			else:
				return [request_result,None]
				
		#############
		# IF COMMIT #
		#############
		elif r_type == 'c':
			variables_accessed = self.lm.transaction_locks[transaction]
			for vid in variables_accessed:
				var = self.site.variables[vid]
				latest_version = var.versions[0]
				latest_version.timestamp = globalz.clock
				latest_version.committed = True
			self.lm.release_locks(transaction)
		
		#############
		# IF ABORT #
		#############		
		elif r_type == 'a':
			self.lm.release_locks(transaction)				
						
		
				
			