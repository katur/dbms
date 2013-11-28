from lm import LockManager
import globalz

class DataManager(object):
	"""
	Data manager object
	"""
	def __init__(self,site):
		self.site = site
		self.lm = LockManager()
		
	def signal_abort(transaction):
		self.site.tm.abort_transaction(transaction)	
		
	def signal_wait(transaction):
		self.site.tm.add_to_wait_list(transaction)	
		
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
					
		#####################
		# IF READ / WRITE 
		#####################							
		elif r_type == 'r' or r_type == 'w':
			request_result = self.lm.request_lock(transaction,vid,r_type)
			if request_result == globalz.Flag.Abort:
				signal_abort(transaction)
				return None
			elif request_result == globalz.Flag.Wait:
				signal_wait(transaction)
				return None
			else:
				version_list = self.site.variables[vid].versions
				if r_type == 'w':
					version = VariableVersion(val,globalz.clock,transaction,False)
					version_list.insert(0,version)
					return val	
				else:
					return version_list[0].value				
					
				
				
			