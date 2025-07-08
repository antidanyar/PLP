# This is an implementation for a Logical Phonology grammar. It implements: feature sets, natural classes, phonological rules, phonetics-phonology interface (construed as mapping from feature sets onto symbols and vice versa)

import pprint # used for string descriptions of feature sets, natural classes, and rules
import networkx as nx #used for topological sort

def toNumbers(s):
	if s == '+':
		return 1
	if s == '-':
		return -1
	return 0

# VFset (Valued Feature set): a mapping from a set of features to their values {-1, 0, 1} (-F; underspecified; +F)
# Since it is a mapping, it is implemented as a custom dictionary
# Note: in this version, there is a consistent ambiguity between underspecification qua mapping a feature onto 0 and underspecification qua not having a feature in the dictionary at all. That should be fixed.

class VFset(dict):
	def fill(self, features):
		for feature in features:
			if feature not in self:
				self[feature] = 0
		return self

	def makeCopy(self): # returns a copy of itself
		vfs = VFset()
		for feature in self:
			vfs[feature] = self[feature]
		return vfs

	def isEmpty(self): # checks if it is empty by the virtue of having no features
		return len(VFset) == 0
	
	def is_empty(self): # checks if it is empty by the virtue of mapping all specified features onto 0
		for feature in self:
			if self[feature] != 0:
				return False
		return True
	
	def toStringList(self) -> list: #transforms itself into a list of "+feature" and "-feature" strings 
		result = []
		for feature in self:
			if self[feature] == 1:
				result.append('+' + feature)
			if self[feature] == -1:
				result.append('-' + feature)
		return result
				
	def to_tuple(self): #transforms itself into a tuple. used for hashing purposes
		result = []
		for feature in self:
			result.append((feature, self[feature]))
		return tuple(result)

	# subtraction: an operation defined on two VFsets X and Y. Returns a third VFset Z which maps any feature F to the same value that X does unless X and Y map the feature to the same value. If so, Z maps F to 0. (Subtraction in Logical Phonology)

	def subtraction(self, other):
		result = self.makeCopy()
		for feature in other:
			if self[feature] == other[feature]:
				result[feature] = 0
		return result
	
	# unification: an operation defined on two VFsets X and Y. If there is any feature F s.t. X and Y map it to 1 and -1 respectively or vice versa, returns X. If there is no such feature, returns a third VFset Z s.t. if X maps a feature F to -1 or 1, Z does too; but if X maps a feature F to 0, Z maps F to the same value that Y does. (Priority Union in Logical Phonology)
	
	def unification(self, other):
		result = self.makeCopy()
		for feature in other:
			if feature in self:
				if self[feature] * other[feature] == -1:
					return self
				else:
					if self[feature] == 0:
						result[feature] = other[feature]
			else:
				result[feature] = other[feature]
		return result
	
	# to_subtract: given two VFsets X and Y return those feature of X that conflict with the feature description of Y. Used to determine which features should be subtracted in transforming a segment-segment mapping into a pair of a deletion rule and an insertion rule

	def to_subtract(self, other):
		change_vfs = VFset()
		for feature in self:
			if self[feature] != 0:
				if self[feature] * other[feature] != 1:
					change_vfs[feature] = self[feature]
		return change_vfs
	
	# to_unify: given two VFsets X and Y return those features of Y that are underspecified in X. Used to determine which features should be unified in transforming a segment-segment mapping into a pair of a deletion rule and an insertion rule
	
	def to_unify(self, other):
		add_vfs = VFset()
		for feature in other: 
			if other[feature] != 0:
				if feature not in self:
					add_vfs[feature] = other[feature]
				else:
					if self[feature] == 0:
						add_vfs[feature] = other[feature]
		return add_vfs
	
WORD_BOUNDARY = VFset() # defines a word boundary VFset
WORD_BOUNDARY['segment'] = -1 
#word boundary will be treated as a -SEGMENT VFset to clean up the types of in rule application
	
# interface: a mapping from VFsets to symbols (IPA characters) and vice versa

