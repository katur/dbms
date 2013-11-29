from db_site import Site
from tm import TransactionManager

# gives the result of a lock request 
class Flag:
	Abort, Wait, Success = range(3)	

# site id range property
site_range = range(1,11)

# variable id table
var_ids = ['x' + str(id) for id in range(1,21)]

# global clock
clock = 0

# one transaction manager
tm = TransactionManager()

# list of 10 sites 
sites = [ Site(i,0,tm) for i in site_range ] 
