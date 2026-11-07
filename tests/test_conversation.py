from cayman_assistant.assistant import Turn, resolve_question


def test_pronoun_followup_retains_topic_but_not_generated_answer():
    history = [Turn("Can I notarize an emailed document?", "Can I notarize an emailed document?", "PR1000")]
    query, doc, method = resolve_question("What if the requester is physically present?", history)
    assert doc == "PR1000" and method == "followup"
    assert "emailed document" in query


def test_explicit_topic_switch_does_not_inherit_previous_procedure():
    history = [Turn("What is the coin machine limit?", "What is the coin machine limit?", "PR63")]
    query, doc, method = resolve_question("What about savings bond redemption fees?", history)
    assert "coin" not in query
    assert doc is None and method == "named_topic"


def test_another_session_cannot_see_previous_topic():
    question = "What if they are physically present?"
    query, doc, method = resolve_question(question, [])
    assert query == question and doc is None


def test_explicit_procedure_selection_takes_precedence():
    history = [Turn("Notary fees?", "Notary fees?", "PR1000")]
    query, doc, method = resolve_question("In PR1277 what is secondary identification?", history)
    assert doc == "PR1277" and method == "explicit_procedure"


def test_followup_naming_a_new_task_keeps_scope_without_old_task_terms():
    history = [Turn("What is the coin-counting machine overnight limit?", "What is the coin-counting machine overnight limit?", "PR63")]
    query, doc, method = resolve_question("And what control is required for monthly testing?", history)
    assert doc == "PR63" and method == "followup"
    assert "overnight" not in query

