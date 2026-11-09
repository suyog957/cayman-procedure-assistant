from cayman_assistant.assistant import Turn, resolve_question
import pytest


def test_pronoun_followup_retains_topic_but_not_generated_answer():
    history = [
        Turn("Can I notarize an emailed document?", "Can I notarize an emailed document?", "PR1000")
    ]
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
    history = [
        Turn(
            "What is the coin-counting machine overnight limit?",
            "What is the coin-counting machine overnight limit?",
            "PR63",
        )
    ]
    query, doc, method = resolve_question(
        "And what control is required for monthly testing?", history
    )
    assert doc == "PR63" and method == "followup"
    assert "overnight" not in query


@pytest.mark.parametrize(
    "question",
    [
        "What if the notary requester is physically present?",
        "What if the requester is physically present under PR1000?",
        "And what if the notary requester is physically present?",
    ],
)
def test_hypothetical_repeating_the_same_procedure_retains_original_condition(question):
    history = [
        Turn(
            "Can a notary notarize an emailed document?",
            "Can a notary notarize an emailed document?",
            "PR1000",
        )
    ]
    query, doc, _ = resolve_question(question, history)
    assert doc == "PR1000"
    assert "emailed document" in query and "physically present" in query


def test_hypothetical_naming_a_different_procedure_does_not_carry_old_situation():
    history = [
        Turn(
            "Can a notary notarize an emailed document?",
            "Can a notary notarize an emailed document?",
            "PR1000",
        )
    ]
    query, doc, method = resolve_question(
        "What if I need a digital driver's license under PR1277?", history
    )
    assert doc == "PR1277" and method == "explicit_procedure"
    assert "emailed" not in query
