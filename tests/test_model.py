import os
import tempfile
import pytest
from spello.model import SpellCorrectionModel
from spello.config import Config


def test_min_length_filter_in_training():
    sp = SpellCorrectionModel(language='en')
    # Train with words having varying lengths: 'a' (len 1), 'in' (len 2), 'hello' (len 5), 'world' (len 5)
    data = ["a in hello world", "hello world", "in the world"]
    sp.config.min_length_for_spellcorrection = 3
    sp.train(data)

    # 'a' and 'in' should be filtered out from symspell dictionary because len < 3
    assert 'hello' in sp.symspell_model.dictionary
    assert 'world' in sp.symspell_model.dictionary
    assert 'a' not in sp.symspell_model.dictionary
    assert 'in' not in sp.symspell_model.dictionary


def test_model_save_and_load():
    sp = SpellCorrectionModel(language='en')
    sp.train(["machine learning artificial intelligence", "deep learning"])

    with tempfile.TemporaryDirectory() as tmpdir:
        saved_path = sp.save(tmpdir)
        assert os.path.exists(saved_path)

        loaded_sp = SpellCorrectionModel(language='en')
        loaded_sp.load(saved_path)

        result = loaded_sp.spell_correct("learnin")
        assert result['spell_corrected_text'] == "learning"


def test_suggest_with_none_submodels():
    sp = SpellCorrectionModel(language='en')
    sp.phoneme_model = None
    sp.symspell_model = None
    suggestions = sp.suggest("test")
    assert suggestions == []
