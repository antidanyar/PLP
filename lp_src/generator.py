# this file generates an artificial dataset given an ipa.txt file (an interface) and the required phonological rules

from LPgrammar import *
import random

voiced_vfs = VFset()
voiced_vfs['voi'] = 1
voiced_vfs['cons'] = 1
voiceless_vfs = VFset()
voiceless_vfs['voi'] = -1
voiceless_vfs['cons'] = 1

voiced_nc = NaturalClass()
voiceless_nc = NaturalClass()
voiced_nc.singleton(voiced_vfs)
voiceless_nc.singleton(voiceless_vfs)

boundary_nc = NaturalClass()
boundary_nc.singleton(WORD_BOUNDARY)

rules = [
	Rule(voiced_nc, voiced_vfs, unification=False, leftTrigger=NaturalClass(), rightTrigger=voiceless_nc),
	Rule(voiceless_nc, voiceless_vfs, unification=False, leftTrigger=NaturalClass(), rightTrigger=voiced_nc),
	Rule(NaturalClass(), voiceless_vfs, unification=True, leftTrigger=NaturalClass(), rightTrigger=voiceless_nc),
	Rule(NaturalClass(), voiced_vfs, unification=True, leftTrigger=NaturalClass(), rightTrigger=voiced_nc),
	Rule(NaturalClass(), voiced_vfs, unification=True, leftTrigger=NaturalClass(), rightTrigger=NaturalClass())
]


rules2 = [
	Rule(voiced_nc, voiced_vfs, unification=False, leftTrigger=NaturalClass(), rightTrigger=voiceless_nc),
	Rule(voiceless_nc, voiceless_vfs, unification=False, leftTrigger=NaturalClass(), rightTrigger=voiced_nc),
	Rule(NaturalClass(), voiceless_vfs, unification=True, leftTrigger=NaturalClass(), rightTrigger=voiceless_nc),
	Rule(NaturalClass(), voiced_vfs, unification=True, leftTrigger=NaturalClass(), rightTrigger=voiced_nc)
]

rules3 = [
	Rule(voiced_nc, voiced_vfs, unification=False, leftTrigger=NaturalClass(), rightTrigger=voiceless_nc),
	Rule(voiceless_nc, voiceless_vfs, unification=False, leftTrigger=NaturalClass(), rightTrigger=voiced_nc),
	Rule(NaturalClass(), voiceless_vfs, unification=True, leftTrigger=NaturalClass(), rightTrigger=voiceless_nc),
	Rule(NaturalClass(), voiced_vfs, unification=True, leftTrigger=NaturalClass(), rightTrigger=voiced_nc),
	Rule(NaturalClass(), voiced_vfs, unification=True, leftTrigger=NaturalClass(), rightTrigger=NaturalClass()),
	Rule(voiced_nc, voiced_vfs, unification=False, leftTrigger=NaturalClass(), rightTrigger=boundary_nc),
	Rule(NaturalClass(), voiceless_vfs, unification=True, leftTrigger=NaturalClass(), rightTrigger=boundary_nc),
]


def get_CV(symbols: list, interface: Interface):
	consonants = []
	vowels = []
	non_sonorants = []
	for symbol in symbols:
		if symbol != '#':
			if interface.toPhonology[symbol]['cons'] == 1:
				consonants.append(symbol)
				if interface.toPhonology[symbol]['son'] == -1:
					vfs = interface.toPhonology[symbol].makeCopy()
					vfs['voi'] = vfs['voi']*(-1)
					if vfs.to_tuple() in interface.toPhonetics:
						non_sonorants.append(symbol)
			else:
				vowels.append(symbol)
	return consonants, vowels, non_sonorants

def get_possible_urs(consonants: list, vowels: list, non_sonorants:list) -> list:
	#all artificial words will have the form CVCC or CCVC (since we care about consonant-consonant interactions)
	words = []
	for a in non_sonorants:
		for b in vowels:
			for c in non_sonorants:
				for d in non_sonorants:
						words.append(a+b+c+d)
		for b in non_sonorants:
			for c in vowels:
				for d in non_sonorants:
						words.append(a+b+c+d)
	return words

def generate_dataset(rules: list, interface: Interface) -> list:
	grammar = Grammar(interface, rules)
	available_symbols  = list(interface.toPhonology.keys())
	#available_symbols = [symbol for symbol in available_symbols if symbol != 'V'] #optional
	consonants, vowels, non_sonorants = get_CV(available_symbols, interface)
	possible_URs = get_possible_urs(consonants, vowels, non_sonorants)
	random.shuffle(possible_URs)
	existing_URs = possible_URs[:1000]
	existing_maps = [(ur, grammar.getSR(ur, rules)) for ur in existing_URs]
	return existing_maps

def write_maps_to_file(maps, filename):
	with open(filename, 'w') as f:
		f.write('UR\tSF\tFREQ\n')
		for map in maps:
			f.write(map[0]+'\t'+map[1]+'\t'+'1\n')
	return filename

import os
dir_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

interface = Interface(dir_path+'/'+'lp_data/generated_data_FD/ipa.txt')

maps = generate_dataset(rules3, interface)
write_maps_to_file(maps, dir_path+'/'+'lp_data/generated_data_FD/data.txt')