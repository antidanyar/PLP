import unittest
import sys
from collections import defaultdict
sys.path.append('../src/')
from utils import powerset, most_freq, windows, insert_empty

class TestUtils(unittest.TestCase):
    def test_powerset_1(self):
        assert(powerset({1, 2, 3}) == {(), (1,), (2,), (3,), (1, 2), (1, 3), (2, 3), (1, 2, 3)})

    def test_powerset_2(self):
        assert(powerset({1}) == {(), (1,)})

    def test_powerset_3(self):
        assert(powerset({}) == {()})

    def test_most_freq_1(self):
        assert(most_freq([1, 2, 1, 3, 4, 1, 1]) == 1)

    def test_most_freq_2(self):
        assert(most_freq([3, 2, 1, 3, 4, 1, 1]) == 1)

    def test_most_freq_3(self):
        assert(most_freq([3]) == 3)

    def test_most_freq_4(self):
        assert(most_freq([1, 2]) == 1)

    def test_most_freq_5(self):
        assert(most_freq(['a', 'b', 'b', 'c']) == 'b')

    def test_windows(self):
        s = 'asdf'
        assert(windows(s, i=0, k=2, split=False) == ['#a', 'as'])
        assert(windows(s, i=2, k=2, split=False) == ['df', 'sd'])
        assert(windows(s, i=2, k=3, split=False) == ['asd', 'df#', 'sdf'])
        assert(windows(s, i=1, k=3, split=False) == ['#as', 'asd', 'sdf'])

        assert(windows('wɔntλd', i=4, k=4, split=False) == ['ntλd', 'tλd#', 'ɔntλ'])

        assert(windows(s, i=0, k=2, split=True) == [('', 's'), ('#', '')])
        assert(windows(s, i=2, k=2, split=True) == [('', 'f'), ('s', '')])
        assert(windows(s, i=2, k=3, split=True) == sorted([('as', ''), ('', 'f#'), ('s', 'f')]))
        assert(windows(s, i=1, k=3, split=True) == sorted([('#a', ''), ('a', 'd'), ('', 'df')]))

    def test_insert_empty(self):
        assert(insert_empty('abcd', k=1) == ['λabcd', 'aλbcd', 'abλcd', 'abcλd', 'abcdλ'])
        assert(insert_empty('abcd', k=0) == ['abcd'])
        assert(set(insert_empty('abcd', k=2)) == {'λλabcd', 'λaλbcd', 'λabλcd', 'λabcλd', 'λabcdλ', 'aλλbcd', 'aλbλcd', 'aλbcλd', 'aλbcdλ', 'abλλcd', 'abλcλd', 'abλcdλ', 'abcλλd', 'abcλdλ', 'abcdλλ'})

if __name__ == "__main__":
    unittest.main()