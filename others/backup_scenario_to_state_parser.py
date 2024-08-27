from transitions import Machine
import json
from transitions.extensions import GraphMachine
from transitions_gui import WebMachine
# import pyperclip

def load_json_from_file(file_path):
    try:
        # Abrindo o arquivo JSON
        with open(file_path, 'r') as json_file:
            # Carregando o conteúdo JSON
            data = json.load(json_file)
            return data
    except FileNotFoundError:
        print(f"Arquivo não encontrado: {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"Erro ao decodificar o arquivo JSON: {file_path}")
        return None

class _StateMachineModel:
    pass


class StateMachineModelManager:
    def __init__(self):
        self._state_machine_model = _StateMachineModel()
        self.state_machine_model = GraphMachine(model=self._state_machine_model, graph_engine="graphviz")


    def add_state(self, state_name, meta=None):
        self.state_machine_model.add_state(state_name, meta)

    def add_transition(self, transition_name, condition, source, dest):
        self.state_machine_model.add_transition(trigger=transition_name,
                                                source=source, dest=dest,
                                                conditions=[condition])


    def scenario_model_to_state_machine(self, scenairo_model_json):
        src_dest_states_by_scenario = {}
        
        # aqui só cria os estados e transições dos cenarios, mas nao liga os cenários (Epson transition)
        for scenario in scenairo_model_json:
            current_given = None

            for key, scenario_content in scenario.items():
                    if key != "_extra":
                        #criar estados initial, transition e final para um cenário

                        BDD_scenario=scenario_content
                        scenario_name = key

                        given = BDD_scenario.get("Given")
                        when = BDD_scenario.get("When")
                        do = BDD_scenario.get("Do")
                        then = BDD_scenario.get("Then")

                        indexed_given = f"{scenario_name}.({given})"
                        indexed_when = f"{scenario_name}.({when})"
                        indexed_do = f"{scenario_name}.({do})[{when}]"
                        indexed_then = f"{scenario_name}.({then})"

                        self.add_state(indexed_given)
                        self.add_state(indexed_then)
                        self.add_transition(transition_name=indexed_do, condition=indexed_when, source=indexed_given, dest=indexed_then)

                        src_dest_states_by_scenario[scenario_name] = [indexed_given, indexed_then]
                        current_given = indexed_given

                    else:
                        #aqui só seta o estado inicial
                        extra_infos_scenario=scenario_content
                        is_initial_scenario = extra_infos_scenario.get("initial")
                        if is_initial_scenario:
                            self.add_transition(transition_name="epson", condition=None, source="initial", dest=current_given)

        # aqui eu percorro novamente para criar as Epson transitions
        for scenario in scenairo_model_json:
            current_scenario_name = None

            for key, scenario_content in scenario.items():
                    if key != "_extra":
                         current_scenario_name = key
                    if key == "_extra":
                        gointo = scenario_content.get("gointo")

                        src_dest_state1=src_dest_states_by_scenario[current_scenario_name]
                        src1=src_dest_state1[0]
                        dest1=src_dest_state1[1]

                        for scenario_name in gointo:

                            src_dest_state2=src_dest_states_by_scenario[scenario_name]
                            src2=src_dest_state2[0]
                            dest2=src_dest_state2[1]
                            self.add_transition(transition_name="epson", condition=None, source=dest1, dest=src2)


        
        return self.state_machine_model
    
    def add_epson_transitions(self, scenario_transitions):
        for transition in scenario_transitions:
            for initial_state, final_states in transition.items():
                for final_state in final_states:
                    self.add_transition(transition_name="epson", condition=None, source=initial_state, dest=final_state)


    def show_diagram(self):
        self.state_machine_model.get_graph().draw('state_diagram.png', prog='dot')
    
if __name__ == "__main__":
    model = StateMachineModelManager()
    file_path = 'expected_scenario.json'
    expected_scenario_json = load_json_from_file(file_path)
    model.scenario_model_to_state_machine(expected_scenario_json)
    model.show_diagram()
    web_machine = WebMachine(model,
                     ignore_invalid_triggers=True,
                     auto_transitions=False)
    web_machine.run()
