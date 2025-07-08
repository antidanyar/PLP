import unittest
import sys
from collections import defaultdict
sys.path.append('../src/')
from utils import load, PRIMARY_STRESS
from segment import Segment
from sequence import Sequence
from alphabet import Alphabet
from rule import Rule
from natural_class import NaturalClass

class TestRule(unittest.TestCase):
    def to_seq(self, pair, alphabet):
        return Sequence(list(alphabet[seg] for seg in pair[0])), Sequence(list(alphabet[seg] for seg in pair[1]))

    def test_rule_part_1(self):
        # test wildcard, wordend
        r = Rule(A='d', B='t', D='#')
        assert(r.stringify() == 'd --> t /  __ #')
        assert(r.C.wildcard())
        assert(not r.A.wildcard())
        assert(not r.D.wildcard())

        assert(r.D.wordend())
        assert(not r.C.wordend())
        assert(not r.A.wordend())

        assert(not r.A.empty())
        assert(not r.C.empty())
        assert(not r.D.empty())

        r = Rule(A='', B='ɘ', C='l', D='K')
        assert(r.stringify() == ' --> ɘ / l __ K')

        assert(r.A.empty())
        assert(not r.C.empty())
        assert(not r.D.empty())

    def test_rule_length(self):
        r = Rule(A='d', B='t', D='#')
        assert(r.stringify() == 'd --> t /  __ #')
        assert(len(r) == 2)

        r = Rule(A='', B='ɘ', C='l', D='K')
        assert(r.stringify() == ' --> ɘ / l __ K')
        assert(len(r) == 2)

        r = Rule(A='aɪ', B='ʌɪ', D='k')
        assert(r.stringify() == 'aɪ --> ʌɪ /  __ k')
        assert(len(r) == 3)

    def test_apply_epenthesis_segments(self):
        alphabet = Alphabet(add_segs=True, nas_vowels=True)
        r = Rule(A='', B='ɘ', C='l', D='k')
        assert(r.stringify() == ' --> ɘ / l __ k')
        s = 'lk'
        res = r.apply(Sequence(list(alphabet[seg] for seg in s)))
        assert(len(res) == 3)
        assert(res == 'lɘk')

    def test_apply_epenthesis_segments_1(self):
        alphabet = Alphabet(add_segs=True, nas_vowels=True)
        r = Rule(A='', B='ɪ', C='t', D='')
        assert(r.stringify() == ' --> ɪ / t __ ')
        assert(r.apply('wɔntd') == 'wɔntɪd')

        r = Rule(A='', B='ɪ', C='nt', D='')
        assert(r.stringify() == ' --> ɪ / nt __ ')
        assert(r.apply('wɔntd') == 'wɔntɪd')

    def test_accuracy_devoicing_segments_1(self):
        alphabet = Alphabet(add_segs=True, nas_vowels=True)
        r = Rule(A='d', B='t', D='#')
        assert(r.stringify() == 'd --> t /  __ #')

        pairs = [('und', 'unt')]
        pairs = list(self.to_seq(pair, alphabet) for pair in pairs)
        assert(r.accuracy(pairs) == 1.0)

        pairs = [('die', 'die'), ('und', 'unt')]
        pairs = list(self.to_seq(pair, alphabet) for pair in pairs)
        assert(r.accuracy(pairs) == 1.0)

    def test_accuracy_devoicing_segments_2(self):
        path = '../data/german/ger.txt'
        alphabet = Alphabet(add_segs=True, nas_vowels=True)
        pairs, _ = load(path, skip_header=True)

        r = Rule(A='d', B='t', D='.')
        assert(r.stringify() == 'd --> t /  __ .')
        assert(r.accuracy(pairs) == 1.0)

        pairs, _ = load(path, skip_header=True)
        assert(r.accuracy(pairs) == 1.0)

    def test_applications_devoicing(self):
        r = Rule(A='d', B='t', D='#')
        assert(r.stringify() == 'd --> t /  __ #')
        pairs = [('diə', 'diə'), ('und', 'unt')]
        assert(r.applications(pairs) == [pairs[1]])

    def test_applications_raising(self):
        r = Rule(A='aɪ', B='ʌɪ', D='k')
        assert(r.stringify() == 'aɪ --> ʌɪ /  __ k')
        pairs = [('laɪk', 'lʌɪk'), ('aʊt', 'ʌʊt')]
        assert(r.applications(pairs) == [pairs[0]])

    def test_applications_epenthesis(self):
        r = Rule(A='', B='ɘ', C='l', D='K')
        pairs = [('lK', 'lɘK'), ('rK', 'rɘK'), ('lr', 'lr')] 
        assert(r.stringify() == ' --> ɘ / l __ K')
        assert(r.applications(pairs) == pairs[:-2])
        r = Rule(A='', B='ɘ', C='r', D='K')
        assert(r.stringify() == ' --> ɘ / r __ K')
        assert(r.applications(pairs) == pairs[1:-1])

    def test_accuracy_aaaa(self):
        r = Rule(A='a', B='b', C='a', D='a')
        assert(r.stringify() == 'a --> b / a __ a')
        assert(r.accuracy([('aaaa', 'abba')]) == 1.0)

    def test_accuracy_segments_aaaa(self):
        uf = Sequence('aaaa')
        sf = Sequence('abba')
        r = Rule(A='a', B='b', C='a', D='a')
        assert(r.stringify() == 'a --> b / a __ a')
        assert(r.accuracy([(uf, sf)]) == 1.0)

    def test_accuracy_segments_greek_deletion_1(self):
        p1 = (Sequence('θθ'), Sequence('θ'))
        p2 = (Sequence('ðθθ'), Sequence('θ'))
        r = Rule(A='θ', B='', D='θ')
        assert(r.stringify() == 'θ -->  /  __ θ')
        pairs = [p1, p2]
        assert(r.accuracy(pairs) == 1.0)

    def test_accuracy_segments_greek_deletion_2(self):
        r1 = Rule(A='θ', B='', D='θ')
        r2 = Rule(A='θ', B='', D='s')
        r3 = Rule(A='ð', B='', D='θ')
        r4 = Rule(A='ð', B='', D='s')

        r1.merge(r2, [])
        r3.merge(r4, [])
        r1.merge(r3, [])
        r = r1
        assert(r.stringify() == '{ð,θ} -->  /  __ {s,θ}')
        assert(r.accuracy([(Sequence('θθ'), Sequence('θ'))]) == 1.0)
        assert(r.accuracy([('θθ', 'θ')]) == 1.0)
        assert(r.apply('θθ') == 'θ')

    def test_accuracy_segments_epenthesis(self):
        r = Rule(A='', B='ɘ', C='l', D='K')
        pairs = [('lK', 'lɘK'), ('rK', 'rɘK'), ('lr', 'lr')]
        pairs = list((Sequence(p[0]), Sequence(p[1])) for p in pairs)
        assert(r.stringify() == ' --> ɘ / l __ K')
        assert(r.accuracy(pairs) == 1.0)
        assert(r.apply(Sequence('lK')) == 'lɘK')

    def test_accuracy_devoicing(self):
        r = Rule(A='d', B='t', D='#')
        assert(r.stringify() == 'd --> t /  __ #')
        pairs = [('diə', 'diə'), ('und', 'unt')]
        assert(r.accuracy(pairs) == 1.0)

    def test_accuracy_aid(self):
        r = Rule(A='', B='ɪ', C='aɪd')
        assert(r.stringify() == ' --> ɪ / aɪd __ ')
        pairs = [('traɪd', 'traɪd'), ('kraɪd', 'kraɪd'), ('dɪsaɪdd', 'dɪsaɪdɪd')]
        assert(r.accuracy(pairs) == 1/3)

    def test_accuracy_greek_deletion_1(self):
        r = Rule(A='θ', B='', D='θ')
        assert(r.stringify() == 'θ -->  /  __ θ')
        pairs = [('θθ', 'θ'), ('ðθθ', 'θ')]
        assert(r.accuracy(pairs) == 1.0)

    def test_accuracy_greek_deletion_2(self):
        alph = ['θ', 'ð', 's', '?']
        ufs = ['θ', 'ð', 's', '?']

        for i in range(4):
            for j in range(4):
                uf = f'{alph[i]}{alph[j]}'
                ufs.append(uf)

        for i in range(4):
            for j in range(4):
                for k in range(4):
                    uf = f'{alph[i]}{alph[j]}{alph[k]}'
                    ufs.append(uf)

        sfs = list()
        for uf in ufs:
            sf = ''
            for i in range(len(uf)):
                if i < len(uf) - 1 and uf[i] in {'θ', 'ð'} and uf[i + 1] in {'θ', 's'}:
                    sf += ''
                else:
                    sf += uf[i]
            sfs.append(sf)
            
        pairs = list()
        for uf, sf in zip(ufs, sfs):
            pairs.append((uf, sf))

        r1 = Rule(A='θ', B='', D='θ')
        r2 = Rule(A='θ', B='', D='s')
        r3 = Rule(A='ð', B='', D='θ')
        r4 = Rule(A='ð', B='', D='s')
        assert(r1.accuracy(pairs) == 1.0)
        assert(r2.accuracy(pairs) == 1.0)
        assert(r3.accuracy(pairs) == 1.0)
        assert(r4.accuracy(pairs) == 1.0)

    def test_get_n_c_epenthesis(self):
        r = Rule(A='', B='ɘ', C='l', D='K')
        pairs = [('lK', 'lɘK')]
        assert(r.get_n_c(pairs) == (1, 1))

    def test_shift_excess_D_into_AB(self):
        r = Rule(A='', B='ɪ', C='t', D='d#')
        assert(r.stringify() == ' --> ɪ / t __ d#')
        r.shift_excess_D_into_AB()
        assert(r.stringify() == 'd --> ɪd / t __ #')

    def test_merge_rules_1(self):
        r1 = Rule(A='z', B='s', C='k', D='#')
        assert(r1.stringify() == 'z --> s / k __ #')
        r2 = Rule(A='z', B='s', C='p', D='#')
        assert(r2.stringify() == 'z --> s / p __ #')
        r1.merge(r2, [])
        assert(r1.stringify() == '{z} --> s / {k,p} __ {#}')
        r3 = Rule(A='z', B='s', C='f', D='#')
        assert(r3.stringify() == 'z --> s / f __ #')
        r1.merge(r3, [])
        assert(r1.stringify() == '{z} --> s / {f,k,p} __ {#}')

    def test_merge_rules_2(self):
        r1 = Rule(A='d', B='-voiced', D='#')
        assert(r1.stringify() == 'd --> [-voiced] /  __ #')
        r2 = Rule(A='b', B='-voiced', D='#')
        assert(r2.stringify() == 'b --> [-voiced] /  __ #')
        r1.merge(r2, [])
        assert(r1.stringify() == '{b,d} --> [-voiced] /  __ #')
        r3 = Rule(A='g', B='-voiced', D='#')
        assert(r3.stringify() == 'g --> [-voiced] /  __ #')
        r1.merge(r3, [])
        assert(r1.stringify() == '{b,d,g} --> [-voiced] /  __ #')

    def test_merge_rules_3(self):
        r1 = Rule(A='θ', B='', D='s')
        assert(r1.stringify() == 'θ -->  /  __ s')
        r2 = Rule(A='θ', B='', D='θ')
        assert(r2.stringify() == 'θ -->  /  __ θ')
        r1.merge(r2, [])
        assert(r1.stringify() == '{θ} -->  /  __ {s,θ}')
        
        r3 = Rule(A='θ', B='', D='θ')
        r1.merge(r3, []) # make sure repeat merge does not break things
        assert(r1.stringify() == '{θ} -->  /  __ {s,θ}')

    def test_merge_rules_4(self):
        r1 = Rule(A=Segment('θ'), B=Segment(''), D=Segment('s'))
        assert(r1.stringify() == 'θ -->  /  __ s')
        r2 = Rule(A=Segment('θ'), B=Segment(''), D=Segment('θ'))
        assert(r2.stringify() == 'θ -->  /  __ θ')
        r1.merge(r2, [])
        assert(r1.stringify() == '{θ} -->  /  __ {s,θ}')
        
        r3 = Rule(A=Segment('θ'), B=Segment(''), D=Segment('θ'))
        r1.merge(r3, []) # make sure repeat merge does not break things
        assert(r1.stringify() == '{θ} -->  /  __ {s,θ}')

    def test_merge_1(self):
        alphabet = Alphabet(add_segs=True, nas_vowels=True)
        r1 = Rule(A='i', B='+nas', D=[{'n', 'm'}], alphabet=alphabet)
        assert(r1 == 'i --> [+nas] /  __ {m,n}')
        r2 = Rule(A='e', B='+nas', D='m', alphabet=alphabet)
        assert(r2 == 'e --> [+nas] /  __ m')

        pairs = [(Sequence('pin', alphabet=alphabet), Sequence('pi\u0303n', alphabet=alphabet)), 
                 (Sequence('pim', alphabet=alphabet), Sequence('pi\u0303m', alphabet=alphabet)), 
                 (Sequence('pem', alphabet=alphabet), Sequence('pe\u0303m', alphabet=alphabet)),
                 (Sequence('pen', alphabet=alphabet), Sequence('pe\u0303n', alphabet=alphabet))]

        r1.merge(r2, pairs)

        assert(r1.apply('pin') == 'pi\u0303n')
        assert(r1.apply('pim') == 'pi\u0303m')
        assert(r2.apply('pem') == 'pe\u0303m')
        assert(r2.apply('pen') == 'pen')

        assert(r1.apply('pen') == 'pe\u0303n')


    def test_accuracy_after_other(self):
        alphabet = Alphabet(add_segs=True, nas_vowels=True)
        r1 = Rule(A='', B=Segment('ɪ'), C=Segment('t'), D=Segment('d'))
        r1.merge(Rule(A='', B=Segment('ɪ'), C=Segment('d'), D=Segment('d')), [])
        assert(r1 == ' --> ɪ / {d,t} __ {d}')
        r2 = Rule(A='d', B='-voi', C=[NaturalClass({'-voi'}, alphabet=alphabet)], alphabet=alphabet)

        pairs = [('wɔntd', 'wɔntɪd')]

        assert(r1.accuracy_after_other(r2, pairs) == 0.0)
        assert(r2.accuracy_after_other(r1, pairs) == 1.0)

    def test_nas_vowels_1(self):
        alphabet = Alphabet(add_segs=True, nas_vowels=True)
        r = Rule(A='i', B='+nas', alphabet=alphabet)
        assert(r.stringify() == 'i --> [+nas] /  __ ')
        assert(r.apply('min') == 'mi\u0303n')
        assert(r.apply('mʌmi') == 'mʌmi\u0303')

    def test_nas_vowels_2(self):
        alphabet = Alphabet(add_segs=True, nas_vowels=True)
        r1 = Rule(A='i', B='+nas', alphabet=alphabet)
        assert(r1.stringify() == 'i --> [+nas] /  __ ')
        r2 = Rule(A='ʌ', B='+nas', D='m', alphabet=alphabet)
        assert(r1.apply('min') == 'mi\u0303n')
        res = r2.apply('mʌmi')
        assert(res == 'mʌ\u0303mi')
        assert(len(res) == 4)
        assert(r1.apply(res) == 'mʌ\u0303mi\u0303')

    def test_update_at_1(self):
        r = Rule(A='a', B='b', C=['x', 'y', 'z'], D=['i', 'j', 'k'])
        r.update_at(0, 'n')
        assert(r == 'a --> b / nyz __ ijk')

        r = Rule(A='a', B='b', C=['x', 'y', 'z'], D=['i', 'j', 'k'])
        r.update_at(1, 'n')
        assert(r == 'a --> b / xnz __ ijk')

        r = Rule(A='a', B='b', C=['x', 'y', 'z'], D=['i', 'j', 'k'])
        r.update_at(2, 'n')
        assert(r == 'a --> b / xyn __ ijk')

        r = Rule(A='a', B='b', C=['x', 'y', 'z'], D=['i', 'j', 'k'])
        r.update_at(3, 'n')
        assert(r == 'n --> b / xyz __ ijk')

        r = Rule(A='a', B='b', C=['x', 'y', 'z'], D=['i', 'j', 'k'])
        r.update_at(4, 'n')
        assert(r == 'a --> b / xyz __ njk')

        r = Rule(A='a', B='b', C=['x', 'y', 'z'], D=['i', 'j', 'k'])
        r.update_at(5, 'n')
        assert(r == 'a --> b / xyz __ ink')

        r = Rule(A='a', B='b', C=['x', 'y', 'z'], D=['i', 'j', 'k'])
        r.update_at(6, 'n')
        assert(r == 'a --> b / xyz __ ijn')

    def test_update_at_2(self):
        r = Rule(A='a', B='b', C=['x', 'y', 'z'])
        assert(r.update_at(0, 'n'))
        assert(r == 'a --> b / nyz __ ')

        r = Rule(A='a', B='b', C=['x', 'y', 'z'])
        assert(r.update_at(1, 'n'))
        assert(r == 'a --> b / xnz __ ')

        r = Rule(A='a', B='b', C=['x', 'y', 'z'])
        assert(r.update_at(2, 'n'))
        assert(r == 'a --> b / xyn __ ')

        r = Rule(A='a', B='b', C=['x', 'y', 'z'])
        assert(r.update_at(3, 'n'))
        assert(r == 'n --> b / xyz __ ')

        r = Rule(A='a', B='b', C=['x', 'y', 'z'])
        assert(not r.update_at(4, 'n'))
        assert(r == 'a --> b / xyz __ ')

    def test_update_at_3(self):
        r = Rule(A='a', B='b', D=['x', 'y', 'z'])
        assert(r.update_at(0, 'n'))
        assert(r == 'n --> b /  __ xyz')

        r = Rule(A='a', B='b', D=['x', 'y', 'z'])
        assert(r.update_at(1, 'n'))
        assert(r == 'a --> b /  __ nyz')

        r = Rule(A='a', B='b', D=['x', 'y', 'z'])
        assert(r.update_at(2, 'n'))
        assert(r == 'a --> b /  __ xnz')

        r = Rule(A='a', B='b', D=['x', 'y', 'z'])
        assert(r.update_at(3, 'n'))
        assert(r == 'a --> b /  __ xyn')

        r = Rule(A='a', B='b', D=['x', 'y', 'z'])
        assert(not r.update_at(4, 'n'))
        assert(r == 'a --> b /  __ xyz')

    def test_update_at_4(self):
        r = Rule(A='', B='b', C=['x', 'y', 'z'])
        assert(r.update_at(0, 'n'))
        assert(r == ' --> b / nyz __ ')

        r = Rule(A='', B='b', C=['x', 'y', 'z'])
        assert(r.update_at(1, 'n'))
        assert(r == ' --> b / xnz __ ')

        r = Rule(A='', B='b', C=['x', 'y', 'z'])
        assert(r.update_at(2, 'n'))
        assert(r == ' --> b / xyn __ ')

        r = Rule(A='', B='b', C=['x', 'y', 'z'])
        assert(not r.update_at(3, 'n'))
        assert(r == ' --> b / xyz __ ')

        r = Rule(A='', B='b', C=['x', 'y', 'z'], D=['i', 'j', 'k'])
        assert(r.update_at(3, 'n'))
        assert(r == ' --> b / xyz __ njk')

    def test_A_index(self):
        r = Rule(A='a', B='b', C=['x', 'y', 'z'], D=['i', 'j', 'k'])
        assert(r.A_index() == 3)

        r = Rule(A='a', B='b', C=['x', 'y', 'z'])
        assert(r.A_index() == 3)

        r = Rule(A='a', B='b', D=['i', 'j', 'k'])
        assert(r.A_index() == 0)

        r = Rule(A='', B='b', C=['x', 'y', 'z'], D=['i', 'j', 'k'])
        assert(r.A_index() == None)

if __name__ == "__main__":
    unittest.main()