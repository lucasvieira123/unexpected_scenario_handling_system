from multiprocessing import Manager, Process
from class_builder import ClassBuilder
from monitor import MockedDataGenerator
from unanticipated_change_identifier import UC_state_identifier
from state_machine_manager import StateMachineModel, StateMachineModelView
from state_machine_manager import load_json_from_file, print_diagram


if __name__ == "__main__":
    expected_scenario_json = load_json_from_file('./res/expected_scenario.json')
    variables_config_json = load_json_from_file('./res/variables_config.json')

    
    #Descomentar esta linha para criar o modelo dinamicamente
    class_builder = ClassBuilder(class_file="src/dinamic_model.py",
                                 expected_scenario_json = expected_scenario_json,
                                  variables_config_json=variables_config_json)
    class_builder.build_dinamic_class()

    delivery_model = StateMachineModel(class_name_model="DynamicClass").scenario_model_to_state_machine(expected_scenario_json)
    delivery_model_view = StateMachineModelView(class_name_model="DynamicClass").scenario_model_to_state_machine(expected_scenario_json)

    #Descomentar esta linha apesas para debugar o diagrama
    print_diagram(delivery_model,'res/outcome/DEBUG_state_diagram.png')
    print_diagram(delivery_model_view,'res/outcome/state_diagram.png')

    # with Manager() as manager:
    #     shared_list = manager.list()  # Lista gerenciada compartilhada

    #     generator = MockedDataGenerator()  # Instancia o gerador de dados simulados
    #     monitor = UC_state_identifier(delivery_model)

    #     # Cria e inicia o processo que executa o add_data_every_second
    #     producer_process = Process(target=generator.add_data_every_second, args=(shared_list,))
    #     monitor_process = Process(target=monitor.monitor_data, args=(shared_list,))

    #     # Inicia os processos
    #     producer_process.start()
    #     monitor_process.start()

    #     # Aguarda o término dos processos
    #     producer_process.join()
    #     monitor_process.join()