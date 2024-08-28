import pandas as pd
import time
from multiprocessing import Manager, Process

class UC_state_identifier:
    def __init__(self, delivery_model):
        self.model = delivery_model

    # Função para monitorar o DataFrame compartilhado
    def monitor_data(self, shared_list):
        last_len = 0
        while True:
            current_len = len(shared_list)
            if current_len > last_len:
                # Obtenha os novos dados
                new_data=shared_list[last_len:current_len][0][0]
                new_df=shared_list[last_len:current_len][0][1]
                # print(f"Novas linhas adicionadas ao DataFrame:{len(shared_list)}")
                last_len = current_len
                
                # Atualiza as variáveis do modelo
                self.model.update_variables(new_data)
                self.check_unanticipated_change(new_data, new_df)
            time.sleep(1)

    def check_unanticipated_change(self, new_data, new_df):
        # Verifica se ocorreu uma mudança não antecipada
        collected_current_action = new_data["action"]
        collected_last_action = new_df["action"].iloc[-2]

        # passou para outra ação
        if collected_current_action != collected_last_action:
            current_state = self.model.state

            scenario, given_expression = current_state.split("__")
            given_sat = eval(given_expression, {"__builtins__": None}, vars(self.model))

            if not given_sat:
                print(f"Erro: A condição {given_expression} não foi satisfeita")
                return
            
            method_name = f"{collected_last_action}__when"
            method_to_call  = getattr(self.model, method_name)
            when_sat = method_to_call()
            if not when_sat:
                print(f"Erro: A condição {method_name} não foi satisfeita")
                return
            
            current_state = self.model.state
            scenario, then_expression = current_state.split("__")
            then_sat = eval(then_expression, {"__builtins__": None}, vars(self.model))

            if not then_sat:
                print(f"Erro: A condição {then_expression} não foi satisfeita")
                return
            

        else: #continua na acao
            current_state = self.model.state

            scenario, given_expression = current_state.split("__")
            given_sat = eval(given_expression, {"__builtins__": None}, vars(self.model))

            if not given_sat:
                print(f"Erro: A condição {given_expression} não foi satisfeita")
                return

        