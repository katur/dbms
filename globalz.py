import re
from db_site import Site
from tm import TransactionManager

class Message:
	"""
	Object giving the result of a lock request,
		to provide simple communication between modules
		via a return value
	"""
	Abort, Wait, Success = range(3)	

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

def var_is_replicated(vid):
	"""
	Check if a var is replaced based on being even or odd.
	Argument:
		- the var
	Return value:
		- Boolean, True if replicated
	"""
	result = re.search("(?P<num>\d+)", vid)
	if result:
		var_num = int(result.group('num'))
	if var_num % 2 == 0:
		return True
	else:
		return False
