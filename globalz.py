from db_site import Site
from tm import TransactionManager

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

# gives the result of a lock request 
class Flag:
	Abort, Wait, Success = range(3)	
