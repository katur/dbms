from db_site import Site
from tm import TransactionManager

# global clock
clock = 0

# list of 10 sites 
sites = [ Site(i,0) for i in range(1,11) ] 

# one transaction manager
tm = TransactionManager()
