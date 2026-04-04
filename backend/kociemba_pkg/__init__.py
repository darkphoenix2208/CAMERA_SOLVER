"""Vendored pure-Python Kociemba two-phase solver (muodov/kociemba, pykociemba only)."""

from .pykociemba import search

_ERRORS = {
    "Error 1": "There is not exactly one facelet of each colour",
    "Error 2": "Not all 12 edges exist exactly once",
    "Error 3": "Flip error: One edge has to be flipped",
    "Error 4": "Not all corners exist exactly once",
    "Error 5": "Twist error: One corner has to be twisted",
    "Error 6": "Parity error: Two corners or two edges have to be exchanged",
    "Error 7": "No solution exists for the given maxDepth",
    "Error 8": "Timeout, no solution within given time",
}


def solve_kociemba(cubestring: str, max_depth: int = 24) -> str:
    res = search.Search().solution(cubestring, max_depth, 1000, False).strip()
    if res in _ERRORS:
        raise ValueError(_ERRORS[res])
    return res
