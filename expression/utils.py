from typing_extensions import Literal
from pyparsing import Dict, ParseResults, Word, alphas, nums, oneOf, infixNotation, opAssoc, ParserElement
from typing import List, Union
import re

from sympy import Tuple, sympify, to_dnf

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

def _extract_conditional_expressions(expression_str: str) -> List[str]:
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

    parse_settings: ParserElement = _configure_expression_parsing()
    parsed_expression: ParseResults = parse_settings.parseString(expression_str, parseAll=True)

    parsed_expr_list=parsed_expression.asList()

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
    


    conditional_expressions_list: List[str] = _extract_conditional_expressions(expression_str)

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

def _decompose_conditional_expression(conditional_expression: str) -> Tuple[str, str, str]:
    """
    Parse the expression into its components: variable, operator, and value.
    """
    match = re.match(r"(\w+)\s*(>=|<=|>|<|==|!=)\s*(.+)", conditional_expression)
    if match:
        variable, operator, value = match.groups()
        return variable, operator, value
    else:
        raise ValueError(f"Invalid expression format: {conditional_expression}")
    
def _get_conditional_expression_region(
    var_name: str,
    operator: str,
    value: Union[int, float, str],
    min_val: float,
    max_val: float,
) -> Union[Tuple[float, float], List[Tuple[float, float]]]:
    """
    Compute the numeric region(s) within [min_val, max_val] that satisfy
    a given conditional expression.

    The function interprets a condition of the form:
        <var_name> <operator> <value>

    and maps it into a numeric interval (or two disjoint intervals in the
    case of '!=').

    Parameters
    ----------
    var_name : str
        The name of the variable in the conditional expression.
        (Currently unused, but included for context/consistency).
    operator : str
        The comparison operator. Supported operators: >=, <=, >, <, ==, !=.
    value : int, float, or str
        The right-hand side of the conditional expression. Converted to float.
    min_val : float
        Minimum possible value for the variable.
    max_val : float
        Maximum possible value for the variable.

    Returns
    -------
    tuple[float, float] or list[tuple[float, float]]
        - A single tuple (low, high) if the operator defines one continuous range.
        - A list of two tuples if the operator is '!=', representing two disjoint ranges.

    Raises
    ------
    ValueError
        If an unsupported operator is provided.

    Examples
    --------
    >>> compute_satisfying_region("a", ">=", 3, 0, 10)
    (3.0, 10.0)

    >>> compute_satisfying_region("b", "<", 5, 0, 10)
    (0.0, 4.999999999)

    >>> compute_satisfying_region("c", "!=", 7, 0, 10)
    [(0.0, 6.999999999), (7.000000001, 10.0)]
    """
    value = float(value)

    if operator == '>=':
        return (value, max_val)
    elif operator == '<=':
        return (min_val, value)
    elif operator == '>':
        return (value + 1e-9, max_val)  # Adding a small value to make it exclusive
    elif operator == '<':
        return (min_val, value - 1e-9) # Subtracting a small value to make it exclusive
    elif operator == '==':
        return (value, value)
    elif operator == '!=':
        return [(min_val, value - 1e-9), (value + 1e-9, max_val)]
    else:
        raise ValueError(f"Unsupported operator: {operator}")

