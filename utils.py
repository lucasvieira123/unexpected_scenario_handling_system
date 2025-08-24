from typing_extensions import Literal
from pyparsing import Dict, ParseResults, Word, alphas, nums, oneOf, infixNotation, opAssoc, ParserElement
from typing import List, Optional, Union
import re

from sympy import Tuple, sympify, to_dnf

from expression.conditional_expression import ConditionalExpression
from scenario.scenario_BDD import ScenarioBDD

def _configure_conditional_expression_parsing() -> ParserElement:
    """
    Configure and return the parsing grammar for logical and relational expressions.

    This function sets up a parsing configuration using the `pyparsing` library. 
    The grammar supports identifiers, numeric values, relational operators, and 
    logical operators, enabling the parsing of relational expressions typically 
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
        >>> parser = _configure_conditional_expression_parsing()
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
    relational_operator = oneOf("<= >= < > == !=")

    # Define operands
    operand = identifier | number

    # Define logical expressions with operator precedence
    parse_settings = infixNotation(operand,
        [
            (relational_operator, 2, opAssoc.LEFT),
            ("AND", 2, opAssoc.LEFT),
            ("OR", 2, opAssoc.LEFT),
        ])

    return parse_settings

def _extract_relational_expressions(conditional_expression_str: str) -> List[str]:
    """
    Recursively extract leaf relational expressions from a parsed conditional expression.

    This function traverses the structure produced by the conditional expression parser
    (e.g., `_configure_conditional_expression_parsing`) and collects only the simple
    relational conditions (e.g., "a > 10", "b <= 20"). It ignores logical
    operators (AND, OR) and nested groupings, drilling down until it reaches
    atomic relational expressions.

    Args:
        parsed_expr (Union[str, ParseResults]): The parsed conditional expression object, which can be:
            - a string (base token)
            - a ParseResults object (possibly nested) returned by pyparsing

    Returns:
        List[str]: A list of leaf relational expressions represented as strings.
                   Each string has the format "<identifier> <operator> <value>".

    Example:
        >>> parser = _configure_conditional_expression_parsing()
        >>> expr = parser.parseString("a > 10 AND (b <= 20 OR c != 5)")
        >>> expr
        ['a > 10', 'b <= 20', 'c != 5']
    """

    parse_settings: ParserElement = _configure_conditional_expression_parsing()
    parsed_conditional_expression: ParseResults = parse_settings.parseString(conditional_expression_str, parseAll=True)

    parsed_conditional_expr_list=parsed_conditional_expression.asList()

    if isinstance(parsed_conditional_expr_list, str):
        return []
    elif len(parsed_conditional_expr_list) == 3 and parsed_conditional_expr_list[1] in ["<=", ">=", "<", ">", "==", "!="]:
        return [" ".join(parsed_conditional_expr_list)]
    else:
        leaves: List[str] = []
        for sub_expr in parsed_conditional_expr_list:
            leaves.extend(_extract_relational_expressions(sub_expr))
        return leaves

def _relational_expressions_to_key_dict(relational_expressions: list[str]) -> dict[str, str]:
    """
    Convert a list of relational expressions (as strings) into a dictionary 
    with indexed keys in the form "x1", "x2", ..., "xn".

    Parameters
    ----------
    relational_expressions : list of str
        List of relational expressions in string format.

    Returns
    -------
    dict
        Dictionary where keys are 'x1', 'x2', ..., 'xn' and values are 
        the relational expressions from the input list.

    Examples
    --------
    >>> relational_expressions_to_key_dict(["a > 10", "b <= 20", "c != 5"])
    {'x1': 'a > 10', 'x2': 'b <= 20', 'x3': 'c != 5'}

    >>> relational_expressions_to_key_dict([])
    {}
    """
    map_key = {f"x{i+1}": expr for i, expr in enumerate(relational_expressions)}

    return map_key

def _replace_relational_expression_to_keys(relational_expression_str: str, map_key:dict) -> str:
    """
    Replace occurrences of dictionary values with their corresponding keys in the relational expression in string.

    This function scans through the input relational expression in string and substitutes every occurrence 
    of each dictionary value with its associated key.

    Parameters
    ----------
    string : relational_expression_str
        The relational expression string where replacements will be performed.
    dictionary : dict
        Dictionary mapping keys to values. Each value in the dictionary will be 
        replaced with its corresponding key when found in the input relational expression string.

    Returns
    -------
    str
        The updated relational expression string with values replaced by keys.

    Examples
    --------
    >>> mapping = {'x1': 'a > 10', 'x2': 'b <= 20'}
    >>> replace_values_with_keys("if (a > 10 AND b <= 20)", mapping)
    'if (x1 AND x2)'

    >>> replace_values_with_keys("c != 5", {'x3': 'c != 5'})
    'x3'
    """
    for key, value in map_key.items():
        relational_expression_str = relational_expression_str.replace(value, key)
    return relational_expression_str

def _replace_logical_operators(conditional_expression_str: str, scenario_operators: bool = False) -> str:
    """
    Replace logical operators in the conditional expression string between symbolic and scenario forms.

    By default, replaces textual logical operators ('AND', 'OR') with symbolic 
    equivalents ('&', '|'). If `scenario_operators` is True, performs the reverse 
    replacement: symbolic operators ('&', '|') are replaced with textual ones.

    Parameters
    ----------
    conditional_expression_str : str
        The conditional expression string where replacements will be performed.
    scenario_operators : bool, optional
        If True, replace '&' with 'AND' and '|' with 'OR'.
        If False (default), replace 'AND' with '&' and 'OR' with '|'.

    Returns
    -------
    str
        The updated conditional expression string with logical operators replaced.

    Examples
    --------
    >>> replace_logical_operators("a > 10 AND b <= 20")
    'a > 10 & b <= 20'

    >>> replace_logical_operators("a > 10 & b <= 20", scenario_operators=True)
    'a > 10 AND b <= 20'
    """
    if scenario_operators:
        return conditional_expression_str.replace('&', 'AND').replace('|', 'OR')
    else:
        return conditional_expression_str.replace('AND', '&').replace('OR', '|')

def _transform_conditional_expression_to_symbolic(conditional_expression_str: str) -> tuple[str, dict[str, str]]:
    """
    Transform a raw conditional expression into a symbolic, indexed form.

    The transformation pipeline:
      1) Parse the input conditional expression using the configured pyparsing grammar.
      2) Extract all leaf relational expressions (e.g., "a <= 3", "b > 10").
      3) Map each relational expression to an indexed key: x1, x2, ..., xn.
      4) Replace those expressions in the original conditional expression by the keys.
      5) Replace logical operators 'AND'/'OR' with '&'/'|'.

    Parameters
    ----------
    conditional_expression_str : str
        Original conditional expression, e.g.:
        "(((a <= 3 AND (b > 10 OR c == 10)) OR ((d != 5 AND e >= 20) OR f < 2)) AND ((g <= 7 OR h > 8) AND (i == 9 OR j != 3)))"

    Returns
    -------
    tuple[str, dict[str, str]]
        - symbolic_conditional_expression_str: the normalized/symbolic conditional expression, e.g.:
          "(((x1 & (x2 | x3)) | ((x4 & x5) | x6)) & ((x7 | x8) & (x9 | x10)))"
        - map_relational_expression_to_key_dict: mapping from keys to original
          relational expressions, e.g.:
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
    - Keys are assigned in the order relational expressions appear.
    - Logical operator mapping: AND -> '&', OR -> '|'.
    """
    


    relational_expressions_list: List[str] = _extract_relational_expressions(conditional_expression_str)

    map_relational_expression_to_key_dict: Dict[str, str] = (
        _relational_expressions_to_key_dict(relational_expressions_list)
    )

    conditional_expression_str = _replace_relational_expression_to_keys(conditional_expression_str, map_relational_expression_to_key_dict)
    conditional_expression_str = _replace_logical_operators(conditional_expression_str)

    symbolic_expression_str = conditional_expression_str
    return symbolic_expression_str, map_relational_expression_to_key_dict

def _symbolic_conditional_to_dnf(symbolic_conditional_expression_str: str) -> str:
    """
    Convert a symbolic conditional expression into Disjunctive Normal Form (DNF).

    The function uses `sympy.sympify` to parse the input conditional expression into a
    symbolic form, and then applies `sympy.to_dnf` to transform it into its DNF
    equivalent.

    Parameters
    ----------
    symbolic_conditional_expression_str : str
        Conditional expression in string format, where variables are indexed keys
        (e.g., x1, x2, ...) and logical operators are symbolic:
        - AND: '&'
        - OR : '|'
        - NOT: '~' (if applicable)

        Example:
            "((x1 & (x2 | x3)) | x4)"

    Returns
    -------
    str
        The conditional expression converted into Disjunctive Normal Form.

    Examples
    --------
    >>> _to_dnf("(x1 & (x2 | x3)) | x4")
    '(x1 & x2) | (x1 & x3) | x4'

    Notes
    -----
    - `simplify=True` reduces the result when possible.
    - `force=True` allows conversion even if the input is not strictly Boolean.
    """
    simplified_conditional_expression = sympify(symbolic_conditional_expression_str)
    dnf_cond_expr = to_dnf(simplified_conditional_expression, simplify=True, force=True)
    return str(dnf_cond_expr)

def _revert_keys_to_relational_expressions(
    dnf_cond_expr: str, 
    map_relational_expression_to_key_dict: dict[str, str]
) -> str:
    """
    Replace occurrences of the mapping keys (e.g., 'x1', 'x2', ...)
    with their original relational expressions in a conditional expression string.

    Parameters
    ----------
    dnf_cond_expr : str
        The conditional expression string (usually in DNF form) containing keys.
        Example: '(x1 & x2) | x3'
    map_relational_expression_to_key_dict : dict[str, str]
        Mapping of keys back to original relational expressions.
        Example: {'x1': 'a <= 3', 'x2': 'b > 10', 'x3': 'c != 5'}

    Returns
    -------
    str
        The conditional expression with the keys replaced by the original conditions.

    Examples
    --------
    >>> mapping = {'x1': 'a <= 3', 'x2': 'b > 10', 'x3': 'c != 5'}
    >>> revert_keys_to_values("(x1 & x2) | x3", mapping)
    '(a <= 3 & b > 10) | c != 5'
    """
    for key, value in map_relational_expression_to_key_dict.items():
        dnf_cond_expr = dnf_cond_expr.replace(key, value)
    return dnf_cond_expr

def _revert_logical_operators(dnf_cond_expr: str) -> str:
    """
    Revert symbolic logical operators ('&', '|') back to their textual forms 
    ('AND', 'OR') in a conditional expression string.

    Parameters
    ----------
    dnf_cond_expr : str
        conditional expression string (typically in DNF form) that contains 
        symbolic operators '&' and '|'.

    Returns
    -------
    str
        The conditional expression string with symbolic operators replaced by 
        their textual equivalents 'AND' and 'OR'.

    Examples
    --------
    >>> revert_logical_operators("(x1 & x2) | x3")
    '(x1 AND x2) OR x3'
    """
    dnf_cond_expr= _replace_logical_operators(dnf_cond_expr, scenario_operators=True)
    return dnf_cond_expr

def conditional_expression_to_dnf(
    conditional_expression_str: str,
    *,
    output_operators: Literal["text", "symbolic"] = "text",
    return_mapping: bool = False,
):
    """
    Compile a raw conditional expression into Disjunctive Normal Form (DNF).

    Pipeline:
      1) _transform_conditional_expression_to_symbolic: parses the conditional expression, extracts
         relational expressions, maps them to x1..xn, and converts AND/OR -> &/|.
      2) _to_dnf: converts the symbolic conditional expression into DNF.
      3) _revert_keys_to_relational_expressions: replaces x1..xn with the
         original relational expressions.
      4) _revert_logical_operators (optional): converts &/| -> AND/OR
         (if output_operators="text").

    Parameters
    ----------
    conditional_expression_str : str
        The original conditional expression in string format.
    output_operators : {"text", "symbolic"}, default "text"
        - "text": the final result uses textual operators AND/OR.
        - "symbolic": the final result uses symbolic operators & and |.
    return_mapping : bool, default False
        If True, also returns the dictionary mapping keys (x1, x2, ...) 
        back to the original relational expressions.

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
    - The key mapping preserves the order in which relational expressions 
      appear in the original input.
    - Logical operator mapping rules:
        AND -> '&'
        OR  -> '|'
        ~   -> NOT (if applicable).
    """
    # 1) Transform into symbolic expression (&, |) + mapping
    symbolic_conditional_expression_str, map_relational_expression_to_key_dict = _transform_conditional_expression_to_symbolic(conditional_expression_str)

    # 2) Convert to DNF in symbolic form
    dnf_symbolic_conditional_str = _symbolic_conditional_to_dnf(symbolic_conditional_expression_str)

    # 3) Replace keys with original conditions
    dnf_conditional_expr_with_relational_expr = _revert_keys_to_relational_expressions(
        dnf_symbolic_conditional_str, map_relational_expression_to_key_dict
    )

    # 4) Adjust operators depending on output format
    if output_operators == "text":
        final_dnf_conditional_exp_str = _revert_logical_operators(dnf_conditional_expr_with_relational_expr)  # &/| -> AND/OR
    else:
        final_dnf_conditional_exp_str = dnf_conditional_expr_with_relational_expr  # keep &/|

    if return_mapping:
        return final_dnf_conditional_exp_str, map_relational_expression_to_key_dict
    return final_dnf_conditional_exp_str

def _decompose_relational_expression(relational_expression: str) -> Tuple[str, str, str]:
    """
    Parse the relational expression into its components: variable, operator, and value.
    """
    match = re.match(r"(\w+)\s*(>=|<=|>|<|==|!=)\s*(.+)", relational_expression)
    if match:
        variable, operator, value = match.groups()
        return variable, operator, value
    else:
        raise ValueError(f"Invalid expression format: {relational_expression}")
    
def _get_relational_expression_region(
    var_name: str,
    operator: str,
    value: Union[int, float, str],
    min_val: float,
    max_val: float,
) -> Union[Tuple[float, float], List[Tuple[float, float]]]:
    """
    Compute the numeric region(s) within [min_val, max_val] that satisfy
    a given relational expression.

    The function interprets a condition of the form:
        <var_name> <operator> <value>

    and maps it into a numeric interval (or two disjoint intervals in the
    case of '!=').

    Parameters
    ----------
    var_name : str
        The name of the variable in the relational expression.
        (Currently unused, but included for context/consistency).
    operator : str
        The comparison operator. Supported operators: >=, <=, >, <, ==, !=.
    value : int, float, or str
        The right-hand side of the relational expression. Converted to float.
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
    relational_expression_1: str,
    relational_expression_2: str,
    monitored_parameters_dict: dict,
) -> float:
    """
    Calculate the Jaccard similarity between two relational expressions.

    This function decomposes each relational expression into its components
    (variable, operator, value), determines the numeric region(s) that satisfy
    each expression given the monitored variable ranges, and computes the
    Jaccard similarity as:

        Jaccard(A, B) = |A ∩ B| / |A ∪ B|

    Special handling is included for cases where one or both expressions use
    the equality operator (`==`) to ensure correct overlap calculation.

    Parameters
    ----------
    relational_expression_1 : str
        First relational expression in the form "<variable> <operator> <value>".
        Example: "temperature >= 30".
    relational_expression_2 : str
        Second relational expression in the same format.
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
        Jaccard similarity score between the two relational expressions,
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
        var1, op1, val1 = _decompose_relational_expression(relational_expression_1)
        var2, op2, val2 = _decompose_relational_expression(relational_expression_2)
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
    region1 = _get_relational_expression_region(var1, op1, val1, min_val, max_val)
    region2 = _get_relational_expression_region(var2, op2, val2, min_val, max_val)

    def compute_region_intersection_union(region1, region2):
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
        intersection_length, union_length = compute_region_intersection_union(region1, region2)

    # Calculate the Jaccard similarity
    similarity = intersection_length / union_length
    return round(similarity,5)

def pair_relational_expressions(relational_expression_1: str,
                                relational_expression_2: str) -> str:
    
    relational_expression_list_1 = _extract_relational_expressions(relational_expression_1)
    relational_expression_list_2 = _extract_relational_expressions(relational_expression_2)
    
    pairs = []
    
    # Extract variable names from leaves
    def extract_variable(leaf):
        return leaf.split()[0]
    
    variables1 = {extract_variable(leaf): leaf for leaf in relational_expression_list_1}
    variables2 = {extract_variable(leaf): leaf for leaf in relational_expression_list_2}
    
    # Create pairs
    for var in variables1:
        if var in variables2:
            pairs.append((variables1[var], variables2[var]))
    
    return pairs

def calculate_parameters_similarity(
    conditional_expression_1: str,
    conditional_expression_2: str,
    monitored_parameters_dict: dict,
) -> list[dict]:
    """
    Calculate similarity scores between two conditional expressions
    by decomposing them into atomic pairs (relational expression) and evaluating each pair.

    This function converts both input conditional expressions into their 
    Disjunctive Normal Form (DNF), generates pairs of atomic 
    relational expressions, and computes the Jaccard similarity 
    for each pair based on the monitored parameter ranges.

    Parameters
    ----------
    conditional_expression_1 : str
        First conditional expression, which can be a simple relational expression
        (e.g., "temperature >= 30") or a compound expression with
        logical operators (e.g., "temperature >= 30 AND battery < 10").
    conditional_expression_2 : str
        Second logical expression, in the same format as conditional_expression_1.
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
        relational expressions (tuple) to their similarity score.
        Example:
        [
            {("temperature >= 30", "temperature < 40"): 0.57143}
        ]

    Notes
    -----
    - Similarity is only computed if both relational expression refer to the 
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

    conditional_expression_1 = conditional_expression_to_dnf(conditional_expression_1, output_operators="text")
    conditional_expression_2 = conditional_expression_to_dnf(conditional_expression_2, output_operators="text")


    pair_relational_expressions_list = pair_relational_expressions(
        conditional_expression_1,
        conditional_expression_2
    )

    matched_relational_expression_and_similarity_dict = []

    for relational_expression_pair in pair_relational_expressions_list:
        relational_expression_1 = relational_expression_pair[0]
        relational_expression_2 = relational_expression_pair[1]

        jaccard_similarity = _calculate_jaccard_similarity(
        relational_expression_1,
        relational_expression_2,
        monitored_parameters_dict)

        matched_relational_expression_and_similarity_dict.append({relational_expression_pair: jaccard_similarity})

    return matched_relational_expression_and_similarity_dict

