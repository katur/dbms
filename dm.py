from lm import LockManager

class DataManager(object):
	"""
	Data manager object
	"""
	def __init__(self,site):
		lm = LockManager()
		self.site = site
		
	def process_request(self,transaction,var,r_type):
		#####################
		# IF READ-ONLY READ #
		#####################		
		if r_type == 'r' and transaction.is_read_only:
			timestamp = transaction.start_time
			version_list = self.site.variables[var].versions
			for version in version_list:
				if version.timestamp <= timestamp:
					return version.value
			