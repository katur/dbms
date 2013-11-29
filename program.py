import sys
from globalz import clock, sites, tm
from initialize_db import initialize
import re

# initialize data in sites, and tm directory
initialize()

for site in sites:
	site.print_site_state()

tm.print_directory()		
	
# accept stdin input stream, line by line
line = sys.stdin.readline()

while line:
	print line
	if re.match("eof",line):
		break

	clock += 1 # advance time by 1
	print "Current time:" + str(clock)

	# re-try all pending instructions
	tm.attempt_pending_instructions()
	
	# parse new instruction(s) from input line
	instructions = line.split(";")

	# send each instruction to tm
	for instruction in instructions:
		tm.process_instruction(instruction.strip())
	
	line = sys.stdin.readline() # repeat
