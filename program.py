import sys, re
import globalz
from initialize_db import initialize

# initialize data in sites, and tm directory
initialize()

#for site in globalz.sites:
#	site.print_site_state()

#globalz.tm.print_directory()		
	
# accept stdin input stream, line by line
line = sys.stdin.readline()
instructions_remaining = False

while line or instructions_remaining:
	globalz.clock += 1 # advance time by 1
	print "Current time:" + str(globalz.clock)
	
	# re-try all pending instructions
	instructions_remaining = globalz.tm.attempt_pending_instructions()
	
	if line:
		print 'Reading: ' + line.strip()

		# parse new instruction(s) from input line
		instructions = line.split(";")

		# send each instruction to tm
		for instruction in instructions:
			globalz.tm.process_instruction(instruction.strip())
	
		line = sys.stdin.readline() # repeat
