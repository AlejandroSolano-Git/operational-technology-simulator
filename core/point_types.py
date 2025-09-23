# core/point_types.py
from enum import Enum
from core.point import Point

class BinaryPoint(Point[bool]): ...
class AnalogPoint(Point[float]): ...
class CounterPoint(Point[int]): ...

class Discrete(Enum): #e.g., value position state
    CLOSED = 0
    OPEN = 1
    TRAVELING = 2

class DiscretePoint(Point[Discrete]): ...