from dataclasses import dataclass
from typing import Any, Callable, Literal, Type, Self
from __future__ import annotations


@dataclass
class Delta0:
    sentence: str
    truth: Callable[[], bool]

    def __or__(self, other: Delta0) -> Delta0:
        return Delta0(
            sentence=f"({self.sentence}) | ({other.sentence})",
            truth=lambda: self.truth() or other.truth(),
        )

    def __and__(self, other: Delta0) -> Delta0:
        return Delta0(
            sentence=f"({self.sentence}) & ({other.sentence})",
            truth=lambda: self.truth() and other.truth(),
        )

    def __invert__(self) -> Delta0:
        return Delta0(
            sentence=f"~({self.sentence})",
            truth=lambda: not self.truth(),
        )


class FOL:

    def __init__(
        self,
        quantifier: Literal["+", "*"] = None,
        subsentences: Callable[["Self.space"], FOL] = None,
        space: Type = None,
        delta: Delta0 = None,
    ):
        if delta is None:
            assert quantifier is not None and subsentences is not None, (
                "If not a delta0 sentence, you must provide quantifier, "
                "space, and subsentences (actually, space can be assumed to be int)."
            )
            space = space or int
        else:
            assert quantifier is None and space is None and subsentences is None, (
                "If a delta0 sentence, you must not provide quantifier, "
                "space, or subsentences."
            )
        self.quantifier = quantifier
        self.space = space
        self.subsentences = subsentences
        self.delta = delta

    @classmethod
    def id(cls, delta0: Delta0 | FOL) -> FOL:
        if isinstance(delta0, Delta0):
            return cls(delta=delta0)
        elif isinstance(delta0, FOL):
            return delta0
        else:
            raise TypeError(f"Expected Delta0 or FOL, got {type(delta0)}")

    @classmethod
    def exists(cls, subsentences: Callable[["space"], FOL], space: Type = None) -> FOL:
        return cls(quantifier="+", subsentences=subsentences, space=space)

    @classmethod
    def forall(cls, subsentences: Callable[["space"], FOL], space: Type = None) -> FOL:
        return cls(quantifier="*", subsentences=subsentences, space=space)

    def __or__(self, other: FOL) -> FOL:
        if self.quantifier is not None:
            return FOL(
                quantifier=self.quantifier,
                subsentences=lambda x: self.subsentences(x) | other,
                space=self.space,
            )
        elif other.quantifier is not None:
            return other | self
        else:
            return FOL(delta=self.delta | other.delta)
    
    def __and__(self, other: FOL) -> FOL:
        if self.quantifier is not None:
            return FOL(
                quantifier=self.quantifier,
                subsentences=lambda x: self.subsentences(x) & other,
                space=self.space,
            )
        elif other.quantifier is not None:
            return other & self
        else:
            return FOL(delta=self.delta & other.delta)
    
    def __invert__(self) -> FOL:
        if self.quantifier is not None:
            return FOL(
                quantifier=("+" if self.quantifier == "*" else "*"),
                subsentences=lambda x: ~self.subsentences(x),
                space=self.space,
            )
        else:
            return FOL(delta=~self.delta)
        
    def subst(self, x: "Self.space"):
        return self.subsentences(x)
    
    def play(self, xs: list["Self.space"]) -> bool:
        if self.quantifier == "+":
            return any(self.subst(x) for x in xs)
        elif self.quantifier == "*":
            return all(self.subst(x) for x in xs)
        elif self.delta is not None:
            return self.delta.truth()
        else:
            raise ValueError("Invalid FOL sentence")