def _extract_parameters(conditional_expression: str) -> List[str]:
    """
    Extract parameter names from a list of relational expressions.

    Each expression must follow the format:
        <variable> <operator> <value>

    Supported operators: ==, !=, <, <=, >, >=
    The value is assumed to be numeric.

    Parameters
    ----------
    relational_expressions : list of str
        List of strings, each containing a relational expression.

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

    relational_expressions = _extract_relational_expressions(conditional_expression)

    variables = []
    for expr in relational_expressions:
        match = re.match(r"([a-zA-Z_]\w*)\s*(==|!=|[<>]=?)\s*([0-9]+)", expr)
        if match:
            variables.append(match.group(1))
    return variables

def _tversky_similarity(parameter_list_1, parameter_list_2, alpha=1.0, beta=1.0) -> float:
    """
    Compute the Tversky similarity index between two sets of parameters.

    The Tversky index is a generalization of several similarity measures:
    - When alpha = beta = 0.5, it reduces to the Dice coefficient.
    - When alpha = beta = 1.0, it reduces to the Jaccard index.
    - When alpha != beta, it allows asymmetric weighting of differences.

    Parameters
    ----------
    parameter_list_1 : list
        First list of parameters.
    parameter_list_2 : list
        Second list of parameters.
    alpha : float, optional (default=1.0)
        Weight for elements unique to `parameter_list_1`.
    beta : float, optional (default=1.0)
        Weight for elements unique to `parameter_list_2`.

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
    set1 = set(parameter_list_1)
    set2 = set(parameter_list_2)

    intersection = len(set1 & set2)
    only_in_set1 = len(set1 - set2)
    only_in_set2 = len(set2 - set1)

    return intersection / (intersection + alpha * only_in_set1 + beta * only_in_set2)