class Interface:
	def __init__(self, ipa_file):
		self.toPhonetics = {WORD_BOUNDARY.to_tuple(): '#'} # initializes phonology -> phonetics mapping
		self.toPhonology = {'#': WORD_BOUNDARY} # initializes phonetics -> phonology mapping
		self.features = ['segment'] #initialized the set of available features
		with open(ipa_file, 'r') as f: 
			#interface is read of an ipa.txt file of the sort present in the data/ and lp_data/ directories
			first_line = f.readline()
			features = first_line[:-1].split('\t')[1:]
			for line in f.readlines():
				info = line[:-1].split('\t')
				newSegment = info[0]
				self.toPhonology[newSegment] = VFset() 
				#phonetics to phonology mapping  maps IPA symbols to VFsets
				self.toPhonology[newSegment]['segment'] = 1
				i = 1
				for feature in features:
					self.toPhonology[newSegment][feature] = toNumbers(info[i])
					i += 1
				self.toPhonetics[tuple(list(self.toPhonology[newSegment].items()))] = newSegment 
				#phonology to phonetics mapping maps tuples to IPA symbols (because dictionaries are non-hashable). Hence, VFset class allows has a to_tuple method.

# note on natural class: in LP, natural class is a set of VFsets. It makes no sense to implement it as such using an extensional definition
# Therefore, natural classes will be stored as a type of VFset. However, for natural classes we define a method match() that checks whether a given VFset matches a natural class.

class NaturalClass(VFset):
	def cardinality(self) -> int:
		size = 0
		for feature in self:
			if self[feature] != 0:
				size += 1
		return size 
	
	def match(self, vfs: VFset) -> bool: 
		#match(): checks whether there is conflict in specified features between the VFset and the natural class
		for feature in self:
			if self[feature] != 0:
				if feature not in vfs:
					return False
				if vfs[feature] != self[feature]:
					return False
		return True
	
	def singleton(self, vfs: VFset): 
		#singleton(): returns a natural class corresponding to a single segment 
		for feature in vfs:
			self[feature] = vfs[feature]
		return self

	def makeCopy(self): 
		#makeCopy(): creates a copy of itself
		nc = NaturalClass()
		for feature in self:
			nc[feature] = self[feature]
		return nc
	
	def intersection(self,other):
		#intersection: returns a Natural Class Z that is an intersection between Natural Classes X and Y
		intersect_nc = NaturalClass()
		for feature in self:
			if feature in other:
				if other[feature] == self[feature]:
					intersect_nc[feature] = self[feature]
		return intersect_nc
	
	def contradicts(self, other) -> bool:
		for feature in self:
			if feature in other:
				if other[feature] * self[feature] == -1:
					return True
		else: 
			return False
	
class VFString(list): #implements a string of VFsets
	def makeCopy(self):
		#makeCopy(): creates a copy of itself
		vfstring = VFString()
		for vfs in self:
			vfstring.append(vfs)
		return vfstring
	
	def fill(self, vfslist: list): #to be changed into __init__()
		#fill(): creates a VFstring from a list of VFsets 
		for vfs in vfslist:
			self.append(vfs)
		return self

	def previous(self, index: int) -> VFset:
		#previous(): returns the previous VFset in the VFstring. if no such, returns the word boundary
		if index == 0:
			return WORD_BOUNDARY
		else:
			return self[index-1]
	
	def next(self, index: int) -> VFset:
		#previous(): returns the next VFset in the VFstring. if no such, returns the word boundary
		if index == len(self)-1:
			return WORD_BOUNDARY
		else:
			return self[index+1]
		
	def __eq__(self, other):
		if len(other) == len(self):
			for i in range(len(self)):
				if self[i] != other[i]:
					return False
			return True
		else:
			return False
		
