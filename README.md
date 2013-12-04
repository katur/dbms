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

### Main program
- call initialize() function to initialize the data in the sites, create the TM's variable directory, and create lock objects for each var at each site, per the spec.
- loop:
	* input a line from stdin (skipping if whitespace or a comment)
	* increment time
	* re-try all unstarted, pending instructions
	* parse the new input line, splitting on semicolon
	* send each instructions to the tm to execute (tm.process_instruction)

### Globals
- clock:
	* integer initialized to 0
	* increments with each line of input
- tm: 1 Transaction Manager object
- sites: list of 10 sites, named site1 through site10
- var_ids: list of all var ids
- var_is_replicated(var): check if var replicated based on even/odd

### Transaction object
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

### Transaction\_Manager object
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
- versions: list of the versions of that variable over time (newest first)
- get_committed_versions(self): iterates over versions to find all committed versions

### VariableVersion object
- value: the value written to this version of the variable
- written_by: the transaction that wrote this version
- is_committed: Boolean of whether or not this version is committed
- time_committed: the time this version was committed (False if not committed)
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
- lock_table: dictionary keyed on var present at the site, value a lock table entry
- transaction_locks: dictionary keyed on transactions holding locks at this site, value a list of the vars the transaction has locks on at this site.
- enqueue_transaction
- release_locks
- request_read_lock
- request_write_lock
- request_lock

### Lock Table Entry object
- var: the var this lock is on
- lock: 'w' for exclusive, 'r' for shared, 'n' for not locked right now
- locking_ts: list of transcations currently holding the lock on this var
- q: queue of QueueEntry objects, i.e., transactions waiting on this lock along with some information regarding the lock request

### Queue Entry object
- transaction: the transcation waiting
- r_type: whether read or write
- value: the value to be written, if any

### Message object
- Abort, Wait, or Success based on lock request result
