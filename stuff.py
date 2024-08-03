from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable, Literal, Type, Self


class Symbol:

    def __init__(self):
        self.counter = 0

    def __call__(self) -> str:
        self.counter += 1
        return f"x_{self.counter}"
    
SYMBOL = Symbol()

@dataclass
class Delta0:
    repr: str
    truth: Callable[[], bool] = lambda: None

    def __or__(self, other: Delta0) -> Delta0:
        return Delta0(
            repr=f"({self.repr}) | ({other.repr})",
            truth=lambda: self.truth() or other.truth(),
        )

    def __and__(self, other: Delta0) -> Delta0:
        return Delta0(
            repr=f"({self.repr}) & ({other.repr})",
            truth=lambda: self.truth() and other.truth(),
        )

    def __invert__(self) -> Delta0:
        return Delta0(
            repr=f"~({self.repr})",
            truth=lambda: not self.truth(),
        )
        
    def __repr__(self) -> str:
        return self.repr


class FOL:

    def __init__(
        self,
        quantifier: Literal["∃", "∀"] = None,
        fol_sequence: FOL_sequence = None,
        delta: Delta0 = None,
    ):
        assert (delta is None) != (quantifier is None)
        assert (fol_sequence is None) == (quantifier is None)
        self.quantifier = quantifier
        self.fol_sequence = fol_sequence
        self.delta = delta
        if fol_sequence is not None:
            self.space = fol_sequence.space

    @classmethod
    def delta0(cls, **kwargs) -> FOL:
        return cls(delta=Delta0(**kwargs))

    @classmethod
    def exists(cls, **kwargs) -> FOL:
        return cls(quantifier="∃", fol_sequence=FOL_sequence(**kwargs))

    @classmethod
    def forall(cls, **kwargs) -> FOL:
        return cls(quantifier="∀", fol_sequence=FOL_sequence(**kwargs))

    def __or__(self, other: FOL) -> FOL:
        if self.quantifier is not None:
            return FOL(
                quantifier=self.quantifier,
                fol_sequence=self.fol_sequence | other,
            )
        elif other.quantifier is not None:
            return other | self
        else:
            return FOL(delta=self.delta | other.delta)

    def __and__(self, other: FOL) -> FOL:
        if self.quantifier is not None:
            return FOL(
                quantifier=self.quantifier,
                fol_sequence=self.fol_sequence & other,
            )
        elif other.quantifier is not None:
            return other & self
        else:
            return FOL(delta=self.delta & other.delta)

    def __invert__(self) -> FOL:
        if self.quantifier is not None:
            return FOL(
                quantifier=("∃" if self.quantifier == "∀" else "∀"),
                fol_sequence=~self.fol_sequence,
            )
        else:
            return FOL(delta=~self.delta)
    
    def __repr__(self) -> str:
        if self.quantifier is not None:
            x = SYMBOL()
            return f"{self.quantifier}{x} ∈ {self.space}. {self.fol_sequence._repr(x)}"
        else:
            return self.delta.repr

    def subst(self, x: "Self.space"):
        return self.fol_sequence(x) if self.quantifier is not None else self.delta.truth()

    def play(self, xs: list["Self.space"]) -> bool:
        if self.quantifier == "∃":
            return any(self.subst(x) for x in xs)
        elif self.quantifier == "∀":
            return all(self.subst(x) for x in xs)
        elif self.delta is not None:
            return self.delta.truth()
        else:
            raise ValueError("Invalid FOL sentence")


@dataclass
class FOL_sequence:

    sequence: Callable[["Self.space"], FOL]
    repr: str # string with placeholder {x}
    space: Type = int

    def _repr(self, x: str = None) -> str:
        if x is None:
            x = SYMBOL()
        return self.repr.format(x=x)
    
    def __repr__(self) -> str:
        return self._repr() 
    
    def __or__(self, other: FOL) -> FOL_sequence:
        return FOL_sequence(
            space=self.space,
            sequence=lambda x: self.sequence(x) | other,
            repr=f"({self.repr}) | ({other})",
        )
    
    def __and__(self, other: FOL) -> FOL_sequence:
        return FOL_sequence(
            space=self.space,
            sequence=lambda x: self.sequence(x) & other,
            repr=f"({self.repr}) & ({other})",
        )
    
    def __invert__(self) -> FOL_sequence:
        return FOL_sequence(
            space=self.space,
            sequence=lambda x: ~self.sequence(x),
            repr=f"~({self.repr})",
        )
    
    def __call__(self, x: "Self.space") -> FOL:
        return self.sequence(x)