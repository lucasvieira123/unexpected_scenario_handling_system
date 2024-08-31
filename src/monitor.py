import os
import pandas as pd
import numpy as np
import time
import csv
from datetime import datetime
from multiprocessing import Manager, Process
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

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

class Px4DroneMonitor(FileSystemEventHandler):
    def __init__(self, monitoring_folder_path):
        self.monitoring_folder_path = os.path.normpath(monitoring_folder_path)
        self.shared_list = None
        self.current_file_path = None

    

    def get_current_file_path(self):
        files = os.listdir(self.monitoring_folder_path)
        num_files = len(files)
        index = num_files - 1
        file_name = f"PX4_collected_telemetry_{index}.csv"
        return os.path.join(self.monitoring_folder_path, file_name)
        
    
    def on_modified(self, event):
        new_file_path = self.get_current_file_path()
        print(f"Arquivo modificado: {new_file_path}")
        if new_file_path != self.current_file_path:
            #clean shared_list
            self.shared_list[:] = []

        self.current_file_path = new_file_path
        self.process_new_lines()

    def process_new_lines(self):
        all_collected_data_df = pd.read_csv(self.current_file_path)
        new_data_df = all_collected_data_df.iloc[-1]
        self.shared_list.append((new_data_df, all_collected_data_df))
        # print(f"Novos dados adicionados ao DataFrame!+ {len(self.shared_list)}")
        # print(f"Novos Dados Monitorados: {new_data_df['time']}")
    
    def start_monitoring(self, shared_list):
        self.shared_list = shared_list
        observer = Observer()
        observer.schedule(self, self.monitoring_folder_path, recursive=False)
        observer.start()
        try:
            while True:
                print("Monitorando arquivo...")
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()

        observer.join()