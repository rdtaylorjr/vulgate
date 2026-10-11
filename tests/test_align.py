from programs import align


def anywhere(word, token):
    return True


def same_verse(words, forms):
    return align.align(words, forms, anywhere)


def test_normal_folds_case_letters_and_the_spellings_of_u_and_i():
    assert align.normal("Vacua") == "uacua"
    assert align.normal("Iesu") == "iesu"
    assert align.normal("jam") == "iam"
    assert align.normal("ω") == ""


def test_align_matches_equal_runs_and_leaves_the_rest_none():
    words = ["in", "principio", "creauit", "Deus", "caelum", "et", "terram", "eas"]
    forms = ["in", "principio", "creavit", "Deus", "et", "terram", "eos"]
    assert same_verse(words, forms) == [0, 1, 2, 3, None, 4, 5, None]


def test_align_matches_a_phrase_the_editions_place_in_different_verses_in_a_second_pass():
    words = [
        "beati",
        "mites",
        "quoniam",
        "ipsi",
        "possidebunt",
        "terram",
        "beati",
        "qui",
        "lugent",
        "quoniam",
        "ipsi",
        "consolabuntur",
    ]
    forms = [
        "beati",
        "qui",
        "lugent",
        "quoniam",
        "ipsi",
        "consolabuntur",
        "beati",
        "mites",
        "quoniam",
        "ipsi",
        "possidebunt",
        "terram",
    ]
    assert align.align(words, forms, align.nearby([4] * 6 + [5] * 6, [4] * 6 + [5] * 6)) == [
        6,
        7,
        8,
        9,
        10,
        11,
        0,
        1,
        2,
        3,
        4,
        5,
    ]
    assert same_verse(["a", "x", "b"], ["b", "y", "a"]) == [2, None, 0]


def test_align_matches_only_the_pairs_the_rule_allows_and_nearby_allows_one_verse_apart():
    words = ["et", "ne", "que", "ego", "dico"]
    forms = ["et", "nec", "ego", "dico", "ne", "que"]
    assert align.align(words, forms, align.nearby([2, 2, 2, 3, 3], [2, 2, 3, 3, 9, 9])) == [0, None, None, 2, 3]
    assert align.align(words, forms, anywhere) == [0, 4, 5, 2, 3]
    assert align.align(["ne"], ["ne"], align.nearby([2], [3])) == [0]


def test_align_handles_empty_input():
    assert align.align([], ["a"], anywhere) == []
    assert align.align(["a"], [], anywhere) == [None]
