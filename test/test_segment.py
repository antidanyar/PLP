import unittest
import sys
sys.path.append('../src/')
from segment import Segment
from alphabet import Alphabet

class TestSegment(unittest.TestCase):
    def test_init(self):
        Segment('b', feature_vec=[])

    def test_string_eq_1(self):
        seg = Segment('b', feature_vec=[])
        assert(seg == 'b')

        alph = Alphabet(add_segs=True, nas_vowels=True)
        assert(alph['b'] == 'b')
        assert(alph['b'] != 'p')

    def test_seg_eq_1(self):
        s1 = Segment('b', feature_vec=[0, 0])
        s2 = Segment('b', feature_vec=[0, 0])
        s3 = Segment('p', feature_vec=[0, 0])
        s4 = Segment('b', feature_vec=[0, 1])
        s5 = Segment('p', feature_vec=[0, 1])

        assert(s1 == s2)
        assert(s1 != s3)
        assert(s1 != s4)
        assert(s1 != s5)

    def test_hash_1(self):
        s1 = Segment('b', feature_vec=[0, 0])
        s2 = Segment('b', feature_vec=[0, 0])
        s3 = Segment('p', feature_vec=[0, 0])

        segs = {s1}
        assert(s1 in segs)
        assert(s2 in segs)
        assert(s3 not in segs)

        s1 = Segment('b', feature_vec=[])
        s2 = Segment('b', feature_vec=[])
        s3 = Segment('p', feature_vec=[])

        segs = {s1}
        assert(s1 in segs)
        assert(s2 in segs)
        assert(s3 not in segs)




if __name__ == "__main__":
    unittest.main()