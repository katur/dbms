class LockManager(object):
	"""
	Lock manager object
	
	lock_table[var] = {
		'x' if some transaction holds an exclusive lock on var
		else 's' for shared lock
		else 'n'
	}					
	
	"""
	def __init__(self):
		self.lock_table = {}
