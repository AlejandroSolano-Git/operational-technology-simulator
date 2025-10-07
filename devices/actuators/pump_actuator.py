# devices\actuators\pump_actuator.py

from dataclasses import dataclass
from core.commands import Ack, AckCode, CommandKind
from devices.base import BaseActuator

@dataclass(kw_only=True)
class OnOffPump(BaseActuator):
    def _on_command(self, cmd) -> Ack:
        if cmd.kind in (CommandKind.START, CommandKind.STOP):
            self._last_cmd = cmd
            return Ack(True)
        return Ack(False, AckCode.INVALID, "Only START/STOP supported.")
        
    
    def update(self, clk):
        # Interlokcs are enforced while running
        if not self._interlocks_ok():
            self._enter(clk, "FAULT") #or "OFF" if default-safe
            return
        
        want_run = bool(self._last_cmd and self._last_cmd.kind == CommandKind.START)

        if self.state == "OFF":
            if want_run and self._permissives_ok():
                self._enter(clk, "RUNNING")
        elif self.state == "RUNNING":
            if not want_run:
                self._enter(clk, "OFF")
            elif not self._permissives_ok():
                # Permissive lost before start? Choose the policy; here we hold RUNNING unless the interlock fails
                pass
        elif self.state == "FAULT":
            #Stay faulted until someone handles reset (to be implemented)
            pass
        #else: remain in curent state (waiting for permissives)