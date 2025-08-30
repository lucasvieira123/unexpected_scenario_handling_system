import itertools

import random
import copy

def generate_full_grid_search(config):
    """
    Generate all possible parameter combinations (Cartesian product),
    preserving the nested structure of the config dictionary.

    Args:
        config (dict): Configuration dictionary where each parameter key points to a list of possible values.
                       Structure example:
                           {
                               "group1": {"param_a": [v1, v2], ...},
                               "group2": {"param_b": [v3, v4], ...},
                               ...
                           }

    Returns:
        List[dict]: List of dictionaries, each containing a unique combination of parameters
                    grouped in the same nested structure as the input config.

    Example:
        configs = generate_full_grid_search(config)
        for conf in configs:
            # Use conf in your experiment
    """
    param_lists = []
    for namespace in config:
        for key, values in config[namespace].items():
            if not isinstance(values, list):
                values = [values]
            param_lists.append((namespace, key, values))
    only_values = [x[2] for x in param_lists]
    combos = itertools.product(*only_values)
    configs = []
    for combo in combos:
        out = {k: {} for k in config}
        for (namespace, key, _), value in zip(param_lists, combo):
            out[namespace][key] = value
        configs.append(out)
    return configs

import random
import copy

def generate_random_grid_search(config, n_samples=10, seed=None):
    """
    Generate a given number of random parameter configurations,
    randomly sampling one value per parameter each time,
    and preserving the nested structure of the config dictionary.

    Args:
        config (dict): Configuration dictionary where each parameter key points to a list of possible values.
        n_samples (int): Number of random configurations to generate.
        seed (int, optional): Random seed for reproducibility.

    Returns:
        List[dict]: List of randomly sampled parameter configurations,
                    each grouped in the same nested structure as the input config.

    Example:
        random_configs = generate_random_grid_search(config, n_samples=5)
        for conf in random_configs:
            # Use conf in your experiment
    """
    if seed is not None:
        random.seed(seed)
    param_lists = []
    for namespace in config:
        for key, values in config[namespace].items():
            if not isinstance(values, list):
                values = [values]
            param_lists.append((namespace, key, values))
    configs = []
    for _ in range(n_samples):
        out = {k: {} for k in config}
        for namespace, key, values in param_lists:
            out[namespace][key] = random.choice(values)
        configs.append(copy.deepcopy(out))
    return configs
