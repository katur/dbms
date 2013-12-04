import sys, re
import globalz
from initialize_db import initialize
from collections import Counter

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
	
		print ">>" + line.strip()

		# parse new instruction(s) from input line
		instructions = line.split(";")

		# send each instruction to tm
		for instruction in instructions:
			globalz.tm.process_instruction(instruction.strip())
	
	line = sys.stdin.readline() # repeat
