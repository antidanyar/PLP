from utils import load, tolerance_principle, sufficiency_principle
from plp import PLP
import LPgrammar

class LP_PLP:
	def __init__(self, pairs, mappings, interface:LPgrammar.Interface):
		#initialized the learner with UR-SR pairs; the mappings that PLP provides and the phonetics-phonology interface
		self.pairs = pairs
		self.interface = interface
		self.features = [k for k in list(self.interface.toPhonology.items())[1][1]]
		print(self.features)
		self.lp_pairs = self.create_vfspairs(self.pairs, self.interface)
		self.mappings = mappings
		self.rules = []

	def create_vfspairs(self,pairs, interface: LPgrammar.Interface):
		#transforms symbolic UR-SR pairs into VFset UR-SR pairs
		vfs_pairs = []
		for pair in pairs:
			input, output = pair
			input_vfs = [interface.toPhonology[c].makeCopy() for c in input]
			output_vfs = [interface.toPhonology[c].makeCopy() for c in output]
			input_vfstring = LPgrammar.VFString()
			input_vfstring.fill(input_vfs)
			output_vfstring = LPgrammar.VFString()
			output_vfstring.fill(output_vfs)
			vfs_pairs.append((input_vfstring, output_vfstring))
		return vfs_pairs

	def split_mappings(self, mappings): 
		#split mappings from Belth's disjunctive representation to single rules
		single_mappings = [] #list of 4-tuples suffices
		for mapping in mappings:
			rule = mappings[mapping]

			#extract information about the rule
			input = str(rule.A)
			output = str(rule.B)
			left_context = rule.C
			right_context = rule.D
			left_triggers = []
			right_triggers = []

			#no treatment of rules where |C|>1 or |D|>1
			if len(left_context) + len(right_context)>1:
				raise Exception("No handling of k-window generalizations is available if k>2")
	
			#encoding the possible triggering segments on the left
			if not left_context.is_wildcard:
				for seg in left_context.seq:
					if type(seg) is set:
						for c in seg:
							left_triggers.append(str(c))
					else:
						left_triggers.append(str(seg))
		
			#encoding the possible triggering segments on the right
			if not right_context.is_wildcard:
				for seg in right_context.seq:
					if type(seg) is set:
						for c in seg:
							right_triggers.append(str(c))
					else:
						right_triggers.append(str(seg))

			#if len(left_triggers) > 0 and len(right_triggers) > 0:
			#	raise Exception("No handling of two-sided rules is available")
	
			#get the list of primitive mappings of the form segment1 -> segment2/(segment3)__(segment4)
			if len(left_triggers) > 0:
				for left_trigger in left_triggers:
					i = 0
					for right_trigger in right_triggers:
						single_mappings.append((input, output, left_trigger, right_trigger))
						i+=1
					if i == 0:
						single_mappings.append((input, output, left_trigger, "*"))
			else:
				i = 0
				for right_trigger in right_triggers:
					single_mappings.append((input, output, "*", right_trigger))
					i+=1
				if i == 0:
					single_mappings.append((input, output, "*", "*"))

		return single_mappings
		
	def mapping_to_lp(self, single_mapping):
		#maps a single mapping (a 4-tuple) to an LP style rule
		input, output, left, right = single_mapping

		#transforms input and output into VFsets
		input_vfs = self.interface.toPhonology[input].makeCopy()
		output_vfs = self.interface.toPhonology[output].makeCopy()

		#transforms input VFset into a natural class
		input_NC = LPgrammar.NaturalClass() #get target, left context, and right context NCs
		input_NC.singleton(input_vfs)
		
		#transforms left and right segments into natural class
		left_nc = LPgrammar.NaturalClass()
		right_nc = LPgrammar.NaturalClass() 
		if left != "*":
			left_vfs = self.interface.toPhonology[left].makeCopy()
			left_nc.singleton(left_vfs) 
		if right != "*":
			right_vfs = self.interface.toPhonology[right].makeCopy()
			right_nc.singleton(right_vfs)

		subtract_change = input_vfs.to_subtract(output_vfs).makeCopy() #structural change for the feature deletion rule
		subtracted = input_vfs.subtraction(subtract_change).makeCopy() #equal to input_vfs if subtract change is empty
		subtracted_nc = LPgrammar.NaturalClass()
		subtracted_nc.singleton(subtracted)
		unification_change = subtracted.to_unify(output_vfs).makeCopy() # structural change for the feature insertion rule

		subtraction_rule = LPgrammar.Rule(input_NC, subtract_change, unification=False, leftTrigger=left_nc, rightTrigger=right_nc)
		unification_rule = LPgrammar.Rule(subtracted_nc, unification_change, unification=True, leftTrigger=left_nc, rightTrigger=right_nc)

		if 'voi' in subtraction_rule.rightTrigger and subtraction_rule.rightTrigger['voi'] == 0:
			print(subtraction_rule.describe())
			print(single_mapping)
			
		return subtraction_rule, unification_rule
	
	def get_LPrules(self, mappings):
		#creates a list of Logical Phonology rules extracted from PLP mappings
		single_mappings = self.split_mappings(mappings)
		single_rules = []
		for mapping in single_mappings:
			subtraction_rule, unification_rule = self.mapping_to_lp(mapping)
			if not subtraction_rule.change.is_empty():
				single_rules.append(subtraction_rule)
			if not unification_rule.change.is_empty():
				single_rules.append(unification_rule)
		return single_rules
	
	def summarize_by_change(self, single_rules):
		#summarizes rules by change
		rules_by_change = {}
		for rule in single_rules:
			change = rule.change.to_tuple()
			if (change, rule.unification) in rules_by_change:
				rules_by_change[(change, rule.unification)].append(rule)
			else:
				rules_by_change[(change, rule.unification)] = [rule]
		return rules_by_change
	
	def unify(self, rule1: LPgrammar.Rule, rule2: LPgrammar.Rule):
		#creates a new rule by intersecting the given rules' contexts and targets
		new_target = rule1.target.intersection(rule2.target).makeCopy()
		new_leftTrigger = rule1.leftTrigger.intersection(rule2.leftTrigger).makeCopy()
		new_rightTrigger = rule1.rightTrigger.intersection(rule2.rightTrigger).makeCopy()
		new_rule = LPgrammar.Rule(new_target, rule1.change, rule1.unification, new_leftTrigger, new_rightTrigger)
		return new_rule
	
	def evaluate(self, new_ruleset, lp_pairs):
		#evaluates a new ruleset
		grammar = LPgrammar.Grammar(self.interface, list(new_ruleset))
		urs = [pair[0] for pair in lp_pairs]
		srs = [pair[1] for pair in lp_pairs]
		predicted_srs = [grammar.getSR_vfs(ur, grammar.orderRules(new_ruleset)) for ur in urs]
		#print(predicted_srs[0])
		n = len(srs)
		e = 0
		for idx in range(len(srs)):
			if srs[idx] != predicted_srs[idx]:
				e += 1
		return sufficiency_principle(n, n-e)

	def unify_by_change(self, rules, rule_set):
		#attempts unification of the rules that incur the same change
		result_rulest = rule_set.copy()
		not_unified = rules.copy()
		#print(self.evaluate(result_rulest, self.lp_pairs))
		while len(not_unified) > 1:
			current_rule = not_unified[0]
			i = 1
			outliers = []
			while i < len(not_unified):
				unified_rule = self.unify(current_rule, not_unified[i])
				new_ruleset = result_rulest.copy()
				new_ruleset.remove(current_rule)
				new_ruleset.remove(not_unified[i])
				new_ruleset.append(unified_rule)
				if self.evaluate(new_ruleset, self.lp_pairs):
					result_rulest = new_ruleset.copy()
					current_rule = unified_rule.makeCopy()
				else:
					outliers.append(not_unified[i])
				i += 1
			not_unified = outliers.copy()
		return result_rulest

	def unify_by_change2(self, rules, rule_set): #deprecated
		result_rulest = rule_set.copy()
		for rule1 in rules:
			for rule2 in rules:
				if rule1 in result_rulest and rule2 in result_rulest and rule1 != rule2:
					unified_rule = self.unify(rule1, rule2)
					if unified_rule not in result_rulest:
						new_ruleset = result_rulest.copy()
						new_ruleset.remove(rule1)
						new_ruleset.remove(rule2)
						new_ruleset.append(unified_rule)
						if self.evaluate(new_ruleset, self.lp_pairs):
							result_rulest = new_ruleset.copy()
						else:
							print("no unification!")
		return result_rulest

	def induce_nat_classes(self, summarized_rules: list, set_rules):
		result_rules = set_rules.copy()
		#print(self.evaluate(set_rules, self.lp_pairs)
		subtraction_rules = [pair for pair in summarized_rules if not pair[1]]
		unification_rules = [pair for pair in summarized_rules if pair[1]]
		for change in unification_rules:
			result_rules = self.unify_by_change(summarized_rules[change], result_rules)
		for change in subtraction_rules:
			result_rules = self.unify_by_change(summarized_rules[change], result_rules)
		return result_rules
	
	def get_new_rules(self, old, new):
		newrules = []
		for rule in new:
			if rule not in old:
				newrules.append(rule)
		return newrules
	
	def train(self):
		single_rules = self.get_LPrules(self.mappings)
		single_ruleset = single_rules.copy()
		summarized_ruleset = self.summarize_by_change(single_rules)
		#print("summarized ruleset", len(single_ruleset), sep=" ")
		#for change in summarized_ruleset:
		#	for rule in summarized_ruleset[change]:
		#		pass
		#		print(rule.describe())
		result_rules = list(self.induce_nat_classes(summarized_ruleset, single_ruleset))
		#print("after nat.class induction:", len(result_rules), sep=" ")
		#for rule in result_rules:
		#	pass
		#	print(rule.describe())
		grammar = LPgrammar.Grammar(self.interface, result_rules)
		return grammar
			
			
