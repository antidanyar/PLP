import unittest
import sys
sys.path.append('../src/')
from utils import load
from plp import PLP
import numpy as np
import random

class TestPLP(unittest.TestCase):
    def assert_correct(self, plp, pairs):
        for uf, sf in pairs:
            pred = plp.produce(uf)
            if pred != sf:
                print(f'UF: {uf}    Pred: {pred}    SF: {sf}')
            assert(pred == sf)

    def test_init(self):
        plp = PLP()
        
    def test_german_devoicing_1(self):
        plp = PLP(verbose=False)
        pairs = [('diə.', 'diə.'), ('und.', 'unt.')]
        plp.train(pairs)
        self.assert_correct(plp, pairs)

    def test_german_devoicing_2(self):
        plp = PLP(verbose=False, ipa_file='../data/german/ipa.txt')
        pairs = [('die.', 'die.'), ('und.', 'unt.'), ('gʊ.kɘn.', 'gʊ.kɘn.'), ('zɪnd.', 'zɪnt.'), ('mʊs.', 'mʊs.'), ('kro.ko.dil.', 'kro.ko.dil.'), ('mal.', 'mal.'), ('dry.kɘn.', 'dry.kɘn.'),
                 ('glai.zɘ.', 'glai.zɘ.'), ('ʃtat.', 'ʃtat.'), ('hɪn.tɘr.', 'hɪn.tɘr.'), ('hɪl.fɘ.', 'hɪl.fɘ.'), ('hʊb.ʃrau.bɘr.', 'hʊp.ʃrau.bɘr.'), ('baum.', 'baum.'), ('mɪt.ne.mɘn.', 'mɪt.ne.mɘn.'),
                 ('gɘ.nug.', 'gɘ.nuk.'), ('an.dɘ.rɘs.', 'an.dɘ.rɘs.'), ('gɛlb.', 'gɛlp.'), ('dax.', 'dax.'), ('fɪ.ŋɘr.', 'fɪ.ŋɘr.'), ('li.gɘn.', 'li.gɘn.')]
        plp.train(pairs)
        self.assert_correct(plp, pairs)
        assert(plp.grammar.rules == ['{+voi,-son} --> [-voi] /  __ .'])

    def test_german_devoicing_3(self):
        plp = PLP(ipa_file='../data/german/ipa.txt', verbose=False)
        pairs, freqs = load('../data/german/ger.txt', skip_header=True)
        p = np.asarray(freqs) / sum(freqs)
        idxs = list(range(len(pairs)))

        np.random.seed(0)
        while len(plp.vocab) < 200:
            train_idx = list(np.random.choice(idxs, p=p, size=1))[0]
            pair = pairs[train_idx]
            plp.train_incremental(pair)

        self.assert_correct(plp, pairs)
        assert(plp.grammar.rules == ['{+voi,-son} --> [-voi] /  __ .'])

    def test_german_devoicing_4(self):
        plp = PLP(verbose=False)
        plp.train_incremental(('und.', 'unt.'))
        assert(plp.produce('und.') == 'unt.')
        plp.train_incremental(('diə.', 'diə.'))
        assert(plp.produce('und.') == 'unt.')
        plp.train_incremental(('ed.', 'et.'))
        assert(plp.produce('und.') == 'unt.')

    def test_german_devoicing_5(self):
        plp = PLP(ipa_file='../data/german/ipa.txt', verbose=False)

        ps1 = [('ganz.', 'gans.'), ('dnd.', 'dnt.'), ('tsug.', 'tsuk.')]
        for pair in ps1:
            plp.train_incremental(pair)
        assert(len(plp.grammar) == 1)
        r = plp.grammar.rules[0]
        assert(len(r.C) == 0 and len(r.C) == 0)

        ps2 = [('nu.', 'nu.'), ('di.', 'di.'), ('zea.', 'zea.'), ('it.', 'it.'), ('ip.', 'ip.'), ('ik.', 'ik.')]
        for pair in ps2:
            plp.train_incremental(pair)
        assert(len(plp.grammar) == 1)

        self.assert_correct(plp, ps1)
        self.assert_correct(plp, ps2)

    def test_german_devoicing_6(self):
        i = 0
        pairs, _ = load('../data/german/ger.txt', skip_header=True)
        pairs = pairs[:200]

        plp = PLP(ipa_file='../data/german/ipa.txt', verbose=False)
        plp.train(pairs)
        self.assert_correct(plp, pairs)

        assert(plp.grammar.rules == ['{+voi,-son} --> [-voi] /  __ .'])

    def test_deletion(self):
        plp = PLP(verbose=False)
        
        plp.train_incremental(('ðð', 'ðð'))
        plp.train_incremental(('ðs', 's'))
        assert(len(plp.grammar) == 1)

        plp.train_incremental(('θð', 'θð'))
        plp.train_incremental(('θs', 's'))
        assert(len(plp.grammar) == 1)

        plp.train_incremental(('ðθ', 'θ'))
        plp.train_incremental(('θθ', 'θ'))
        assert(len(plp.grammar) == 1)

    def test_abaa(self):
        '''
        Test a --> b / a __ a (See Chandlee's disserstation, Fig. 3.1)
        '''
        alph = ['a', 'b']
        ufs = ['a', 'b']

        for ai in alph:
            uf = f'{ai}'
            ufs.append(uf)
            for aj in alph:
                uf = f'{ai}{aj}'
                ufs.append(uf)
                for ak in alph:
                    uf = f'{ai}{aj}{ak}'
                    ufs.append(uf)
                    for al in alph:
                        uf = f'{ai}{aj}{ak}{al}'
                        ufs.append(uf)

        sfs = list()
        for uf in ufs:
            sf = ''
            for i in range(len(uf)):
                if i > 0 and i < len(uf) - 1 and uf[i - 1] == 'a' and uf[i + 1] == 'a' and uf[i] == 'a':
                    sf += 'b'
                else:
                    sf += uf[i]
            sfs.append(sf)
            
        pairs = list()
        for uf, sf in zip(ufs, sfs):
            pairs.append((uf, sf))

        plp = PLP(ipa_file='../data/ipa_ab.txt', n_grams_lens=[1, 2, 3], verbose=False)        
        for pair in pairs:
            plp.train_incremental(pair)

        assert(f'{plp}' == '1: {+a} --> b / {+a} __ {+a}')

        assert(plp.produce('aaaaa') == 'abbba')
        assert(plp.produce('a') == 'a')
        assert(plp.produce('aa') == 'aa')
        assert(plp.produce('aab') == 'aab')
        assert(plp.produce('aabaaa') == 'aababa')
        assert(plp.produce('aaabaaabaaa') == 'abababababa')
        assert(plp.produce('aaaaaaaaaaa') == 'abbbbbbbbba')

    def test_english_1(self):
        pairs, _ = load('../data/english/eng.txt', skip_header=True)
        pairs = pairs[:500]

        plp = PLP(nas_vowels=True, verbose=False)
        plp.train(pairs)

        self.assert_correct(plp, pairs)

    def test_english_2(self):
        pairs, _ = load('../data/english/eng.txt', skip_header=True)
        s_pairs = [('wɑntz', 'wɑnts'), ('laɪkz', 'laɪks'), ('greɪpz', 'greɪps'), ('læfz', 'læfs')]
        z_pairs = [('saʊndz', 'saʊndz'), ('dɑgz', 'dɑgz')]
        uz_pairs = [('glæsz', 'glæsɪz'), ('saɪzz', 'saɪzɪz'), ('mætʃz', 'mætʃɪz')]

        pairs = s_pairs + z_pairs + uz_pairs

        plp = PLP(nas_vowels=True, verbose=False)
        plp.train(pairs)

        self.assert_correct(plp, pairs)

    def test_english_3(self):
        plp = PLP(ipa_file='../data/english/ipa.txt', nas_vowels=True, verbose=False)
        pairs, freqs = load('../data/english/eng.txt', skip_header=True)
        num_train = 1750
        num_test = 2000
        plp.train(pairs[:num_train])

        assert(len(plp.grammar) == 4)
        assert(plp.accuracy(pairs[num_train:num_train+num_test]) >= 0.99)

    def test_english_nas_1(self):
        pairs = [('ənd', 'ə̃nd'), ('ju', 'ju'), ('ðæt', 'ðæt'), ('goʊɪŋ', 'goʊɪ̃ŋ'), ('wɑnə', 'wɑ̃nə'), 
                 ('daʊn', 'daʊ̃n'), ('ðɪs', 'ðɪs'), ('bɪkɔz', 'bɪkɔz'), ('duɪŋ', 'duɪ̃ŋ'), ('wɛn', 'wɛ̃n'),
                 ('meɪk', 'meɪk'), ('əbaʊt', 'əbaʊt'), ('hæpənd', 'hæpə̃nd'), ('kʌmɪŋ', 'kʌ̃mɪ̃ŋ'),
                 ('pipəl', 'pipəl'), ('naɪt', 'naɪt'), ('θæŋkju', 'θæ̃ŋkju'), ('grin', 'grĩn'),
                 ('skul', 'skul'), ('hɛlp', 'hɛlp'), ('mʌtʃ', 'mʌtʃ'), ('dædi', 'dædi'), ('bɪt', 'bɪt'),
                 ('læst', 'læst'), ('drɪŋk', 'drɪ̃ŋk'), ('æftɝ', 'æftɝ'), ('dɔg', 'dɔg'), ('tɑp', 'tɑp'),
                 ('hʌni', 'hʌ̃ni'), ('pʊʃ', 'pʊʃ'), ('bʌs', 'bʌs'), ('trʌk', 'trʌk'), ('ɪnʌf', 'ɪ̃nʌf'),
                 ('pɪktʃɝ', 'pɪktʃɝ'), ('ɪnsaɪd', 'ɪ̃nsaɪd'), ('ʌndɝ', 'ʌ̃ndɝ'), ('koʊld', 'koʊld'), ('hʌŋgri', 'hʌ̃ŋgri'),
                 ('mɔrnɪŋ', 'mɔrnɪ̃ŋ'), ('ɛlənɔr', 'ɛlə̃nɔr'), ('keɪm', 'keɪ̃m'), ('pleɪɪŋ', 'pleɪɪ̃ŋ'), ('jus', 'jus')]

        plp = PLP(nas_vowels=True, verbose=False)
        plp.train(pairs)
        
        self.assert_correct(plp, pairs)

    def test_rule_ordering_1(self):
        dd_pairs = [('lændd', 'lændɪd'), ('saʊndd', 'saʊndɪd'), ('foʊldd', 'foʊldɪd'), ('hɛdd', 'hɛdɪd'), ('ɪkstɛndd', 'ɪkstɛndɪd'), ('klaʊdd', 'klaʊdɪd'), ('plidd', 'plidɪd')]
        td_pairs = [('ʃaʊtd', 'ʃaʊtɪd'), ('mɛltd', 'mɛltɪd'), ('pɔɪntd', 'pɔɪntɪd'), ('kɑmpləkeɪtd', 'kɑmpləkeɪtɪd'), ('maʊntd', 'maʊntɪd')]
        t_pairs = [('pʌfd', 'pʌft'), ('drɑpd', 'drɑpt'), ('mɪsd', 'mɪst'), ('nɑkd', 'nɑkt'), ('dʒʌmpd', 'dʒʌmpt'), ('wɔkd', 'wɔkt'), ('fɪksd', 'fɪkst'), ('bʌmpd', 'bʌmpt'), ('pɑpd', 'pɑpt'), ('kræʃd', 'kræʃt'), ('stæʃd', 'stæʃt'), ('grupd', 'grupt')]
        d_pairs = [('dæmd', 'dæmd'), ('ɑrgjud', 'ɑrgjud'), ('skaʊɝd', 'skaʊɝd'), ('hæmpstɛd', 'hæmpstɛd'), ('klaɪmd', 'klaɪmd'), ('jɑrd', 'jɑrd'), ('waɪld', 'waɪld'), ('kʌlɝd', 'kʌlɝd')]
        non_pairs = [('əndɝkʌvɝ', 'əndɝkʌvɝ'), ('ɪnfɔrmətɪv', 'ɪnfɔrmətɪv'), ('əræknɪdz', 'əræknɪdz'), ('kʌmɪŋ', 'kʌmɪŋ'), ('kaɪnd', 'kaɪnd'), 
                     ('bɑtəm', 'bɑtəm'), ('ɔlmoʊst', 'ɔlmoʊst'), ('rʌn', 'rʌn'), ('sɔrt', 'sɔrt'), ('bɪhaɪnd', 'bɪhaɪnd'), ('kʊki', 'kʊki'),
                     ('grændmɑ', 'grændmɑ'), ('saɪd', 'saɪd'), ('gɑtə', 'gɑtə'), ('seɪɪŋ', 'seɪɪŋ'),
                     ('wɑtʃ', 'wɑtʃ'), ('ʌm', 'ʌm'), ('traɪ', 'traɪ'), ('θæŋk', 'θæŋk'), ('fɝst', 'fɝst'), ('skul', 'skul'), ('kʌlɝ', 'kʌlɝ')]

        pairs = d_pairs + t_pairs + dd_pairs + non_pairs + td_pairs
        random.seed(0)
        random.shuffle(pairs)

        plp = PLP(verbose=False)
        plp.train(pairs)

        assert(len(plp.grammar) == 2)
        assert(plp.grammar[0].A.empty()) # epenthesis before devoicing

    def test_polish(self):
        pairs, _ = load('../data/polish/pol.txt', skip_header=True)
        plp = PLP(ipa_file='../data/polish/ipa.txt', verbose=False)
        plp.train(pairs)

        assert(len(plp.grammar) == 2)
        r1, r2 = plp.grammar[0], plp.grammar[1]
        assert(f'{r1.B}' == 'u')
        assert(f'{r1.C}' == '')
        assert(f'{r1.D}' == '{+voi}#')
        assert(r2 == '{+voi,-son} --> [-voi] /  __ #')

    def test_paper_ex(self):
        '''
        Test the running example used in the journal submission.
        '''
        pairs = [('dɑgz', 'dɑgz'), ('seɪfz', 'seɪfs'), ('mæpz', 'mæps'), ('hɔrsz', 'hɔrsəz'), ('kætz', 'kæts'), ('bɝdz', 'bɝdz'), ('wɛbz', 'wɛbz')]

        plp = PLP(nas_vowels=True, verbose=False)
        plp.train(pairs)
        assert(plp.discrepancies[('z', 's')] == 'z --> s / {f,p,t} __ ')

if __name__ == "__main__":
    unittest.main()