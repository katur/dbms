import sys
import globalz
from initialize_db import initialize
import re

# initialize data in sites, and tm directory
initialize()

#for site in globalz.sites:
#	site.print_site_state()

#globalz.tm.print_directory()		
	
# accept stdin input stream, line by line
line = sys.stdin.readline()
instructions_remaining = False

while line or instructions_remaining:
	if line:
		print 'Reading: ' + line.strip()

	globalz.clock += 1 # advance time by 1
	print "Current time:" + str(globalz.clock)

	# re-try all pending instructions
	instructions_remaining = globalz.tm.attempt_pending_instructions()
	
	# parse new instruction(s) from input line
	instructions = line.split(";")

	# send each instruction to tm
	for instruction in instructions:
		globalz.tm.process_instruction(instruction.strip())
	
	if line:
		line = sys.stdin.readline() # repeat
