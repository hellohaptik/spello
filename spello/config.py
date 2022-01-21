SYMSPELL_ALLOWED_DISTANCES_MAP = {
    3: 1,
    4: 1,
    5: 1,
    6: 2,
    7: 2,
    8: 2,
    9: 3,
    10: 3,
    11: 3,
    12: 3,
    13: 3,
    14: 3,
    15: 3
}

PHONEME_ALLOWED_DISTANCES_MAP = {
    3: 1,
    4: 2,
    5: 2,
    6: 3,
    7: 3,
    8: 3,
    9: 3,
    10: 3,
    11: 4,
    12: 4,
    13: 4,
    14: 4,
    15: 4
}


# TODO: can be written better with dataclasses
class Config(object):
    def __init__(self):
        self.max_length_for_spellcorrection: int = 15
        self.min_length_for_spellcorrection: int = 3
        self.allow_1_extra_edit_for_char_end: bool = True
        self.allow_1_extra_edit_for_char_start: bool = True
        self.symspell_allowed_distance_map = SYMSPELL_ALLOWED_DISTANCES_MAP.copy()
        self.phoneme_allowed_distance_map = PHONEME_ALLOWED_DISTANCES_MAP.copy()
        # 0: top suggestion
        # 1: all suggestions of smallest edit distance
        # 2: all suggestions <= max_edit_distance (slower, no early termination)
        self.symspell_verbosity: int = 1
