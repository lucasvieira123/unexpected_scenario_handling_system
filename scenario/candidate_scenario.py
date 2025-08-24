from scenario.antecipated_scenario import AntecipatedScenario


class CandidateScenario(AntecipatedScenario):
    """
    Candidate Scenario: identical to AntecipatedScenario, inherits all logic.
    """
    def to_dict(self) -> dict:
        d = super().to_dict()
        d["type"] = self.__class__.__name__ # Ensure correct type
        return d
