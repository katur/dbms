from pprint import pprint
import globalz

class LockManager(object):
	"""
	Lock manager object	
	"""
	def __init__(self,dm):
		# corresponding data manager
		self.dm = dm
	
		# lock table key:var; value:lock table entry
		self.lock_table = {} 
		
		# transaction_locks: key:transaction; 
		#		value:list of vars at this site
		#		for which transaction has locks
		self.transaction_locks = {}

	def print_lock_table(self):
		pprint(self.lock_table) 

	def reset_lock_table(self):
		for vid in self.lock_table.keys( ):
			self.lock_table[vid] = LockTableEntry(vid)

	# checks lock queue for variable @var, popping transactions and 
	# granting them locks if available.
	def update_queue(self,var):
		"""
		@var: variable whose lock queue to be updated
		
		side effects: Transactions waiting at the head of the queue
					  will be granted locks if possible. When this 
					  happens, the requested read/write will be 
					  performed immediately. Finally the transaction's
					  instruction buffer will be reset if the new lock
					  was the last one it was waiting for. 					
		"""
		q = self.lock_table[var].q
		if len(q) == 0:
			return	
		# pending transaction(s) requests shared lock
		if q[0].r_type == 'r':
			self.lock_table[var].lock = 'r' # apply shared lock to var
			while len(q) > 0 and q[0].r_type == 'r':				
				q_entry = q.pop(0) # pop t from queue
				t = q_entry.transaction
				#print 'assigning shared lock on ' + var + ' to ' + str(t)
				self.lock_table[var].locking_ts.append(t) # assign shared lock to t
				if not t in self.transaction_locks:
					self.transaction_locks[t] = []
				self.transaction_locks[t].append(var) # assign shared lock to t
				self.dm.do_read(t,var) # get and print read result
				t.grant_lock(self.dm.site) # update t 
		# pending transaction(s) requests exclusive lock				
		else:
			self.lock_table[var].lock = 'w' # apply exclusive lock to var
			q_entry = q.pop(0)# pop t from queue
			t = q_entry.transaction
			#print 'assigning exclusive lock on ' + var + ' to ' + str(t)			
			self.lock_table[var].locking_ts = [t] # assign exclusive lock to t	
			if not t in self.transaction_locks:
				self.transaction_locks[t] = []
			self.transaction_locks[t].append(var) # assign exclusive lock to t	
			val = q_entry.value 
			self.dm.apply_write(t,var,val) # apply write and print result to console
			t.grant_lock(self.dm.site) # update t
				
	
	def enqueue_transaction(self,t,vid,r_type,val):
		"""
		Returns False if older transaction 
		already enqueued on a conflicting lock.
		
		Otherwise, enqueues transaction
		and returns True.
		"""
		if r_type == 'w' or self.lock_table[vid].lock == 'w':
			for t2 in self.lock_table[vid].locking_ts:
				if t2.start_time < t.start_time:
					return False		
					
		lt_entry = self.lock_table[vid]
		for q_entry in lt_entry.q:
			if((r_type=='w' or q_entry.r_type=='w') and q_entry.transaction.start_time < t.start_time):
				return False
		lt_entry.q.append(QueueEntry(t,r_type,val))
		return True		


	def release_locks(self,t):
		"""
		Release all the locks at this site
		held by t.
		
		side effects: if t was the only transaction holding a lock
					  on some variable, then upon releasing 
					  that variable's queue will be updated, and 
					  new locks potentially granted, per function
					  @update_queue
		
		"""	
		for var in self.transaction_locks[t]:
			print "\t" + str(t) + " releasing a lock on " + var
			if t in self.lock_table[var].locking_ts:
				self.lock_table[var].locking_ts.remove(t)
			#else:
				# print str(t) + " did not hold a lock on " + var
			if len(self.lock_table[var].locking_ts)==0:
				self.lock_table[var].lock = 'n'
				self.update_queue(var)

	def request_lock(self,t,vid,r_type,value):
		"""
		Request a lock to read/write a variable.
		
		@t: The transaction requesting a lock
		@vid: Name of the variable being read/written to
		@r_type: 'r' if request for a shared (read) lock,
				 else 'w' for an exclusive (write) lock
		@value: if the request is for a write lock,
				the value to be written
		
		Note: this fxn called on any RW transaction's
			reads or writes (covers the case of it 
			already having a lock)
			
		returns a globalz.Message instance indicating whether
		the request was successful, will cause t to wait,
		or will cause t to abort
		"""
		lt_entry = self.lock_table[vid]
		
		# if no lock on variable
		if lt_entry.lock == 'n':
			self.lock_table[vid].lock = r_type
			self.lock_table[vid].locking_ts = [t]
			if not t in self.transaction_locks:
				self.transaction_locks[t] = []
			self.transaction_locks[t].append(vid)
			return globalz.Message.Success
		
		# if transaction already holds a lock
		elif t in lt_entry.locking_ts:
			if lt_entry.lock == 'w': # if exclusive
				return globalz.Message.Success
			else: # if shared
			# transaction requests an upgrade from shared lock to exclusive
				# transaction holds the only shared lock on variable
				if len(lt_entry.locking_ts) == 1:
					lt_entry.lock = 'w'
					return globalz.Message.Success
				else:
					# release t's shared lock
					lt_entry.locking_ts.remove(t)
					for i in range(len(t.sites_in_progress)):
						if t.sites_in_progress[i][0] == self.dm.site:
							t.sites_in_progress[i][1] = False
							break
					self.transaction_locks[t].remove(vid)
							
					enqueue_result = self.enqueue_transaction(t,vid,r_type,value)
					if enqueue_result:
						return globalz.Message.Wait
					else:
						return globalz.Message.Abort
				
		# if transaction wants a write
		elif r_type == 'r':
			return self.request_read_lock(t,vid)
		
		# if transaction wants a write lock
		else:
			return self.request_write_lock(t,vid,value)

	
	def request_read_lock(self,t,vid):
		"""
		This fxn called by request_lock
		if a read lock is needed.
		
		@t: the transaction requesting the lock
		@vid: name of the variable to be read
		
		returns a globalz.Message instance indicating whether
		the request was successful, will cause t to wait,
		or will cause t to abort		
		"""
		# if currently a shared lock on variable
		if self.lock_table[vid].lock == 'r' and len(self.lock_table[vid].q) == 0:
			self.lock_table[vid].locking_ts.append(t)
			if not t in self.transaction_locks:
				self.transaction_locks[t] = []
			self.transaction_locks[t].append(vid)
			return globalz.Message.Success
		
		else: # if currently an exclusive lock
			locking_t = self.lock_table[vid].locking_ts[0]
			if locking_t.start_time < t.start_time:
				return globalz.Message.Abort
			enqueue_result = self.enqueue_transaction(t,vid,'r',None)
			if enqueue_result:
				# NOTE: katherine changed to wait from success
				return globalz.Message.Wait
			else:
				return globalz.Message.Abort
		

	def request_write_lock(self,t,vid,value):
		"""
		This fxn called by request_lock
		if a write lock is needed.
		
		@t: the transaction requesting the lock
		@vid: name of the variable to be written to
		@value: the value to be written		
		
		returns a globalz.Message instance indicating whether
		the request was successful, will cause t to wait,
		or will cause t to abort		
		"""
		for locking_t in self.lock_table[vid].locking_ts:
			if locking_t.start_time < t.start_time:
				return globalz.Message.Abort
			enqueue_result = self.enqueue_transaction(t,vid,'w',value)
			if enqueue_result:
				return globalz.Message.Wait
			else:
				return globalz.Message.Abort


class LockTableEntry(object):
	"""
	Lock Table Entry object
	"""
	def __init__(self,vid):
		self.vid = vid # the variable this lock is on
		self.lock = 'n' # 'w' for exclusive, 'r' for shared
		self.locking_ts = [] # list of transactions currently holding the lock on this var
		self.q = [] # list of transactions waiting to receive a lock on this var
	
	def __repr__(self):
		result = "{lock type:" + self.lock + "; " + "held by:"
		for t in self.locking_ts:
			result += str(t) + " "
		result += "; " + "queue:" + str(self.q) + "}"
		return result
	
	def __str__(self):
		return self.vid
	
		
class QueueEntry(object):
	def __init__(self,transaction,r_type,value):
		self.transaction = transaction # transaction waiting for lock
		self.r_type = r_type # 'r' if transaction requesting a shared lock, else 'w'
		self.value = None # if write request, the value to be written
		if r_type == 'w':
			self.value = value

	def __repr__(self):
		return '{' + str(self.transaction) + ', ' + self.r_type + '}'
