import sys, re
import globalz
from initialize_db import initialize
from collections import Counter

"""
This is the main program to be run.
After initializing the database state,
	it accepts a line at a time from standard
	input, and handles incrementing the clock,
	attempting pending instructions, and sending
	each new instruction to the transaction manager.
"""

# initialize data in sites, and tm directory
initialize()

# accept stdin input stream, line by line
line = sys.stdin.readline()

while line:
	if re.match("^\/\/", line): # if comment
		print ">>comment: " + line
	
	elif line.strip() != "": # skip blank lines
		globalz.clock += 1 # advance time by 1
		print "\n----- time " + str(globalz.clock) + " -----"
	
		# re-try unstarted pending instructions
		globalz.tm.attempt_unstarted_buffered_instructions()
	
		# print the line to console (for clarity)
		print ">>" + line.strip()

		# parse new instruction(s) from input line
		instructions = line.split(";")

		# send each instruction to tm
		for instruction in instructions:
			globalz.tm.process_instruction(instruction.strip())
	
	line = sys.stdin.readline() # repeat
