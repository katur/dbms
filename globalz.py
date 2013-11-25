from db_site import Site
from tm import TransactionManager

# site id range property
site_range = range(1,11)

# variable id table
var_ids = ['x' + str(id) for id in range(1,21)]

# global clock
clock = 0

# list of 10 sites 
sites = [ Site(i,0) for i in site_range ] 

# one transaction manager
tm = TransactionManager()
