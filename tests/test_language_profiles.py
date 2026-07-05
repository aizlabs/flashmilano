from scripts.language_profiles import (
    DEFAULT_GLOSSARY_RULES,
    DEFAULT_PROMPT_PACK,
    DEFAULT_SPACY_MODEL,
    SUPPORTED_GLOSSARY_RULES,
    SUPPORTED_PROMPT_PACKS,
)
from scripts.models import LanguageConfig


def test_language_config_uses_builtin_italian_profile_defaults():
    config = LanguageConfig()

    assert config.target_language == "Italian"
    assert config.target_language_code == "it"
    assert config.locale == "it-IT"
    assert config.spacy_model == DEFAULT_SPACY_MODEL
    assert config.prompt_pack == DEFAULT_PROMPT_PACK
    assert config.glossary_rules == DEFAULT_GLOSSARY_RULES
    assert config.glossary_headings() == ["Vocabolario"]


def test_builtin_prompt_and_glossary_profiles_are_declared():
    assert SUPPORTED_PROMPT_PACKS == {"italian"}
    assert SUPPORTED_GLOSSARY_RULES == {"italian"}
