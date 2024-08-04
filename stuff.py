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
        if self == Delta0.true() or other == Delta0.true():
            return Delta0.true()
        if self == Delta0.false():
            return other
        if other == Delta0.false():
            return self
        return Delta0(
            repr=f"({self.repr}) | ({other.repr})",
            truth=lambda: self.truth() or other.truth(),
        )

    def __and__(self, other: Delta0) -> Delta0:
        if self == Delta0.false() or other == Delta0.false():
            return Delta0.false()
        if self == Delta0.true():
            return other
        if other == Delta0.true():
            return self
        return Delta0(
            repr=f"({self.repr}) & ({other.repr})",
            truth=lambda: self.truth() and other.truth(),
        )

    def __invert__(self) -> Delta0:
        if self == Delta0.true():
            return Delta0.false()
        if self == Delta0.false():
            return Delta0.true()
        return Delta0(
            repr=f"~({self.repr})",
            truth=lambda: not self.truth(),
        )
        
    def __repr__(self) -> str:
        return self.repr
    
    @classmethod
    def true(cls) -> Delta0:
        return cls(repr="True", truth=lambda: True)
    
    @classmethod
    def false(cls) -> Delta0:
        return cls(repr="False", truth=lambda: False)

    def __eq__(self, other: Any) -> bool:
        return self.repr == other.repr and self.truth() == other.truth()

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
        if self == FOL.true() or other == FOL.true():
            return FOL.true()
        if self == FOL.false():
            return other
        if other == FOL.false():
            return self
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
        if self == FOL.false() or other == FOL.false():
            return FOL.false()
        if self == FOL.true():
            return other
        if other == FOL.true():
            return self
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
        if self == FOL.true():
            return FOL.false()
        if self == FOL.false():
            return FOL.true()
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
            return f"{self.quantifier} ({x} : {self.space}), {self(x)}"
        else:
            return self.delta.repr

    @classmethod
    def true(cls) -> FOL:
        return cls(delta=Delta0.true())
    
    @classmethod
    def false(cls) -> FOL:
        return cls(delta=Delta0.false())

    def __call__(self, x: "Self.space"):
        return self.fol_sequence(x) if self.quantifier is not None else self.delta.truth()

    def play(self, xs: list["Self.space"]) -> FOL:
        if self.quantifier == "∃":
            res = FOL.false()
            for x in xs:
                res |= self(x)
            return res
        elif self.quantifier == "∀":
            res = FOL.true()
            for x in xs:
                res &= self(x)
            return res
        elif self.delta is not None:
            return self.delta.truth()
        else:
            raise ValueError("Invalid FOL sentence")
        
    def __eq__(self, other: Any) -> bool:
        return self.quantifier == other.quantifier and self.fol_sequence == other.fol_sequence and self.delta == other.delta


@dataclass
class FOL_sequence:

    sequence: Callable[["Self.space"], FOL]
    space: Type = int
        
    def __or__(self, other: FOL) -> FOL_sequence:
        return FOL_sequence(
            space=self.space,
            sequence=lambda x: self.sequence(x) | other,
        )
    
    def __and__(self, other: FOL) -> FOL_sequence:
        return FOL_sequence(
            space=self.space,
            sequence=lambda x: self.sequence(x) & other,
        )
    
    def __invert__(self) -> FOL_sequence:
        return FOL_sequence(
            space=self.space,
            sequence=lambda x: ~self.sequence(x),
        )
    
    def __call__(self, x: "Self.space") -> FOL:
        return self.sequence(x)