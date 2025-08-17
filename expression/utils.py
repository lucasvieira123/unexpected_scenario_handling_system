from typing_extensions import Literal
from pyparsing import Dict, ParseResults, Word, alphas, nums, oneOf, infixNotation, opAssoc, ParserElement
from typing import List, Union

from sympy import sympify, to_dnf

def _configure_expression_parsing() -> ParserElement:
    """
    Configure and return the parsing grammar for logical and conditional expressions.

    This function sets up a parsing configuration using the `pyparsing` library. 
    The grammar supports identifiers, numeric values, conditional operators, and 
    logical operators, enabling the parsing of conditional expressions typically 
    used in scenarios or rule-based systems.

    The configuration includes:
        - Identifiers: variable names composed of letters, digits, and underscores.
        - Numbers: sequences of digits.
        - Comparison operators: <=, >=, <, >, ==, !=
        - Logical operators: AND, OR
        - Support for nested expressions via infix notation.

    The returned grammar can be used to parse strings such as:
        - "temperature > 30 AND humidity <= 70"
        - "(x != 10) OR (y >= 5 AND z < 100)"

    Returns:
        pyparsing.ParserElement: A parsing object configured to handle 
        logical and comparison expressions with nested structures.

    Example:
        >>> parser = configure_expression_parsing()
        >>> result = parser.parseString("a > 10 AND (b <= 20 OR c != 5)")
        >>> print(result.asList())
        ['a', '>', '10', 'AND', ['b', '<=', '20', 'OR', 'c', '!=', '5']]
    """
    # Configure pyparsing to ignore whitespace
    ParserElement.enablePackrat()

    # Define basic expression elements
    identifier = Word(alphas, alphas + nums + "_")
    number = Word(nums)

    # Define comparison operators
    comparison_operator = oneOf("<= >= < > == !=")

    # Define operands
    operand = identifier | number

    # Define logical expressions with operator precedence
    parse_settings = infixNotation(operand,
        [
            (comparison_operator, 2, opAssoc.LEFT),
            ("AND", 2, opAssoc.LEFT),
            ("OR", 2, opAssoc.LEFT),
        ])

    return parse_settings

def _extract_conditional_expressions(parsed_expr: Union[str, ParseResults]) -> List[str]:
    """
    Recursively extract leaf conditional expressions from a parsed expression.

    This function traverses the structure produced by the expression parser
    (e.g., `configure_expression_parsing`) and collects only the simple
    conditional conditions (e.g., "a > 10", "b <= 20"). It ignores logical
    operators (AND, OR) and nested groupings, drilling down until it reaches
    atomic conditional expressions.

    Args:
        parsed_expr (Union[str, ParseResults]): The parsed expression object, which can be:
            - a string (base token)
            - a ParseResults object (possibly nested) returned by pyparsing

    Returns:
        List[str]: A list of leaf conditional expressions represented as strings.
                   Each string has the format "<identifier> <operator> <value>".

    Example:
        >>> parser = configure_expression_parsing()
        >>> expr = parser.parseString("a > 10 AND (b <= 20 OR c != 5)")
        >>> conditional_expressions(expr)
        ['a > 10', 'b <= 20', 'c != 5']
    """
    parsed_expr_list=parsed_expr.asList()

    if isinstance(parsed_expr_list, str):
        return []
    elif len(parsed_expr_list) == 3 and parsed_expr_list[1] in ["<=", ">=", "<", ">", "==", "!="]:
        return [" ".join(parsed_expr_list)]
    else:
        leaves: List[str] = []
        for sub_expr in parsed_expr_list:
            leaves.extend(_extract_conditional_expressions(sub_expr))
        return leaves

def _conditional_expressions_to_key_dict(expressions: list[str]) -> dict[str, str]:
    """
    Convert a list of conditional expressions (as strings) into a dictionary 
    with indexed keys in the form "x1", "x2", ..., "xn".

    Parameters
    ----------
    expressions : list of str
        List of conditional expressions in string format.

    Returns
    -------
    dict
        Dictionary where keys are 'x1', 'x2', ..., 'xn' and values are 
        the conditional expressions from the input list.

    Examples
    --------
    >>> conditional_expressions_to_key_dict(["a > 10", "b <= 20", "c != 5"])
    {'x1': 'a > 10', 'x2': 'b <= 20', 'x3': 'c != 5'}

    >>> conditional_expressions_to_key_dict([])
    {}
    """
    map_key = {f"x{i+1}": expr for i, expr in enumerate(expressions)}

    return map_key

