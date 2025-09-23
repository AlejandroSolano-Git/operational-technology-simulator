# core/point_types.py
from enum import Enum
from core.point import Point

class BinaryPoint(Point[bool]): ... #run, ready, fault, limit switches
class AnalogPoint(Point[float]): ... #temps, pressure, flows, level
class CounterPoint(Point[int]): ... #pulse totals, energy counters

class Discrete(Enum): #e.g., value position state
    CLOSED = 0
    OPEN = 1
    TRAVELING = 2

class DiscretePoint(Point[Discrete]): ... #multi-state devices (value OPEN/CLOSED/TRAVELING, breaker OPEN/CLOSED/TRIPPED)