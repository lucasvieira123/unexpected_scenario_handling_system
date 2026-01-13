# DejaVuArch: A Reference Architecture for Handling Unanticipated Scenarios through Similarity-Based Adaptation

## Table of Contents
- [Overview](#overview)
- [Installation](#installation)
- [Configuration](#configuration)
- [Quick Run](#quick-run)
- [Reproducing the Paper Experiments](#reproducing-the-paper-experiments)
- [License](#license)

## Overview
**DejaVuArch** is a reference architecture that enables **self-evolving systems** to **detect**, **identify**, **diagnose**, and **remediate** unanticipated scenarios using **similarity-based adaptation**.

In this repository, the pipeline can (optionally) **replay/simulate a target system execution** (e.g., from traces) and then perform scenario monitoring and similarity-based analysis to support unanticipated scenario handling.

## Installation
To run DejaVuArch, you only need a recent version of **Python** and the project dependencies installed from `requirements.txt`.  
We strongly recommend using a **Python virtual environment** to keep dependencies isolated.

### 1) Create and activate a virtual environment

### 2) Install dependencies
```bash
pip install -U pip
pip install -r requirements.txt
```

## Configuration
All configuration files and generated artifacts are located in the `res/` folder.

### Configuration folder (`res/`)
- **`dejavu_conf.yaml`**: main configuration file (paths, flags, thresholds, experiment options).
- **`scenario_state_machine.yaml`**: executable state machine used by the monitor (states, transitions, guards, invariants), generated from the anticipated scenarios.
- **`scenario_state_machine.puml`**: PlantUML version of the state machine (visualization).
- **`anticipated_scenarios.yaml`**: modeled anticipated scenarios (what is expected/monitored).
- **`monitored_parameters.json`**: list of monitored variables/features (i.e., which trace columns are used).
- **`weights_config.yaml`**: similarity configuration (feature weights, factors, thresholds).
- **`shared_scenarios.json`**: shared candidate scenarios used to keep comparisons consistent during the similarity step.
- **`similarities.jsonl`**: similarity results (often precomputed) used by the adaptation strategy.
- **`runtime_replays/`**: traces for replay (execution traces, actions, historical runs) used to simulate a target system execution.
- **`checked_scenarios/`**: outputs produced by the monitoring process (per-execution scenario checks and SAT results).

## Quick Run
After configuring the files in `res/` and deciding whether you will **replay/simulate the target system execution** or **skip directly to the detection, identification, diagnosis, and similarity-based adaptation steps**, you can run DejaVuArch with:

```bash
python dejavu.py
```

## Reproducing the Paper Experiments
The default configuration files included in this repository are already set to match the experimental setup reported in the paper. Therefore, to reproduce the experiments, simply run:

```bash
python dejavu.py
```

After the execution finishes, check the generated results in:
- `res/similarities.jsonl`

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE.txt) file for details.
