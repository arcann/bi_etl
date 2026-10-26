from typing import Iterable

import pytest

from bi_etl.utility import ask


@pytest.fixture
def feed_input(monkeypatch):
    """Return a function that patches ``input`` to yield the given responses in order."""

    def _feed(responses: Iterable[str]):
        iterator = iter(responses)
        monkeypatch.setattr('builtins.input', lambda *args: next(iterator))

    return _feed


class TestYesNo:
    @pytest.mark.parametrize('answer', ['yes', 'y', 'ye', 'YES', 'Y', 'Ye'])
    def test_affirmative_answers(self, feed_input, answer):
        feed_input([answer])
        assert ask.yes_no('Continue?') is True

    @pytest.mark.parametrize('answer', ['no', 'n', 'NO', 'N'])
    def test_negative_answers(self, feed_input, answer):
        feed_input([answer])
        assert ask.yes_no('Continue?') is False

    def test_default_yes_on_empty(self, feed_input):
        feed_input([''])
        assert ask.yes_no('Continue?', default='yes') is True

    def test_default_is_yes_when_not_specified(self, feed_input):
        feed_input([''])
        assert ask.yes_no('Continue?') is True

    def test_default_no_on_empty(self, feed_input):
        feed_input([''])
        assert ask.yes_no('Continue?', default='no') is False

    def test_explicit_answer_overrides_default(self, feed_input):
        feed_input(['n'])
        assert ask.yes_no('Continue?', default='yes') is False

    def test_no_default_requires_answer(self, feed_input, capsys):
        feed_input(['', 'y'])
        assert ask.yes_no('Continue?', default=None) is True
        assert "Please respond with 'yes' or 'no'" in capsys.readouterr().out

    def test_invalid_answer_reprompts(self, feed_input, capsys):
        feed_input(['maybe', 'what', 'no'])
        assert ask.yes_no('Continue?') is False
        out = capsys.readouterr().out
        assert out.count("Please respond with 'yes' or 'no'") == 2

    def test_invalid_default_raises(self):
        with pytest.raises(ValueError, match='invalid default answer'):
            ask.yes_no('Continue?', default='maybe')

    @pytest.mark.parametrize(
        'default, expected_prompt',
        [
            (None, 'Continue? [y/n] '),
            ('yes', 'Continue? [Y/n] '),
            ('no', 'Continue? [y/N] '),
        ],
    )
    def test_prompt_reflects_default(self, feed_input, capsys, default, expected_prompt):
        feed_input(['y'])
        ask.yes_no('Continue?', default=default)
        assert capsys.readouterr().out == expected_prompt


class TestMultiChoiceQuestion:
    def test_exact_match(self, feed_input):
        feed_input(['red'])
        assert ask.multi_choice_question('Color? ', ['red', 'green', 'blue']) == 'red'

    def test_exact_match_is_case_insensitive_and_returns_lowercase(self, feed_input):
        feed_input(['RED'])
        assert ask.multi_choice_question('Color? ', ['Red', 'Green']) == 'red'

    def test_unique_prefix_returns_original_choice(self, feed_input):
        feed_input(['gr'])
        assert ask.multi_choice_question('Color? ', ['Red', 'Green', 'Blue']) == 'Green'

    def test_prefix_is_case_insensitive(self, feed_input):
        feed_input(['BL'])
        assert ask.multi_choice_question('Color? ', ['Red', 'Green', 'Blue']) == 'Blue'

    def test_ambiguous_prefix_reprompts(self, feed_input, capsys):
        feed_input(['gr', 'green'])
        assert ask.multi_choice_question('Color? ', ['green', 'grey', 'blue']) == 'green'
        assert 'Please respond with one of' in capsys.readouterr().out

    def test_exact_match_wins_over_longer_choice_with_same_prefix(self, feed_input):
        feed_input(['car'])
        assert ask.multi_choice_question('Vehicle? ', ['car', 'cart']) == 'car'

    def test_invalid_answer_reprompts(self, feed_input, capsys):
        feed_input(['purple', 'blue'])
        assert ask.multi_choice_question('Color? ', ['red', 'blue']) == 'blue'
        out = capsys.readouterr().out
        assert 'Please respond with one of' in out
        assert 'Got purple' in out

    def test_default_returned_on_empty(self, feed_input):
        feed_input([''])
        assert ask.multi_choice_question('Color? ', ['red', 'blue'], default='blue') == 'blue'

    def test_default_not_used_when_answer_given(self, feed_input):
        feed_input(['red'])
        assert ask.multi_choice_question('Color? ', ['red', 'blue'], default='blue') == 'red'

    def test_empty_without_default_reprompts_when_multiple_choices(self, feed_input, capsys):
        feed_input(['', 'red'])
        assert ask.multi_choice_question('Color? ', ['red', 'blue']) == 'red'
        assert 'Please respond with one of' in capsys.readouterr().out

    def test_invalid_default_raises(self, feed_input):
        feed_input(['red'])
        with pytest.raises(ValueError, match='invalid default answer'):
            ask.multi_choice_question('Color? ', ['red', 'blue'], default='green')

    def test_question_is_written_to_stdout(self, feed_input, capsys):
        feed_input(['red'])
        ask.multi_choice_question('Pick one: ', ['red'])
        assert capsys.readouterr().out.startswith('Pick one: ')
