"""
Created on Mar 13, 2014

@author: woodd
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
            possible_macthes = 0
            for candidate in choices:
                if choice == candidate[:len(choice)].lower():
                    best_candidate = candidate
                    possible_macthes += 1
            if possible_macthes == 1:
                return best_candidate
            else:
                print(("Please respond with one of {}.  Got {}".format(choices, choice)))


def yes_no(question, default="yes"):
    """
    Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
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
