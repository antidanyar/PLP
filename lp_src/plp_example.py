#compare lp_data/generated_data/description.txt with what PLP ends up with

#the example for LP_PLP application
import os

dir_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

def write_the_rules(result, filename):
	with open(filename, 'w') as f:
		f.write(result)
	return filename

from utils import load
#pairs, freqs = load(dir_path+'/'+'lp_data/mixedV/rus.txt', skip_header=True)
#pairs, freqs = load(dir_path+'/'+'lp_data/generated_data/data.txt', skip_header=True)
pairs, freqs = load(dir_path+'/'+'lp_data/generated_data_FD/data.txt', skip_header=True)
from plp import PLP
plp = PLP(ipa_file='../lp_data/generated_data_FD/ipa.txt')
plp.train(pairs)

#write_the_rules(str(plp), filename=dir_path+'/'+'lp_data/generated_data/description_plp.txt')
write_the_rules(str(plp), filename=dir_path+'/'+'lp_data/generated_data_FD/description_plp.txt')

