# %%
import json
import os
import time
import yaml
from logger import setup_logger, trace
from scenario.candidate_scenario import CandidateScenario
from scenario.diagnosed_scenario import DiagnosedScenario
from similarity.dejavu_similarity import calculate_scenario_similarity
from simulation_utils import generate_weight_grid
from concurrent.futures import ProcessPoolExecutor
import json
from tqdm import tqdm  # pip install tqdm (opcional, mas super útil)

# %%
def get_weight_config(name_app):
    with open(f"../res/application/{name_app}/weights_config.yaml", "r") as file:
        settings = yaml.safe_load(file)
    return settings

def get_initialize_config():
    with open("../initialize_config.yaml", "r") as file:
        settings = yaml.safe_load(file)
    return settings

def get_scenarios_pipeline(name_app):
    with open(f"../res/application/{name_app}/scenarios_pipeline.json", "r") as file:
        scenarios_pipeline = json.load(file)
        return scenarios_pipeline

def get_monitored_parameters(name_app):
    with open(f"../res/application/{name_app}/monitored_parameters.json", "r") as file:
        monitored_parameters_dict = json.load(file)
        return monitored_parameters_dict

def get_shared_scenarios(name_app):
    with open(f"../res/application/{name_app}/shared_scenarios.json", "r") as file:
        shared_scenerios = json.load(file)
        return shared_scenerios

# %%
# @trace
# def simulation_mode(name_app):
#     """
#     Runs scenario similarity simulations over all grid search weight configurations
#     for a given application. Each configuration is applied to all diagnosed and candidate
#     scenarios in the application's scenario pipeline.

#     Args:
#         name_app (str): Name of the application (used to load relevant configs and scenarios).
#     """

#     # --- Load data ---
#     shared_scenarios_list = get_shared_scenarios(name_app)
#     scenarios_pipeline_dict = get_scenarios_pipeline(name_app)
#     weight_configs_dict = get_weight_config(name_app)
#     monitored_parameters_dict = get_monitored_parameters(name_app)

#     # --- Generate grid of parameter configurations ---
#     grid_search_configs = generate_full_grid_search(weight_configs_dict)

#     # --- Main simulation loop ---
#     for current_config in grid_search_configs:
#         # Prepare arguments for similarity calculation
#         kargs = current_config.copy()
#         kargs["monitored_parameters"] = monitored_parameters_dict

#         for diagnosed_data in scenarios_pipeline_dict["diagnosed"]:
#             diagnosed_scenario = DiagnosedScenario(data=diagnosed_data)

#             for candidate_data in shared_scenarios_list:
#                 candidate_scenario = CandidateScenario(data=candidate_data)

#                 # Início do tempo
#                 start_time = time.perf_counter()

#                 similarity_result = calculate_scenario_similarity(
#                     diagnosed_scenario,
#                     candidate_scenario,
#                     **kargs
#                 )

#                  # Fim do tempo
#                 end_time = time.perf_counter()
#                 elapsed_time = end_time - start_time

#                 print(f"Similarity result: {similarity_result} | Time: {elapsed_time:.6f} seconds")
#                 # Optionally: Store or process the result (append to list, save, log, etc.)


def calculate_similarity_task(args):
        diagnosed_data, candidate_data, current_config, monitored_parameters_dict = args

        diagnosed_scenario = DiagnosedScenario(data=diagnosed_data)
        candidate_scenario = CandidateScenario(data=candidate_data)

        kargs = current_config.copy()
        kargs["monitored_parameters"] = monitored_parameters_dict

        start_time = time.perf_counter()
        similarity_result = calculate_scenario_similarity(
            diagnosed_scenario,
            candidate_scenario,
            **kargs
        )
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time

        return {
            "similarity_result": similarity_result,
            "elapsed_time": elapsed_time,
            "diagnosed": diagnosed_scenario.to_dict(),    # Supondo que existe
            "candidate": candidate_scenario.to_dict(),    # Supondo que existe
            "config": current_config,
        }

@trace
def simulation_mode(name_app):
    """
    Runs scenario similarity simulations over all grid search weight configurations
    for a given application. Each configuration is applied to all diagnosed and candidate
    scenarios in the application's scenario pipeline.

    Args:
        name_app (str): Name of the application (used to load relevant configs and scenarios).
    """

    # --- Load data ---
    shared_scenarios_list = get_shared_scenarios(name_app)
    scenarios_pipeline_dict = get_scenarios_pipeline(name_app)
    weight_configs_dict = get_weight_config(name_app)
    monitored_parameters_dict = get_monitored_parameters(name_app)

    # --- Generate grid of parameter configurations ---
    # grid_search_configs = generate_full_grid_search(weight_configs_dict)
    grid_search_configs = generate_weight_grid(weight_configs_dict)
    tasks = []
    count = 0
    for current_config in grid_search_configs:
        for diagnosed_data in scenarios_pipeline_dict["diagnosed"]:
            for candidate_data in shared_scenarios_list:
                tasks.append((diagnosed_data, candidate_data, current_config, monitored_parameters_dict))
                count += 1


    

    with ProcessPoolExecutor() as executor, open(f"../res/application/{name_app}/"+"similarity_results.jsonl", "w", encoding="utf-8") as f:
        results_iter = executor.map(calculate_similarity_task, tasks)
        for result in tqdm(results_iter, total=len(tasks)):
            # Salva cada resultado como uma linha JSON
            f.write(json.dumps(result, ensure_ascii=False) + "\n")
            # print ou qualquer outro processamento se quiser



            
def normal_mode(name_app):
    #TODO - implement normal mode
    kargs = get_weight_config(name_app)
    kargs["monitored_parameters"] = get_monitored_parameters(name_app)

    shared_scenarios = get_shared_scenarios(name_app)
    scenarios_pipeline = get_scenarios_pipeline(name_app)

# %%
def main():
    setup_logger()
    settings = get_initialize_config()
    name_app = settings["NAME_APPLICATION"]
    simulation = settings["SIMULATION"]

    if simulation:
        print("Simulation mode activated")
        simulation_mode(name_app)
    else:
        
        print("Normal mode activated")
        normal_mode(name_app)

# %%
if __name__ == "__main__":
    main()


# %%