class Rule: #class of phonological rules
	def __init__(self, target: NaturalClass, change: VFset, unification: bool, leftTrigger: NaturalClass = NaturalClass(), rightTrigger: NaturalClass = NaturalClass()):
		self.target = target# a set of VFsets
		self.change = change  # a VF set
		self.leftTrigger = leftTrigger  # a set of VFsets
		self.rightTrigger = rightTrigger  # a set of VFsets
		self.unification = unification # type of rule

	def __eq__(self, other): #defines equality over rules
		return (self.target == other.target) and (self.change == other.change) and (self.leftTrigger == other.leftTrigger)  and (self.rightTrigger == other.rightTrigger)

	def apply(self, vfstring: VFString) -> VFString: 
		# apply(): implements simultaneous application of the rule to a VFstring. returns a VFstring
		result = vfstring.makeCopy()
		for i in range(len(vfstring)):
			if self.leftTrigger.match(vfstring.previous(i)) and self.rightTrigger.match(vfstring.next(i)) and self.target.match(vfstring[i]):
				if self.unification:
					result[i] = vfstring[i].unification(self.change)
				else:
					result[i] = vfstring[i].subtraction(self.change)
		return result

	def describe(self) -> str:
		#describe(): returns a string that describes the phonological rule
		description = {}
		description['TARGET'] = '[' + ';'.join(self.target.toStringList()) + ']'
		description['CHANGE'] = '{' + ';'.join(self.change.toStringList()) + '}'
		description['LEFT'] = '[' + ';'.join(self.leftTrigger.toStringList()) + ']'
		description['RIGHT'] = '[' + ';'.join(self.rightTrigger.toStringList()) + ']'
		if self.unification:
			description['TYPE'] = 'unification'
		else:
			description['TYPE'] = 'subtraction'
		return pprint.pformat(description)
	
	def makeCopy(self):
		#makeCopy(): returns a copy of itself
		newrule = Rule(self.target, self.change, self.unification, self.leftTrigger, self.rightTrigger)
		return newrule
	
	def more_specific(self, other) -> bool: 
		#TO DO: adapt Belth's procedure. right now, simple comparison of targets and contexts
		#the intuition: given that the initial segment-to-segment mappings are surface true, the bleeding interactions should be identified
		pass

	def contradicts(self, other) -> bool:
		for feature in self.change:
			for feature in other.change:
				if self.change[feature] * other.change[feature] == -1:
					return True
		return False
	
class Grammar:
	def __init__(self, interface: Interface, rules: list):
		#initialized a grammar with an interface and a list of phonological rules
		self.interface = interface
		self.rules = rules

	def addRule(self, rule:Rule): #not used yet, should be used in lp_plp
		#adds a rule
		self.rules.append(rule)

	def deleteRule(self, rule:Rule):
		#deletes a rule
		pass #todo

	def orderByScope(self, rules) -> list:
		if len(rules) <= 1: # can't order one rule
			return
		nodes = list(rules)
		nodes_lookup = {}
		for i in range(len(nodes)):
			nodes_lookup[i] = nodes[i]
		nodes_idx = list(range(len(nodes)))
		edges = list()
		for i in range(len(nodes)):
			for j in range(i + 1, len(nodes)):
				ri, rj = nodes[i], nodes[j]
				if ri.contradicts(rj):
					if not ri.target.contradicts(rj.target):
						if ri.leftTrigger.cardinality() + ri.rightTrigger.cardinality() > rj.leftTrigger.cardinality() + rj.rightTrigger.cardinality():
							edges.append((i, j))
						else:
							edges.append((j, i))
		G = nx.DiGraph()
		G.add_nodes_from(nodes_idx)
		G.add_edges_from(edges)
		ordered_rules = [nodes_lookup[i] for i in list(nx.topological_sort(G))]
		return ordered_rules

	def orderRules(self, rules) -> list:
		#a simplified rule ordering procedure: orders all feature deletion rules before all feature insertion rules. As it stands, is unable to account for process interactions
		subtraction = []
		unification = []
		for rule in rules:
			if not rule.unification:
				subtraction.append(rule)
			else:
				unification.append(rule)
		#subtraction rules are ordered by scope + topological sort
		#subtraction = self.orderByScope(subtraction) to appear
		#subtraction rules are ordered by scope + topological sort
		unification = self.orderByScope(unification)
		order = subtraction + unification
		return order

	def getSR(self, UR:str, rules:list) -> str: 
		#gets a surface form from an underlying form, both represented as symbols
		vfstring = VFString()
		for symbol in UR:
			vfstring.append(self.interface.toPhonology[symbol])
		vfstring2 = self.getSR_vfs(vfstring, self.orderRules(self.rules))
		result = ''
		for vfs in vfstring2:
			result += self.interface.toPhonetics[vfs.to_tuple()]
		return result
	
	def getSR_vfs(self, ur:VFString, rules) -> VFString: 
		#applies the phonological rules in the grammar to a VFstring
		vfstring = ur.makeCopy()
		for rule in rules:
			vfstring = rule.apply(vfstring)
		return vfstring


	def describe(self): #describes the list of rules
		s = 'Length of the rule list: ' + str(len(self.rules)) + ' rules\n'
		for rule in self.orderRules(self.rules):
			s += rule.describe()
			s += '\n'
		return s