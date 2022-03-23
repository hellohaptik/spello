import logging
import operator
import os
import pickle
import re
import warnings
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple, Any, Union, Optional

from spello.config import Config
from spello.context.context import ContextModel
from spello.phoneme.phoneme import PhonemeModel
from spello.settings import logger, loglevel
from spello.symspell.symspell import SymSpell
from spello.utils import get_clean_text
from spello.utils import mkdirs

ORIGINAL_TEXT = 'original_text'
CORRECTED_TEXT = 'spell_corrected_text'
CORRECTIONS_DICT = 'correction_dict'


class SpellCorrectionModel(object):
    """
    Model to find and correct miss-spelled words utter in text from two words corpus, domain and global dictionary.
    For each word in text which do not belong to either of domain or global dictionary, model considered it as
    miss-spelled word and try to find out most suitable suggestion first from domain dict, and then from global.

    Current model works on 4 key algorithms, which are
        1) Symspell Model - Suggest words based on simple edit distance.
        2) Phoneme Model - Suggest words based on Soundex code of word.
        3) Context Model -  Model to suggest most suitable word from suggestion list given by above two model
        4) Normalize Model -  Model to Normalize unigrams which also occurs as bigrams or trigrams to split form.
                              for example - Login to log in.
    """

    def __init__(
            self,
            language: str = 'en',
            config: Optional[Config] = None
    ) -> None:
        self.language = language
        if language not in PhonemeModel.supported_languages + ['en']:
            raise Exception(f'"{language}" language is not yet supported')

        self.config = config or Config()
        self.symspell_model = None
        self.phoneme_model = None
        self.context_model = None

    def set_default_config(self):
        self.config = Config()

    def symspell_train(self, words_counter: Dict[str, int]) -> 'SymSpell':
        """
        Train symspell model
        Args:
            words_counter (dict): dict of word and their count
        Returns:
            (SymSpell)
        """
        self.symspell_model = SymSpell(config=self.config, script=self.language)
        self.symspell_model.create_dictionary_from_words(words_counter)
        return self.symspell_model

    def phoneme_train(self, words_counter: Dict[str, int]) -> 'PhonemeModel':
        """
        Train phoneme model
        Args:
            words_counter (dict): dict of word and their count
        Returns:
            (PhonemeModel)
        """
        if self.language not in PhonemeModel.supported_languages:
            return self.phoneme_model
        self.phoneme_model = PhonemeModel(config=self.config, script=self.language)
        self.phoneme_model.create_phoneme_dictionary_from_words(words_counter)
        return self.phoneme_model

    def context_train(self, texts: List[str]) -> 'ContextModel':
        """
        Train context model
        Args:
            texts (list): list of text
        Returns:
            (ContextModel)
        """
        self.context_model = ContextModel()
        self.context_model.create_model_dict(texts)
        return self.context_model

    def context_suggestion(self, text: str, suggestions_dict: Dict[str, List[str]]) -> Tuple[str, Dict[str, str]]:
        """
        Get context suggested text for given text and suggestions dict with misspelled words and their list
        of suggestions
        Args:
            text (str): text
            suggestions_dict: dict with misspelled words and their list of suggestions
        Returns:
            (str): contextually corrected text
            (dict): token level suggestion from context model

        Examples:
            >>> text = 'i wnt to pley kriket'
            >>> suggestions_dict = {'wnt': ['want', 'went', 'what'], 'pley': ['play'], 'kriket': ['cricket']}
            >>> SpellCorrectionModel().context_suggestion(text, suggestions_dict)
            (i want to play cricket, {'wnt': 'want', 'pley: 'play', 'kriket': 'cricket'})
        """
        if not self.context_model or not suggestions_dict:
            suggestions_dict = {key: value[0] for key, value in suggestions_dict.items()}
            return text, suggestions_dict
        text, context_corrections = self.context_model.context_spell_correct(text, suggestions_dict)
        return text, context_corrections

    def train(self, data: Union[List[str], Dict[str, int]], **kwargs):
        """
        Train all models of spellcorrection
        Args:
            data (list|dict): list of text or dict having word and their count
        Returns:
            None
        """

        logger.debug("Spello training started..")

        words_counter = {}
        if not isinstance(data, list) and not isinstance(data, dict):
            raise ValueError('Argument `data` should be either List[str] or Dict[str, int]')

        if isinstance(data, list):
            # TODO: cleaning and preprocessing should really be left to the user!
            texts = [get_clean_text(text) for text in data]
            lower_case_texts = [text.lower() for text in texts]

            logger.debug("Context model training started ...")
            # Context model get trained only when list of text are given for training
            # train context model: find most probable correct word for given suggestions for each word in texts
            # based on context word
            self.context_train(lower_case_texts)

            tokens = " ".join(lower_case_texts).strip().split()

            words_counter = dict(Counter(tokens))

        elif isinstance(data, dict):
            words_counter = {word.lower(): count for word, count in data.items()}

        words_counter = {word: count for word, count in words_counter.items()
                         if self.config.min_length_for_spellcorrection}

        logger.debug("Symspell training started ...")
        # train symspell model: give suggestion based on edit distance
        self.symspell_train(words_counter)

        logger.debug("Phoneme training started ...")
        # train phoneme model: give suggestion for similar sounding words
        self.phoneme_train(words_counter)

        logger.debug("Spello training completed successfully ...")

    def suggest(self, word: str) -> List[Tuple[str, int]]:
        """
        Suggest words for given word, follow below steps:
            - check if length of word is eligible for correction from min max length allowed from config,
                else return []
            - if word belong to domain word correction (created for words which occur less in domain words and are
                replaced with most similar words, either from domain or global), return suggested word from dict
            - if word exists in global dictionary, return []
            - if word exists in domain dictionary, return []
            - get suggestions from domain symspell & phoneme
            - if not suggestions from domain, get suggestions from global symspell and phoneme
            - filter top 5 suggestions
            - also add top 3 suggestions from global data up to min edit distance of above dict
            - return final suggestions
        Args:
            word (str): word to be corrected
        Returns:
            (list): list of suggested words
        """
        if ((self.config.min_length_for_spellcorrection > len(word)) or
                (len(word) > self.config.max_length_for_spellcorrection) or
                (re.search(r'\d', word))):
            return []

        phoneme = self.phoneme_model.spell_correct(word)
        if phoneme.is_correct:
            return []
        phoneme_suggestions = phoneme.suggestions

        symspell = self.symspell_model.spell_correct(word)
        if symspell.is_correct:
            return []
        symspell_suggestions = symspell.suggestions

        logger.debug(f"Symspell suggestions: {symspell_suggestions}")
        logger.debug(f"Phoneme suggestions: {phoneme_suggestions}")

        phoneme_suggestions = [(word, edit_distance, 0) for (word, edit_distance) in phoneme_suggestions]
        symspell_suggestions = [(word, edit_distance, 1) for (word, edit_distance) in symspell_suggestions]

        suggestions = list(phoneme_suggestions + symspell_suggestions)
        suggestions.sort(key=operator.itemgetter(1, 2))

        # filtering duplicate suggestions
        unique_suggestions = set()
        final_suggestions = []
        for (suggestion, edit_distance, _) in suggestions:
            if suggestion not in unique_suggestions:
                final_suggestions.append((suggestion, edit_distance))
                unique_suggestions.add(suggestion)
        return final_suggestions

    def _correct_word(self, word: str) -> List[str]:
        """
        Suggest words for given word, follow below steps:
            - check if length of word is eligible for correction from min max length allowed from config,
                else return []
            - if word belong to domain word correction (created for words which occur less in domain words and are
                replaced with most similar words, either from domain or global), return suggested word from dict
            - if word exists in global dictionary, return []
            - if word exists in domain dictionary, return []
            - get suggestions from domain symspell & phoneme
            - if not suggestions from domain, get suggestions from global symspell and phoneme
            - filter top 5 suggestions
            - also add top 3 suggestions from global data up to min edit distance of above dict
            - return final suggestions
        Args:
            word (str): word to be corrected
        Returns:
            (list): list of suggested words
        """
        suggestions = [suggestion for suggestion, _ in self.suggest(word)]
        return suggestions

    def spell_correct(self, text: str, verbose=0) -> Dict[str, Any]:
        """
        Get spell corrected text, and dict of token level suggestion
        Args:
            text (str):
            verbose (int): define verbose level
        Returns:
            (str): spell corrected text
            (dict): dict of token level suggestion

        Examples:
            >>> text = 'i wnt to play kricket'
            >>> SpellCorrectionModel().spell_correct(text)
            {
                'original_text': 'i wnt to play kricket',
                'corrected_text': 'i want to play cricket',
                'correction_dict': {'wnt': 'want', 'kricket': 'cricket'}
            }
        """
        levels = [logging.CRITICAL, logging.ERROR, logging.INFO, logging.DEBUG]
        verbosity = min(verbose, len(levels) - 1)
        with loglevel(levels[verbosity]):
            spellcorrection_result = {
                ORIGINAL_TEXT: text,
                CORRECTED_TEXT: text,
                CORRECTIONS_DICT: {}
            }

            suggestions_dict = {}
            # TODO: cleaning and preprocessing should really be left to the user!
            clean_text = get_clean_text(text)
            tokens = clean_text.split()
            for token in tokens:
                lowercase_token = token.lower()
                token_suggestion = self._correct_word(lowercase_token)
                if token_suggestion:
                    suggestions_dict[lowercase_token] = token_suggestion

            logger.debug(f"Suggestions dict from phoneme and symspell are: {suggestions_dict}")

            context_corrected_text, context_corrections = self.context_suggestion(clean_text, suggestions_dict)

            logger.debug(f"text after context model: {context_corrected_text}")

            spellcorrection_result[CORRECTED_TEXT] = context_corrected_text
            spellcorrection_result[CORRECTIONS_DICT] = context_corrections

            logger.debug(f"Spell-correction Results {spellcorrection_result}")

        return spellcorrection_result

    def get_state(self) -> Dict[str, Any]:
        return {
            'language': self.language,
            'symspell_model': self.symspell_model,
            'phoneme_model': self.phoneme_model,
            'context_model': self.context_model,
            'config': self.config
        }

    def set_state(self, state_dict: Dict[str, Any]) -> None:
        self.language = state_dict['language']
        self.config = state_dict['config']
        if not isinstance(self.config, Config):
            self.set_default_config()
            warnings.warn("This model was saved on spell<1.3.0. As such due to a bug in previous versions, "
                          "none of customisations made to the config at the time of training were saved along with "
                          "the model. It is recommended to load the model, apply all required customizations "
                          "to config and save it again. E.g.\n\n"
                          "from spello.model import SpellCorrectionModel \n"
                          "sp = SpellCorrectionModel(language='en')  \n"
                          "sp.load('/home/ubuntu/model.pkl')\n"
                          "sp.config.min_length_for_spellcorrection = 4 # default is 3\n"
                          "sp.config.max_length_for_spellcorrection = 12 # default is 15\n"
                          "sp.save(model_save_dir='/home/ubuntu/')\n\n"
                          "After this the model will load without any warnings\n")
        self.symspell_model: SymSpell = state_dict['symspell_model']
        self.phoneme_model: PhonemeModel = state_dict['phoneme_model']
        self.context_model: ContextModel = state_dict['context_model']
        # fix all config references downstream
        self.symspell_model.config = self.config
        self.phoneme_model.config = self.config

    def load(
            self,
            model_path: str,
            **kwargs
    ) -> 'SpellCorrectionModel':
        model_state = pickle.load(open(model_path, 'rb'))
        self.set_state(model_state)
        return self

    def save(self, model_save_dir: str, **kwargs) -> str:
        save_dir = Path(model_save_dir)
        mkdirs(save_dir, err_if_already_exists=False)
        state = self.get_state()
        pickle.dump(state, open(save_dir / 'model.pkl', "wb"))
        path = os.path.join(save_dir, 'model.pkl')
        return path
