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


class Config(object):
    max_length_for_spellcorrection: int = 15
    min_length_for_spellcorrection: int = 3
    allow_1_extra_edit_for_char_end: bool = True
    allow_1_extra_edit_for_char_start: bool = True
    symspell_allowed_distance_map = SYMSPELL_ALLOWED_DISTANCES_MAP
    phoneme_allowed_distance_map = PHONEME_ALLOWED_DISTANCES_MAP
