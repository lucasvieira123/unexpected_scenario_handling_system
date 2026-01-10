# %%
from drone_behavior_simulator import DroneBehaviorSimulator, TelemetryBus
from antecipated_scenario_monitor import AntecipatedScenarioMonitor
import os
SCENARIO_STATE_MACHINE_YAML_PATH = os.path.join("laboratory", "scenario_state_machine.yaml")
CSV_PATH = os.path.join("laboratory", "drone_trace_simulation.csv")

if __name__ == "__main__":
    EXECUTION_ID = 1                    # 1..4
    TICK_SECONDS = 1.0                  # 0 = sem delay
    bus = TelemetryBus()

    simulator = DroneBehaviorSimulator(bus, CSV_PATH, EXECUTION_ID, TICK_SECONDS)
    monitor = AntecipatedScenarioMonitor(SCENARIO_STATE_MACHINE_YAML_PATH)
    bus.subscribe(monitor.handle_runtime_data)
    simulator.run()

    # em qualquer momento você pode consultar:
    print("\nÚltimo tick visto pelo monitor:")
    print(monitor.latest)
    print(monitor.history_runtime_data)
    

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