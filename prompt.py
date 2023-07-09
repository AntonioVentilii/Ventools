# -*- coding: utf-8 -*-
"""
Module for prompting user input and asking yes/no questions.

Author: antonio.ventilii
"""

from __future__ import annotations

import sys

import easygui


def dialog_prompt(message: str, title: str = '', open_question: bool = False) -> bool | str:
    """
    Display a dialog prompt and return the user's answer.

    Args:
        message (str): The message to display in the dialog.
        title (str, optional): The title of the dialog. Defaults to an empty string.
        open_question (bool, optional): If True, an open-ended question dialog will be displayed.
                                         If False, a yes/no question dialog will be displayed. Defaults to False.

    Returns:
        bool | str: The user's answer.

    """
    if open_question:
        answer = easygui.enterbox(msg=message, title=title)
    else:
        answer = easygui.ynbox(msg=message, title=title)
    return answer


def query_yes_no(question: str, default: str = None, use_prompt: bool = False) -> bool:
    """
    Ask a yes/no question and return the user's answer.

    Args:
        question (str): The question to ask the user.
        default (str, optional): The default answer if the user just hits <Enter>.
                                 It can be "yes", "no", or None. Defaults to None.
        use_prompt (bool, optional): If True, a dialog prompt will be displayed instead of printing to stdout.
                                     Defaults to False.

    Returns:
        bool: True for "yes" or False for "no".

    Raises:
        ValueError: If the default answer is invalid.

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
        if use_prompt:
            choice = dialog_prompt(message=question + prompt)
        else:
            sys.stdout.write(question + prompt)
            choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        elif isinstance(choice, bool):
            return choice
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")
