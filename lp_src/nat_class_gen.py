from collections import defaultdict

from sequence import Sequence
from natural_class import NaturalClass
from utils import tolerance_principle, epsilon

class NatClassGen:
    def __init__(self, alphabet, skip_gen_A):
        self.alphabet = alphabet
        self.skip_gen_A = skip_gen_A

    def induce_nat_classes(self, r, ngrams):
        target_index = r.A_index()
        _seq = list()
        feat_space = set()
        for idx, seg in enumerate(r.CAD()):
            if seg in {'#', '.'} or '#' in seg or '.' in seg: # we cannot induce a natural class over word or syllable boundaries
                _seq.append(seg)
            elif self.skip_gen_A and idx == target_index: # if skip_gen_A = True, don't induce a nat class over the target (This is just an optimization for the locality experiment that does not affect the result).
                _seq.append(seg)
            else: # add the feature options for 
                _seq.append(NaturalClass({}, self.alphabet))
                # add all the feature options (+/- f, idx)
                for feat in self.alphabet.shared_feats(seg):
                    feat_space.add((feat, idx))
        seq = Sequence(_seq, self.alphabet) # build an initial nat class sequence

        # retain only the ngrams that match the sequence
        ngrams = list(filter(lambda ngram_f: seq.matches(ngram_f[0]), ngrams))
        # add labels to the ngrams that encode whether they match the rule or not
        ngrams = list((ngram, f, r.equals_CAD(ngram)) for ngram, f in ngrams)
        # build the seq recursively
        seq, success = self.build_new_seq(seq, feat_space, ngrams)

        # if no productive generalization is possible, return the original rule
        if not success:
            # print('----', r, seq, feat_space, self.get_n_c(seq, ngrams))
            es = list(filter(lambda ngram: seq.matches(ngram[0]) and not ngram[-1], ngrams))
            # print(es)
            return r
        
        # cache the segments that take each feature
        feat_to_segs = defaultdict(set)
        for seg in self.alphabet.segments:
            for feat in self.alphabet.feat_vals(seg):#self.alphabet.plus_minus(seg):
                feat_to_segs[feat].add(seg)

        new_r = r.copy() # copy the rule
        i = 0
        for seq_seg, r_seg in zip(seq, new_r.CAD()):
            if len(seq_seg) == 0: # make sure every seg has at least one feature
                options = sorted(self.alphabet.shared_feats(r_seg), key=lambda feat: (len(feat_to_segs[feat]), feat))
                seq_seg.add_feat(options[0])
            new_r.update_at(i, seq_seg)
            i += 1

        return new_r

    def build_new_seq(self, seq, feat_space, ngrams):
        '''
        Builds a new CAD sequence to replace the rule's, where the new seq's segments are nat classes—where possible—instead of explicit sets of segments.

        :seq: the initialized seq, with empty nat classes in positions that could potentially get nat classes
        :feat_space: the options of how to narrow the :seq: (each option is a distinctive feature and a position in the seq where it can be added)
        :ngrams: the ngrams that currently match :seq:

        :return: the new nat class sequence, along with and True if the seq is productive and False otherwise.
        '''
        last_score = None
        while len(feat_space) > 0:
            feat, score = self.get_best_feat(seq, feat_space, ngrams)
            feat_space.discard(feat)
            if score == last_score:
                continue
            last_score = score
            f, idx = feat
            seq[idx].add_feat(f)
            n, c = self.get_n_c(seq, ngrams)
            if tolerance_principle(n, c):
            # if epsilon(n, c, eps=1.0):
                return seq, True
            # retain only the ngrams that match the sequence
            ngrams = list(filter(lambda ngram_f: seq.matches(ngram_f[0]), ngrams))
        return seq, False

    def get_best_feat(self, seq, feat_space, ngrams):
        '''
        :return: the best-scoring feature in the :feat_space:
        '''
        _max = -1
        _argmax = None
        for feat in sorted(feat_space):
            score = self.get_feat_score(seq, feat, ngrams)
            if score > _max:
                _max = score
                _argmax = feat        
        return _argmax, _max

    def get_feat_score(self, seq, feat, ngrams):
        '''
        A :feat:'s score is the fraction of :ngrams: that match :seq:, after adding the :feat: to the :seq:, and that have a pos-label

        :return: the score of :feat: on the :ngrams:
        '''
        f, idx = feat
        assert(f not in seq[idx].feats)
        seq[idx].add_feat(f)
        n, c = self.get_n_c(seq, ngrams)
        seq[idx].remove_feat(f)
        return c / n

    def get_n_c(self, seq, ngrams):
        n, c = 0, 0
        for ngram, freq, lab in ngrams:
            if seq.matches(ngram):
                n += freq
                if lab:
                    c += freq
            else:
                assert(not lab)
        return n, c