def _penalty(parameter_list_1, parameter_list_2, alpha=1.0, beta=1.0) -> float:
    """
    Compute the penalty score as the complement of the Tversky similarity.

    The penalty quantifies dissimilarity between two sets of variables.
    It is defined as:

        penalty(A, B) = 1 - Tversky(A, B)

    where `Tversky(A, B)` is the Tversky similarity index.

    Parameters
    ----------
    parameter_list_1 : list
        First list of parameters.
    parameter_list_2 : list
        Second list of parameters.
    alpha : float, optional (default=1.0)
        Weight for the elements unique to `parameter_list_1`.
    beta : float, optional (default=1.0)
        Weight for the elements unique to `parameter_list_2`.

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
      or measuring differences between parameter sets.

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
    return 1 - _tversky_similarity(parameter_list_1, parameter_list_2, alpha, beta)



def _extract_parameter_and_similarity(
    parameter_similarities: List[Dict[Tuple[str, str], float]]
) -> Dict[str, float]:
    """
    Extract variable names and their similarities from a dictionary of leaf pairs.

    Args
    ----
    local_similarity : dict[tuple[str, str], float]
        A dictionary with tuples of leaf pairs as keys and similarity values as values.

    Returns
    -------
    dict[str, float]
        A dictionary with variable names as keys and similarity values as values.
        (If multiple pairs for the same variable exist in `local_similarity`,
            later entries will overwrite earlier ones; aggregation happens at the outer level.)
    """
    final_parameter_similarity_dict: Dict[str, float] = {}
    for (leaf1, leaf2), similarity in parameter_similarities.items():
        # Variable is assumed to be the first token in the leaf
        variable = leaf1.split()[0]
        final_parameter_similarity_dict[variable] = similarity
    return final_parameter_similarity_dict

def _parameter_similarity_weighted_avg(
    parameter_similarities: List[Dict[Tuple[str, str], float]],
    weight_dict: Dict[str, float] | None = None,
    ) -> float:
    """
    Calculate the weighted average similarity across parameters.

    This function aggregates similarities from multiple conditional 
    expression pairs and computes a weighted mean. Each parameter can 
    have a custom weight provided in `weight_dict`.

    Parameters
    ----------
    parameter_similarities : list[dict[tuple[str, str], float]]
        A list of dictionaries where:
            - key: tuple of two leaf expressions 
            (e.g., ("temperature >= 30", "temperature < 40"))
            - value: similarity score (float) between the two leaves
    weight_dict : dict[str, float], optional
        Dictionary mapping parameter names to their weights.
        If not provided, all parameters are weighted equally (weight=1).

    Returns
    -------
    float
        The weighted average similarity across all parameters.
        Returns 0.0 if no weights are available (to avoid division by zero).

    Notes
    -----
    - The parameter name is extracted as the first token of each leaf 
    expression string.
    - Example of input:
        parameter_similarities = [
            {("temperature >= 30", "temperature < 40"): 0.57},
            {("battery > 10", "battery != 5"): 0.8}
        ]
        weight_dict = {"temperature": 2.0, "battery": 1.0}
    - Example of output:
        0.6467 (weighted average)
    """

    # Extract a flat mapping of parameter -> similarity
    parameter_and_similarity_dict = _extract_parameter_and_similarity(parameter_similarities)

    if weight_dict is None:
        weight_dict = {}

    weighted_sum = 0.0
    total_weight = 0.0

    for var, similarity in parameter_and_similarity_dict.items():
        weight = weight_dict.get(var, 1.0)
        weighted_sum += similarity * weight
        total_weight += weight

    if total_weight == 0.0:
        return 0.0  # Avoid division by zero

    weighted_average = weighted_sum / total_weight
    return weighted_average


def calculate_scenario_similarity(scenario_1 :ScenarioBDD, sceanrio_2: ScenarioBDD, **kwargs) -> float:
    #TODO: fazer a documentação dessa função

    def weighted_average_conditional_similarity(
        given_similarity: float,
        when_similarity: float,
        then_similarity: float,
        given_weight: float = 1.0,
        when_weight: float = 1.0,
        then_weight: float = 1.0,
    ) -> float:
        
        #TODO: fazer a documentação dessa função

        if weights is None:
            weights = {}

        total_weight = given_weight + when_weight + then_weight
        if total_weight == 0:
            return 0.0

        weighted_avg = (
            (given_similarity * given_weight) +
            (when_similarity * when_weight) +
            (then_similarity * then_weight)
        ) / total_weight

        return weighted_avg

    #TODO: ajustar esses pesos para 1 e 1
    alpha = kwargs.get("alpha", 1.0)
    beta = kwargs.get("beta", 1.0)
    given_weight = kwargs.get("given_weight", 1.0)
    when_weight = kwargs.get("when_weight", 1.0)
    then_weight = kwargs.get("then_weight", 1.0)

    given_conditional_expression_1 = scenario_1.given()
    given_conditional_expression_2 = sceanrio_2.given()

    when_conditional_expression_1 = scenario_1.when()
    when_conditional_expression_2 = sceanrio_2.when()

    then_conditional_expression_1 = scenario_1.then()
    then_conditional_expression_2 = sceanrio_2.then()

    #monitored_parameters_dict = scenario_1.get_monitored_parameters_dict() #TODO
    monitored_parameters_dict = {} #TODO

    given_conditional_similarity = calculate_conditional_similarity(
        given_conditional_expression_1,
        given_conditional_expression_2,
        monitored_parameters_dict,
        alpha=alpha,
        beta=beta)
    
    when_conditional_similarity = calculate_conditional_similarity(
        when_conditional_expression_1,
        when_conditional_expression_2,
        monitored_parameters_dict,
        alpha=alpha,
        beta=beta)
    
    then_conditional_similarity = calculate_conditional_similarity(
        then_conditional_expression_1,
        then_conditional_expression_2,
        monitored_parameters_dict,
        alpha=alpha,
        beta=beta)
    
    scenario_similarity = weighted_average_conditional_similarity(given_conditional_similarity,
                                                                 when_conditional_similarity,
                                                                 then_conditional_similarity,
                                                                 given_weight,
                                                                 when_weight,
                                                                 then_weight)

    return scenario_similarity



def calculate_conditional_similarity(conditional_expression_1: str,
                                     conditional_expression_2: str,
                                     monitored_parameters_dict: dict,
                                     alpha: float = 1.0,
                                     beta: float = 1.0,
                                     ) -> float:
    #TODO: fazer a documentação dessa função e colocar os tipos esperados
    
    parameter_and_similarity_dict = calculate_parameters_similarity(
        conditional_expression_1,
        conditional_expression_2,
        monitored_parameters_dict)
    
    weight_dict = {} #TODO

    parameter_similarity_avg = _parameter_similarity_weighted_avg(
    parameter_and_similarity_dict,
    weight_dict=weight_dict)

    monitored_parameters_1 = _extract_parameters(conditional_expression_1)
    monitored_parameters_2 = _extract_parameters(conditional_expression_2)
    penalty = _penalty(monitored_parameters_1, monitored_parameters_2, alpha=alpha, beta=beta)


    final_similarity = parameter_similarity_avg - penalty

    return final_similarity

def main():
    kargs = {"alpha": 0.9, "beta": 0.1}

    monitored_parameters_dict = {
        "a": {"min_value": 0, "max_value": 100, "type": "int"},
        "b": {"min_value": 0, "max_value": 100, "type": "int"},
    }

    conditional_expression_1 = ConditionalExpression("a >= 3 AND b < 10")
    conditional_expression_2 = ConditionalExpression("a >= 3 AND b < 10")

    conditional_similarity = calculate_conditional_similarity(
        conditional_expression_1,
        conditional_expression_2,
        monitored_parameters_dict,
        **kargs
    )
    
    scenario_1 = None
    scenario_2 = None

    scenario_similarity = calculate_scenario_similarity(scenario_1, scenario_2, kargs)