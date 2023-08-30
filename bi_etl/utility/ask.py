"""
Created on Mar 13, 2014

@author: Derek Wood
"""

import sys


def multi_choice_question(question, choices, default=None):
    while True:
        sys.stdout.write(question)
        choice = input().lower()
        choices_lower = [c.lower() for c in choices]
        if default is not None and default not in choices:
            raise ValueError("invalid default answer: '%s'" % default)
        if default is not None and choice == '':
            return default
        elif choice in choices_lower:
            return choice
        else:
            best_candidate = None
            possible_matches = 0
            for candidate in choices:
                if choice == candidate[:len(choice)].lower():
                    best_candidate = candidate
                    possible_matches += 1
            if possible_matches == 1:
                return best_candidate
            else:
                print(f"Please respond with one of {choices}.  Got {choice}")


def yes_no(
    question: str,
    default: str = "yes"
):
    """
    Ask a yes/no question via raw_input() and return their answer.

    Parameters
    ----------
    question:
        String that is presented to the user.
    default:
        The presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is one of "yes" or "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' (or 'y' or 'n').\n")
