from variable import Variable
from variable_version import VariableVersion
from lm import LockTableEntry
from globalz import sites, tm

def initialize():
	def initialize_variable(var_name, site, val, replicated):
		var = Variable(var_name,replicated)
		vers = VariableVersion(val, 0, None, True)
		var.versions.append(vers)
		site.variables[var_name] = var
		tm.directory[var_name]['sitelist'].append(site)
		#site.dm.lm.lock_table[var_name] = {'lock':'n', 'ts':[], 'q':[]}
		site.dm.lm.lock_table[var_name] = LockTableEntry(var_name)
	
	# for each variable, x1 through x20
	for i in range(1,21):
		var_name = 'x' + str(i)

		# add new var to tm directory
		tm.directory[var_name] = { 'sitelist': [], 'next': 0 }

		if i % 2 == 0: # if even, at all sites
			for site in sites:
				initialize_variable(var_name, site, i*10, True)
		
		else: # if odd, at one particular site
			site = sites[((1+i) % 10) - 1]
			initialize_variable(var_name, site, i*10, False)
