from collections import defaultdict
from itertools import repeat

from spello.utils import dameraulevenshtein, SpellSuggestions
from spello.phoneme.constant import (
    indic_char_map,
    indic_language_chars
)
import operator


class PhonemeModel(object):
    indic_languages = list(indic_language_chars.keys())
    supported_languages = indic_languages + ['en']

    def __init__(self, config, script, phoneme_dict=None):
        self.phoneme_dict = phoneme_dict
        self.script = script
        self.config = config

    @staticmethod
    def get_latin_soundex(token):
        """
        Get the phoneme code for the latin word
        Args:
            token: word
        Returns:
            (str): soundex code
        Examples:
            >>> token = 'availability'
            >>> PhonemeModel().get_latin_soundex(token)
            'A181870000'
        """
        token = token.upper()

        soundex = ""

        # first letter of input is always the first letter of phoneme
        soundex += token[0]

        # create a dictionary which maps letters to respective phoneme codes. Vowels and 'H', 'W' and 'Y' will be
        # represented by '.'
        dictionary = {"BPV": "1", "F": "2", "C": "3", "GJ": "4", "KQ": "5", "SXZ": "6", "DT": "7", "L": "8",
                      "MN": "9", "R": "10", "AEIOUHWY": "."}

        for char in token[1:]:
            for key in dictionary.keys():
                if char in key:
                    code = dictionary[key]
                    if code != soundex[-1]:
                        soundex += code

        # remove vowels and 'H', 'W' and 'Y' from phoneme
        soundex = soundex.replace(".", "")

        # trim or pad to make phoneme a 10-character code
        soundex = soundex[:10].ljust(10, "0")

        return soundex

    def get_indic_soundex(self, token, length=8):
        """
        Get Soundex code for indic languages
        Args:
            token (word): word
            length (int): length of soundex code
        Returns:
            (str): soundex code
        Examples:
            >>> token = 'उपलब्धता'
            >>> PhonemeModel().get_latin_soundex(token)
            'उMQMKA00'

        """
        sndx = []
        fc = token[0]

        # translate alpha chars in name to phoneme digits
        for char in token[1:].lower():
            if char not in indic_language_chars[self.script]:
                continue
            char_sound = str(indic_char_map[indic_language_chars[self.script].index(char)])

            # remove all 0s from the phoneme code
            if char_sound == '0':
                continue

            # duplicate consecutive phoneme digits are skipped
            if len(sndx) == 0:
                sndx.append(char_sound)
            elif char_sound != sndx[-1]:
                sndx.append(char_sound)

        # append first character to result
        sndx.insert(0, fc)

        if len(sndx) < length:
            sndx.extend(repeat('0', length))
            return ''.join(sndx[:length])

        return ''.join(sndx[:length])

    def get_soundex(self, word):
        """
        Return soundex code of word
        Args:
            word (str): word
        Returns:
            (str): soundex code
        """
        if self.script not in PhonemeModel.supported_languages:
            return None
        if self.script == "en":
            return self.get_latin_soundex(word)
        else:
            return self.get_indic_soundex(word)

    def create_phoneme_dictionary_from_sentences(self, sentences):
        """
        Create phoneme dictionary from sentences.
        - get all tokens from sentences
        - find soundex code for each token
        - create dict with
            - key: soundex code
            - value : list of words belong to key (soundex code)
        Args:
            sentences (list): list of sentences
        Returns:
            (dict): phoneme dict
        """
        phoneme_dict = defaultdict(set)
        words = " ".join(sentences).strip().split()

        words_soundex = {word: self.get_soundex(word) for word in words if len(word) > 2}
        for word, soundex in words_soundex.items():
            phoneme_dict[soundex].add(word)
        self.phoneme_dict = phoneme_dict
        return self.phoneme_dict

    def create_phoneme_dictionary_from_words(self, words_counter):
        """
        Create phoneme dict from words counter (having dict of word and their count)
        follow below steps to create dict:
        - get all tokens from words counter
        - find soundex code for each token
        - create dict with
            - key: soundex code
            - value : list of words belong to key (soundex code)
        Args:
            words_counter (dict): word and their count
        Returns:
            (dict): phoneme dict
        """
        phoneme_dict = defaultdict(set)
        words_soundex = {word: self.get_soundex(word) for word in words_counter if len(word) > 2}
        for word, soundex in words_soundex.items():
            phoneme_dict[soundex].add(word)
        self.phoneme_dict = phoneme_dict
        return self.phoneme_dict

    def spell_correct(self, word) -> SpellSuggestions:
        """
        Suggest words from same soundex code
        Steps are:
            - Find soundex code of word
            - Return None if
                - no soundex of word is found
                - or word soundex not exists in phoneme dict
                - or word exists in word soundex list
            - else:
                - get all words of same soundex code from phoneme dict

                - if len(word) == 3
                    - allow all 1 edit word
                    - allow 2 edit word if suggested word and mispelled word ends with same character
                      (by default all suggestions will start with same character)

                if 4 <= len(word) <= 5:
                    - allow all words upto 2 edit distance
                    - allow 3 edit word if suggested word
                      same character as of word

                if 6 <= len(word) <= 9:
                    - allow all words up to 3 edit distance

                if len(word) >= 10:
                    - allow all words up to 4 edit distance
        Args:
            word (str): word to be corrected
        Returns:
            (list): list of tuples of word with their edit distances

        Examples:
            >>> word = 'apple'
            >>> PhonemeModel().spell_correct(word)
            SpellSuggestions(is_correct=False, suggestions=[('aple', 1), ('aaple', 1)])
        """

        spell_suggestions = SpellSuggestions(is_correct=False, suggestions=[])
        word_soundex = self.get_soundex(word)
        if not word_soundex or (word_soundex not in self.phoneme_dict):
            return spell_suggestions

        if word in self.phoneme_dict[word_soundex]:
            spell_suggestions.is_correct = True
            return spell_suggestions

        possible_suggestions = self.phoneme_dict[word_soundex]
        distances = [dameraulevenshtein(word, s_word) for s_word in possible_suggestions]

        # if script belongs to indic language, don't filter suggestion based on edit distance
        if self.script in PhonemeModel.indic_languages:
            spell_suggestions.suggestions = [(word, distances[index])
                                             for index, word in enumerate(possible_suggestions)]
            return spell_suggestions

        suggestions = []
        word_len = len(word)
        edit_distance_allowed = self.config.phoneme_allowed_distance_map[word_len]
        for index, s_word in enumerate(possible_suggestions):
            if distances[index] <= edit_distance_allowed:
                suggestions.append((s_word, distances[index]))

            if self.config.allow_1_extra_edit_for_char_start:
                edit_distance = edit_distance_allowed + 1
                if s_word not in suggestions and s_word[0] == word[0] and distances[index] <= edit_distance:
                    suggestions.append((s_word, distances[index]))

            if self.config.allow_1_extra_edit_for_char_end:
                edit_distance = edit_distance_allowed + 1
                if s_word not in suggestions and s_word[-1] == word[-1] and distances[index] <= edit_distance:
                    suggestions.append((s_word, distances[index]))

        suggestions.sort(key=operator.itemgetter(1))
        spell_suggestions.suggestions = suggestions
        return spell_suggestions

