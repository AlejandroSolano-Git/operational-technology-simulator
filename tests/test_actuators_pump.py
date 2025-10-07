# tests/test_actuators_pump.py

from core.clock import SimClock
from core.commands import CommandKind
from devices.actuators.pump_actuator import OnOffPump
from devices.base import Mode

#Tiny command to avoid coupling Command ctor details
class Cmd:
    def __init__(self, kind): self.kind = kind

def test_pump_accepts_start_stop_only():
    p = OnOffPump(id="P_101")
    ok = p.command(Cmd(CommandKind.START))
    assert ok.ok

    bad = p.command(Cmd(CommandKind.SETPOINT)) # Anything not START/STOP should be invalid
    assert not bad.ok
    assert bad.code.name in ("INVALID", "BAD_REQUEST", "ERROR")

def test_pump_respects_mode_lock_and_local():
    p = OnOffPump(id="P_102")

    #LOCKED: reject commands
    p.set_mode(Mode.LOCKED)
    ack = p.command(Cmd(CommandKind.START))
    assert not ack.ok
    assert ack.code.name == "CONFLICT"
    assert p.state == "OFF"

def test_pump_runs_when_permissives_ok():
    p = OnOffPump(id="P_103")

    #permissives/interlocks use callables; makes them toggable
    flags = {"perm": True, "il": True}
    p.add_permissive(lambda: flags["perm"])
    p.add_interlock(lambda: flags["il"])

    clk = SimClock(0.5)

    p.command(Cmd(CommandKind.START))
    p.update(clk)
    assert p.state== "RUNNING"

def test_pump_stays_off_without_permissive():
    p= OnOffPump(id="P_104")
    flags = {"perm": False, "il": True}
    p.add_permissive(lambda: flags["perm"])
    p.add_interlock(lambda: flags["il"])

    clk = SimClock(0.5)

    p.command(Cmd(CommandKind.START))
    p.update(clk)
    assert p.state == "OFF"

def test_pump_faults_on_interlock_loss():
    p = OnOffPump(id="P_105")
    flags = {"perm": True, "il": True}
    p.add_permissive(lambda: flags["perm"])
    p.add_interlock(lambda: flags["il"])

    clk = SimClock(0.5)

    #Start and reach RUNNING
    p.command(Cmd(CommandKind.START))
    p.update(clk)
    assert p.state == "RUNNING"

    # Interlock drops -> should fault on next scan
    flags["il"] = False
    p.update(clk)
    assert p.state == "FAULT"

def test_pump_stop_transitions_off():
    p = OnOffPump(id="P_106")
    flags = {"perm": True, "il": True}
    p.add_permissive(lambda: flags["perm"])
    p.add_interlock(lambda: flags["il"])

    clk = SimClock(0.5)

    p.command(Cmd(CommandKind.START))
    p.update(clk)
    assert p.state == "RUNNING"

    p.command(Cmd(CommandKind.STOP))
    p.update(clk)
    assert p.state == "OFF"