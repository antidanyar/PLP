import unittest
import sys
from collections import defaultdict
sys.path.append('../src/')
from utils import load
from alphabet import Alphabet

class TestAlphabet(unittest.TestCase):
    def test_getitem_1(self):
        alphabet = Alphabet(add_segs=True)

        b = alphabet['b']
        assert(alphabet['b'].ipa == 'b')
        assert(alphabet[','.join(b.feature_vec)].ipa == 'b')
        assert(alphabet[b.feature_vec].ipa == 'b')
        assert(alphabet[b] == b)

        p = alphabet['p']
        assert(alphabet['p'].ipa == 'p')
        assert(alphabet[','.join(p.feature_vec)].ipa == 'p')
        assert(alphabet[p.feature_vec].ipa == 'p')
        assert(alphabet[p] == p)

    def test_without_feats_1(self):
        alphabet = Alphabet(add_segs=True)

        b = alphabet['b']
        p = alphabet['p']

        assert(alphabet.without_feats('b', 'voi') == p)
        assert(alphabet.without_feats(','.join(b.feature_vec), 'voi') == p)
        assert(alphabet.without_feats(b.feature_vec, 'voi') == p)

    def test_with_feats_1(self):
        alphabet = Alphabet(add_segs=True)

        b = alphabet['b']
        p = alphabet['p']

        assert(alphabet.with_feats('p', 'voi') == b)
        assert(alphabet.with_feats(','.join(p.feature_vec), 'voi') == b)
        assert(alphabet.with_feats(p.feature_vec, 'voi') == b)

    def test_eng(self):
        '''
        Check uniquness of segs
        '''
        alph = Alphabet(ipa_file='../data/english/ipa.txt', add_segs=True, nas_vowels=True)

        vecs = dict()
        for seg in alph:
            vec = ','.join(seg.feature_vec)
            assert(vec not in vecs)
            vecs[vec] = seg

    def test_ger(self):
        '''
        Check uniquness of segs
        '''
        alph = Alphabet(ipa_file='../data/german/ipa.txt', add_segs=True, nas_vowels=True)

        vecs = dict()
        for seg in alph:
            vec = ','.join(seg.feature_vec)
            assert(vec not in vecs)
            vecs[vec] = seg

if __name__ == "__main__":
    unittest.main()