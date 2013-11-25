import sys
from globalz import clock, sites, tm
from initialize_db import initialize
import re

# initialize data in sites, and tm directory
initialize()

for site in sites:
	site.print_site_state()

tm.print_directory()


reading_file = False
if len(sys.argv) > 1:
	input = open(sys.argv[1],'r')
	reading_file = True
else:
	input = sys.stdin
	
# accept stdin input stream, line by line
line = input.readline()
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
<<<<<<< HEAD
	
	line = input.readline() # repeat
	
if reading_file:
	input.close( )
=======

	line = sys.stdin.readline() # repeat
>>>>>>> 4920caa9887ecd028be94778f9627f3273e91112
