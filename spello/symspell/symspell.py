"""
LICENSES
===
https://github.com/ppgmg/github_public/blob/master/spell/symspell_python.py
---
This program is free software; you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License,
version 3.0 (LGPL-3.0) as published by the Free Software Foundation.
http://www.opensource.org/licenses/LGPL-3.0
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU General Public License for more details.
Please acknowledge Wolf Garbe, as the original creator of SymSpell,
(see note below) in any use.


https://github.com/wolfgarbe/SymSpell
---
MIT License

Copyright (c) 2018 Wolf Garbe

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import logging
import re
from timeit import default_timer as timer

from spello.utils import dameraulevenshtein, SpellSuggestions

spellcorrection_logger = logging.getLogger('spellcorrection')


class SymSpell:
    # TODO: remove `verbose` as argument as it can be configured via `config`
    def __init__(self, config, max_edit_distance=3, script="en"):
        """
        SymSpell is Symmetric Delete spelling correction algorithm

        SymSpell Algorithm resources :-
        https://github.com/wolfgarbe/SymSpell
        https://medium.com/@wolfgarbe/1000x-faster-spelling-correction-algorithm-2012-8701fcd87a5f

        Generate terms with an edit distance (deletes only) from each dictionary term and add them together
        with the original term to the dictionary. This is done only during model creation.
        Generate terms with an edit distance (deletes only) from the input term and searches them in the dictionary.

        It is language independent since it relies only on deletes instead of transposes + replaces + inserts + deletes

        Args:
            max_edit_distance (int): max edit distance
            script (str): language script
        """
        self.max_edit_distance = max_edit_distance
        self.dictionary = {}
        self.longest_word_length = 0
        self.script = script
        self.config = config

    @staticmethod
    def get_deletes_list(w):
        """
        Given a word, derive strings with up to max_edit_distance characters deleted

        Args:
            w (str): word for which we need to derive strings with up to max_edit_distance characters deleted

        Returns:
            deletes (list): list of words
        """
        deletes = []
        queue = [w]

        if len(w) <= 2:
            return [w]
        elif len(w) == 3:
            max_edit_distance = 1
        elif 4 <= len(w) < 6:
            max_edit_distance = 2
        elif 6 <= len(w) < 15:
            max_edit_distance = 3
        else:
            return [w]
        for d in range(max_edit_distance):
            temp_queue = []
            for word in queue:
                if len(word) > 1:
                    for c in range(len(word)):  # character index
                        word_minus_c = word[:c] + word[c + 1:]
                        if word_minus_c not in deletes:
                            deletes.append(word_minus_c)
                        if word_minus_c not in temp_queue:
                            temp_queue.append(word_minus_c)
            queue = temp_queue
        return deletes

    def create_dictionary_entry(self, w, count=None):
        """
        Add word and its derived deletions to dictionary

        Args:
            w (str): word for which we need to derive strings with up to max_edit_distance characters deleted
            count (int): count of word in corpus
        Returns:
            new_real_word_added (bool): whether word was added to dictionary i.e. first appearance of word in corpus
        """
        # check if word is already in dictionary
        # dictionary entries are in the form: (list of suggested corrections,
        # frequency of word in corpus)
        new_real_word_added = False
        if w in self.dictionary:
            # increment count of word in corpus
            if count:
                self.dictionary[w] = (self.dictionary[w][0], count)
            else:
                self.dictionary[w] = (self.dictionary[w][0], self.dictionary[w][1] + 1)
        else:
            self.dictionary[w] = ([], count)
            self.longest_word_length = max(self.longest_word_length, len(w))

        if self.dictionary[w][1] > 0:
            # first appearance of word in corpus
            # n.b. word may already be in dictionary as a derived word
            # (deleting character from a real word)
            # but counter of frequency of word in corpus is not incremented
            # in those cases)
            new_real_word_added = True
            deletes = self.get_deletes_list(w)
            for item in deletes:
                if item in self.dictionary:
                    # add (correct) word to delete's suggested correction list
                    self.dictionary[item][0].append(w)
                else:
                    # note frequency of word in corpus is not incremented
                    self.dictionary[item] = ([w], 0)

        return new_real_word_added

    def create_dictionary_from_sentences(self, lines):
        """
        Create dictionary from list of sentences

        Args:
            lines (list): list of sentences

        Returns:
            dictionary (dict): spell check dictionary
        """
        total_word_count = 0
        unique_word_count = 0
        start_time = timer()
        spellcorrection_logger.info("Creating spell check dictionary...")
        punctuation = r""",+:?!"()!'.%[]"""
        pattern = re.compile(re.escape(punctuation))
        for line in lines:
            line = pattern.sub(' ', line.lower().strip())
            words = line.lower().strip().split()
            for word in words:
                total_word_count += 1
                if self.create_dictionary_entry(word):
                    unique_word_count += 1
        run_time = timer() - start_time
        spellcorrection_logger.info("%.2f seconds to run" % run_time)
        spellcorrection_logger.info("total words processed: %i" % total_word_count)
        spellcorrection_logger.info("total unique words in corpus: %i" % unique_word_count)
        spellcorrection_logger.info("total items in dictionary (corpus words & deletions): %i" % len(self.dictionary))
        spellcorrection_logger.info("edit distance for deletions: %i" % self.max_edit_distance)
        spellcorrection_logger.info("length of longest word in corpus: %i" % self.longest_word_length)
        return self.dictionary

    def create_dictionary_from_words(self, words_counter):
        """
        Create dictionary from list of sentences

        Args:
            words_counter (dict): dict with word and their count

        Returns:
            dictionary (dict): spell check dictionary
        """
        total_word_count = 0
        unique_word_count = 0
        start_time = timer()
        spellcorrection_logger.info("Creating spell check dictionary...")

        for word, count in words_counter.items():
            total_word_count += 1
            if self.create_dictionary_entry(word, count):
                unique_word_count += 1
        run_time = timer() - start_time
        spellcorrection_logger.info("%.2f seconds to run" % run_time)
        spellcorrection_logger.info("total words processed: %i" % total_word_count)
        spellcorrection_logger.info("total unique words in corpus: %i" % unique_word_count)
        spellcorrection_logger.info("total items in dictionary (corpus words & deletions): %i" % len(self.dictionary))
        spellcorrection_logger.info("edit distance for deletions: %i" % self.max_edit_distance)
        spellcorrection_logger.info("length of longest word in corpus: %i" % self.longest_word_length)
        return self.dictionary

    def get_suggestions(self, string, silent=False):
        """
        Return list of suggested corrections for potentially incorrectly spelled word

        Option 1:
        ['file', 'five', 'fire', 'fine', ...]

        Option 2:
        [('file', (5, 0)),
         ('five', (67, 1)),
         ('fire', (54, 1)),
         ('fine', (17, 1))...]

        Args:
            string (str): word which needs to be corrected
            silent (bool): if silent is True, then logs won't be printed

        Returns:
            outlist (list): output list
        """
        if (len(string) - self.longest_word_length) > self.max_edit_distance:
            if not silent:
                spellcorrection_logger.info("no items in dictionary within maximum edit distance")
            return []

        suggest_dict = {}
        min_suggest_len = float('inf')

        queue = [string]
        q_dictionary = {}  # items other than string that we've checked

        while len(queue) > 0:
            q_item = queue[0]  # pop
            queue = queue[1:]

            # early exit
            if ((self.config.symspell_verbosity < 2) and (len(suggest_dict) > 0) and
                    ((len(string) - len(q_item)) > min_suggest_len)):
                break

            # process queue item
            if (q_item in self.dictionary) and (q_item not in suggest_dict):
                if self.dictionary[q_item][1] > 0:
                    # word is in dictionary, and is a word from the corpus, and
                    # not already in suggestion list so add to suggestion
                    # dictionary, indexed by the word with value (frequency in
                    # corpus, edit distance)
                    # note q_items that are not the input string are shorter
                    # than input string since only deletes are added (unless
                    # manual dictionary corrections are added)
                    assert len(string) >= len(q_item)
                    suggest_dict[q_item] = (self.dictionary[q_item][1],
                                            len(string) - len(q_item))
                    # early exit
                    if (self.config.symspell_verbosity < 2) and (len(string) == len(q_item)):
                        break
                    elif (len(string) - len(q_item)) < min_suggest_len:
                        min_suggest_len = len(string) - len(q_item)

                # the suggested corrections for q_item as stored in
                # dictionary (whether or not q_item itself is a valid word
                # or merely a delete) can be valid corrections
                for sc_item in self.dictionary[q_item][0]:
                    if sc_item not in suggest_dict:

                        # compute edit distance
                        # suggested items should always be longer
                        # (unless manual corrections are added)
                        assert len(sc_item) > len(q_item)

                        # q_items that are not input should be shorter
                        # than original string
                        # (unless manual corrections added)
                        assert len(q_item) <= len(string)

                        if len(q_item) == len(string):
                            assert q_item == string
                            # item_dist = len(sc_item) - len(q_item)

                        # item in suggestions list should not be the same as
                        # the string itself
                        assert sc_item != string

                        # calculate edit distance using, for example,
                        # Damerau-Levenshtein distance
                        item_dist = dameraulevenshtein(sc_item, string)

                        # do not add words with greater edit distance if
                        # verbose setting not on
                        if (self.config.symspell_verbosity < 2) and (item_dist > min_suggest_len):
                            pass
                        elif item_dist <= self.max_edit_distance:
                            assert sc_item in self.dictionary  # should already be in dictionary if in suggestion list
                            suggest_dict[sc_item] = (self.dictionary[sc_item][1], item_dist)
                            if item_dist < min_suggest_len:
                                min_suggest_len = item_dist

                        # depending on order words are processed, some words
                        # with different edit distances may be entered into
                        # suggestions; trim suggestion dictionary if verbose
                        # setting not on
                        if self.config.symspell_verbosity < 2:
                            suggest_dict = {k: v for k, v in suggest_dict.items() if v[1] <= min_suggest_len}

            # now generate deletes (e.g. a substring of string or of a delete)
            # from the queue item
            # as additional items to check -- add to end of queue
            assert len(string) >= len(q_item)

            # do not add words with greater edit distance if verbose setting
            # is not on
            if (self.config.symspell_verbosity < 2) and ((len(string) - len(q_item)) > min_suggest_len):
                pass
            elif (len(string) - len(q_item)) < self.max_edit_distance and len(q_item) > 1:
                for c in range(len(q_item)):  # character index
                    word_minus_c = q_item[:c] + q_item[c + 1:]
                    if word_minus_c not in q_dictionary:
                        queue.append(word_minus_c)
                        q_dictionary[word_minus_c] = None  # arbitrary value, just to identify we checked this

        # queue is now empty: convert suggestions in dictionary to
        # list for output
        if not silent and self.config.symspell_verbosity != 0:
            spellcorrection_logger.info("number of possible corrections: %i" % len(suggest_dict))
            spellcorrection_logger.info("edit distance for deletions: %i" % self.max_edit_distance)

        # output option 1
        # sort results by ascending order of edit distance and descending
        # order of frequency
        #     and return list of suggested word corrections only:
        # return sorted(suggest_dict, key = lambda x:
        #               (suggest_dict[x][1], -suggest_dict[x][0]))

        # output option 2
        # return list of suggestions with (correction,
        #                                  (frequency in corpus, edit distance)):
        as_list = list(suggest_dict.items())
        # e.g. [('a', (3, 1)), ('b', (2, 1)), ('c', (5, 2))]
        # outlist = sorted(as_list, key=lambda (term, (freq, dist)): (dist, -freq))
        outlist = sorted(as_list, key=lambda suggestion_tuple: (suggestion_tuple[1][1], -suggestion_tuple[1][0]))

        if self.config.symspell_verbosity == 0:
            return outlist[0]
        else:
            return outlist

    def load_dictionary_data(self, dictionary_data):
        """
        Load dictionary data from dict

        Args:
            dictionary_data (dict): dict containing max_edit_distance, longest_word_length, dictionary and script keys

        Returns:
            None
        """
        if not dictionary_data:
            raise ValueError("dictionary_data is empty")

        if type(dictionary_data) != dict:
            raise TypeError("dictionary_data should be a dict")

        self.max_edit_distance = dictionary_data["max_edit_distance"]
        self.longest_word_length = dictionary_data["longest_word_length"]
        self.dictionary = dictionary_data["dictionary"]
        self.script = dictionary_data["script"]

    def get_dictionary_data(self):
        """
        Get dictionary data

        Returns:
            dictionary_data (dict): dict containing max_edit_distance, longest_word_length, dictionary and script keys

        """
        dictionary_data = {
            "max_edit_distance": self.max_edit_distance,
            "longest_word_length": self.longest_word_length,
            "dictionary": self.dictionary,
            "script": self.script
        }
        return dictionary_data

    def spell_correct(self, word):
        """
        Suggesting word from dictionary using below logic
        - if word exists in dictionary having count > 0 , return None
        - else
            - get suggestions list

                - if len(word) == 3,
                   - allow only 1 edit distance words

                - if 4 <= len(word) <= 5,
                    - allow all 1 edit distance words
                    - allow 2 edit word
                        - if first and last character of word and suggested word are same
                        - first letter of both are same

                - if 6 <= len(word) <=8:
                    - allow all upto 2 edit distance
                    - allow 3 edit word
                      - if first and last character of word and suggested word are same
                      - first letter of both are same

                - if len(word) >= 9:
                    - allow all word upto 3 edit distance
        Args:
            word (str): word to be corrected
        Returns:
            (SpellSuggestions): Spell suggestions instance with keys
                                is_correct: whether given spelling is correct
                                suggestions: List of tuples with words and their edit distance

        Examples:
            >>> word = 'ablee'
            >>> SymSpell().spell_correct(word)
            SpellSuggestions(is_correct=False, suggestions=[('able', 1), ('bleed', 2)])
        """

        spell_suggestions = SpellSuggestions(is_correct=False, suggestions=[])

        value = self.dictionary.get(word)
        if value and value[1] > 0:
            spell_suggestions.is_correct = True
            return spell_suggestions

        _suggestions = self.get_suggestions(word)
        if _suggestions:
            word_len = len(word)
            edit_distance_allowed = self.config.symspell_allowed_distance_map[word_len]
            suggestions = [(w, meta[1]) for w, meta in _suggestions if meta[1] <= edit_distance_allowed]

            if self.config.allow_1_extra_edit_for_char_end:
                edit_distance = edit_distance_allowed + 1
                for w, meta in _suggestions:
                    if w not in suggestions and w[0] == word[0] and meta[1] <= edit_distance:
                        suggestions.append((w, meta[1]))

            if self.config.allow_1_extra_edit_for_char_start:
                edit_distance = edit_distance_allowed + 1
                for w, meta in _suggestions:
                    if w not in suggestions and w[-1] == word[-1] and meta[1] <= edit_distance:
                        suggestions.append((w, meta[1]))

            spell_suggestions.suggestions = suggestions

        return spell_suggestions
