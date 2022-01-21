import re
from collections import defaultdict
from itertools import combinations
from typing import Dict, List, Tuple, NamedTuple, Union

from spello.utils import get_ngrams

MAX_COUNT_ALLOWED = 100


class MemoryItem(NamedTuple):
    score: float
    decoded: Tuple[int, ...]


def get_context_pairs(tokens):
    """
    For given list of tokens, return all pairs possible within window of 4 words, ignore single letter word
    Args:
        tokens (list): list of tokens
    Returns:
        (list): list of pairs with their distances in token list
    Examples:
        >>> tokens
        >>> get_context_pairs(["please", "book", "a", "flight", "for", "me", "to", " pune"])
        {((' pune', 'for'), 3),
         ((' pune', 'me'), 2),
         ((' pune', 'to'), 1),
         (('book', 'flight'), 2),
         (('book', 'for'), 3),
         (('book', 'please'), 1),
         (('flight', 'for'), 1),
         (('flight', 'me'), 2),
         (('flight', 'please'), 3),
         (('flight', 'to'), 3),
         (('for', 'me'), 1),
         (('for', 'to'), 2),
         (('me', 'to'), 1)}
    """
    data = set()
    ngrams = get_ngrams(tokens, 4)
    if not ngrams:
        ngrams = [tokens]
    for ngrams_batch in ngrams:
        for pair in combinations(ngrams_batch, 2):
            diff_index = abs(tokens.index(pair[0]) - abs(tokens.index(pair[1])))
            if len(pair[0]) < 2 or len(pair[1]) < 2:
                continue
            data.add((pair, diff_index))
    return data


class ContextModel(object):
    """
    Context Model to suggest most suitable word in a sentence from given list of suggested words
    """
    START_TOKENS = ['^^', '^']
    END_TOKENS = ['$']

    def __init__(self):
        self.default_prob = None
        self.model_dict_count = None
        self.model_dict = None

    @staticmethod
    def get_corrected_words_map(correct_sentence: str, original_sentence: str) -> Dict[str, str]:
        """
        Create a dict having mapping of original words and their changed form in corrected sentence
        Args:
            correct_sentence (str): sentence formed after context suggestion
            original_sentence (str): original sentence
        Returns:
            (dict):
        """
        words_map = {}
        correct_words = correct_sentence.split()
        original_words = original_sentence.split()

        for correct_word, original_word in zip(correct_words, original_words):
            if correct_word != original_word.lower():
                words_map[original_word] = correct_word
        return words_map

    def create_model_dict(
            self,
            sentences: List[str],
    ) -> Dict[Tuple[str, ...], float]:

        """
        Create context model dict from given list of sentences
        steps followed are:
         - for each sentence find all context pairs possible
         - create dict having context pairs and their count
         - create dict from above to convert them into probabilities
        Args:
            sentences (list): list of sentences
        Returns:
            (dict): model dict
        """
        sentences_tokens = [
            ContextModel.START_TOKENS + str(sentence).lower().strip().split() + ContextModel.END_TOKENS
            for sentence in sentences
        ]
        model_dict_count: Dict[Tuple[str, ...], Union[float, int]] = defaultdict(int)
        model_dict: Dict[Tuple[str, ...], float] = defaultdict(float)

        for sentence_tokens in sentences_tokens:
            tokens = sentence_tokens
            context_pairs = get_context_pairs(tokens)
            for (pair, diff) in context_pairs:
                model_dict_count[pair] = min(model_dict_count[pair] + 1, MAX_COUNT_ALLOWED)

        values_model_dict_count = model_dict_count.values()
        total_count = float(sum(values_model_dict_count))
        self.default_prob = (min(values_model_dict_count) / total_count) * 0.5
        # to ensure self.default_prob is smaller than the smallest probability.

        for tup in model_dict_count:
            model_dict[tup] = model_dict_count[tup] / total_count

        self.model_dict = dict(model_dict)
        self.model_dict_count = dict(model_dict_count)

        return self.model_dict

    def get_most_probable_sentence(
            self,
            suggestions: List[List[str]]
    ) -> str:
        """
        Find most probable sentence from given list of sentences that can be formed trying all combination of
        words from suggestion
        Uses context model dict to find overall probability of formed sentence and return sentence with max
        probability

        Args:
            suggestions (List[List[str]]): List of lists representation of all probable sentences.

        Returns:
            (str): Spell corrected sentence.
        """
        sent_word_count = len(suggestions)
        suggestions = [[tok] for tok in ContextModel.START_TOKENS] + suggestions + \
                      [[tok] for tok in ContextModel.END_TOKENS]
        memory = [[MemoryItem(score=0.0, decoded=tuple())], [MemoryItem(score=0.0, decoded=tuple())]]
        for t in range(2, len(suggestions)):
            memory.append([])
            for i, word in enumerate(suggestions[t]):
                mx_score, pick_1, pick_2 = 0, 0, 0
                for j, suggestion_1 in enumerate(suggestions[t - 1]):
                    for k, suggestion_2 in enumerate(suggestions[t - 2]):
                        curr_score = memory[-3][k].score \
                                     + self.model_dict.get((suggestion_2, suggestion_1), self.default_prob) \
                                     + self.model_dict.get((suggestion_1, word), self.default_prob) \
                                     + self.model_dict.get((suggestion_2, word), self.default_prob)
                        if curr_score > mx_score:
                            mx_score, pick_1, pick_2 = curr_score, j, k
                memory_item = MemoryItem(score=mx_score, decoded=memory[-3][pick_2].decoded + (pick_2, pick_1,))
                memory[-1].append(memory_item)
            memory = memory[1:]

        decoded = ' '.join([suggestions[t][i] for t, i in enumerate(memory[-1][0].decoded[-sent_word_count:],
                                                                    start=2)])
        # score = memory[-1][0].score
        return decoded

    def context_spell_correct(
            self,
            sentence: str,
            suggestions_dict: Dict[str, List[str]]
    ) -> (str, Dict[str, str]):
        """
        Get most probable suggestion for miss-spelled words from suggestions list
        Args:
            sentence (str): sentence
            suggestions_dict (dict): dict having miss-spelled word as key and list of suggestions as values
        Returns(str, Dict[str, str]): Tuple containing corrected string and word-to-word correction dictionary.
        """
        sentence_tokens = sentence.lower().split()
        possible_sent_list = []
        for each in sentence_tokens:
            if each in suggestions_dict:
                possible_sent_list.append(suggestions_dict[each])
            else:
                possible_sent_list.append([each])

        corrected_sent = self.get_most_probable_sentence(possible_sent_list)
        corrected_dict = self.get_corrected_words_map(corrected_sent, sentence)
        context_corrected_sentence = " " + sentence + " "
        for token, suggestion in corrected_dict.items():
            context_corrected_sentence = re.sub(" " + re.escape(token) + " ",
                                                " " + suggestion + " ",
                                                context_corrected_sentence)
        context_corrected_sentence = context_corrected_sentence.strip()
        return context_corrected_sentence, corrected_dict
