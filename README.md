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
- begin(T) or beginRO(T)
- various printing functions
	* print_directory
	* print_transactions
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
		+ mark all replicated variable's versions as not available_for_read
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
lm: lock manager for this data manager
processing message from TM
site failure
set active=False
site recovery
set active=True and site_activation_time=clock
request to read a variable for a RO transaction T
no lock needed. Simply read the appropriate version of the variable based on T’s start_time. Need to think through what to do if an appropriate version is not available
request to read a variable for a RW transaction T
request lock from LM. if rejected due to wait-die, respond with signal to TM that T was killed. otherwise, whenever lock is granted (perhaps after being put in waiting queue), read the most recent committed version and send signal to TM with the value read
request to write a variable for a RW transaction T
request lock from LM. if rejected due to wait-die, respond with signal to TM that T was killed. otherwise, whenever lock is granted (perhaps after being put in waiting queue), create new variable version but with committed=False
request to commit T
for any variable that had been write locked by T, commit the variable version representing T’s write (by setting committed=True and time_written to current time)
tell LM to unlock all T’s locks (the LM will also handle assigning newly unlocked locks to transactions waiting on the lock)
request to abort T
tell LM to unlock all T’s locks (again, the LM handles re-assigning the locks). we will just leave T’s uncommitted writes as is (with committed=False to signify not to use these values). alternately we could find and delete these values.

### Lock Manager object
lock_table: dictionary keyed on var present at the site, value a lock if there is one at the site
Handles all locks for this site. Separate notion of shared read lock and exclusive write lock. Implements wait-die by rejecting younger if a lock is held by older (sending a message to TM that transaction is killed), or putting older in a queue if lock is held by younger. Must be able to both access lock state by variable name, but also access all locks for a particular transaction (so that when the transaction ends the LM can find all its locks to release). Whenever a lock is released, LM is responsible for re-assigning the lock if transactions are waiting.

### Lock object

### Message object
