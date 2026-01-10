# from __future__ import annotations
from typing import  List
import time
import pandas as pd
from drone_telemetry import TelemetryBus, TelemetryTick

class DroneBehaviorSimulator:
    def __init__(self, bus: TelemetryBus, csv_path: str, execution_id: int, tick_seconds: float) -> None:
        self.csv_path = csv_path
        self.execution_id = execution_id
        self.tick_seconds = tick_seconds
        self.bus = bus

    def load_ticks(self, csv_path: str, execution: int) -> List[TelemetryTick]:
        df = pd.read_csv(csv_path)

        # garante ordenação
        df = df[df["execution"] == execution].sort_values(["execution", "t"], ascending=True)

        ticks: List[TelemetryTick] = []
        for _, r in df.iterrows():
            action = r["Action"]
            action = None if action == "-" else str(action)

            ticks.append(
                TelemetryTick(
                    execution=int(r["execution"]),
                    t=int(r["t"]),
                    h=float(r["h"]),
                    dt=float(r["dt"]),
                    b=float(r["b"]),
                    armed=bool(r["Armed_Status"]),
                    wind_speed=float(r["Wind_Speed"]),
                    humidity=float(r["Humidity"]),
                    vibration=float(r["Vibration"]),
                    action=action,
                )
            )
        return ticks

    def run(self):
        ticks = self.load_ticks(self.csv_path, execution=self.execution_id)
        for tick in ticks:
            self.bus.publish(tick)
            if self.tick_seconds > 0:
                time.sleep(self.tick_seconds)
        
    