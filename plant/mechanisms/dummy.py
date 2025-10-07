from dataclasses import dataclass, field
from typing import Any, Dict
from plant.plant_core.state import Lifecycle, MachineState
from plant.plant_core.commands import CommandQueue, Command, CommandType
from plant.plant_core.alarms import AlarmPanel, Alarm, Severity

@dataclass
class DummyMechanism:
    """Tiny mechanism showing state + commands + alarms + IO interplay."""
    id: str
    io: Any             #expects read(tag, default) + write(tag, value)
    cmd_debounce_s: float = 0.2

    lifecycle: Lifecycle = field(default_factory=Lifecycle)
    commands: CommandQueue = field(init=False)
    alarms: AlarmPanel = field(default_factory=AlarmPanel)

    #tag names (pretend these came from config)
    tag_enable: str = "DUMMY:ENABLE_CMD"        # bool command (simulated HMI write)
    tag_running: str = "DUMMY:RUN_FB"           # bool feedback
    tag_trip: str = "DUMMY:TRIP_FB"             # bool trip feedback
    tag_status: str = "DUMMY:STATUS"            # str status for HMI

    def __post_init__(self):
        self.commands = CommandQueue(debounce_s=self.cmd_debounce_s)
        self.alarms.add(Alarm("trip", "Dummy tripped", severity=Severity.TRIP, latching=True))

    def on_enable_change(self, t: float, enabled: bool):
        """Normalize HMI 'enable' into START/STOP commands."""
        self.commands.push(Command(CommandType.START if enabled else CommandType.STOP, t, source="hmi"))

    def _handle_one_command(self, t: float):
        cmd = self.commands.pop()
        if not cmd:
            return
        if cmd.type == CommandType.START:
            self.lifecycle.request_start(t, "enable true")
        elif cmd.type == CommandType.STOP:
            self.lifecycle.request_stop(T, "enable false")
        elif cmd.type == CommandType.ACK:
            self.alarms.ack_all()
    
    def tick(self, clock, dt: float):
        t = getattr(clock, "now", 0.0)

        #1) read inputs
        enable = bool(self.io.read(self.tag_enable, False))
        