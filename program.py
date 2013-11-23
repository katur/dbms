import sys
import config
from db_site import Site
from tm import TransactionManager
from initialize_db import initialize

# create list of 10 sites
sites = [ Site(i) for i in range(1,11) ] 

# create the transaction manager
tm = TransactionManager()

# according to project spec,
# initialize site data
# along with tm's directory
initialize(sites, tm)

for site in sites:
	site.print_site_state()

tm.print_directory()

# accept stdin input stream, line by line
line = sys.stdin.readline()
while line:
	config.clock += 1
	print "Current time:" + str(config.clock)
	instructions = line.split(";")
	for instruction in instructions:
		# send instructions to the tm
		tm.process_instruction(instruction.strip())
	line = sys.stdin.readline()
