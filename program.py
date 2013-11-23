import sys
import config
from db_site import Site
from tm import TransactionManager
from initialize_db import initialize

# create list of 10 sites
sites = [ Site(i) for i in range(1,11) ] 

# create a transaction manager
tm = TransactionManager()

# according to project spec,
# initialize the data at the sites
# along with the tm's directory
initialize(sites, tm)

for site in sites:
	site.print_site_state()

# accept stdin input stream, line by line
line = sys.stdin.readline()
while line:
	print "Current time:" + str(config.clock)
	print line
	config.clock += 1
	line = sys.stdin.readline()
