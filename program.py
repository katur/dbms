import sys
from db_site import Site
from initialize_db import initialize
import config

# create list of 10 sites
sitelist = [ Site(i) for i in range(1,11) ] 

# initialize the initial db state, as defined in spec
initialize(sitelist)

for site in sitelist:
	site.print_site_state()


# accept stdin input stream, line by line
line = sys.stdin.readline()
while line:
	config.clock += 1
	print "Current time:" + str(config.clock)
	print line
	line = sys.stdin.readline()
