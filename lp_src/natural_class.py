from utils import PRIMARY_STRESS, SECONDARY_STRESS, SYLLABLE_BOUNDARY

class NaturalClass:
    def __init__(self, feats, alphabet, params=None):
        self.feats = set(feats)
        self.alphabet = alphabet
        self.params = params
        self._update()

    def segments(self):
        segs = set()
        for seg in self.alphabet.segments:
            if seg == '_':
                continue
            if seg in self:
                segs.add(seg)
        return segs

    def _update(self):
        self.name = '{' + ','.join(sorted(self.feats)) + '}'
        self.extension_str = '{' + ','.join(sorted(f'{seg}' for seg in self.alphabet.extension(self))) + '}'

    def add_feat(self, feat):
        self.feats.add(feat)
        self._update()

    def remove_feat(self, feat):
        self.feats.discard(feat)
        self._update()

    def __str__(self):
        return self.name if self.params is None or self.params.NC_AS_FEATURES else self.extension_str

    def __repr__(self):
        return self.__str__()

    def __contains__(self, item):
        if item == '#' or item == SYLLABLE_BOUNDARY:
            return False
        return self.alphabet.feat_vals(f'{item}').intersection(self.feats) == self.feats

    def __len__(self):
        return len(self.feats)

    def copy(self):
        return NaturalClass(self.feats, self.alphabet, self.params)