from natural_class import NaturalClass
from segment import Segment

from utils import PRIMARY_STRESS, SECONDARY_STRESS, WORD_BOUNDARY, SYLLABLE_BOUNDARY, NASALIZED

class Sequence:
    '''
    A class representing a sequence of Segments, sets of Segments, or Natural Classes.

    For instance, in {+voice} / [-voice] __ #, {+voice} is a natural class, and "#" is a segment. 
    Both of these components can be a sequence.

    Similarly, in aʊ --> ʌʊ /  __ t, "aʊ" and "ʌʊ" are sequences of Segments.

    Also handles wildcards, '*'
    '''
    def __init__(self, seq, alphabet=None):
        self.alphabet = alphabet
        if type(seq) == str:
            if alphabet is None:
                seq = list(seq)
            else:
                temp = str(seq)
                seq = list()
                for i in range(len(temp)):
                    if temp[i] not in {PRIMARY_STRESS, SECONDARY_STRESS, WORD_BOUNDARY, SYLLABLE_BOUNDARY, '\u0303'}:
                        seq.append(alphabet[temp[i]])
                    elif temp[i] in {WORD_BOUNDARY, SYLLABLE_BOUNDARY}:
                        seq.append(Segment(temp[i]))
                    elif temp[i] == f'{NASALIZED}': # nasalized
                        seq[-1] = alphabet.with_feats(seq[-1], 'nas')
                    else:
                        seq[-1] = alphabet[f'{seq[-1]}{temp[i]}']
                        seq[-1].set_stress(temp[i])
        elif type(seq) == Segment:
            assert(len(seq) == 1)
            seq = [seq]
        self.seq = seq

    def copy(self):
        return Sequence(list(self.seq), self.alphabet)

    def __len__(self):
        return len(self.seq)

    def __str__(self):
        s = ''
        for seg in self.seq:
            if type(seg) is set:
                s += '{'
                for i, _seg in enumerate(sorted(seg)):
                    if i > 0:
                        s += ','
                    s += f'{_seg}'
                s += '}'
            else:
                s += f'{seg}'
        return s

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if type(other) is str:
            return f'{self}' == other
        if type(other) is Segment:
            return f'{self}' == f'{other}'
        if len(self) != len(other):
            return False
        for seg, other_seg in zip(self.seq, other if type(other) is not Sequence else other.seq):
            if seg != other_seg:
                return False
        return True

    def __neq__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        return self.__str__() < other.__str__()

    def __getitem__(self, idx):
        res = self.seq.__getitem__(idx)
        if len(res) == 1 and type(idx) is int:
            return res
        if type(res) is NaturalClass and type(idx) is int:
            return res
        return Sequence(res)

    def __setitem__(self, idx, val):
        self.seq[idx] = val

    def __iter__(self):
        return self.seq.__iter__()

    def __hash__(self):
        return hash(self.__str__())

    def windows(self, i, k):
        '''
        :return: all windows of length k around pos i in s (including i in the length).
        '''
        _windows = set()
        for left in reversed(range(k)): # k - 1, ..., 0
            right = k - 1 - left
            left_idx = i - left
            right_idx = i + right

            if right_idx > len(self):
                break

            C = Sequence(list())
            D = Sequence(list())
            for idx in range(left_idx, right_idx + 1):
                if idx < -1 or idx > len(self):
                    continue
                if idx == -1:
                    C += '#'
                elif idx == len(self):
                    D += '#'
                elif idx < i:
                    C += self[idx]
                elif idx > i:
                    D += self[idx]
            _windows.add((C, D))
        return sorted(_windows, key=lambda it: (it[0].__str__(), it[1].__str__()))

    def __iadd__(self, other):
        if type(other) is str:
            self.seq += [other]
        elif type(other) is Segment:
            self.seq += [other]
        else:
            assert(type(other) is Sequence)
            self.seq += list(other.seq)
        return self

    def __add__(self, other):
        if type(other) is str:
            return self.seq + [other]
        elif type(other) is Segment:
            return self.seq + [other.ipa]
        assert(type(other) is Sequence)
        return self.seq + list(other.seq)

    def matches(self, seq):
        if len(self) != len(seq):
            return False
        for seg, other_seg in zip(self.seq, seq):
            if seg == '*':
                continue
            typ = type(seg)
            if typ is str and seg != other_seg:
                return False
            elif typ is Segment and seg != other_seg:
                return False
            elif typ is set and other_seg not in seg:
                return False
            elif typ is NaturalClass and other_seg not in seg:
                return False
        return True

    def merge(self, other):
        if len(self) > 1 or len(other) > 1:
            raise ValueError('Can only merge sequences of length 1.')
        if 0 == len(self) == len(other): # merging len-0 sequences is trivial
            return
        new_seg = set()
        if type(self.seq[0]) is str or type(self.seq[0]) is Segment:
            new_seg.add(self.seq[0])
        else:
            new_seg.update(self.seq[0])
        if type(other.seq[0]) is str or type(other.seq[0]) is Segment:
            new_seg.add(other.seq[0])
        else:
            new_seg.update(other.seq[0])
        self.seq[0] = new_seg

    def count(self, item):
        c = 0
        for seg in self.seq:
            if seg == item:
                c += 1
        return c

    def to_natural_classes(self, segments=True):
        if not self.alphabet:
            raise ValueError('Cannot construct Natural Classes without an alphabet.')
        for idx in range(len(self.seq)):
            seg = self.seq[idx]
            if type(seg) is str or type(seg) is Segment:
                if segments:
                    self.seq[idx] = NaturalClass(self.alphabet.shared_feats({seg}), self.alphabet)
            elif type(seg) is set:
                self.seq[idx] = NaturalClass(self.alphabet.shared_feats(seg), self.alphabet)