def _calculate_jaccard_similarity(
    conditional_expression_1: str,
    conditional_expression_2: str,
    monitored_parameters_dict: dict,
) -> float:
    """
    Calculate the Jaccard similarity between two conditional expressions.

    This function decomposes each conditional expression into its components
    (variable, operator, value), determines the numeric region(s) that satisfy
    each expression given the monitored variable ranges, and computes the
    Jaccard similarity as:

        Jaccard(A, B) = |A ∩ B| / |A ∪ B|

    Special handling is included for cases where one or both expressions use
    the equality operator (`==`) to ensure correct overlap calculation.

    Parameters
    ----------
    conditional_expression_1 : str
        First conditional expression in the form "<variable> <operator> <value>".
        Example: "temperature >= 30".
    conditional_expression_2 : str
        Second conditional expression in the same format.
        Example: "temperature < 40".
    monitored_parameters_dict : dict
        Dictionary containing the monitored variables with their value ranges.
        Expected format:
        {
            "variable_name": {
                "min_value": float,
                "max_value": float,
                "type": str   # e.g., "int" or "float"
            },
            ...
        }

    Returns
    -------
    float
        Jaccard similarity score between the two conditional expressions,
        in the range [0.0, 1.0].
        - 0.0 means no overlap between the value ranges.
        - 1.0 means complete overlap (identical ranges).

    Raises
    ------
    ValueError
        If either expression cannot be parsed or an unsupported operator is used.

    Notes
    -----
    - If the expressions reference different variables, similarity is 0.0.
    - Supported operators: <=, >=, <, >, ==, !=.
    - For '!=' the range is split into two disjoint intervals.
    - For equality comparisons (== vs other operators), overlap is counted as a
      single point within the range.

    Examples
    --------
    >>> monitored_params = {
    ...     "a": {"min_value": 0, "max_value": 10, "type": "int"}
    ... }
    >>> _calculate_jaccard_similarity("a >= 3", "a <= 7", monitored_params)
    0.57143

    >>> _calculate_jaccard_similarity("a == 5", "a != 5", monitored_params)
    0.0

    >>> _calculate_jaccard_similarity("a == 5", "a >= 0", monitored_params)
    0.1
    """

    try:
        var1, op1, val1 = _decompose_conditional_expression(conditional_expression_1)
        var2, op2, val2 = _decompose_conditional_expression(conditional_expression_2)
    except ValueError as e:
        print(e)
        return 0.0

    # Ensure the variable names are the same
    if var1 != var2:
        return 0.0

    # Get variable ranges
    var_info = monitored_parameters_dict.get(var1)
    if not var_info:
        print(f"Variable {var1} not found in ranges.")
        return 0.0

    min_val = var_info['min_value']
    max_val = var_info['max_value']

    # Get ranges for each expression
    region1 = _get_conditional_expression_region(var1, op1, val1, min_val, max_val)
    region2 = _get_conditional_expression_region(var2, op2, val2, min_val, max_val)

    def calculate_intersection_union(region1, region2):
        """
        Helper function to calculate intersection and union of two ranges.
        """
        if isinstance(region1, list):
            intersections = []
            for r1 in region1:
                if isinstance(region2, list):
                    for r2 in region2:
                        intersections.append((max(r1[0], r2[0]), min(r1[1], r2[1])))
                else:
                    intersections.append((max(r1[0], region2[0]), min(r1[1], region2[1])))
        else:
            if isinstance(region2, list):
                intersections = [(max(region1[0], r2[0]), min(region1[1], r2[1])) for r2 in region2]
            else:
                intersections = [(max(region1[0], region2[0]), min(region1[1], region2[1]))]
        
        valid_intersections = [r for r in intersections if r[0] <= r[1]]
        intersection_length = sum(r[1] - r[0] for r in valid_intersections)
        
        union_min = min(region1[0] if not isinstance(region1, list) else min(r[0] for r in region1),
                        region2[0] if not isinstance(region2, list) else min(r[0] for r in region2))
        union_max = max(region1[1] if not isinstance(region1, list) else max(r[1] for r in region1),
                        region2[1] if not isinstance(region2, list) else max(r[1] for r in region2))
        union_length = union_max - union_min
        
        return intersection_length, union_length

    # Calculate intersection and union considering the equality operator cases
    if op1 == '==' and op2 != '==':
        if isinstance(region2, list):
            region2_min, region2_max = min(region2[0][0], region2[1][0]), max(region2[0][1], region2[1][1])
            if region2_min <= region1[0] <= region2_max:
                intersection_length = 1
                union_length = region2_max - region2_min
            else:
                return 0.0
        else:
            if region2[0] <= region1[0] <= region2[1]:
                intersection_length = 1
                union_length = region2[1] - region2[0]
            else:
                return 0.0
    elif op2 == '==' and op1 != '==':
        if isinstance(region1, list):
            region1_min, region1_max = min(region1[0][0], region1[1][0]), max(region1[0][1], region1[1][1])
            if region1_min <= region2[0] <= region1_max:
                intersection_length = 1
                union_length = region1_max - region1_min
            else:
                return 0.0
        else:
            if region1[0] <= region2[0] <= region1[1]:
                intersection_length = 1
                union_length = region1[1] - region1[0]
            else:
                return 0.0
    elif op1 == '==' and op2 == '==':
        if val1 == val2:
            return 1.0
        else:
            return 0.0
    else:
        intersection_length, union_length = calculate_intersection_union(region1, region2)

    # Calculate the Jaccard similarity
    similarity = intersection_length / union_length
    return round(similarity,5)


