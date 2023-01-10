import os
from typing import Union, Literal, Pattern

from prompt_toolkit import prompt
from prompt_toolkit.completion import Completer, FuzzyWordCompleter, PathCompleter, FuzzyCompleter
from prompt_toolkit.validation import Validator, ThreadedValidator
from tabulate import tabulate


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
    # Do validation on another thread
    value_validator = ThreadedValidator(value_validator)


    # If word suggestions provided, initialize suggestions and fuzzy completer
    if isinstance(value_suggestions, list):    
        # Cut off printed suggestions if they are too long
        value_suggestions_length = 0
        value_suggestions_length_max = os.get_terminal_size().columns // 2
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


        # Create fuzzy completer
        completer = FuzzyWordCompleter(value_suggestions)
    # Else, assign completer (or None)
    else:
        completer = value_suggestions


    # Create prompt string
    n = '\n'
    prompt_text = f"{info_text}{n}{f'Suggested values: [{value_suggestions_text}]{n}' if isinstance(value_suggestions, list) else ''}>>> "


    # Prompt user
    response = prompt(
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
    return value_suggestion if response == '' else response



def prompt_string(
    info_text: str, 
    value_allowed: list[str] = None, 
    value_disallowed: list[str] = None, 
    str_disallowed: list[str] = None, 
    value_suggestion: str = "", 
    value_suggestions: Union[list[str], Completer] = None
) -> str:
    """Prompts the user for a string input, and validates the input against a list of
    allowed values, a list of disallowed values, a list of disallowed substrings. 
    Also provides a suggestion and auto-completion via a list of suggestions.

    Args:
        info_text (str): String describing prompt
        value_allowed (list[str], optional): Inputs that can be submitted. Defaults to None.
        value_disallowed (list[str], optional): Inputs that may not be submitted. Defaults to None.
        str_disallowed (list[str], optional): Substrings that the input may not contain. Defaults to None.
        value_suggestion (str, optional): Suggestion to display when no input provided. Defaults to "".
        value_suggestions (Union[list[str], Completer], optional): Suggestions for auto-completion engine. Defaults to None.

    Returns:
        str: User input that passes validation
    """
    # Callable that checks if input is valid
    def check_input(s: str):
        if value_allowed and s not in value_allowed:
            return False
        
        if value_disallowed and s in value_disallowed:
            return False
        
        if str_disallowed and any([disallowed in s for disallowed in str_disallowed]):
            return False

        return True


    return prompt_base(
        info_text,
        Validator.from_callable(check_input),
        value_suggestion,
        value_suggestions
    )


def prompt_regex(info_text: str, value_regex: Pattern, value_suggestion: str = "", value_suggestions: Union[list[str], Completer] = None) -> bool:
    """Prompts the user for a string input, and validates the input against a compiled regex.
    Also provides a suggestion and auto-completion via a list of suggestions.

    Args:
        info_text (str): String describing prompt
        value_regex (Pattern): Compiled regex to validate input against
        value_suggestion (str, optional): Suggestion to display when no input provided. Defaults to "".
        value_suggestions (Union[list[str], Completer], optional): Suggestions for auto-completion engine. Defaults to None.

    Returns:
        str: User input that passes validation
    """
    return prompt_base(
        info_text, 
        Validator.from_callable(lambda s: value_regex.search(s) is not None),
        value_suggestion,
        value_suggestions
    )


def prompt_range_integer(
    info_text: str, 
    value_min: Union[int, float], 
    value_max: Union[int, float], 
    value_suggestion: int = None, 
    value_suggestions: list[Union[int, str]] = None
) -> int:
    """Prompts the user for an integer, and validates the input against a range.
    Also provides a suggestion and auto-completion via a list of suggestions.

    Args:
        info_text (str): String describing prompt
        value_min (Union[int, float]): Minimum value (inclusive)
        value_max (Union[int, float]): Maximum value (exclusive)
        value_suggestion (str, optional): Suggestion to display when no input provided. Defaults to "".
        value_suggestions (Union[list[str], Completer], optional): Suggestions for auto-completion engine. Defaults to None.

    Returns:
        str: User input that passes validation
    """
    # Check if input is an integer
    def check_int(s: str):
        if len(s) and s[0] in ('-', '+'):
            return s[1:].isdigit()
        else:
            return s.isdigit()


    return int(prompt_base(
        info_text,
        Validator.from_callable(lambda s: check_int(s) and value_min <= int(s) < value_max),
        str(value_suggestion) if value_suggestion else value_suggestion,
        [str(val) for val in value_suggestions] if value_suggestions else value_suggestion
    ))


def prompt_boolean(
    info_text: str, 
    value_true: list[str] = ["y", "yes", "true", "1"], 
    value_false: list[str] = ["n", "no", "false", "0"], 
    value_suggestion: str = ""
) -> bool:
    """Prompts the user for a boolean input, and validates the input against a list of boolean names.
    
    Args:
        info_text (str): String describing prompt
        value_true (list[str], optional): Inputs that represent True. Defaults to ["y", "yes", "true", "1"].
        value_false (list[str], optional): Inputs that represent False. Defaults to ["n", "no", "false", "0"].
        value_suggestion (str, optional): Suggestion to display when no input provided. Defaults to "".
    """
    response = prompt_string(
        info_text,
        value_allowed=value_true + value_false,
        value_suggestions=value_suggestion,
        # Weave elements together [a, 1, b, 2] with length shortest list
        value_suggestion=[elem for pair in zip(value_true, value_false) for elem in pair]
    )

    return response in value_true


def prompt_path(
    info_text: str,
    path_type: Literal["file", "directory"] = "file",
    value_allow_empty: bool = False,
    value_suggestion: str = None, 
) -> str:
    """Prompts the user for a path, and validates the input against a list of boolean names.
    
    Args:
        info_text (str): String describing prompt
        path_type (Literal["file", "directory"], optional): Whether to prompt for a file or directory. Defaults to "file".
        value_allow_empty (bool, optional): Whether to allow empty input. Defaults to False.
        value_suggestion (str, optional): Suggestion to display when no input provided. Defaults to None.

    Returns:
        str: User input that passes validation
    """
    return prompt_base(
        info_text,
        Validator.from_callable(lambda s: (value_allow_empty and s == "") 
                                       or (os.path.isfile(s) if path_type == "file" else os.path.isdir(s))),
        value_suggestion,
        FuzzyCompleter(PathCompleter(only_directories=path_type == "directory", expanduser=True), )
    )


def prompt_choice(
    info_text: str, 
    choices: Union[list[str], list[list[str]], list[list[list[str]]]],
    index: Union[list[str], list[list[str]]] = None,
    headers: list[str] = None,
    value_suggestion: str = ""
) -> str:
    """Prompts the user for a choice, and validates the input against a list of choices.
    
    Args:
        info_text (str): String describing prompt
        choices (Union[list[str], list[list[str]], list[list[list[str]]]]): List of choices, or list of grouped choices, or list of grouped choices with values.
        index (Union[list[str], list[list[str]]], optional): List of indexes or grouped indexes for choices. Defaults to None, which numerically 0-indexes the choices.
        headers (list[str], optional): List of headers for choices and their values. Defaults to None.
        value_suggestion (str, optional): Suggestion to display when no input provided. Defaults to "".

    Returns:
        str: User input that passes validation
    """
    # Normalize choice to triple nested list form
    if isinstance(choices[0], str):
        choices = [[[choice] for choice in choices]]
    elif isinstance(choices[0][0], str):
        choices = [[[choice] for choice in choice_group] for choice_group in choices]

    # Normalize index to double nested list form
    if not index:
        index = []
        i = 0

        for choice_group in choices:
            index.append([str(i) for i in range(i, i + len(choice_group))])
            i += len(choice_group)

    elif isinstance(index[0], str):
        index = [index]

    # Normalize headers to list form
    if headers is None:
        headers = []


    # Get dimension of choice + values
    choices_inner_len = len(choices[0][0])
    # Get width of separator for index
    index_width_max = max(len(idx) for index_group in index for idx in index_group)

    # Build table data
    choices_table, index_table = [], []
    choices_values, index_values = [], []
    for choice_group, index_group in zip(choices, index):
        choices_table.extend(choice_group)
        index_table.extend(index_group)
        choices_values.extend([choice[0] for choice in choice_group])
        index_values.extend(index_group)

        choices_table.append([''] * choices_inner_len)
        index_table.append('-' * index_width_max)


    # Pop last redundant separator row
    choices_table.pop()
    index_table.pop()

    # Create prompt text from table and info text
    prompt_text = f"{tabulate(choices_table, headers=headers, showindex=index_table)}\n\n{info_text}"

    # Set allowed values to be either choice or index values
    value_allowed=choices_values + index_values
    # Set suggestions to choices
    value_suggestions=choices_values
    
    # Prompt user for input
    response = prompt_string(
        info_text=prompt_text,
        value_allowed=value_allowed,
        value_suggestion=value_suggestion,
        value_suggestions=value_suggestions
    )


    # Return associated index value
    if response in index_values:
        return response
    else:
        return index_values[value_allowed.index(response)]
