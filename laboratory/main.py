# %%
from pathlib import Path
import re

import pandas as pd
from drone_behavior_simulator import DroneBehaviorSimulator, TelemetryBus
from antecipated_scenario_monitor import AntecipatedScenarioMonitor
import yaml

from unanticipated_scenario_diagnoser import UnanticipatedScenarioDiagnoser
from unanticipated_scenario_identifier import UnanticipatedScenarioIdentifier

def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
    
cfg = load_config("unexpected_scenario_handling_system/laboratory/dejavu-conf.yaml")


def detected_unanticipated_scenario() -> pd.DataFrame:
    def extract_id(p: Path) -> int:
        m = re.search(r"checked_scenarios_(\d+)\.csv$", p.name)
        return int(m.group(1)) if m else -1
    
    def pick_latest_checked_csv() -> Path:
        folder = Path(cfg["checked_scenarios_folder"])
        candidates = list(folder.glob("checked_scenarios_*.csv"))
        if not candidates:
            raise FileNotFoundError(f"Nenhum 'checked_scenarios_*.csv' em: {folder}")

        latest = max(candidates, key=extract_id)
        return latest
    
    def read_fail_rows() -> pd.DataFrame:
        latest_csv = pick_latest_checked_csv()
        df = pd.read_csv(latest_csv)
        i = df.index[df["SAT"] == False][0]   # único índice com falha
        return df.iloc[i:i+2]                 # falha + linha seguinte (se existir)
    
    return read_fail_rows()


if __name__ == "__main__":
    # bus = TelemetryBus()
    
    # simulator = DroneBehaviorSimulator(bus, cfg)

    # initial_context = simulator.get_initial_context()
    # monitor = AntecipatedScenarioMonitor(initial_context, cfg)
    # bus.subscribe(monitor.handle_runtime_data)
    # simulator.run()

    identifier = UnanticipatedScenarioIdentifier(cfg)
    diagnoser = UnanticipatedScenarioDiagnoser(cfg)

    detected_unanticipated_scenarios_df = detected_unanticipated_scenario()

    if not detected_unanticipated_scenarios_df.empty:
        print("Unanticipated scenarios detected")

        identificated_unanticipatd_scenario_dict = identifier.identify(detected_unanticipated_scenarios_df)
        diagnosed_unanticipatd_scenario_dict = diagnoser.diagnose(detected_unanticipated_scenarios_df, identificated_unanticipatd_scenario_dict)






    # em qualquer momento você pode consultar:
    # print("\nÚltimo tick visto pelo monitor:")
    # print(monitor.latest)
    # print(monitor.history_runtime_data)
    

    # ticks = load_ticks(CSV_PATH, execution=EXECUTION_ID)

    # bus = TelemetryBus()
    # monitor = RuntimeDataMonitor()
    # bus.subscribe(monitor.handle_tick)

    # drone = TraceDroneReplayer(ticks)
    # drone.run(bus, tick_seconds=TICK_SECONDS)

    # # em qualquer momento você pode consultar:
    # print("\nÚltimo tick visto pelo monitor:")
    # print(monitor.latest)
    # print(monitor.history_runtime_data)