def pair_conditional_expressions(conditional_expression_1: str,
                                conditional_expression_2: str) -> str:
    
    conditional_expression_list_1 = _extract_conditional_expressions(conditional_expression_1)
    conditional_expression_list_2 = _extract_conditional_expressions(conditional_expression_2)
    
    pairs = []
    
    # Extract variable names from leaves
    def extract_variable(leaf):
        return leaf.split()[0]
    
    variables1 = {extract_variable(leaf): leaf for leaf in conditional_expression_list_1}
    variables2 = {extract_variable(leaf): leaf for leaf in conditional_expression_list_2}
    
    # Create pairs
    for var in variables1:
        if var in variables2:
            pairs.append((variables1[var], variables2[var]))
    
    return pairs


def calculate_parameter_similarity(
    expression_1: str,
    expression_2: str,
    monitored_parameters_dict: dict,
) -> list[dict]:
    """
    Calculate similarity scores between two expressions
    by decomposing them into atomic pairs (conditional expression) and evaluating each pair.

    This function converts both input expressions into their 
    Disjunctive Normal Form (DNF), generates pairs of atomic 
    conditional expressions, and computes the Jaccard similarity 
    for each pair based on the monitored parameter ranges.

    Parameters
    ----------
    expression_1 : str
        First logical expression, which can be a simple conditional
        (e.g., "temperature >= 30") or a compound expression with
        logical operators (e.g., "temperature >= 30 AND battery < 10").
    expression_2 : str
        Second logical expression, in the same format as expression_1.
        Example: "temperature < 40 OR humidity == 50".
    monitored_parameters_dict : dict
        Dictionary containing metadata of monitored parameters with 
        their valid ranges. Example:
        {
            "temperature": {"min_value": 0, "max_value": 100, "type": "float"},
            "battery": {"min_value": 0, "max_value": 100, "type": "int"}
        }

    Returns
    -------
    list of dict
        A list of dictionaries, where each dictionary maps a pair of
        conditional expressions (tuple) to their similarity score.
        Example:
        [
            {("temperature >= 30", "temperature < 40"): 0.57143}
        ]

    Notes
    -----
    - Similarity is only computed if both conditions refer to the 
      same variable.
    - Operators supported: <=, >=, <, >, ==, !=.
    - Each pair is compared using the Jaccard similarity measure.

    Examples
    --------
    >>> monitored_params = {
    ...     "a": {"min_value": 0, "max_value": 10, "type": "int"}
    ... }
    >>> calculate_parameter_similarity("a >= 3", "a <= 7", monitored_params)
    [
        {("a >= 3", "a <= 7"): 0.57143}
    ]
    """

    expression_1 = expression_to_dnf(expression_1, output_operators="text")
    expression_2 = expression_to_dnf(expression_2, output_operators="text")


    pair_conditional_expressions_list = pair_conditional_expressions(
        expression_1,
        expression_2
    )

    parameter_similarities = []

    for conditional_expression_pair in pair_conditional_expressions_list:
        conditional_expression_1 = conditional_expression_pair[0]
        conditional_expression_2 = conditional_expression_pair[1]

        jaccard_similarity = _calculate_jaccard_similarity(
        conditional_expression_1,
        conditional_expression_2,
        monitored_parameters_dict)

        parameter_similarities.append({conditional_expression_pair: jaccard_similarity})

    return parameter_similarities

