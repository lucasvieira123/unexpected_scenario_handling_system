import pandas as pd
import numpy as np
import time
from datetime import datetime
from multiprocessing import Manager, Process

class MockedDataGenerator:
    def __init__(self):
        self.df = pd.DataFrame(columns=[
            "time", "scenario_name", "position", "altitude", "target_distance", "velocity",
            "battery", "attitude", "current_lat", "current_lon", "current_alt",
            "destination_lat", "destination_lon", "destination_alt",
            "destination_distance", "relative_altitude_m"
        ])

    def generate_mock_data(self):
        return {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "scenario_name": f"Scenario_{np.random.randint(1, 10)}",
            "position": np.random.randint(1, 100),
            "altitude": np.random.uniform(100, 1000),
            "target_distance": np.random.uniform(0, 500),
            "velocity": np.random.uniform(0, 50),
            "battery": np.random.uniform(20, 100),
            "attitude": np.random.uniform(-180, 180),
            "current_lat": np.random.uniform(-90, 90),
            "current_lon": np.random.uniform(-180, 180),
            "current_alt": np.random.uniform(0, 10000),
            "destination_lat": np.random.uniform(-90, 90),
            "destination_lon": np.random.uniform(-180, 180),
            "destination_alt": np.random.uniform(0, 10000),
            "destination_distance": np.random.uniform(0, 1000),
            "relative_altitude_m": np.random.uniform(-50, 50),
            "bad_connection": np.random.choice([True, False])
        }

    def add_data_every_second(self, shared_list):
        try:
            while True:
                new_data = self.generate_mock_data()
                new_dt = pd.DataFrame([new_data])
                self.df = pd.concat([self.df, new_dt], ignore_index=True)
                
                # Adiciona os novos dados e todos os dados à lista compartilhada
                shared_list.append((new_data, self.df))
                
                time.sleep(1)  # Espera 3 segundos
                print(f"Novos dados adicionados ao DataFrame!+ {len(shared_list)}")
        except KeyboardInterrupt:
            print("Interrompido pelo usuário.")
            self.df.to_csv('res/outcome/mocked_telemetry.csv', index=False)