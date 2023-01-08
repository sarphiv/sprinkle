import os

from prompt_toolkit import prompt
from prompt_toolkit.completion import Completer, FuzzyWordCompleter, PathCompleter
from prompt_toolkit.validation import Validator, ThreadedValidator
from typing import Optional, Union


def prompt_base(info_text: str, value_validator: Validator = None, value_suggestion: str = "", value_suggestions: Union[list[str], Completer] = None) -> str:
    """Base prompt method for prompting user for input

    Args:
        info_text (str): String describing prompt
        value_validator (Validator, optional): A function that takes a string 
            and returns a boolean. If the function returns True, the input is accepted. 
            If the function returns False, the input is rejected
        value_suggestion (str, optional): Initial input suggestion for user. 
            Default response is this. Defaults to "".
        value_suggestions (Union[list[str], Completer], optional): Input suggestions that can be autocompleted or a completer. Defaults to None.

    Returns:
        str: User input that passes the validator
    """
    # Cut off printed suggestions if they are too long
    value_suggestions_length = 0
    value_suggestions_length_max = 20
    value_suggestions_text = ""
    for value in value_suggestions:
        if value_suggestions_length + len(value) > value_suggestions_length_max:
            value_suggestions_text = f"{value_suggestions_text}, ..."
            break

        if value_suggestions_text == "":
            value_suggestions_text = f'"{value}"'
        else:
            value_suggestions_text = f'{value_suggestions_text}, "{value}"'

        value_suggestions_length += len(value)


    # Create prompt string
    n = '\n'
    prompt_text = f"{info_text}{n}{f'Suggested values: [{value_suggestions_text}]{n}' if value_suggestions else ''}>>> "


    # If word suggestions provided, initialize fuzzy completer
    if value_suggestions and isinstance(value_suggestions, list):
        completer = FuzzyWordCompleter(value_suggestions)

    # NOTE: Completer is now either None or a completer


    # Prompt user
    answer = prompt(
        prompt_text,
        placeholder=value_suggestion,
        reserve_space_for_menu=0,
        completer=completer,
        complete_while_typing=True, 
        complete_in_thread=True,
        validator=value_validator, 
        validate_while_typing=True, 
        mouse_support=True,
    )
    

    # Return default answer, if no answer, else return answer
    return value_suggestion if answer == '' else answer


def prompt_integer(info_text: str, min: int, max: int, value_suggestion: int, value_suggestions: list[int] = None) -> int:
    def check_int(s: str):
        if len(s) and s[0] in ('-', '+'):
            return s[1:].isdigit()
        else:
            return s.isdigit()


    return int(prompt_base(
        info_text,
        Validator.from_callable(lambda s: check_int(s) and min <= int(s) < max),
        value_suggestion,
        value_suggestions
    ))

def prompt_string(info_text: str, value_allowed: Optional[list[str]], value_suggestion: str = "", value_suggestions: list[str] = None) -> str:
    return prompt_base(
        info_text,
        Validator.from_callable(lambda s: s in value_allowed if value_allowed else True),
        value_suggestion,
        value_suggestions
    )
    
def prompt_list():
    pass