DBMS project
============

To run:
```
python program.py
```
and then enter instructions on the command line,
carriage return being the time delimiter,
semicolon to delimit cotemporaneous events.

If input is in file `input.txt`:
```
python program.py < input.txt
```


## Updated Project Specification 

Note: This is separate from our higher-level design document.
This is simply an updated version of the previously submitted spec.

#### Main program
- call initialize() function to initialize the data in the sites, create the TM's variable directory, and create lock objects for each var at each site, per the spec.
- loop:
	* input a line from stdin (skipping if whitespace or a comment)
	* increment time
	* re-try all unstarted, pending instructions
	* parse the new input line, splitting on semicolon
	* send each instructions to the tm to execute (tm.process_instruction)

#### Globals
- clock:
	* integer initialized to 0
	* increments with each line of input
- tm: 1 Transaction Manager object
- sites: list of 10 sites, named site1 through site10
- var_ids: list of all var ids
- var_is_replicated(var): check if var replicated based on even/odd

#### Transaction object
- id: the transaction id
- status: "active", "committed", "aborted"
- start_time: clock time when transaction was created
- is_read_only Boolean
- instruction_buffer
	* any pending instruction not completed (either not started due to no active site, or started but blocked on locks)
- instruction_in_progress
	* Boolean of whether the instruction in instruction buffer is started or unstared (if unstarted, will just be attempted at clock tick. If started, is handled by particular triggers: site failure, site recovery, or lock release)
- sites_in_progress
	* also just related to buffered instruction, this is a list of [site, written], i.e. the sites that that an in-progress transaction is waiting to read to, or is waiting to or already written to
- sites_accessed list
	* for read-write only
	* list of tuples, each tuple being a site that was accessed and the initial time of access. needed for available copies algorithm
- impossible_sites
	* for read-only only
	* list of sites the transaction has deemed impossible to read from due to their being no old enough, committed, avail to read versions
	* used to determine if RO should abort if ALL sites are impossible
- add_site_access(self,site): adds a site w/current clock if not in sites_accessed
- grant_lock(self,site): simply update sites_in_progress to reflect a lock being granted (and therefore the write occurring)
- reset_buffer, add_started_instruction_to_buffer, and add_unstarted_instruction_to_buffer
	* updates the instruction buffer and related fields (instruction_in_progress and sites_in_progress) based on instruction completion, instruction being deemed unstarted, and instruction starting, respectively

#### TransactionManager object
- directory dictionary
	* keyed on variable name
	* per var, a list with all sites including copies of that var
	* per var, a next counter indicating the site (list index) to try next, so that we don't overuse any one site for reads
- transactions dictionary
	* keyed on transaction name, value is the transaction object
- locate read site(self,t,vid): locate next read site for this variable, taking into account updating "next" field so no one site becomes a hotspot, and also examining that any selected site has a version that is committed, available to read, and old enough in the case of RO
- abort_transaction(self,t,reason)
	* marks t as aborted, prints why, and calls dm.process_abort(t) at all sites to relase locks
- commit_transaction(self,t)
	* marks t as committed and calls dm.process_commit(t) at all sites to mark writes as committed
- attempt_unstarted_pending_instructions
	* try all unstarted pending instructions (as if they arrived from scratch), and reset instruction buffer (buffer might simply be filled by the same instruction again)
	* NOTE: we should modify this to not attempt these in an arbitrary order. but for the assignment, the professor said it was okay.
