import os
from segment import Segment
from natural_class import NaturalClass
from utils import SYLLABLE_BOUNDARY, UNKNOWN_CHAR, NASALIZED

class Alphabet:
    def __init__(self,
                 ipa_file='../data/ipa.txt',
                 segs=None,
                 add_segs=False,
                 nas_vowels=False):
        self.segments = set()
        self.nas_vowels = nas_vowels
        dir_path = os.path.dirname(os.path.realpath(__file__))

        self.seg_to_feats = dict()
        with open(f'{dir_path}/{ipa_file}', 'r') as f:
            for i, line in enumerate(f):
                line = line.strip().split('\t')
                seg, feats = line[0], line[1:]
                if i == 0:
                    self.feature_space = feats
                else:
                    self.seg_to_feats[seg] = feats

        self.seg_to_feats[UNKNOWN_CHAR] = ['?'] * len(self.feature_space)

        self.ipa_to_segment = dict()
        self.feats_to_segment = dict()

        if segs:
            self.add_segments(segs)
        if add_segs:
            segs = set(self.seg_to_feats.keys())
            self.add_segments(segs)

        self.add_segment(UNKNOWN_CHAR)

    def add_segment(self, ipa_seg):
        if ipa_seg in self:
            return True
        if ipa_seg == SYLLABLE_BOUNDARY:
            return False
        feature_vec = self.seg_to_feats[ipa_seg]
        seg = Segment(ipa_seg, feature_vec)
        self.segments.add(seg)
        self.feats_to_segment[seg._hashable] = seg
        self.ipa_to_segment[f'{seg}'] = seg
        if self.nas_vowels: # add nasal versions of vowel segments
            self.add_nas_vowel(ipa_seg)
        return True

    def add_segments(self, segments):
        for ipa in segments:
            self.add_segment(ipa)

    def add_segments_from_str(self, s):
        for i in range(len(s)):
            seg = s[i]
            if seg == NASALIZED: # skip nasalization unicode symbols 
                continue
            self.add_segment(seg)

    def add_nas_vowel(self, seg):
        '''
        Ads a nasalized version of :seg: if :seg: is a vowel.

        :seg: a segment to be nasalized, if it is a vowel and does not already have a nasalized version in the alphabet
        '''
        if self.get_val(seg, 'cons') == '-' and self.get_val(seg, 'nas') != '+':
            feature_vec = list(self.seg_to_feats[seg])
            feature_vec[self.feature_space.index('nas')] = '+'
            nas_seg = Segment(f'{seg}{NASALIZED}', feature_vec)
            self.segments.add(nas_seg)
            self.feats_to_segment[nas_seg._hashable] = nas_seg
            self.ipa_to_segment[f'{seg}{NASALIZED}'] = nas_seg

    def add_nas_vowels(self):
        '''
        Creates a nasalized version of every vowel currently in the alphabet. 
        '''
        for seg in list(self.segments):
            self.add_nas_vowel(seg)

    def _add_or_remove_feats(self, seg, feats, add=True):
        '''
        :seg: a segment (in any format supported by __getitem__)
        :feats: a feature (string) or iterable of features (e.g., list of strings)

        :return: the segment with the same features as :seg: plus/minus those in :feats:, if such a segment exists 
        '''
        seg = self[seg]
        if type(feats) is str:
            feats = (feats,)
        if not add and not all(seg.feature_vec[self.feature_space.index(feat)] for feat in feats):
            return None
        new_feat_vec = list(seg.feature_vec)
        for feat in feats:
            feat_index = self.feature_space.index(feat)
            new_feat_vec[feat_index] = '+' if add else '-'
        if new_feat_vec not in self:
            return None
        if new_feat_vec == list(seg.feature_vec): # if the vector is unchanged, return None
            return None
        return self[new_feat_vec]

    def without_feats(self, seg, feats):
        '''
        :seg: a segment (in any format supported by __getitem__)
        :feats: a feature (string) or iterable of features (e.g., list of strings)

        :return: the segment with the same features as :seg: but not those in :feats:, if such a segment exists 
        '''
        return self._add_or_remove_feats(seg, feats, add=False)

    def with_feats(self, seg, feats):
        '''
        :seg: a segment (in any format supported by __getitem__)
        :feats: a feature (string) or iterable of features (e.g., list of strings)

        :return: the segment with the same features as :seg: and those in :feats:, if such a segment exists 
        '''
        return self._add_or_remove_feats(seg, feats, add=True)

    def set_feats(self, seg, feats, vals):
        '''
        :seg: a segment (in any format supported by __getitem__)
        :feats: an iterable of features (e.g., list of strings)
        :vals: an iterable of values (e.g., list of values) - must be the same length as :feats:

        :return: the segment with the same features as :seg: and those in :feats: set to :vals:, if such a segment exists
        '''
        if len(feats) != len(vals):
            raise ValueError(f'Length of :feats: and :vals: must be equal, but are |feats| = {len(feats)} and |vals| = {len(vals)}')
        seg = self[seg]
        new_feat_vec = list(seg.feature_vec)
        for feat, val in zip(feats, vals):
            feat_idx = self.feature_space.index(feat)
            new_feat_vec[feat_idx] = val
        if new_feat_vec not in self:
            return None
        return self[new_feat_vec]

    def __getitem__(self, key):
        '''
        :key: Can be any of the following:
            - A hashable, which is a string of comma-separated binary features characterizing the segment
            - A string IPA representation of the segment
            - A list of binary features characterizing the segment
            - A Segment object

        :return: the Segment object corresponding to the :key: if present, otherwise None
        '''
        typ = type(key)
        if typ is str and ',' not in key and key in self.ipa_to_segment:
            return self.ipa_to_segment[key]
        elif typ is Segment:
            return self[f'{key}']
        elif typ is str and ',' in key and key in self.feats_to_segment:
            return self.feats_to_segment[key]
        elif typ is list:
            return self[','.join(str(f) for f in key)]

        # otherwise, raise an error
        raise KeyError(f'"{key}" is not in the alphabet.')


    def __contains__(self, item):
        '''
        :item: Can be any of the following:
            - A hashable, which is a string of comma-separated binary features characterizing the segment
            - A string IPA representation of the segment
            - A list of binary features characterizing the segment
            - A Segment object

        :return: True if the :item: (segment) is in the alphabet, False if not
        '''
        typ = type(item)
        if typ is str and ',' not in item:
            return item in self.ipa_to_segment
        elif typ is Segment:
            return f'{item}' in self
        elif typ is str and ',' in item:
            return item in self.feats_to_segment
        elif typ is list:
            return ','.join(str(f) for f in item) in self
        return False

    def __str__(self):
        return ','.join(sorted(self.ipa_to_segment.keys()))

    def __repr__(self):
        return self.__str__()

    def __iter__(self):
        return self.segments.__iter__()

    def extension(self, nat_class):
        '''
        :nat_class: a set of features or a NaturalClass object

        :return: Extension(:nat_class:)
        '''
        if type(nat_class) is set:
            nat_class = NaturalClass(nat_class, self)
        return set(filter(lambda seg: seg in nat_class, self.segments))

    def extension_complement(self, nat_class):
        '''
        :nat_class: a set of features or a NaturalClass object

        :return: self.segments \ Extension(:nat_class:)
        '''
        if type(nat_class) is set:
            nat_class = NaturalClass(nat_class, self)
        return set(filter(lambda seg: seg not in nat_class, self.segments))

    def complement(self, segs):
        '''
        :segs: an iterable of segments

        :return: self.segments \ segs
        '''
        return self.segments.difference(segs)

    def feat_vals(self, seg, exclude_unspec=False):
        '''
        :seg: a segment (in any format supported by __getitem__)
        :exclude_unspec: if True, excludes features for which :seg: is unspecified

        :return: a set of the features, marked with their values for :seg: (e.g., {+cons, -ant, ?back, ...})
        '''
        seg = self[seg]
        if exclude_unspec:
            return set(filter(lambda feat: feat[0] != '?', set(f'{seg.feature_vec[i]}{feat}' for i, feat in enumerate(self.feature_space))))
        return set(f'{seg.feature_vec[i]}{feat}' for i, feat in enumerate(self.feature_space))

    def plus(self, seg):
        '''
        :seg: a segment (in any format supported by __getitem__)

        :return: a set of features that this seg has '+' for
        '''
        return set(filter(lambda feat: feat[0] == '+', self.feat_vals(seg)))

    def shared_feats(self, segs, exclude_unsepc=True):
        '''
        :segs: an iterable of segments

        :return: the features shared by the :segs:
        '''
        return set.intersection(*list(self.feat_vals(seg, exclude_unspec=exclude_unsepc) for seg in segs))

    def feat_diff(self, seg1, seg2):
        diff = set()
        seg1, seg2 = self[seg1], self[seg2]
        for i, feat in enumerate(self.feature_space):
            if seg1.feature_vec[i] != seg2.feature_vec[i]:
                diff.add(feat)
        return diff

    def get_val(self, seg, feat):
        '''
        :seg: a segment (in any format supported by __getitem__)
        :feat: a feature

        :return: the value of :feat: for :seg:
        '''
        seg = self[seg]
        return seg.feature_vec[self.feature_space.index(feat)]