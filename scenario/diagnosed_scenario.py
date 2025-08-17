from typing import Optional
from expression.expression import ActionExpression, ConditionalExpression
from scenario.scenario import Scenario


class DiagnoedScenario(Scenario):
    """Cenário de diagnóstico: não possui ação (do)."""

    def __init__(
        self,
        name: str,
        given: ConditionalExpression,
        when: ConditionalExpression,
        then: ConditionalExpression,
    ) -> None:
        super().__init__(name, given, when, then)

    @property
    def do(self) -> Optional[ActionExpression]:
        return None  # explicitamente sem ação

    @do.setter
    def do(self, value: ActionExpression) -> None:
        raise AttributeError("DiagnosticScenario não suporta 'do'.")