def _replace_conditional_expression_to_keys(expression_str: str, map_key:dict) -> str:
    """
    Replace occurrences of dictionary values with their corresponding keys in a string.

    This function scans through the input string and substitutes every occurrence 
    of each dictionary value with its associated key.

    Parameters
    ----------
    string : str
        The string where replacements will be performed.
    dictionary : dict
        Dictionary mapping keys to values. Each value in the dictionary will be 
        replaced with its corresponding key when found in the input string.

    Returns
    -------
    str
        The updated string with values replaced by keys.

    Examples
    --------
    >>> mapping = {'x1': 'a > 10', 'x2': 'b <= 20'}
    >>> replace_values_with_keys("if (a > 10 AND b <= 20)", mapping)
    'if (x1 AND x2)'

    >>> replace_values_with_keys("c != 5", {'x3': 'c != 5'})
    'x3'
    """
    for key, value in map_key.items():
        expression_str = expression_str.replace(value, key)
    return expression_str

def _replace_logical_operators(expression_str: str, scenario_operators: bool = False) -> str:
    """
    Replace logical operators in an expression string between symbolic and scenario forms.

    By default, replaces textual logical operators ('AND', 'OR') with symbolic 
    equivalents ('&', '|'). If `scenario_operators` is True, performs the reverse 
    replacement: symbolic operators ('&', '|') are replaced with textual ones.

    Parameters
    ----------
    expression_str : str
        The expression string where replacements will be performed.
    scenario_operators : bool, optional
        If True, replace '&' with 'AND' and '|' with 'OR'.
        If False (default), replace 'AND' with '&' and 'OR' with '|'.

    Returns
    -------
    str
        The updated expression string with logical operators replaced.

    Examples
    --------
    >>> replace_logical_operators("a > 10 AND b <= 20")
    'a > 10 & b <= 20'

    >>> replace_logical_operators("a > 10 & b <= 20", scenario_operators=True)
    'a > 10 AND b <= 20'
    """
    if scenario_operators:
        return expression_str.replace('&', 'AND').replace('|', 'OR')
    else:
        return expression_str.replace('AND', '&').replace('OR', '|')

def _transform_expression_to_symbolic(expression_str: str) -> tuple[str, dict[str, str]]:
    """
    Transform a raw logical expression into a symbolic, indexed form.

    The transformation pipeline:
      1) Parse the input expression using the configured pyparsing grammar.
      2) Extract all leaf conditional expressions (e.g., "a <= 3", "b > 10").
      3) Map each conditional expression to an indexed key: x1, x2, ..., xn.
      4) Replace those expressions in the original string by the keys.
      5) Replace logical operators 'AND'/'OR' with '&'/'|'.

    Parameters
    ----------
    expression_str : str
        Original logical expression, e.g.:
        "(((a <= 3 AND (b > 10 OR c == 10)) OR ((d != 5 AND e >= 20) OR f < 2)) AND ((g <= 7 OR h > 8) AND (i == 9 OR j != 3)))"

    Returns
    -------
    tuple[str, dict[str, str]]
        - symbolic_expression_str: the normalized/symbolic expression, e.g.:
          "(((x1 & (x2 | x3)) | ((x4 & x5) | x6)) & ((x7 | x8) & (x9 | x10)))"
        - map_conditional_expression_to_key_dict: mapping from keys to original
          conditional expressions, e.g.:
          {
            "x1": "a <= 3",
            "x2": "b > 10",
            ...
          }

    Raises
    ------
    pyparsing.ParseException
        If the input expression cannot be parsed by the configured grammar.

    Notes
    -----
    - Keys are assigned in the order conditional expressions appear.
    - Logical operator mapping: AND -> '&', OR -> '|'.
    """
    parse_settings: ParserElement = _configure_expression_parsing()
    parsed_expression: ParseResults = parse_settings.parseString(expression_str, parseAll=True)


    conditional_expressions_list: List[str] = _extract_conditional_expressions(parsed_expression)

    map_conditional_expression_to_key_dict: Dict[str, str] = (
        _conditional_expressions_to_key_dict(conditional_expressions_list)
    )

    expression_str = _replace_conditional_expression_to_keys(expression_str, map_conditional_expression_to_key_dict)
    expression_str = _replace_logical_operators(expression_str)

    symbolic_expression_str = expression_str
    return symbolic_expression_str, map_conditional_expression_to_key_dict

def _symbolic_to_dnf(symbolic_expression_str: str) -> str:
    """
    Convert a symbolic logical expression into Disjunctive Normal Form (DNF).

    The function uses `sympy.sympify` to parse the input expression into a
    symbolic form, and then applies `sympy.to_dnf` to transform it into its DNF
    equivalent.

    Parameters
    ----------
    symbolic_expression_str : str
        Logical expression in string format, where variables are indexed keys
        (e.g., x1, x2, ...) and logical operators are symbolic:
        - AND: '&'
        - OR : '|'
        - NOT: '~' (if applicable)

        Example:
            "((x1 & (x2 | x3)) | x4)"

    Returns
    -------
    str
        The logical expression converted into Disjunctive Normal Form.

    Examples
    --------
    >>> _to_dnf("(x1 & (x2 | x3)) | x4")
    '(x1 & x2) | (x1 & x3) | x4'

    Notes
    -----
    - `simplify=True` reduces the result when possible.
    - `force=True` allows conversion even if the input is not strictly Boolean.
    """
    logical_expression = sympify(symbolic_expression_str)
    dnf_expr = to_dnf(logical_expression, simplify=True, force=True)
    return str(dnf_expr)

