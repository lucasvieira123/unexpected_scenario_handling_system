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
                print(f"Novas linhas adicionadas ao DataFrame:{len(shared_list)}")
                last_len = current_len
                
                # Atualiza as variáveis do modelo
                self.model.update_variables(new_data)
            time.sleep(1)