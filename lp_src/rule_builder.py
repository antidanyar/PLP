from segment import Segment
from sequence import Sequence
from rule import Rule
from utils import EMPTY_STRING

import numpy as np
import networkx as nx

class RuleBuilder():
    def __init__(self, target, alphabet, threshold):
        self.target = target
        self.alphabet = alphabet
        self.threshold = threshold

        self.instances = list()
        self.pairs = set()

    class Context:
        def __init__(self, lc, rc, b):
            self.lc = lc
            self.rc = rc
            self.b = b

        def __str__(self):
            return f'{self.lc}_{self.rc} ({self.b})'

        def __repr__(self):
            return self.__str__()

        def matches(self, window):
            middle = window.index({'_'})
            lc = window[:middle]
            rc = window[middle + 1:]

            for i in range(len(lc)):
                if self.lc[-1 - i] not in lc[-1 - i]:
                    return False
            for i in range(len(rc)):
                if self.rc[i] not in rc[i]:
                    return False
            return True

    class Node:
        def __init__(self, pos, neg, condition):
            self.condition = condition
            self.pos = pos
            self.neg = neg
            self.pos_child = None

        def __str__(self):
            if self.condition == '*':
                return self.condition
            else:
                return f'{self.condition[0]} = [{"|".join(sorted(self.condition[1]))}]'

    def get_left_and_right_context(self, uf, i, around_emtpy):
        if type(uf) is str:
            lc, rc = '#', ''
        else:
            lc, rc = Sequence('#'), Sequence('')
        for idx in range(len(uf)):
            if idx < i:
                lc += uf[idx]
            elif idx > i:
                rc += uf[idx]
            elif idx == i and around_emtpy:
                lc += uf[idx]
        rc += '#'
        return lc, rc

    def add_instance(self, uf, i, b, sf, around_empty=False):
        lc, rc = self.get_left_and_right_context(uf, i, around_empty)
        self.instances.append(RuleBuilder.Context(lc=lc, rc=rc, b=b))
        self.pairs.add((uf, sf))

    def pad_to_len(self, s, target_len, pad_left):
        padded = list()

        if not pad_left:
            for seg in s:
                padded.append(seg)
        else:
            target_len -= len(s)

        while len(padded) < target_len:
            padded.append('')

        if pad_left:
            for seg in s:
                padded.append(seg)

        return padded

    def size_k_windows(self, mat, k, middle):
        windows = list()

        window_start = 0
        # move first window start to start of shortest left context
        while '' in mat[:,window_start]:
            window_start += 1
        window_end = window_start + k

        while window_end <= mat.shape[1]:
            window = mat[:,window_start:window_end]
            window_start += 1
            window_end = window_start + k

            if '_' not in window:
                continue
            if '' in window: # if we've reached the end of the shortest right context
                break

            windows.append([0] * k)
            for col in range(window.shape[1]):
                windows[-1][col] = set(window[:,col])
            if window_end >= mat.shape[1]:
                break

        return windows

    def build_rule_from_window(self, window, b):
        if window is None:
            C = '*'
            D = '*'
        else:
            C = list()
            D = list()
            left = True
            for seg in window:
                if len(seg) == 1:
                    seg = list(seg)[0]
                if seg == '_':
                    left = False
                    continue
                if type(seg) is str:
                    seg = Segment(seg)
                if left:
                    C.append(seg)
                else:
                    D.append(seg)

            if len(C) == 0:
                C = '*'
            if len(D) == 0:
                D = '*'

        r = Rule(A=self.target if self.target != EMPTY_STRING else '', B=b if b != EMPTY_STRING else '', C=C, D=D, alphabet=self.alphabet)
        return r

    def build(self, b):
        '''
        Builds a rule to map a --> b, using left and right contexts as features.

        :b: the value that :self.target: should be mapped to.

        :return: the built rule
        '''

        # grab the instances relevant to this particular self.target --> b
        pos = list(filter(lambda it: it.b == b, self.instances))

        zero_rule = self.build_rule_from_window(None, b)
        n, c = zero_rule.get_n_c(self.pairs)

        if self.threshold(n=n, c=c): # see if context-free rule is good enough
            return zero_rule
        else:
            max_lc = max(len(it.lc) for it in self.instances)
            max_rc = max(len(it.rc) for it in self.instances)

            num_cols = max_lc + max_rc + 1
            middle = max_lc
            pos_mat = np.zeros((len(pos), num_cols), dtype=object)

            for i, context in enumerate(pos):
                padded_lc = self.pad_to_len(context.lc, target_len=max_lc, pad_left=True)
                padded_rc = self.pad_to_len(context.rc, target_len=max_rc, pad_left=False)
                pos_mat[i] = padded_lc + ['_'] + padded_rc       

            return self.build_from_contexts(b, pos_mat, middle)

    def build_from_contexts(self, b, pos_mat, middle):
        for k in range(2, pos_mat.shape[1]):
            pos_windows = self.size_k_windows(pos_mat, k=k, middle=middle)

            if len(pos_windows) == 0:
                break

            window_scores = list()
            for window in pos_windows:
                r = self.build_rule_from_window(window, b)
                n, c = r.get_n_c(self.pairs)
                score = - c / n if n > 0 else 0 # since n is the same for all windows, the more correct predictions, the better the window
                # tie-breakers
                score -= 0.1 * window.count({'#'}) # prefer word boundaries
                score -= 0.01 * window.count({'.'}) # prefer syllable boundaries
                num_left = window.index({'_'})
                score -= 0.001 * (num_left / (len(window) - 1)) # prefer left contexts
                window_scores.append((window, score))
            best_window = sorted(window_scores, key=lambda it: it[-1])[0][0]

            r = self.build_rule_from_window(best_window, b)
            n, c = r.get_n_c(self.pairs)
            if self.threshold(n=n, c=c):
                return self.build_rule_from_window(best_window, b)
            elif k > 2 and (k - 1) % 2 == 0: # test for mutually exclusive contexts (e.g., intervocalic and post-nasl voicing)
                edges = list()
                offset = int((k - 1) / 2)
                for row in pos_mat:
                    l = ''.join(list(f'{seg}' for seg in row[middle - offset:middle]))
                    r = ''.join(list(f'{seg}' for seg in row[middle + 1:middle + 1 + offset]))
                    edges.append((l, r))
                G = nx.Graph(edges)
                ccs = list(nx.connected_components(G))
                if len(ccs) > 1:
                    res = self.mutually_exclusive(ccs, offset, b, pos_mat, middle)
                    if res:
                        return res

        return self.build_lexicalized(b, pos_mat, middle)

    def mutually_exclusive(self, ccs, offset, b, pos_mat, middle):
        def cc_id(ccs, seg):
            for i, cc in enumerate(ccs):
                if seg in cc:
                    return i
        if len(ccs) > 1:
            ecs = list(list() for _ in range(len(ccs)))
            for row in pos_mat:
                l = ''.join(list(f'{seg}' for seg in row[middle - offset:middle]))
                r = ''.join(list(f'{seg}' for seg in row[middle + 1:middle + 1 + offset]))
                assert(cc_id(ccs, l) == cc_id(ccs, r))
                ecs[cc_id(ccs, l)].append(row)
            ecs = list(np.asarray(ec) for ec in ecs)
            rules = list()
            for ec in ecs:
                r = self.build_from_contexts(b, ec, middle)
                if type(r) is Rule:
                    rules.append(r)
                else:
                    rules.extend(r)
            return rules


    def build_lexicalized(self, b, pos_mat, middle):
        print(f'WARNING: Building lexicalized rules for {self.target} --> {b}.')
        rules = list()
        for row in pos_mat:
            r = self.build_from_contexts(b, row.reshape(1, pos_mat.shape[1]), middle)
            if r not in rules:
                rules.append(r)

        return rules
