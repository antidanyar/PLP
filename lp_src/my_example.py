#the example for LP_PLP application
import os
import pprint

dir_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

def write_the_rules(result, filename):
	with open(filename, 'w') as f:
		f.write(result)
	return filename

from utils import load
#pairs, freqs = load(dir_path+'/'+'lp_data/mixedV/data.txt', skip_header=True)
#pairs, freqs = load(dir_path+'/'+'lp_data/generated_data/data.txt', skip_header=True)
pairs, freqs = load(dir_path+'/'+'lp_data/generated_data_FD/data.txt', skip_header=True)
from plp import PLP
#plp = PLP(ipa_file='../lp_data/generated_data/ipa.txt')
plp = PLP(ipa_file='../lp_data/generated_data_FD/ipa.txt')
#plp = PLP(ipa_file='../lp_data/mixedV/ipa.txt')
#plp.train(pairs)
mappings = plp.get_mappings(pairs)
print(mappings)

import LPgrammar

#interface = LPgrammar.Interface(dir_path+'/'+'lp_data/mixedV/ipa.txt')
#interface = LPgrammar.Interface(dir_path+'/'+'lp_data/generated_data/ipa.txt')
interface = LPgrammar.Interface(dir_path+'/'+'lp_data/generated_data_FD/ipa.txt')

from lp_plp import LP_PLP

lp_learner = LP_PLP(pairs, mappings, interface)

grammar = lp_learner.train()

description = grammar.describe()
#write_the_rules(description, filename=dir_path+'/'+'lp_data/mixedV/description.txt')
#write_the_rules(description, filename=dir_path+'/'+'lp_data/generated_data/description.txt')
write_the_rules(description, filename=dir_path+'/'+'lp_data/generated_data_FD/description.txt')

#these are mostly sanity check, given that PLP mappings generate this too. 
# Mostly to ensure no information loss in generalization

print(len(grammar.rules)) #to double check that the rules used to compute SRs below are the generalized ones
print(grammar.getSR('Vbab', grammar.rules)) # should return vbab without FD; vbap with FD
print(grammar.getSR('Vpab', grammar.rules)) # should return fpab without FD; fpap with FD
print(grammar.getSR('pVab', grammar.rules)) # should return pvab without FD; pfap with FD
print(grammar.getSR('bVab', grammar.rules)) # should return bvab without FD; bvap with FD
print(grammar.getSR('pbab', grammar.rules)) #  should return bbab without FD; bbap with FD
print(grammar.getSR('bpab', grammar.rules)) # should return ppab without FD; ppap with FD
