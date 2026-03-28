from __future__ import annotations

import random
from typing import Sequence, TypeVar

T = TypeVar("T")


class SeededRNG:
    def __init__(self, seed: int) -> None:
        self.seed = seed
        self._random = random.Random(seed)

    def random(self) -> float:
        return self._random.random()

    def randint(self, a: int, b: int) -> int:
        return self._random.randint(a, b)

    def choice(self, values: Sequence[T]) -> T:
        if not values:
            raise ValueError("choice requires a non-empty sequence")
        return self._random.choice(values)

    def shuffle(self, values: list[T]) -> None:
        self._random.shuffle(values)
