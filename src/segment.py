from natural_class import NaturalClass

class Segment:
    def __init__(self, ipa, feature_vec=[]):
        self.ipa = ipa
        self.feature_vec = feature_vec
        self._str = ipa
        self._hashable = ','.join(str(f) for f in self.feature_vec)

    def __eq__(self, other):
        if type(other) is Segment:
            return hash((self.ipa, self._hashable)) == hash((other.ipa, other._hashable))
        if type(other) is NaturalClass:
            return False
        if type(other) is str or type(other) is set:
            return self.ipa == other
        if len(other) == 1: # other should be a Sequence
            return self == other[0]
        assert(False)

    def __neq__(self, other):
        return not self.__eq__(other)

    def __gt__(self, other):
        return self.ipa.__gt__(other if type(other) is str else other.ipa)

    def __ge__(self, other):
        return self.ipa.__ge__(other if type(other) is str else other.ipa)

    def __lt__(self, other):
        return self.ipa.__lt__(other if type(other) is str else other.ipa)

    def __le__(self, other):
        return self.ipa.__le__(other if type(other) is str else other.ipa)

    def __hash__(self):
        return hash(self.ipa)

    def __str__(self):
        return self._str

    def __repr__(self):
        return self.__str__()

    # overload string functions
    def __len__(self):
        return 1

    def __iter__(self):
        return self.ipa[0].__iter__()

    def count(self, val):
        return self.ipa.count(val)

    def __getitem__(self, idx):
        return self.ipa[idx]