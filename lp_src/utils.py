WORD_BOUNDARY = '#'
SYLLABLE_BOUNDARY = '.'
PRIMARY_STRESS = 'ˈ'
SECONDARY_STRESS = 'ˌ'
LONG = 'ː'
NASALIZED = '\u0303'
EMPTY_STRING = 'λ'
UNKNOWN_CHAR = '?'

from collections import defaultdict
from itertools import chain, combinations
import numpy as np
from scipy.spatial.distance import hamming

def load(fname, sep='\t', skip_header=False, alphabet=False):
    pairs = list()
    freqs = list()
    with open(fname, 'r') as f:
        if skip_header:
            next(f)
        for line in f:
            line = line.strip().split(sep)
            line_length = len(line)
            if line_length == 2:
                uf, sf = line
                freq = 0
            if line_length == 3:
                uf, sf, freq = line
            elif line_length == 4:
                _, uf, sf, freq = line
            freq = float(freq)
            pairs.append((uf, sf))
            freqs.append(freq)
    if alphabet:
        _alph = set()
        for uf, sf in pairs:
            for i in range(len(uf)):
                seg = uf[i]
                _alph.add(seg)
                if i + 1 < len(uf) and uf[i + 1] in {PRIMARY_STRESS, SECONDARY_STRESS}:
                    _alph.add(f'{seg}{uf[i+1]}')
            for i in range(len(sf)):
                seg = sf[i]
                _alph.add(seg)
                if i + 1 < len(sf) and sf[i + 1] in {PRIMARY_STRESS, SECONDARY_STRESS}:
                    _alph.add(f'{seg}{sf[i+1]}')
        return pairs, freqs, _alph
    return pairs, freqs

def tolerance_principle(n, c, e=None):
    if n == c:
        return True
    if e == None:
        e = n - c
    return c > 2 and c > n / 2 and e <= n / np.log(n)

def epsilon(n, c, eps=0.99):
    if n == c:
        return True
    return c > 2 and c / n >= eps

def sufficiency_principle(n, m):
    return n - m < n / np.log(n) and m > n / 2

def identity_accuracy(test_path):
    t, c, = 0, 0
    for line in open(test_path, 'r'):
        uf, sf = line.strip().split('\t')
        pred = uf
        if sf == pred:
            c += 1
        t += 1
    return c / t if t > 0 else 0

def hd(w1, w2):
    w1, w2 = list(w1), list(w2)
    while len(w1) > len(w2):
        w2 = ['0'] + w2
    while len(w1) < len(w2):
        w1 = ['0'] + w1
    return hamming(w1, w2)

def powerset(iterable, smallest=0, largest=None, proper_subset_only=False):
    '''
    Adapted From: https://stackoverflow.com/questions/1482308/how-to-get-all-subsets-of-a-set-powerset
    '''
    s = list(iterable)
    if largest == None:
        largest = len(s) + 1 if not proper_subset_only else len(s)
    return set(chain.from_iterable(combinations(s, r) for r in range(smallest, largest)))

def most_freq(l):
    item_to_count = defaultdict(int)
    for item in l:
        item_to_count[item] += 1
    argmax = None
    max_val = -1000
    for item, count in item_to_count.items():
        if count > max_val:
            argmax = item
            max_val = count
    return argmax

def windows(s, i, k, split=False):
    '''
    :return: all windows of length k around pos i in s (including i in the length).
    '''
    ws = set()
    for left in reversed(range(k)): # k - 1, ..., 0
        right = k - 1 - left
        left_idx = i - left
        right_idx = i + right

        if right_idx > len(s):
            break

        w = ''
        for idx in range(left_idx, right_idx + 1):
            if idx < -1 or idx > len(s):
                continue
            if idx == -1 or idx == len(s):
                w += '#'
            else:
                if idx == i and split:
                    w += '~~~'
                else:
                    w += s[idx]
        if split:
            ws.add(tuple(w.split('~~~')))
        else:
            ws.add(w)
    return sorted(ws)

def insert_empty(s, k=1):
    options = list()
    e = EMPTY_STRING
    new = [''] * (len(s) + k)
    choices = list(range(len(new)))
    for idxs in combinations(choices, k):
        j = 0
        for i in range(len(new)):
            if i in idxs:
                new[i] = e
            else:
                new[i] = s[j]
                j += 1
        options.append(''.join(new))
    return options

def align_blanks(s1, s2, return_ties=False):
    '''
    Add blanks ('EMPTY_STRING'), so that s1 and s2 are optimaly aligned and of the same length.
    Assumes that len(s1) < len(s2).
    '''
    delta = len(s2) - len(s1)
    options = sorted(insert_empty(s1, k=delta), key=lambda op: (hd(op, s2), op.index(EMPTY_STRING)))
    if return_ties and len(options) > 1:
        res = [options[0]]
        i = 1
        while i < len(options) and hd(options[i], s2) == hd(options[0], s2):
            res.append(options[i])
            i += 1
        return res
    return options[0]
