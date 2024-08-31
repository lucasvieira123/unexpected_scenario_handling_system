import json
import re
import numpy as np
import pandas as pd
import time
from multiprocessing import Manager, Process

class UC_state_identifier:
    def __init__(self, delivery_model, machine):
        self.model = delivery_model
        self.machine = machine
        self.action_initial_index = 0
        self.action_final_index = 0
        self.offset = 0
        self.var_config = self.get_var_config()
        self.var_list =  [item['name'] for item in self.var_config]

    def get_var_config(self):
        with open('./res/variables_config.json') as f:
            var_config = json.load(f)
        return var_config
    
    # Função para monitorar o DataFrame compartilhado
    def check_states(self, shared_list):
        last_len = 0
        while True:
            current_len = len(shared_list)

            if current_len == 0:
                continue

            if current_len == last_len:
                continue

            new_data_df, all_data_df=shared_list[-1]
            # print(f"Novas dados para checar:{new_data_df['time']}")

            last_len = current_len

            # Atualiza as variáveis do modelo
            self.model.create_update_variables(new_data_df)
            self.check_unanticipated_change(new_data_df, all_data_df)
            time.sleep(1)

    def check_expression(self, expression, context):
        for var in self.var_list:
            # Verifica se a variável está na expressão
            if var in expression:
                # Substitui a variável na expressão pelo valor correspondente do DataFrame
                value = context[var]
                # Substitui a variável na expressão pelo seu valor. Usando regex para substituir exato.
                expression = re.sub(rf'\b{var}\b', str(value), expression)

        # Avalia a expressão
        print(f"expression: {expression}")
        resultado = eval(expression)
        return resultado

    def check_given(self, data_to_specific_action):
        precondition_df = data_to_specific_action.iloc[0]
        current_action = str(data_to_specific_action.iloc[1]["action"]).lower()

        current_transition = self.machine.get_transitions(current_action)[0]
        current_state = current_transition.source

        _, given_expression = current_state.split("__")

        given_sat=self.check_expression(given_expression, precondition_df)

        return given_sat
        
    def check_when(self, data_to_specific_action):

        current_action = str(data_to_specific_action.iloc[1]["action"]).lower()

        method_name=self.machine.get_transitions(current_action)[0].conditions[0].func

        method_to_call  = getattr(self.model, method_name)
        when_sat = method_to_call()
        print(f"when_sat: {when_sat}")
        return when_sat
    
    def check_then(self, data_to_specific_action):
        # current_state = self.model.state

        postcondition_df = data_to_specific_action.iloc[-1]
        current_action = str(data_to_specific_action.iloc[1]["action"]).lower()

        current_transition = self.machine.get_transitions(current_action)[0]
        current_state = current_transition.dest

        _, then_expression = current_state.split("__")

        then_sat=self.check_expression(then_expression, postcondition_df)

        return then_sat

    # def check_given(self, data_to_specific_action):
    #     current_state = self.model.state
    #     _, given_expression = current_state.split("__")

    #     precontext = data_to_specific_action.iloc[0]

    #     given_sat=self.check_expression(given_expression, precontext)

    #     return given_sat
        
    # def check_when(self, data_to_specific_action):
    #     current_state = self.model.state
    #     scenario, _ = current_state.split("__")
    #     method_name = f"{scenario}"
    #     method_to_call  = getattr(self.model, method_name)
    #     when_sat = method_to_call()
    #     print(f"when_sat: {when_sat}")
    #     return when_sat
    
    # def check_then(self, data_to_specific_action):
    #     current_state = self.model.state
    #     _, then_expression = current_state.split("__")

    #     postcontext = data_to_specific_action.iloc[-1]

    #     then_sat =self.check_expression(then_expression, postcontext)

    #     return then_sat

    def check_unanticipated_change(self, new_data, new_df):
        # Verifica se ocorreu uma mudança não antecipada
        current_action = str(new_data["action"])

        if current_action == "nan":
            self.offset = self.offset + 1
            self.action_initial_index = self.offset
            self.action_final_index = self.offset
            return
        
        current_collected_data = new_data
        last_action = str(new_df["action"].iloc[-2])
        last_collected_data = new_df.iloc[-2]

        if current_action == last_action:
            self.action_final_index = self.action_final_index +1
            # print(f"current_action: {current_action} == last_action: {last_action}")
            # print(f"action_initial_index: {self.action_initial_index} action_final_index: {self.action_final_index}")

        else:

            if last_action != "nan":
                data_to_specific_action = new_df.iloc[self.action_initial_index-1:self.action_final_index+2]
                print(f"data_to_specific_action: {data_to_specific_action}")
                print(f"current_action: {current_action}")
                given_is_sat = self.check_given(data_to_specific_action)
                when_is_sat = self.check_when(data_to_specific_action)
                then_is_sat = self.check_then(data_to_specific_action)

                if given_is_sat and when_is_sat and then_is_sat:
                    print(f"Condição do cenário satisfeita")
                    print(f"Estado atual: {self.model.state}")

            self.action_initial_index = self.action_final_index
            self.action_final_index = self.action_final_index +1
            
            # print(f"current_action: {current_action} != last_action: {last_action}")
            # print(f"action_initial_index: {self.action_initial_index} action_final_index: {self.action_final_index}")
            
            
            
            # current_state = self.model.state
            # scenario, given_expression = current_state.split("__")
            # given_sat = eval(given_expression, {"__builtins__": None}, vars(self.model))

            # if not given_sat:
            #     print(f"Erro: A condição {given_expression} não foi satisfeita")
            # return


        # # passou para outra ação
        # if collected_current_action != collected_last_action:
        #     current_state = self.model.state

        #     scenario, given_expression = current_state.split("__")
        #     given_sat = eval(given_expression, {"__builtins__": None}, vars(self.model))

        #     if not given_sat:
        #         print(f"Erro: A condição {given_expression} não foi satisfeita")
        #         return
            
        #     method_name = f"{collected_last_action}__when"
        #     method_to_call  = getattr(self.model, method_name)
        #     when_sat = method_to_call()
        #     if not when_sat:
        #         print(f"Erro: A condição {method_name} não foi satisfeita")
        #         return
            
        #     current_state = self.model.state
        #     scenario, then_expression = current_state.split("__")
        #     then_sat = eval(then_expression, {"__builtins__": None}, vars(self.model))

        #     if not then_sat:
        #         print(f"Erro: A condição {then_expression} não foi satisfeita")
        #         return
            

        # else: #continua na acao
        #     current_state = self.model.state

        #     scenario, given_expression = current_state.split("__")
        #     given_sat = eval(given_expression, {"__builtins__": None}, vars(self.model))

        #     if not given_sat:
        #         print(f"Erro: A condição {given_expression} não foi satisfeita")
        #         return

        