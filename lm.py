import globalz

class LockManager(object):
	"""
	Lock manager object
	
	"""
	def __init__(self):
		# lock table: keyed on var; value is lock table entry
		self.lock_table = {} 
		
		# transaction_locks: keyed on transaction; 
		#		value list of vars it has locked at this site
		self.transaction_locks = {}

	def update_queue(self,vid):
		lt_entry = self.lock_table[vid]
		if lt_entry.lock == 'n' and len(lt_entry.q) > 0:
			updates = {'lock_type':None, 'ts':[]}
			
			# pending transaction(s) requests shared lock
			while lt_entry.q[0].r_type == 'r':
				updates['lock_type'] = 'r'
				q_entry = lt_entry.q.pop( )
				updates['ts'].append(q_entry.transaction)				
			
			# pending transaction requests exclusive lock
			if lt_entry.lock == 'n':
				updates['lock_type'] = 'w'
				q_entry = lt_entry.q.pop( )
				updates['ts'] = [q_entry.transaction]
				updates['write_value'] = q_entry.value
			return updates
		else:
			return None
		
	def enqueue_transaction(self,transaction,vid,r_type,value):
		"""
		returns false if older transaction requesting exclusive
			lock causes enqueueing transaction to abort.
		returns true otherwise.
		"""
		lt_entry = self.lock_table[vid]
		for q_entry in lt_entry.q:
			if( (r_type == 'w' or q_entry.r_type == 'w') and
			q_entry.transaction.start_time < transaction.start_time ):
				return False
		lt_entry.q.append(QueueEntry(transaction,r_type,value))
		return True
		
	def release_locks(self,transaction):
		for vid in self.transaction_locks[transaction]:
			print "releasing a lock"
			self.lock_table[vid].locking_ts.remove(transaction)
			if len(self.lock_table[vid].locking_ts) == 0:
				self.lock_table[vid].lock = 'n'				

	def request_read_lock(self,transaction,vid):
		# shared lock on variable
		if self.lock_table[vid].lock == 'r':
			self.lock_table[vid].locking_ts.append(transaction)
			if not transaction in self.transaction_locks:
				self.transaction_locks[transaction] = []
			self.transaction_locks[transaction].append(vid)
			return globalz.Message.success
		# exclusive lock on variable
		else:
			locking_t = self.lock_table[vid].locking_ts[0]
			if locking_t.start_time < transaction.start_time:
				return globalz.Message.abort
			enqueue_result = self.enqueue_transaction(transaction,vid,'r',None)
			if enqueue_result: 
				return globalz.Message.success
			else:
				return globalz.Message.abort
		
	def request_write_lock(self,transaction,vid,value):
		for t in self.lock_table[vid].locking_ts:
			if t.start_time < transaction.start_time:
				return globalz.Message.abort
			enqueue_result = self.enqueue_transaction(transaction,vid,'w',value)
			if enqueue_result: 
				return globalz.Message.wait
			else:
				return globalz.Message.abort				

	def request_lock(self,transaction,vid,r_type,value):
		lt_entry = self.lock_table[vid]
		# no lock on variable
		if lt_entry.lock == 'n':
			self.lock_table[vid].lock = r_type
			self.lock_table[vid].locking_ts = [transaction]
			if not transaction in self.transaction_locks:
				self.transaction_locks[transaction] = []
			self.transaction_locks[transaction].append(vid)
			return globalz.Message.success
		elif transaction in lt_entry.locking_ts:
			# transaction already holds an exclusive lock
			if lt_entry.lock == 'w':
				return globalz.Message.success
			else:
			# transaction requests an upgrade from shared lock to exclusive
				# transaction holds the only shared lock on variable
				if len(lt_entry.locking_ts) == 1:
					lt_entry.lock = 'w'
					return globalz.Message.success
				else:
					enqueue_result = self.enqueue_transaction(transaction,vid,r_type,value)
					if enqueue_result:
						return globalz.Message.wait
					else:
						return globalz.Message.abort
				
		elif r_type == 'r':
			return self.request_read_lock(transaction,vid)
		else:	
			return self.request_write_lock(transaction,vid,value)							

class LockTableEntry(object):
	"""
	Lock Table Entry object
	"""
	def __init__(self,var):
		self.var = var # the variable this lock is on
		self.lock = 'n' # 'w' for exclusive, 'r' for shared
		self.locking_ts = [] # list of transactions currently holding the lock on this var
		self.q = [] # list of transactions waiting to receive a lock on this var
	
	"""
	def __repr__(self):
		r = '{Lock table entry: ' + self.var + '; ' + self.lock + '; ' + \
			   str(self.locking_ts) + '; ' + str(self.q) + '}'
		return r

	def __str__(self):		
		s = '{Lock table entry: ' + self.var + '; ' + self.lock + '; ' + \
			   str(self.locking_ts) + '; ' + str(self.q) + '}'
		return s
	"""	
		
class QueueEntry(object):
	def __init__(self,transaction,r_type,value):
		self.transaction = transaction
		self.r_type = r_type
		self.value = None
		if r_type == 'w':
			self.value = value
