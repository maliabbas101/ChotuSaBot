import question_bank as qb


def test_trivia_questions_have_required_shape():
    assert len(qb.TRIVIA_QUESTIONS) > 0
    for item in qb.TRIVIA_QUESTIONS:
        assert isinstance(item["question"], str) and item["question"]
        assert isinstance(item["answers"], list) and item["answers"]
        assert all(a == a.lower() for a in item["answers"])
        assert isinstance(item["category"], str) and item["category"]


def test_riddles_have_required_shape():
    assert len(qb.RIDDLES) > 0
    for item in qb.RIDDLES:
        assert isinstance(item["riddle"], str) and item["riddle"]
        assert isinstance(item["answers"], list) and item["answers"]
        assert all(a == a.lower() for a in item["answers"])


def test_wyr_prompts_are_nonempty_strings():
    assert len(qb.WOULD_YOU_RATHER) > 0
    assert all(isinstance(p, str) and p.strip() for p in qb.WOULD_YOU_RATHER)


def test_qotd_prompts_are_nonempty_strings():
    assert len(qb.QOTD_PROMPTS) > 0
    assert all(isinstance(p, str) and p.strip() for p in qb.QOTD_PROMPTS)


def test_roast_templates_contain_user_placeholder():
    assert len(qb.ROAST_TEMPLATES) > 0
    for template in qb.ROAST_TEMPLATES:
        assert "{user}" in template
        template.format(user="@someone")  # must not raise


def test_compliment_templates_contain_user_placeholder():
    assert len(qb.COMPLIMENT_TEMPLATES) > 0
    for template in qb.COMPLIMENT_TEMPLATES:
        assert "{user}" in template
        template.format(user="@someone")  # must not raise


def test_rekhta_couplets_have_required_shape():
    assert len(qb.REKHTA_COUPLETS) > 0
    for item in qb.REKHTA_COUPLETS:
        assert isinstance(item["couplet"], str) and item["couplet"]
        assert isinstance(item["poet"], str) and item["poet"]
