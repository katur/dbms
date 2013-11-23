from variable import Variable
from variable_version import VariableVersion

def initialize(sitelist):
	def add_init_var_to_site(var_name, site, i):
		var = Variable(var_name)
		vers = VariableVersion(10*i, True)
		var.versions.append(vers)
		site.variables[var_name] = var
	
	# for each variable, x1 through x20
	for i in range(1,21):
		var_name = 'x' + str(i)

		if i % 2 == 0: # even
			for site in sitelist:
				add_init_var_to_site(var_name, site, i)
		
		else: # odd
			add_init_var_to_site(var_name, sitelist[((1+i)%10)-1], i)
