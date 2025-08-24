from typing import Optional, Dict, Any, Type, TypeVar
from expression.action_expression import ActionExpression
from expression.conditional_expression import ConditionalExpression
from scenario.scenario_BDD import ScenarioBDD

class AntecipatedScenario(ScenarioBDD):
    """
    Concrete scenario class: has an action ('do').
    """

    def __init__(
        self,
        name: str = None,
        given: ConditionalExpression = None,
        when: ConditionalExpression = None,
        then: ConditionalExpression = None,
        do: ActionExpression = None,
        data: dict = None,
    ) -> None:
        if data is not None:
            if data.get("do") is None:
                raise ValueError("DO must be provided in data.")
            do = ActionExpression(data.get("do"))
            self._do = do
        else:
            if given is None or when is None or then is None or do is None:
                raise ValueError("given, when, then, and do must be provided if data is not given.")
        super().__init__(name, given, when, then, data)
        

    @property
    def do(self) -> ActionExpression:
        return self._do

    @do.setter
    def do(self, value: ActionExpression) -> None:
        self._do = value


    def to_dict(self) -> dict:
        return {
            "type": self.__class__.__name__,
            "name": self._name,
            "given": self._given.expression,
            "when": self._when.expression,
            "do": self._do.expression,
            "then": self._then.expression
            
        }
