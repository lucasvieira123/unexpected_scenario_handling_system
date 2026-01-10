from schema import Optional
from typing import Optional, List

from drone_behavior_simulator import TelemetryTick
from sismic.io import import_from_yaml
from sismic.interpreter import Interpreter

class StateMachineEngine:
    def __init__(self, state_machine_yaml_path):
        self.state_machine = import_from_yaml(filepath=state_machine_yaml_path)
        self.itp = Interpreter(self.state_machine, initial_context={"neutral": True, "asterisk": True, "armed": False, "h": 0, "dt": 0, "b": 100, "delta_dt": 0})
        ms=self.itp.execute()
        print("MACROSTEP:", ms)
        print("CONFIG AFTER:", list(self.itp.configuration))

    def check_state_machine(self, runtime_data_tick: TelemetryTick) -> list:
        
        self.itp.context.update({
            "armed": runtime_data_tick.armed,
            "h": runtime_data_tick.h,
            "dt": runtime_data_tick.dt,
            "b": runtime_data_tick.b,
            "wind_speed": runtime_data_tick.wind_speed,
            "humidity": runtime_data_tick.humidity,
            "vibration": runtime_data_tick.vibration,
            "delta_dt": runtime_data_tick.dt,
            "action": runtime_data_tick.action})

        print(runtime_data_tick)

        if self.itp._external_queue:
            for _ in range(2):
                ms = self.itp.execute_once()
                print("MACROSTEP:", ms)
                print("external_queue raw:", self.itp._external_queue)
                print("CONFIG AFTER:", list(self.itp.configuration))
                
                if ms is None:
                    break
                
            
            

        # Execute the state machine
        for _ in range(2):
            ms = self.itp.execute_once()
            print("MACROSTEP:", ms)
            print("external_queue raw:", self.itp._external_queue)
            print("CONFIG AFTER:", list(self.itp.configuration))

            if ms is None:
                break
            
        
        if runtime_data_tick.action:
            self.itp.queue(runtime_data_tick.action)
            print("external_queue raw:", self.itp._external_queue)

        # Return the current state
        return self.itp.configuration


class AntecipatedScenarioMonitor:
    def __init__(self, state_machine_yaml_path: str) -> None:
        self.latest: Optional[TelemetryTick] = None
        self.history_runtime_data: List[TelemetryTick] = []  # opcional (pode desligar se ficar grande)
        self.state_machine_engine = StateMachineEngine(state_machine_yaml_path)

        self.current_state: Optional[str] = None
        self.current_scenario = None

    def handle_runtime_data(self, runtime_data_tick: TelemetryTick) -> None:
        self.latest = runtime_data_tick
        self.history_runtime_data.append(runtime_data_tick)

        report = self.state_machine_engine.check_state_machine(runtime_data_tick)

        act = runtime_data_tick.action if runtime_data_tick.action else "-"

        print(f"[exec={runtime_data_tick.execution} t={runtime_data_tick.t:02d}] action={act:15s} h={runtime_data_tick.h:6.1f} b={runtime_data_tick.b:5.1f} vib={runtime_data_tick.vibration:.2f}")
