from variable import Variable
from variable_version import VariableVersion
from globalz import sites, tm

def initialize():
	def add_var_to_site_and_dir(var_name, site, val):
		var = Variable(var_name)
		vers = VariableVersion(val, 0, None, True)
		var.versions.append(vers)
		site.variables[var_name] = var
		tm.directory[var_name]['sitelist'].append(site.name)
		site.dm.lm.lock_table[var_name] = 'n'
	
	# for each variable, x1 through x20
	for i in range(1,21):
		var_name = 'x' + str(i)

		# add new var to tm directory
		tm.directory[var_name] = { 'sitelist': [], 'next': 0 }

		if i % 2 == 0: # even
			for site in sites:
				add_var_to_site_and_dir(var_name, site, i*10)
		
		else: # odd
			site = sites[((1+i) % 10) - 1]
			add_var_to_site_and_dir(var_name, site, i*10)
