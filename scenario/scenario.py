from expression.expression import ConditionalExpression, ActionExpression
from abc import ABC, abstractmethod
from typing import Optional

class Scenario(ABC):
    def __init__(
        self,
        name: str,
        given: ConditionalExpression,
        when: ConditionalExpression,
        then: ConditionalExpression,
    ) -> None:
        self._name = name
        self._given = given
        self._when = when
        self._then = then

    # --- comuns ---
    @property
    def name(self) -> str:
        return self._name

    @property
    def given(self) -> ConditionalExpression:
        return self._given

    @property
    def when(self) -> ConditionalExpression:
        return self._when

    @property
    def then(self) -> ConditionalExpression:
        return self._then

    @given.setter
    def given(self, value: ConditionalExpression) -> None:
        self._given = value

    @when.setter
    def when(self, value: ConditionalExpression) -> None:
        self._when = value

    @then.setter
    def then(self, value: ConditionalExpression) -> None:
        self._then = value

    @property
    @abstractmethod
    def do(self) -> Optional[ActionExpression]:
        """Retorna a ação do cenário (ou None se não existir)."""
        raise NotImplementedError
    
    @do.setter
    @abstractmethod
    def do(self, value: ActionExpression) -> None:
        """Define a ação (se suportado)."""
        raise NotImplementedError
    
    def to_dict(self) -> dict:
        return {
            "type": self.__class__.__name__,
            "name": self._name,
            "given": self._given.expression,
            "when": self._when.expression,
            "then": self._then.expression,
            "do": None if self.do is None else self.do.action,
        }
    