def _revert_keys_to_conditional_expressions(
    dnf_expr: str, 
    map_conditional_expression_to_key_dict: dict[str, str]
) -> str:
    """
    Replace occurrences of the mapping keys (e.g., 'x1', 'x2', ...)
    with their original conditional expressions in a logical expression string.

    Parameters
    ----------
    dnf_expr : str
        The logical expression string (usually in DNF form) containing keys.
        Example: '(x1 & x2) | x3'
    map_conditional_expression_to_key_dict : dict[str, str]
        Mapping of keys back to original conditional expressions.
        Example: {'x1': 'a <= 3', 'x2': 'b > 10', 'x3': 'c != 5'}

    Returns
    -------
    str
        The expression with the keys replaced by the original conditions.

    Examples
    --------
    >>> mapping = {'x1': 'a <= 3', 'x2': 'b > 10', 'x3': 'c != 5'}
    >>> revert_keys_to_values("(x1 & x2) | x3", mapping)
    '(a <= 3 & b > 10) | c != 5'
    """
    for key, value in map_conditional_expression_to_key_dict.items():
        dnf_expr = dnf_expr.replace(key, value)
    return dnf_expr

def _revert_logical_operators(dnf_expr: str) -> str:
    """
    Revert symbolic logical operators ('&', '|') back to their textual forms 
    ('AND', 'OR') in a logical expression string.

    Parameters
    ----------
    dnf_expr : str
        Logical expression string (typically in DNF form) that contains 
        symbolic operators '&' and '|'.

    Returns
    -------
    str
        The expression string with symbolic operators replaced by 
        their textual equivalents 'AND' and 'OR'.

    Examples
    --------
    >>> revert_logical_operators("(x1 & x2) | x3")
    '(x1 AND x2) OR x3'
    """
    dnf_expr= _replace_logical_operators(dnf_expr, scenario_operators=True)
    return dnf_expr

def expression_to_dnf(
    expression_str: str,
    *,
    output_operators: Literal["text", "symbolic"] = "text",
    return_mapping: bool = False,
):
    """
    Compile a raw logical expression into Disjunctive Normal Form (DNF).

    Pipeline:
      1) _transform_expression_to_symbolic: parses the expression, extracts
         conditionals, maps them to x1..xn, and converts AND/OR -> &/|.
      2) _to_dnf: converts the symbolic expression into DNF.
      3) _revert_keys_to_conditional_expressions: replaces x1..xn with the
         original conditional expressions.
      4) _revert_logical_operators (optional): converts &/| -> AND/OR
         (if output_operators="text").

    Parameters
    ----------
    expression_str : str
        The original logical expression in string format.
    output_operators : {"text", "symbolic"}, default "text"
        - "text": the final result uses textual operators AND/OR.
        - "symbolic": the final result uses symbolic operators & and |.
    return_mapping : bool, default False
        If True, also returns the dictionary mapping keys (x1, x2, ...) 
        back to the original conditional expressions.

    Returns
    -------
    str  or  (str, dict[str, str])
        - If return_mapping=False: the final DNF expression as a string.
        - If return_mapping=True: a tuple (dnf_str, mapping_dict).

    Raises
    ------
    pyparsing.ParseException
        If the input expression cannot be parsed by the configured grammar.

    Notes
    -----
    - The key mapping preserves the order in which conditional expressions 
      appear in the original input.
    - Logical operator mapping rules:
        AND -> '&'
        OR  -> '|'
        ~   -> NOT (if applicable).
    """
    # 1) Transform into symbolic expression (&, |) + mapping
    symbolic_expression_str, map_conditional_expression_to_key_dict = _transform_expression_to_symbolic(expression_str)

    # 2) Convert to DNF in symbolic form
    dnf_symbolic_str = _symbolic_to_dnf(symbolic_expression_str)

    # 3) Replace keys with original conditions
    dnf_with_values = _revert_keys_to_conditional_expressions(
        dnf_symbolic_str, map_conditional_expression_to_key_dict
    )

    # 4) Adjust operators depending on output format
    if output_operators == "text":
        final_str = _revert_logical_operators(dnf_with_values)  # &/| -> AND/OR
    else:
        final_str = dnf_with_values  # keep &/|

    if return_mapping:
        return final_str, map_conditional_expression_to_key_dict
    return final_str