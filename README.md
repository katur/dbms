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

# Design Document

## Main program
- initialize the data in the sites, as well as the TM’s directory, per the spec
- loop inputting a lint at a time from stdin
- for each line, parse the individual instructions
- send each instruction to TM to process

## Globals
- clock integer
	* =0 at beginning of program
	* increments with each line of input
- 1 TM
- 10 sites

## Transaction object
- start_time integer
	* clock time when transaction was created
- is_read_only Boolean
- sites_accessed list
	* sites accessed in T’s lifetime (to see if all up since T began, per Available Copies Algorithm)
- instruction_buffer string
	* pending instruction not performed due to no active site being found on a previous cycle (this instruction to be attempted in all subsequent clock cycles until site(s) available)
*Note that Transaction objects must be made accessible to DMs (so DM can access start_time for wait-die and MV)*

## Transaction\_Manager object
directory dictionary
keyed on variable name
per var, a list with all sites including copies of that var
per var, a next counter indicating the site (list index) to try next, so that we don’t overuse any one site for reads
transactions dictionary
keyed on transaction name.
Note: at every clock cycle, this list must be iterated to see if any transactions have pending instructions to execute.
process_instruction function, accepts string, returns nothing
begin(T) or beginRO(T)
create transaction with start_time=clock and RO bit set
end(T)
for each site in in T.sites_accessed, confirm that its site_activation_time precedes T.start_time. If so, commit T by sending a message to all sites telling them to commit T (described in DM) and printing to console that T committed. If not, abort T by sending a message to all sites telling them to abort T, and printing to console that T aborted due to our available copies algorithm / site x’s failure.
R(T,var)
use directory to look up the next active read site for var. If no active sites, save the read instruction in T.instruction_buffer, and add T to pending_instructions (to try at subsequent clock cycles). If an active site is found, send read request message to the corresponding DM, specifying if the transaction is RO or RW. If DM responds with the value read, print to console. If DM responds that the transaction was killed due to wait-die, take appropriate actions and print this info to console. Or, if instruction is waiting on a lock, possibly print this to console (and note that some subsequent DM response will include the value read).
W(T,var,value)
use directory to look up all active sites with var. Send write request messages to all corresponding DMs. If none available, save the write instruction in T.instruction_buffer and add T to pending_instructions.
fail(site)
send failure message to site’s corresponding DM
recover(site)
send recovery message to site’s corresponding DM
dump(), dump(site), dump(var)
iterate over relevant information and print it to console
querystate(): a function for our own debugging sanity

## Site object (10 total)
name: this site’s name (e.g. “site1”)
active: Boolean for whether or not site is currently active, init to True.
activation_time: most recent recovery time, init to 0
variables: hash with variables present at this site. key is variable name, value is Variable object
dm: data manager for this site

## Variable object
versions: linked list of the versions of that variable over time (needed for multiversion for RO transactions)
locked_by: the transaction, if any, holding a lock on this variable (note that our “per site lock table” is actually just a field on our variable objects, so the operation of wiping all locks involves traversing the entire hashmap of variables

## VariableVersion object
value: the value written to this version of the variable
time_written: the time this version was written by some transaction
written_by: the transaction that wrote this version
committed: Boolean of whether or not this version is committed

## DataManager object
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

##Lock Manager object
lock_table: dictionary keyed on var present at the site, value a lock if there is one at the site
Handles all locks for this site. Separate notion of shared read lock and exclusive write lock. Implements wait-die by rejecting younger if a lock is held by older (sending a message to TM that transaction is killed), or putting older in a queue if lock is held by younger. Must be able to both access lock state by variable name, but also access all locks for a particular transaction (so that when the transaction ends the LM can find all its locks to release). Whenever a lock is released, LM is responsible for re-assigning the lock if transactions are waiting.

## Lock object

## Message object
