from typing import Optional
from expression.expression import ActionExpression, ConditionalExpression
from scenario.scenario import Scenario

class CompleteScenario(Scenario):
    """Cenário normal: possui ação (do)."""

    def __init__(
        self,
        name: str,
        given: ConditionalExpression,
        when: ConditionalExpression,
        then: ConditionalExpression,
        do: ActionExpression,
    ) -> None:
        super().__init__(name, given, when, then)
        self._do = do  # obrigatório

    @property
    def do(self) -> ActionExpression:
        return self._do

    @do.setter
    def do(self, value: ActionExpression) -> None:
        self._do = value