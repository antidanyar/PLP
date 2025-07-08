import unittest
import sys
sys.path.append('../src/')
from segment import Segment
from sequence import Sequence
from alphabet import Alphabet
from natural_class import NaturalClass

class TestSequence(unittest.TestCase):
    def test_init(self):
        Sequence('seq')

    def test_string_eq_1(self):
        seq = Sequence('aaaa')
        assert(seq == 'aaaa')

    def test_string_eq_2(self):
        seq = Sequence(['a', 'a', 'a', 'a'])
        assert(seq == 'aaaa')

    def test_seq_eq_1(self):
        s1 = Sequence('aaaa')
        s2 = Sequence('abba')
        s3 = Sequence('aaaa')
        assert(s1 == s3)
        assert(s1 != s2)

    def test_seq_eq_2(self):
        alph = Alphabet(add_segs=True)
        s1 = Sequence([alph['a'], alph['a'], alph['a'], alph['a']])
        s2 = Sequence([alph['a'], alph['b'], alph['b'], alph['a']])
        s3 = Sequence([alph['a'], alph['a'], alph['a'], alph['a']])
        assert(s1 == s3)
        assert(s1 != s2)

    def test_eq_rule_merge_1(self):
        s = Segment('s')
        thh = Segment('ð')
        th = Segment('θ')
        s1 = Sequence([{s, th}])
        s2 = Sequence([{s, th}])
        s3 = Sequence([{s, thh}])
        s4 = Sequence([{s, Segment('θ')}])

        assert(s1 == s2)
        assert(s1 != s3)
        assert(s1 == s4)
        
    def test_set_matches_1(self):
        seq = Sequence([{'a', 'b'}, 'c'])
        assert(not seq == 'ac')
        assert(seq.matches('ac'))
        assert(seq.matches('bc'))
        assert(not seq.matches('cc'))

    def test_nat_class_matches_1(self):
        nat_class = NaturalClass(feats={'+voi', '-son'}, alphabet=Alphabet(add_segs=True))
        seq = Sequence([nat_class, '#'])
        assert(seq.matches('d#'))
        assert(seq.matches('b#'))
        assert(not seq.matches('t#'))
        assert(not seq.matches('k#'))
        assert(not seq.matches('s#'))
        assert(not seq.matches('a#'))

    def test_wildcard_matches_1(self):
        seq = Sequence('*')
        assert(seq.matches('a'))
        assert(seq.matches('b'))
        assert(seq.matches('c'))
        assert(seq.matches('#'))

        seq = Sequence('*#')
        assert(seq.matches('a#'))
        assert(seq.matches('b#'))
        assert(seq.matches('c#'))

        nat_class = NaturalClass(feats={'+voi', '-son'}, alphabet=Alphabet(add_segs=True))
        seq = Sequence(['*', nat_class, '#'])
        assert(seq.matches('ad#'))
        assert(seq.matches('ab#'))
        assert(not seq.matches('at#'))
        assert(not seq.matches('aa#'))

    def test_segment_eq_1(self):
        alph = Alphabet(add_segs=True)
        seq = Sequence([alph['a'], alph['a'], alph['a'], alph['a']])
        assert(seq == 'aaaa')
        assert(seq != 'aaab')
        assert(seq == Sequence([alph['a'], alph['a'], alph['a'], alph['a']]))
        assert(seq != Sequence([alph['a'], alph['a'], alph['a'], alph['b']]))

    def test_windows_1(self):
        seq = Sequence('asdf')

        assert(seq.windows(i=0, k=2) == [('', 's'), ('#', '')])
        assert(seq.windows(i=2, k=2) == [('', 'f'), ('s', '')])
        assert(seq.windows(i=2, k=3) == sorted([('as', ''), ('', 'f#'), ('s', 'f')]))
        assert(seq.windows(i=1, k=3) == sorted([('#a', ''), ('a', 'd'), ('', 'df')]))

        seq = Sequence('wɔntλd')
        assert(seq.windows(i=4, k=4) == sorted([('nt', 'd'), ('t', 'd#'), ('ɔnt', '')]))

    def test_str_1(self):
        seq = Sequence('abc')
        assert(f'{seq}' == 'abc')

        seq = Sequence(['a', 'b', 'c'])
        assert(f'{seq}' == 'abc')

        seq = Sequence([{'a', 'b'}, 'c'])
        assert(f'{seq}' == '{a,b}c')

        nat_class = NaturalClass(feats={'+voiced', '-sonorant'}, alphabet=Alphabet(add_segs=True))
        seq = Sequence(['*', nat_class, '#'])
        assert(f'{seq}' == '*{+voiced,-sonorant}#')

    def test_merge_1(self):
        s1 = Sequence(Segment('a'))
        s2 = Sequence(Segment('b'))

        s1.merge(s2)
        assert(f'{s1}' == '{a,b}')

        s3 = Sequence(Segment('d'))
        s1.merge(s3)
        assert(f'{s1}' == '{a,b,d}')

        s3.merge(s1)
        assert(f'{s3}' == '{a,b,d}')

    def test_nas_vowels(self):
        alph = Alphabet(add_segs=True, nas_vowels=True)
        s1 = Sequence('pu\u0303', alphabet=alph)
        s2 = Sequence('pu', alphabet=alph)
        assert(s1 == 'pu\u0303')
        assert(len(s1) == 2)
        assert(s1 != s2)

if __name__ == "__main__":
    unittest.main()