def _extract_parameters(conditional_expressions: List[str]) -> List[str]:
    """
    Extract variable names from a list of conditional expressions.

    Each expression must follow the format:
        <variable> <operator> <value>

    Supported operators: ==, !=, <, <=, >, >=
    The value is assumed to be numeric.

    Parameters
    ----------
    conditional_expressions : list of str
        List of strings, each containing a conditional expression.

    Returns
    -------
    list of str
        List of variable names found in the expressions.

    Examples
    --------
    >>> extract_parameters(["a > 10", "b <= 20", "c != 5"])
    ['a', 'b', 'c']
    >>> extract_parameters(["x == 1", "y >= 100"])
    ['x', 'y']
    """
    variables = []
    for expr in conditional_expressions:
        match = re.match(r"([a-zA-Z_]\w*)\s*(==|!=|[<>]=?)\s*([0-9]+)", expr)
        if match:
            variables.append(match.group(1))
    return variables

def _tversky_similarity(vars1, vars2, alpha=1.0, beta=1.0) -> float:
    """
    Compute the Tversky similarity index between two sets of variables.

    The Tversky index is a generalization of several similarity measures:
    - When alpha = beta = 0.5, it reduces to the Dice coefficient.
    - When alpha = beta = 1.0, it reduces to the Jaccard index.
    - When alpha != beta, it allows asymmetric weighting of differences.

    Parameters
    ----------
    vars1 : list
        First list of variables.
    vars2 : list
        Second list of variables.
    alpha : float, optional (default=1.0)
        Weight for elements unique to `vars1`.
    beta : float, optional (default=1.0)
        Weight for elements unique to `vars2`.

    Returns
    -------
    float
        Tversky similarity score in the range [0.0, 1.0].
        - 1.0 indicates identical sets.
        - 0.0 indicates no overlap.

    Notes
    -----
    - This metric is useful for comparing sets when false positives 
      and false negatives need different penalties.
    - The formula is:

        T(A, B) = |A ∩ B| / (|A ∩ B| + α|A \ B| + β|B \ A|)

    Examples
    --------
    >>> tversky_similarity(["a", "b", "c"], ["b", "c", "d"])
    0.5
    >>> tversky_similarity(["a", "b", "c"], ["b", "c", "d"], alpha=0.7, beta=0.3)
    0.5555555555555556
    >>> tversky_similarity(["x", "y"], ["x", "y"], alpha=1.0, beta=1.0)
    1.0
    >>> tversky_similarity(["x"], ["y"], alpha=1.0, beta=1.0)
    0.0
    """
    set1 = set(vars1)
    set2 = set(vars2)

    intersection = len(set1 & set2)
    only_in_set1 = len(set1 - set2)
    only_in_set2 = len(set2 - set1)

    return intersection / (intersection + alpha * only_in_set1 + beta * only_in_set2)

def _penalty(vars1, vars2, alpha=1.0, beta=1.0) -> float:
    """
    Compute the penalty score as the complement of the Tversky similarity.

    The penalty quantifies dissimilarity between two sets of variables.
    It is defined as:

        penalty(A, B) = 1 - Tversky(A, B)

    where `Tversky(A, B)` is the Tversky similarity index.

    Parameters
    ----------
    vars1 : list
        First list of variables.
    vars2 : list
        Second list of variables.
    alpha : float, optional (default=1.0)
        Weight for the elements unique to `vars1`.
    beta : float, optional (default=1.0)
        Weight for the elements unique to `vars2`.

    Returns
    -------
    float
        Penalty score in the range [0.0, 1.0].
        - 0.0 indicates identical sets.
        - Values closer to 1.0 indicate greater dissimilarity.

    Notes
    -----
    - This is essentially a dissimilarity measure derived from the Tversky index.
    - It can be used as a distance-like metric in clustering, anomaly detection,
      or measuring differences between variable sets.

    Examples
    --------
    >>> penalty(["a", "b", "c"], ["b", "c", "d"])
    0.5
    >>> penalty(["a", "b"], ["a", "b"])
    0.0
    >>> penalty(["x"], ["y"])
    1.0
    >>> penalty(["a", "b", "c"], ["b", "c", "d"], alpha=0.7, beta=0.3)
    0.4444444444444444
    """
    return 1 - _tversky_similarity(vars1, vars2, alpha, beta)
