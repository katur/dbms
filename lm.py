import globalz

class LockManager(object):
	"""
	Lock manager object
	
	lock_table[var][lock] = {
		'w' if some transaction holds an exclusive lock on var
		else 'r' for shared lock
		else 'n'
	}					
	lock_table[var][t] = list of all transactions 
					     holding locks on var
	
	"""
	def __init__(self):
		self.lock_table = {}
		self.transaction_locks = {}
		
	def request_lock(self,transaction,vid,r_type):
		lock = self.lock_table[vid]['lock']
		# no lock on variable
		if lock == 'n':
			self.lock_table[vid]['lock'] = r_type
			self.lock_table[vid]['ts'] = [transaction]
			if not transaction in self.transaction_locks:
				self.transaction_locks[transaction] = []
			self.transaction_locks[transaction].append(vid)
			return globalz.Flag.Success
		else:
			lockers = self.lock_table[vid]['ts']
			# lock held by older transaction
			if lockers[0].start_time < transaction.start_time:
				return globalz.Flag.Abort
			# write request conflicts with younger transaction
			elif r_type == 'w':
				return globalz.Flag.Wait
			else:
				# read request conflicts with younger 
				# transaction holding a write lock
				if lock == 'w':
					return globalz.Flag.Wait
				# read request on variable held by younger 
				# transaction holding a read lock
				else:
					i = 0
					while lockers[i].start_time < transaction.start_time:
						i += 1
					lockers.insert(i,transaction)
					if not transaction in self.transaction_locks:
						self.transaction_locks[transaction] = []
					self.transaction_locks[transaction].append(vid)										
					return globalz.Flag.Success								