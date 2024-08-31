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
    
def add_state(machine, state_name, meta=None):
    machine.add_state(state_name, meta)

def add_transition(machine, transition_name, condition, source, dest):
    machine.add_transition(trigger=transition_name,
                                            source=source, dest=dest,
                                            conditions=condition)

def print_diagram(model,file_name):
    model.get_graph().draw(file_name, prog='dot')
    
class StateMachineModel:
    def __init__(self, class_name_model):
        # Importar o módulo dinamicamente
        module = __import__("dinamic_model")

        # Obter a classe do módulo e instanciá-la
        self.model = getattr(module, class_name_model)()

        # self.model = Machine(model=_model)
        self.machine = GraphMachine(model=self.model, graph_engine="graphviz", show_conditions=True)

    def scenario_model_to_state_machine(self, scenairo_model_json):
        src_dest_states_by_scenario = {}
        
        # aqui só cria os estados e transições dos cenarios, mas nao liga os cenários (Epson transition)
        for scenario in scenairo_model_json:
            current_given = None
            when_from_scenario = {}

            for key, scenario_content in scenario.items():
                    if key != "_extra":
                        #criar estados initial, transition e final para um cenário

                        BDD_scenario=scenario_content
                        scenario_name = key

                        given = BDD_scenario.get("Given")
                        if given == "*": given = "True"
                        when = BDD_scenario.get("When")
                        do = BDD_scenario.get("Do")
                        then = BDD_scenario.get("Then")
                        if then == "*": then = "True"

                        indexed_given = f"{scenario_name.lower()}__{given}"
                        adapted_when = f"{scenario_name.lower()}__when"
                        # indexed_given = f"{scenario_name}__{given}"
                        # adapted_when = f"{scenario_name}__when"
                        when_from_scenario[scenario_name] = when
                        indexed_do = f"{do}"
                        indexed_then = f"{scenario_name.lower()}__{then}"
                        # indexed_then = f"{scenario_name}__{then}"

                        add_state(self.machine,indexed_given)
                        add_state(self.machine, indexed_then)
                        add_transition(self.machine, transition_name=indexed_do, condition=adapted_when, source=indexed_given, dest=indexed_then)

                        src_dest_states_by_scenario[scenario_name] = [indexed_given, indexed_then]
                        current_given = indexed_given

                    else:
                        #aqui só seta o estado inicial
                        extra_infos_scenario=scenario_content
                        is_initial_scenario = extra_infos_scenario.get("initial")
                        if is_initial_scenario:
                            add_transition(self.machine,transition_name="epson", condition=None, source="initial", dest=current_given)

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
                            add_transition(self.machine, transition_name="epson", condition=None, source=dest1, dest=src2)

        # apenas para ir realmente para o estado inicial do cenário
        
        self.model.epson()

        return self.model, self.machine
    




class StateMachineModelView:
    def __init__(self, class_name_model):

        # Importar o módulo dinamicamente
        module = __import__("dinamic_model")

        # Obter a classe do módulo e instanciá-la
        self.model = getattr(module, class_name_model)()

        self.machine = GraphMachine(model=self.model, graph_engine="graphviz", show_conditions=True)
    
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

                        indexed_given = f"{scenario_name}\n{given}"
                        indexed_when = f"{when}"
                        indexed_do = f"{do}"
                        indexed_then = f"{scenario_name}\n{then}"

                        add_state(self.machine,indexed_given)
                        add_state(self.machine, indexed_then)
                        add_transition(self.machine, transition_name=indexed_do, condition=indexed_when, source=indexed_given, dest=indexed_then)

                        src_dest_states_by_scenario[scenario_name] = [indexed_given, indexed_then]
                        current_given = indexed_given

                    else:
                        #aqui só seta o estado inicial
                        extra_infos_scenario=scenario_content
                        is_initial_scenario = extra_infos_scenario.get("initial")
                        if is_initial_scenario:
                            add_transition(self.machine,transition_name="epson", condition=None, source="initial", dest=current_given)

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
                            add_transition(self.machine, transition_name="epson", condition=None, source=dest1, dest=src2)
        
        return self.model