from app.utils.import_utils import (
    clean_float,
    find_col_by_keyword,
    is_fuzzy_match,
    levenshtein_distance,
    normalize_text,
    sort_semicolon_list,
)


# ---------------------------------------------------------
# TEST NORMALIZE_TEXT.
# ---------------------------------------------------------
def test_normalize_text():
    # ARRANGE & ACT & ASSERT.
    assert normalize_text(None) == ""
    assert normalize_text("  ") == ""
    assert normalize_text("  Héllò-World  ") == "hello world"
    assert normalize_text("C'est l'été") == "c'est l'ete"


# ---------------------------------------------------------
# TEST SORT_SEMICOLON_LIST.
# ---------------------------------------------------------
def test_sort_semicolon_list():
    # ARRANGE.
    input_text = "  Zèbre ; Abeille ;  Biche "

    # ACT.
    result = sort_semicolon_list(input_text)

    # ASSERT.
    assert result == "Abeille;Biche;Zèbre"
    assert sort_semicolon_list(None) is None
    assert sort_semicolon_list("   ") is None
    assert sort_semicolon_list(";;;") is None


# ---------------------------------------------------------
# TEST LEVENSHTEIN_DISTANCE.
# ---------------------------------------------------------
def test_levenshtein_distance():
    # ARRANGE & ACT & ASSERT.
    assert levenshtein_distance("chat", "chat") == 0
    assert levenshtein_distance("chat", "chats") == 1
    assert levenshtein_distance("chats", "chat") == 1
    assert levenshtein_distance("", "test") == 4
    assert levenshtein_distance("test", "") == 4
    assert levenshtein_distance("kitten", "sitting") == 3


# ---------------------------------------------------------
# TEST IS_FUZZY_MATCH.
# ---------------------------------------------------------
def test_is_fuzzy_match():
    # ARRANGE & ACT & ASSERT.
    assert is_fuzzy_match("Jean-Pierre", "jean pierre") is True

    assert is_fuzzy_match("Logiciel", "Logitiel") is True
    assert is_fuzzy_match("Logiciel", "Logitial") is True
    assert is_fuzzy_match("Logiciel", "Loxitialx") is False

    assert is_fuzzy_match("abc", "abd") is False


# ---------------------------------------------------------
# TEST CLEAN_FLOAT.
# ---------------------------------------------------------
def test_clean_float():
    # ARRANGE & ACT & ASSERT.
    assert clean_float(None) is None
    assert clean_float("") is None
    assert clean_float(15) == 15.0
    assert clean_float(15.5) == 15.5
    assert clean_float(float("nan")) is None

    assert clean_float(" 15,5 % ") == 15.5
    assert clean_float("1 000,50") == 1000.5

    assert clean_float("pas un nombre") is None


# ---------------------------------------------------------
# TEST FIND_COL_BY_KEYWORD.
# ---------------------------------------------------------
def test_find_col_by_keyword():
    # ARRANGE.
    headers = ["Nom de l'élève", "Prénom", "Note Initiale", "Note Finale"]

    # ACT & ASSERT.
    assert find_col_by_keyword(headers, ["identifiant", "nom"]) == "Nom de l'élève"
    assert find_col_by_keyword(headers, "note", exclude=["finale"]) == "Note Initiale"
    assert find_col_by_keyword(headers, "prénom") == "Prénom"
    assert find_col_by_keyword(headers, "age") is None
    assert find_col_by_keyword(headers, "finale") == "Note Finale"
