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

import itertools

def get_namespace_length(namespace_dict):
    """Retorna o comprimento das listas dentro de um namespace.
       Exige que todas as listas tenham o mesmo tamanho."""
    lengths = set()
    for key, values in namespace_dict.items():
        if isinstance(values, list):
            lengths.add(len(values))
        else:
            # Se não for lista, tratamos como lista de tamanho 1
            lengths.add(1)
    if not lengths:
        return 1
    if len(lengths) > 1:
        raise ValueError(
            f"Inconsistent lengths inside namespace: found lengths={lengths}"
        )
    return lengths.pop()


def generate_weight_grid(config):
    """
    Gera combinações de configurações combinando índices por namespace:

    - Para cada namespace (e.g., parameter_weights, tversky_weights, conditional_weights),
      usamos um índice de coluna.
    - Fazemos o produto cartesiano dos índices entre namespaces.
    - Dentro de cada namespace, todos os parâmetros usam o mesmo índice.
    """
    namespaces = list(config.keys())

    # 1) descobre o número de colunas (configs) em cada namespace
    ns_lengths = {}
    for ns in namespaces:
        ns_lengths[ns] = get_namespace_length(config[ns])

    # 2) gera o produto cartesiano dos índices de cada namespace
    index_ranges = [range(ns_lengths[ns]) for ns in namespaces]
    index_combos = list(itertools.product(*index_ranges))

    configs = []
    for combo in index_combos:
        # combo é algo como (i_pw, i_tv, i_cond)
        ns_index = dict(zip(namespaces, combo))

        out = {ns: {} for ns in namespaces}
        for ns in namespaces:
            idx = ns_index[ns]
            for key, values in config[ns].items():
                if isinstance(values, list):
                    # assume-se que todas as listas têm tamanho ns_lengths[ns]
                    out[ns][key] = values[idx]
                else:
                    out[ns][key] = values
        configs.append(out)

    return configs