import sys, re
import globalz
from initialize_db import initialize
from collections import Counter

# initialize data in sites, and tm directory
initialize()

#for site in globalz.sites:
#	site.print_site_state()

#globalz.tm.print_directory()		
	
# accept stdin input stream, line by line
line = sys.stdin.readline()

while line:
	if re.match("^\/\/", line): # if comment
		print "// printing comment: " + line
	
	else:
		globalz.clock += 1 # advance time by 1
		# print "Current time:" + str(globalz.clock)
	
		# re-try all pending instructions
		globalz.tm.attempt_pending_instructions()
	
		print "Input Line: " + line.strip()

		# parse new instruction(s) from input line
		instructions = line.split(";")

		# send each instruction to tm
		for instruction in instructions:
			globalz.tm.process_instruction(instruction.strip())
	
	line = sys.stdin.readline() # repeat

# in case there are still pending instructions
# continue incrementing clock and attempting them
for loop in range(globalz.tm.num_active_transactions()):
	globalz.clock += 1
	globalz.tm.attempt_pending_instructions()
