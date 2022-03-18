import errno
import os
import re
from pathlib import Path
from typing import Optional, List, Sequence, Any, Union

from nltk import ngrams


class SpellSuggestions(object):
    def __init__(self, is_correct: bool = False, suggestions: Optional[List[str]] = None):
        self.is_correct = is_correct
        self.suggestions = suggestions or []


def dameraulevenshtein(seq1: Sequence[Any], seq2: Sequence[Any]):
    """
    Calculate the Damerau-Levenshtein distance between sequences.

    This method has not been modified from the original.
    Source: http://mwh.geek.nz/2009/04/26/python-damerau-levenshtein-distance/

    This distance is the number of additions, deletions, substitutions,
    and transpositions needed to transform the first sequence into the
    second. Although generally used with strings, any sequences of
    comparable objects will work.

    Transpositions are exchanges of *consecutive* characters; all other
    operations are self-explanatory.

    This implementation is O(N*M) time and O(M) space, for N and M the
    lengths of the two sequences.

    >>> dameraulevenshtein('ba', 'abc')
    2
    >>> dameraulevenshtein('fee', 'deed')
    2

    It works with arbitrary sequences too:
    >>> dameraulevenshtein('abcd', ['b', 'a', 'c', 'd', 'e'])
    2

    Args:
       seq1 (str): word 1
       seq2 (str): word 2

    Returns:
        edit_distance (int): Damerau-Levenshtein distance
    """
    # Conceptually, this is based on a len(seq1) + 1 * len(seq2) + 1 matrix.
    # However, only the current and two previous rows are needed at once,
    # so we only store those.
    oneago = None
    thisrow = []
    for num in range(1, len(seq2) + 1):
        thisrow.append(num)
    thisrow += [0]
    for x in range(len(seq1)):
        # Python lists wrap around for negative indices, so put the
        # leftmost column at the *end* of the list. This matches with
        # the zero-indexed strings and saves extra calculation.
        twoago, oneago, thisrow = oneago, thisrow, [0] * len(seq2) + [x + 1]
        for y in range(len(seq2)):
            delcost = oneago[y] + 1
            addcost = thisrow[y - 1] + 1
            subcost = oneago[y - 1] + (seq1[x] != seq2[y])
            thisrow[y] = min(delcost, addcost, subcost)
            # This block deals with transpositions
            if x > 0 and y > 0 and seq1[x] == seq2[y - 1] and seq1[x - 1] == seq2[y] and seq1[x] != seq2[y]:
                thisrow[y] = min(thisrow[y], twoago[y - 2] + 1)
    return thisrow[len(seq2) - 1]


def batch(iterable, n=1):
    iter_len = len(iterable)
    for ndx in range(0, iter_len, n):
        yield iterable[ndx:min(ndx + n, iter_len)]


def get_ngrams(tokens, n):
    return list(ngrams(tokens, n))


def get_clean_text(sentence):
    clean_text = re.sub(r'[.,:;\"?\\]', ' ', str(sentence))
    clean_text = re.sub(r'{.*}', '', clean_text)
    return clean_text.strip()


def mkdirs(path: Union[str, Path], err_if_already_exists: bool = True) -> None:
    """
    Given a path to a directory, create the directory and all intermediate directories if they don't exist

    Args:
        path: path to some directory
        err_if_already_exists: whether to throw error if directory already exists

    Returns:
        None

    Raises:
        OSError: If the directory already exists

    """
    path = str(path)
    try:
        os.makedirs(path)
    except FileExistsError:
        if err_if_already_exists:
            raise
    except OSError as e:
        if e.errno == errno.EEXIST:
            if err_if_already_exists:
                raise
        else:
            raise
