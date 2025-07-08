from collections import defaultdict
from nltk import ngrams
from utils import EMPTY_STRING
from utils import tolerance_principle, align_blanks, UNKNOWN_CHAR

from rule import Rule
from alphabet import Alphabet
from sequence import Sequence
from rule_builder import RuleBuilder
from nat_class_gen import NatClassGen
from discrepancies import Discrepancies
from plp_grammar import PLPgrammar

class PLP:
    def __init__(self,
                 threshold=tolerance_principle, 
                 ipa_file='../data/ipa.txt',
                 nas_vowels=False, 
                 add_segs=False,
                 n_grams_lens=[1, 2, 3], 
                 skip_gen_A=False,
                 verbose=True):
        self.threshold = threshold
        self.vocab = set()
        self.verbose = verbose
        self.alphabet = Alphabet(ipa_file=ipa_file, nas_vowels=nas_vowels, add_segs=add_segs)
        self.grammar = PLPgrammar()
        self.n_gram_lens = n_grams_lens
        self.n_grams = dict((k, defaultdict(int)) for k in self.n_gram_lens)
        self.skip_gen_A = skip_gen_A

        self.rule_builders = {EMPTY_STRING: self.new_rule_builder(EMPTY_STRING)}
        self.discrepancies = Discrepancies()

    def new_rule_builder(self, target):
        '''
        :target: the target around which a rule will be built.
        '''
        return RuleBuilder(target, alphabet=self.alphabet, threshold=self.threshold)

    def align(self, uf, sf):
        if len(sf) == len(uf): # no alignment needed
            return uf, sf
        if len(sf) < len(uf): # epenthesis
            if type(sf) is str:
                return uf, align_blanks(sf, uf)
            else:
                return uf, Sequence(align_blanks(f'{sf}', f'{uf}'))
        elif len(sf) > len(uf): # deletion
            if type(uf) is str:
                return align_blanks(uf, sf), sf
            else:
                return Sequence(align_blanks(f'{uf}'.replace('\u0303', ''), f'{sf}'.replace('\u0303', ''))), sf

    def produce(self, uf):
        self.alphabet.add_segments_from_str(uf)
        if type(uf) is str:
            uf = Sequence(uf, alphabet=self.alphabet)
        return self.grammar.apply(uf)

    def __call__(self, uf):
        return self.produce(uf)

    def induce_natural_classes(self):
        '''
        Induce natural classes over the rules.
        '''
        g = NatClassGen(self.alphabet, self.skip_gen_A)
        for r_idx in range(len(self.grammar)):
            r = self.grammar[r_idx]
            k = len(r)
            # compute the n-grams needed to compute the new rule's accuracy
            _ngrams = defaultdict(int)
            for ngram, f in self.n_grams[k].items():
                # apply all the rules ranked above it in the grammar
                for _r in self.grammar[:r_idx]:
                    ngram = _r.apply(ngram)
                if len(ngram) == k:
                    _ngrams[ngram] += f
            new_r = g.induce_nat_classes(r, list(_ngrams.items()))
            self.grammar[r_idx] = new_r

    def train(self, pairs):
        discrepancies = set()
        for pair in pairs:
            _, _, aligned_uf, aligned_sf = self.add_incremental(pair)
            if aligned_uf != aligned_sf:
                for i in range(len(aligned_uf)):
                    if aligned_uf[i] != aligned_sf[i]: # discrepancy
                        discrepancies.add((aligned_uf[i], aligned_sf[i]))

        for seg, b in sorted(discrepancies): # account for each discrepancy
            r = self.rule_builders[seg].build(b=b)
            self.discrepancies[(seg, b)] = r

        self.update_rules() # update the rules
        return self

    def add_incremental(self, pair):
        '''
        Add a (UR, SR) pair.

        :return: the orig pair (:uf: and :sf:) and the aligned pair (:aligned_uf:, :aligned_sf:)
        '''
        uf, sf = pair
        self.alphabet.add_segments_from_str(uf) # add segments to alphabet
        self.alphabet.add_segments_from_str(sf)
        for k in self.n_gram_lens: # cache n-grams
            for ngram in ngrams(f'{uf}#', k):
                self.n_grams[k][Sequence(list(ngram), self.alphabet)] += 1
        uf, sf = Sequence(uf, self.alphabet), Sequence(sf, self.alphabet) # turn the strings into sequences
        self.vocab.add((uf, sf)) # add the pair to the vocab

        # make rule builders for each segment. 
        for i in range(len(uf)):
            seg = uf[i]
            if seg not in self.rule_builders:
                self.rule_builders[seg] = self.new_rule_builder(seg)

        aligned_uf, aligned_sf = self.align(uf, sf)
        idx = -1
        for i in range(len(aligned_uf)):
            seg = aligned_uf[i]
            if seg != EMPTY_STRING:
                idx += 1
                self.rule_builders[seg].add_instance(uf, i, b=aligned_sf[i], sf=sf)
                if i + 1 < len(aligned_uf) and aligned_uf[i + 1] == EMPTY_STRING:
                    pass
                else:
                    self.rule_builders[EMPTY_STRING].add_instance(uf, i, b=EMPTY_STRING, sf=sf, around_empty=True)
            else:
                self.rule_builders[EMPTY_STRING].add_instance(uf, idx, b=aligned_sf[i], sf=sf, around_empty=True)
        
        return uf, sf, aligned_uf, aligned_sf

    def train_incremental(self, pair):
        uf, sf, aligned_uf, aligned_sf = self.add_incremental(pair)
        rules_changed = False
        '''
        Find all overapplications
        '''
        for seg_b, rule in self.discrepancies.items():
            if type(rule) is Rule:
                n, c = rule.applies(uf, sf)
            else:
                n, c = 0, 0
                for r in rule:
                    _n, _c = r.applies(uf, sf)
                    n += _n
                    c += _c
            if n != c: # overapplication
                seg, b = seg_b
                r = self.rule_builders[seg].build(b=b)
                self.discrepancies[(seg, b)] = r
                rules_changed = True

        '''
        Find all underapplications
        '''
        if aligned_uf != aligned_sf:
            for i in range(len(aligned_uf)):
                if aligned_uf[i] != aligned_sf[i]: # discrepancy
                    seg, b = aligned_uf[i], aligned_sf[i]
                    rule = self.discrepancies[(seg, b)] if (seg, b) in self.discrepancies else None
                    if not rule or (rule.apply(aligned_uf) == aligned_uf if type(rule) is Rule else all(r.apply(aligned_uf) == _uf for r in rule)): # underapplication
                        r = self.rule_builders[seg].build(b=b)
                        self.discrepancies[(seg, b)] = r
                        rules_changed = True

        if rules_changed:
            self.update_rules()
        elif UNKNOWN_CHAR in self.produce(uf): # if a natural class over-applied, make sure the rule is still tolerable
            self.update_rules()        

    def merge_rules(self):
        '''
        Tries to combine rules that make the same change.
        '''
        change = True
        while change: # while there is a change to some rule
            change = False
            num_rules = len(self.grammar)
            pool = sorted(self.grammar.rules)
            for i in range(num_rules):
                for j in range(i + 1, num_rules):
                    r1 = pool[i]
                    r2 = pool[j]
                    if r1 not in self.grammar or r2 not in self.grammar:
                        continue
                    if r1.merge(r2, self.vocab):
                        self.grammar.remove(r2)
                        change = True

    def update_rules(self):
        '''
        Call after adding any rule.
        '''
        rules = self.discrepancies.get_rules() # get the rules accounting for all the discrepancies
        self.grammar.set_rules(list(r.copy().feature_changeify() for r in rules)) # set the grammar's rules
        self.merge_rules() # combine the rules
        self.grammar.order_rules_by_scope(self.vocab) # assign some non-arbitrary initial ordering (by scope); actual ordering is after natural classes are induced
        self.induce_natural_classes() # induce nat classes
        self.grammar.order_rules(self.vocab) # order the rules

    def accuracy(self, test, return_errors=False):
        '''
        Compute accuracy of model on :test: (ur, sr) pairs.

        :test: the (ur, sr) pairs to test over.
        :return_errors: if True, returns a list of printable errors.
        '''
        errors = list()
        t, c, = 0, 0
        is_path = type(test) is str
        if is_path:
            iterable = open(test, 'r')
        else:
            iterable = test
        for line in iterable:
            if is_path:
                uf, sf = line.strip().split('\t')
            else:
                uf, sf = line
            pred = self.produce(uf)
            if sf == pred:
                c += 1
            elif return_errors:
                errors.append(f'UF: {uf}    Pred: {pred}    SF: {sf}')
            t += 1
        if return_errors:
            return c / t if t > 0 else 0, errors
        return c / t if t > 0 else 0

    def __str__(self):
        return self.grammar.__str__()

    def __repr__(self):
        return self.__str__()