from lm import LockManager

class DataManager(object):
	"""
	Data manager object
	"""
	def __init__(self,site):
		lm = LockManager()
		self.site = site
		
	