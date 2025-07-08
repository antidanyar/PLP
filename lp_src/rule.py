from utils import UNKNOWN_CHAR
from utils import align_blanks, tolerance_principle
from sequence import Sequence

class Rule:
    '''
    Rule of the form A --> B / C __ D
    '''
    def __init__(self, A, B, C='*', D='*', alphabet=None):
        self.alphabet = alphabet
        if A is None and B is None and C is None and D is None:
            return
        self.A = Rule.RulePart(A, alphabet=alphabet)
        self.B = Rule.BPart(B, alphabet=alphabet)
        self.C = Rule.RulePart(C, alphabet=alphabet)
        self.D = Rule.RulePart(D, alphabet=alphabet)

    def copy(self):
        copy = Rule(A=None, B=None, C=None, D=None, alphabet=self.alphabet)
        copy.A = self.A.copy()
        copy.B = self.B.copy()
        copy.C = self.C.copy()
        copy.D = self.D.copy()
        return copy

    def CAD(self):
            CAD = []
            if not self.C.wildcard():
                CAD += self.C.seq
            if not self.A.empty():
                CAD += self.A.seq
            if not self.D.wildcard():
                CAD += self.D.seq
            return Sequence(CAD, self.alphabet)

    def update_C(self, seq):
        if type(seq) is list:
            seq = Sequence(seq, self.alphabet)
        self.C = Rule.RulePart(seq, self.alphabet)

    def update_A(self, seq):
        if type(seq) is list:
            seq = Sequence(seq, self.alphabet)
        self.A = Rule.RulePart(seq, self.alphabet)

    def update_D(self, seq):
        if type(seq) is list:
            seq = Sequence(seq, self.alphabet)
        self.D = Rule.RulePart(seq, self.alphabet)

    def to_natural_classes(self, segments=True):
        if not self.C.wildcard():
            self.C.seq.to_natural_classes(segments=segments)
        if not self.A.empty():
            self.A.seq.to_natural_classes(segments=segments)
        if not self.D.wildcard():
            self.D.seq.to_natural_classes(segments=segments)

    def A_index(self):
        if self.A.empty():
            return None
        len_C = len(self.C)
        if len_C == 0:
            return 0
        return len_C

    def update_at(self, idx, seg):
        len_A = len(self.A)
        len_C = len(self.C)
        len_D = len(self.D)
        
        C_start = 0 if len_C > 0 else -1
        C_end = len_C - 1 if len_C > 0 else -1
        A_start = C_end + 1
        A_end = A_start + len_A - 1
        D_start = A_end + 1
        D_end = D_start + len_D - 1

        if C_start <= idx <= C_end:
            self.C.seq[idx] = seg
            return True
        if A_start <= idx <= A_end:
            self.A.seq[idx - len_C] = seg
            return True
        if D_start <= idx <= D_end:
            self.D.seq[idx - len_C - len_A] = seg
            return True
        return False

    class RulePart:
        def __init__(self, seq, alphabet=None):
            self.alphabet = alphabet
            self.is_wildcard = False
            if seq == '*':
                self.is_wildcard = True
            elif type(seq) is Sequence:
                self.seq = seq
            else:
                self.seq = Sequence(seq, alphabet=alphabet)

        def copy(self):
            return Rule.RulePart(self.seq.copy() if not self.is_wildcard else '*', self.alphabet)

        def match(self, seq):
            if self.is_wildcard:
                return seq == ''
            return self.seq.matches(seq)

        def empty(self):
            return not self.is_wildcard and self.seq == ''

        def wildcard(self):
            return self.is_wildcard

        def wordend(self):
            return not self.is_wildcard and self.seq == '#'

        def __len__(self):
            if self.is_wildcard:
                return 0
            return len(self.seq) - self.seq.seq.count('*')

        def __str__(self):
            if self.is_wildcard:
                return ''
            return self.seq.__str__().replace('*', '')

        def __eq__(self, other):
            if self.wildcard() != other.wildcard():
                return False
            if self.wildcard() and other.wildcard():
                return True
            return self.seq == other.seq

        def __neq__(self, other):
            return not self.__eq__(other)

    class BPart:
        def __init__(self, seq, alphabet):
            self.seq = seq
            self.alphabet = alphabet

        def copy(self):
            return Rule.BPart(self.seq, self.alphabet)

        def apply(self, seq):
            if self.feature_change():
                assert(len(seq) == 1)
                seg = seq[0]
                val = self.seq[0]
                feat = self.seq[1:]
                new_seg = self.alphabet.set_feats(seg, [feat], [val])
                return new_seg if new_seg else UNKNOWN_CHAR
            return self.seq

        def empty(self):
            return self.seq == ''

        def feature_change(self):
            return not self.empty() and self.seq[0] in {'+', '-'}

        def __len__(self):
            return len(self.seq)
    
        def __str__(self):
            return f'{self.seq}' if not self.feature_change() else f'[{self.seq}]'

        def __eq__(self, other):
            return self.seq == other.seq

        def __neq__(self, other):
            return not self.__eq__(other)

    def more_specific(self, other, pairs):
        '''
        :return: True if this rule needs to apply before the other
        '''
        pairs = set(self.applications(pairs)).intersection(other.applications(pairs))

        if len(pairs) == 0:
            return False

        return self.accuracy_after_other(other, pairs) < other.accuracy_after_other(self, pairs)

    def shift_excess_D_into_AB(self):
        excess_D = self.D.seq.seq[:-1]
        self.D.seq = Sequence(self.D.seq.seq[-1])
        self.A.seq = Sequence(self.A.seq.seq + excess_D)
        self.B.seq = Sequence(f'{self.B.seq}' + ''.join(excess_D))

    def merge(self, other, pairs):
        '''
        Merge two :other: rule with :self: rule, if possible.

        :return: True if the rules are mergeable, False otherwise.
        '''
        n, _ = self.get_n_c(pairs)
        no, _ = other.get_n_c(pairs)
        n_both = n + no
        # the rules must do the same thing to the target
        if self.B.seq != other.B.seq:
            return False
        # if the left and right contexts are identical, then we can just go ahead and merge straight away
        if self.A != other.A and len(self.A) == 1 and len(other.A) == 1 and self.C == other.C and self.D == other.D:
            self.A.seq.merge(other.A.seq)
            return True
        elif len(self.C) <= 1 and len(self.D) <= 1 and len(other.C) <= 1 and len(other.D) <= 1:
            nr = self.copy()
            if not nr.C.wildcard() and not other.C.wildcard():
                nr.C.seq.merge(other.C.seq)
            nr.A.seq.merge(other.A.seq)
            if not nr.D.wildcard() and not other.D.wildcard():
                nr.D.seq.merge(other.D.seq)
            n, c = nr.get_n_c(pairs)
            if n >= n_both and tolerance_principle(n, c):
                if not self.C.wildcard() and not other.C.wildcard():
                    self.C.seq.merge(other.C.seq)
                self.A.seq.merge(other.A.seq)
                if not self.D.wildcard() and not other.D.wildcard():
                    self.D.seq.merge(other.D.seq)
                return True
        return False

    def feature_changeify(self):
        if len(self.A) == 1 and len(self.B) == 1: # check if just a feature change
            A_feats = set(filter(lambda feat: feat[0] == '+', self.alphabet.feat_vals(f'{self.A}')))
            B_feats = set(filter(lambda feat: feat[0] == '+', self.alphabet.feat_vals(f'{self.B}')))
            added = B_feats.difference(A_feats)
            removed = A_feats.difference(B_feats)
            if len(added) + len(removed) == 1:
                if len(added) == 1:
                    B = f'+{list(added)[0].replace("+", "")}'
                else:
                    B = f'-{list(removed)[0].replace("+", "")}'
                self.B.seq = B
        return self

    def stringify(self):
        return f'{self.A} --> {self.B} / {self.C} __ {self.D}'

    def __str__(self):
        return self.stringify()

    def __repr__(self):
        return self.__str__()
    
    def __lt__(self, other):
        return self.__str__() < other.__str__()

    def equals_CAD(self, window):
        len_C = len(self.C)
        len_A = len(self.A)
        len_D = len(self.D)

        window_C = window[0:len_C]
        window_A = window[len_C:len_C+len_A]
        window_D = window[len_C+len_A:len_C+len_A+len_D]

        return self.C.match(window_C) and self.A.match(window_A) and self.D.match(window_D)
    
    def get_B(self, CAD):
        if self.B.feature_change():
            A_start = len(self.C)
            return self.B.apply(CAD[A_start])

        return f'{self.B}'

    def __len__(self):
        return len(self.C) + len(self.A) + len(self.D)

    def apply(self, s):
        '''
        Apply the rule to the string :s:
        '''
        len_C = len(self.C) if not self.C.wildcard() else 0
        A_start, A_end = len_C, len_C + len(self.A)
        k = len(self)
        out_tape = [''] * len(s)
        window = '' if type(s) is str else Sequence('', self.alphabet)
        if len(self.C) > 0 and (self.C.seq[0] == '#' or self.C.seq[0] == {'#'}):
            window = Sequence('#', self.alphabet)
        for i in range(len(s) + 1): # +1 for word end
            if i < len(s):
                window += s[i]
                out_tape[i] = s[i] # pencil in identity
            else:
                window += '#'
            if len(window) > k:
                window = window[1:]
            if self.equals_CAD(window):
                window_start_idx = i - k + 1
                if self.A.empty(): # epenthesis
                    C_index = window_start_idx + len_C - 1
                    out_tape[C_index] = Sequence(f'{out_tape[C_index]}{self.B}', self.alphabet)
                else:
                    if self.B.feature_change(): # change the feature
                        out_tape[window_start_idx + A_start] = self.B.apply(s[window_start_idx + A_start])
                    else:
                        for b_i, a_i in enumerate(range(A_start, A_end)): # for each character in A
                            out_tape[window_start_idx + a_i] = Sequence(self.B.seq[b_i], self.alphabet) if len(self.B) > 0 else '' # overwrite with the next character in B
                            rest = len(self.B) - b_i # compute what is left of B
                            if a_i == A_end - 1 and b_i < len(self.B) - 1:
                                out_tape[window_start_idx + a_i] += self.B.seq[b_i + 1:rest]
        
        out_seq = Sequence('', self.alphabet)
        for seq in out_tape:
            if seq != '':
                out_seq += seq

        return out_seq

    def __call__(self, s):
        return self.apply(s)

    def applies(self, uf, sf):
        '''
        Comptes the number of times :self: applies to :uf: and how many of those are correct predictions w.r.t. :sf:
        '''
        n, c = self.matches(uf, sf)
        return len(n), len(c)

    def matches(self, uf, sf):
        '''
        Computes the matches of :self: on :uf: w.r.t. :sf:
        '''
        n, c = list(), list()

        window = '' if type(uf) is str else Sequence('', self.alphabet)
        k = len(self)
        for i in range(len(uf) + 1): # +1 for word end
            if i < len(uf):
                window += uf[i]
                window_C = window[0:len(self.C)]
            else:
                window += '#'
            if len(window) > k: # update window
                window = window[1:]

            if self.equals_CAD(window):
                n.append(window)
                window_start_idx = i - k + 1
                if self.A.empty(): # epenthesis
                    sf_B = sf[window_start_idx+len(self.C):window_start_idx+len(self.C)+len(self.B)]
                else:
                    sf_B = sf[window_start_idx+len(self.C):window_start_idx+len(self.C)+len(self.A)]
                if sf_B == 'λ':
                    sf_B = ''
                pred_B = self.get_B(window)
                if pred_B == sf_B:
                    c.append(window)
        return n, c

    def get_n_c(self, pairs, num=True):
        n, c = (0, 0) if num else (list(), list())
        for uf, sf in pairs:
            if len(sf) < len(uf): # deletion
                sf = align_blanks(f'{sf}', f'{uf}', return_ties=True)
                if type(sf) is str:
                    sf = Sequence(sf)
                else:
                    sf = list(Sequence(_sf) for _sf in sf)
                    def _acc(__n, __c):
                        return __c / __n if __n > 0 else 0
                    sf = sorted(sf, reverse=True, key=lambda _sf: _acc(*self.applies(uf, _sf)))[0]

            if num:
                _n, _c = self.applies(uf, sf)
                n += _n
                c += _c
            else:
                _n, _c = self.matches(uf, sf)
                n.extend(_n)
                c.extend(_c)

        return n, c

    def accuracy(self, pairs):
        N, c = self.get_n_c(pairs)
        return c / N if N > 0 else 0

    def accuracy_after_other(self, other, pairs):
        c = 0
        for uf, sf in pairs:
            other_pred = other.apply(uf)
            if UNKNOWN_CHAR not in other_pred and self.apply(other_pred) == sf:
                c += 1
        return c / len(pairs)

    def applications(self, pairs):
        apps = list()
        for uf, sf in pairs:
            if self.apply(uf) != uf:
                apps.append((uf, sf))
        return apps

    def __eq__(self, other):
        if type(other) is str:
            return self.stringify() == other
        return self.stringify() == other.stringify()

    def __neq__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.stringify())