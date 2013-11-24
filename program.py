import sys
from config import clock, sites, tm
from initialize_db import initialize

# initialize data in sites, and tm directory
initialize(sites, tm)

for site in sites:
	site.print_site_state()

tm.print_directory()

# accept stdin input stream, line by line
line = sys.stdin.readline()
while line:
	clock += 1
	print "Current time:" + str(clock)
	instructions = line.split(";")
	for instruction in instructions:
		# send instructions to the tm
		tm.process_instruction(instruction.strip())
	line = sys.stdin.readline()
