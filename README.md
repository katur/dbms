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

## Design Document

### Main program
- call initialize() function to initialize the data in the sites, create the TM's variable directory, and create lock objects for each var at each site, per the spec.
- loop:
	* input a line from stdin (skipping if whitespace or a comment)
	* increment time
	* try all pending instructions (site.dm.try_pending())
	* parse the new input line, splitting on semicolon
	* send each instructions to the tm to execute (tm.process_instruction)
- finally, loop until no more pending instructions

### Globals
- clock:
	* integer initialized to 0
	* increments with each line of input
- tm: 1 Transaction Manager object
- sites: list of 10 sites, named site1 through site10
- var_ids: list of all var ids
- Flag class: signal for result of a lock request

### Transaction object
- id: the transaction id
- status: "active", "committed", "aborted"
- start_time: clock time when transaction was created
- is_read_only Boolean
- instruction_buffer
	* pending instruction not completed (due to no active site, or blocked on locks)
- sites_accessed list
	* list of tuples, each tuple being a site that was accessed and the initial time of access. needed for available copies algorithm
- blocking_locks: list of locks the transactions is enqueued waiting for. Note that this list must be updated when the transaction is dequeued, or if the site fails.
- add_site_access(self,site): adds a site w/current clock if not in sites_accessed

### Transaction\_Manager object
- directory dictionary
	* keyed on variable name
	* per var, a list with all sites including copies of that var
	* per var, a next counter indicating the site (list index) to try next, so that we don’t overuse any one site for reads
- transactions dictionary
	* keyed on transaction name.
- abort_transaction(self,t)
	* marks t as aborted and calls dm.process_abort(t) at all sites
- num_active_transactions(self)
- transactions_active(self): returns Boolean if any active transactions
- update_waiting_transaction(self,t,site): for each in t.pending_accesses, remove the access if site matches site
- locate read site: locate next read site
- attempt_pending_instructions
	* try all pending instructions, and clear instruction buffer (buffer might simply be filled by the same instruction again)
- process_instruction(self, i):
	* begin(T) or beginRO(T): create transaction with start_time=clock and RO bit set
	* end(T)
		+ if RO reached this point, can commit no matter what.  
		+ for RW, do avail copies: for each site in in T.sites_accessed, confirm that the site is currently up, and that its site_activation_time precedes the transaction's access time. If so, commit T by sending a message to all sites telling them to commit T. If not, abort T by sending a message to all sites telling them to abort T. Either way, print result to console.
	* R(T,var)
		+ use directory to look up the next active read site for var
		+ if no active sites, save the read instruction in T.instruction_buffer (to try at subsequent clock cycles)
		+ If an active site is found, send read request message to the corresponding DM, specifying if the transaction is RO or RW. If DM responds with the value read, print to console. If DM responds that the transaction was killed due to wait-die, take appropriate actions and print this info to console. Or, if instruction is waiting on a lock, possibly print this to console (and note that some subsequent DM response will include the value read).
	* W(T,var,value)
		+ use directory to look up all active sites with var. Send write request messages to all corresponding DMs. If none available, save the write instruction in T.instruction_buffer.
	* fail(site)
		+ mark the site as failed
		+ clear lock table
		+ mark all replicated variable's versions as not available_for_read (Note: could just delete them, but we're keeping them for debugging purposes)
	* recover(site)
		+ mark the site as active
		+ see if any transcations waiting on write should be writing to the newly recovered site 
	* dump(), dump(site), dump(var), querystate(): dump info to console

### Site object (10 total)
- name: this site's name (e.g. "site1")
- active: Boolean for whether or not site is currently active (initially True)
- activation_time: most recent recovery time (initially 0)
- variables: dictionary of variables present at this site, keyed on variable name, value variable object
- dm: data manager for this site

### Variable object
- name: this variable's name
- replicated: Boolean if whether this is a replicated var (initialized at beginning of program)
- versions: list of the versions of that variable over time (newest first)
- get_committed_version(self): iterates over versions to find the most recent committed version 

### VariableVersion object
- value: the value written to this version of the variable
- timestamp: the time this version was written
- written_by: the transaction that wrote this version
- is_committed: Boolean of whether or not this version is committed
- available_for_read: Boolean of whether or not this version is available to read (versus not available to read, due to failure)

### DataManager object
- site: the site the DM is managing 
- lm: lock manager for this data manager
- try_pending(): try all to complete all pending accesses for variables at this site (note: Katherine thinks we should switch this to instead be event driven: if a site fails, or if a site recovers, certain pending accesses might happen. Or, if a lock is released, certain actions might be performed)
- process_ro_read(self,t,vid): process a ro read of vid for t
	* iterate through versions of the variable, until finding one the first committed one that is old enough
	* while iterating, if find one not available for read, stop and return none because all preceding would also be unavailable for read
	* if iterate all the way back to the beginning, return None (shouldn't reach this point...)
- process_rw_read(self,t,vid): process rw read of vid for t
	* try to get the lock. if success, find the most recently committed version, and return it. if not, the alert the tm to either abort or wait (wait-die). if wait, the lm will eventually finish and somehow alert the tm... (still need to figure this out...). Also, need to account for cases of site failure/recovery before the read has happened.
- process_write(self,t,vid,val):
	* try to get the lock. again, if success, create a new version and insert it at the head of the list, and alert the tm. if wait/die, alert the tm. but still need to figure out how to manage the write happening later...
- process_commit(self,t)
	* find all the variables WRITTEN by t at this site, and mark them as committed. (this might be done wrong...), adding the commit timestamp.
	* unlock all T's locks, which might result in more transactions proceeding 
- process_abort(self,t)
	 * release the locks for this transaction. Could delete its uncommitted writes at this point, but we're keeping them in for debugging purposes.


### Lock Manager object
lock_table: dictionary keyed on var present at the site, value a lock if there is one at the site
Handles all locks for this site. Separate notion of shared read lock and exclusive write lock. Implements wait-die by rejecting younger if a lock is held by older (sending a message to TM that transaction is killed), or putting older in a queue if lock is held by younger. Must be able to both access lock state by variable name, but also access all locks for a particular transaction (so that when the transaction ends the LM can find all its locks to release). Whenever a lock is released, LM is responsible for re-assigning the lock if transactions are waiting.

### Lock object

### Message object