- process_instruction(self, i):
	* begin(T) or beginRO(T): create transaction with start_time=clock and RO bit set
	* end(T)
		+ if RO reached this point, can commit no matter what.  
		+ for RW, do avail copies: for each site in in T.sites_accessed, confirm that the site is currently up, and that its site_activation_time precedes the transaction's access time. If so, commit T by sending a message to all sites telling them to commit T. If not, abort T by sending a message to all sites telling them to abort T. Either way, print result to console.
	* R(T,var)
		+ use directory to look up the next active, applicable read site for var
		+ if no active sites, buffer the instruction to perform later
		+ If an active site is found, send read request message to the corresponding DM, specifying if the transaction is RO or RW. If DM responds with the value read, print to console. If DM responds that the transaction was killed due to wait-die, take appropriate actions and print this info to console. Or, if instruction is waiting on a lock, print this to console (NOTE: some subsequent DM response will perform the read).
	* W(T,var,value)
		+ use directory to look up all active sites with var. Send write request messages to all corresponding DMs. If none available, save the write instruction in T.instruction_buffer. If wait or die triggered, take appropraite actions.
	* fail(site)
		+ mark the site as failed
		+ clear lock table
		+ mark all replicated variable's versions as not available_for_read (Note: could just delete them, but we're keeping them for debugging purposes)
		+ update any transactions with in-progress reads/writes in response to the failure (if read, should start over since not pending locks on other sites; if write, should be removed from progress list and transaction either restarted or finished if empty or all written)
	* recover(site)
		+ mark the site as active, w/current activation time
		+ find any transactions with in-progress writes on a var present at this site, and add the recovered site to the write
	* dump(), dump(site), dump(var), querystate(), transactions(): dump info to console

#### Site object (10 total)
- name: this site's name (e.g. "site1")
- active: Boolean for whether or not site is currently active (initially True)
- activation_time: most recent recovery time (initially 0)
- variables: dictionary of variables present at this site, keyed on variable name, value variable object
- dm: data manager for this site

#### Variable object
- name: this variable's name
- versions: list of the versions of that variable over time (newest first)
- get_committed_versions(self): iterates over versions to find all committed versions

#### VariableVersion object
- value: the value written to this version of the variable
- written_by: the transaction that wrote this version
- is_committed: Boolean of whether or not this version is committed
- time_committed: the time this version was committed (False if not committed)
- available_for_read: Boolean of whether or not this version is available to read (versus not available to read, due to failure)

#### DataManager object (one per Site)
- site: the site the DM is managing 
- lm: lock manager for this data manager
- get_read_version(self,t,vid)
	* get the applicable read version for a read request, taking into account the site being active and having an appropriate version "available to read"
- process_ro_read(self,t,vid): process a ro read of vid for t
	* get the appropriate version to read, print it, and reset the buffer
- process_rw_read(self,t,vid): process rw read of vid for t
	* try to get a lock
	* if success, call do_read. otherwise, return the abort/wait msg
- do_read(self,t,vid)
	* add to sites_accessed (for available copies)
	* get the appropriate version to read, print it, and reset buffer
- process_write(self,t,vid,val):
	* try to get lock
	* if success, call apply_write. otherwise, return the abort/wait msg
- apply_write(self,t,vid,val)
	* add to sites_accesed (for available copies)
	* create new var version
	* update transaction so it knows that write succeeded
	* check if ALL the transcation's write sites have succeeded, to reset pending instruction buffer if need be

- process_commit(self,t)
	* find all the variables written by t at this site, and mark them as committed, adding the commit timestamp.
	* unlock all T's locks, which might result in more transactions proceeding 

- process_abort(self,t)
	 * release the locks for this transaction. Could delete its uncommitted writes at this point, but we're keeping them in for debugging purposes.


#### LockManager object (one per DataManager)
- lock_table: dictionary keyed on var present at the site, value a lock table entry
- transaction_locks: dictionary keyed on transactions holding locks at this site, value a list of the vars the transaction has locks on at this site.
- request_lock(self,t,vid,r_type,value)
	* process a transactions's lock request, implementing wait-die if applicable, and calling enqueue if there is a queue
- request_read_lock(self,t,vid)
	* handles read-specific details for request_lock
- request_write_lock(self,t,vid,value)
	* handles write-specific details for request_lock
- enqueue_transaction(self,t,vid,r_type,val)
	* add new transaction to queue
- update_queue(self,var)
	* cycles through lock queues for variable var, popping transactions and granting locks where available
- release_locks(self,t)
	* release all locks held by this transaction (at transaction's abort and commit time)
- reset_lock_table(self)
	* reset lock table (to use after site failure)

#### LockTableEntry object
- vid: the variable id this lock is on
- lock: 'w' for exclusive, 'r' for shared, 'n' for not locked right now
- locking_ts: list of transcations currently holding the lock on this var
- q: queue of QueueEntry objects, i.e., transactions waiting on this lock along with some information regarding the lock request

#### QueueEntry object
- transaction: the transcation waiting
- r_type: whether read or write
- value: the value to be written, if any

#### Message object
- Abort, Wait, or Success based on lock request result
