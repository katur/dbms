import re
from db_site import Site
from tm import TransactionManager

# gives the result of a lock request 
class Message:
	abort, wait, success = range(3)	

# global clock
clock = 0

# one transaction manager
tm = TransactionManager()

# site id range property
site_range = range(1,11)

# list of 10 sites 
sites = [ Site(i,tm) for i in site_range ] 

# variable id table
var_ids = ['x' + str(id) for id in range(1,21)]

# check if a var is replicated based on even vs odd
def var_is_replicated(vid):
	result = re.search("(?P<num>\d+)", vid)
	if result:
		var_num = int(result.group('num'))
	if var_num % 2 == 0:
		return True
	else:
		return False

# generic print messages for when a read or write happens,
#		to be used by whatever module needs it
def print_read_result(val,site,transaction):
	print str(val) + " read from " + str(site) + " for " + str(transaction)

def print_write_result(vid,val,site,t):
	print vid + "=" + str(val) + " written at " + str(site) + " for " + str(t) 
