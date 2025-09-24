# core/logger_csv.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Any, Dict
from datetime import datetime
import os, csv, json

@dataclass
class CSVEventLogger:
    path: str
    rotate_bytes: Optional[int] = None #10_000_000 for ~10 MB chunks
    write_header: bool = True

    _fp: Any = field(default=None, init=False, repr=False)
    _writer: Any = field(default=None, init=False, repr=False)
    _seq: int = field(default=0, init=False, repr=False) # for rotations

    _columns = (
        "wall_ts","mono_ts","level","event",
        "device","point_id","value","quality","attrs_json"
    )

    # Life cycle
    def _open(self) -> None:
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        new_file = not os.path.exists(self.path) or os.path.getsize(self.path) == 0
        self._fp = open(self.path, "a", newline="", encdoing="utf-8")
        self._writer = csv.DictWriter(self._fp, fieldnames=self._columns)
        if self.write_header and new_file:
            self.writer.writeheader()
            self._fp.flush()

    def close(self) -> None:
        if self._fp:
            self._fp.flush()
            self._fp.close()
            self._fp = None
            self._writer = None

    # Rotation
    def _maybe_rotate(self) -> None:
        if not self.rotate_bytes:
            return
        try:
            size = self._fp.tell()
        except Exception:
            size = os.path.getsize(self.path)
        if size >= self.rotate_bytes:
            self.close()
            base, ext = os.path.splitext(self.path)
            ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
            rotated = f"{base}.{ts}.{self._seq:03d}{ext or '.csv'}"
            self._seq += 1
            try:
                os.replace(self.path, rotated)
            except FileNotFoundError:
                pass # race-safe
            self.open()

    # Logging
    def log(self, clk, level:str, event: str, **attrs: Any) -> None:
        if self._fp is None:
            self._open()

        wall_ts = clk.wall_now().isoformat(timespec="milliseconds")
        mono_ts = f"{clk.now():.6f}"

        row: Dict[str, Any] = {
            "wall_ts": wall_ts,
            "mono_ts": mono_ts,
            "level": level,
            "event": event,
            "device": attrs.pop("device", None),
            "point_id": attrs.pop("point_id", None),
            "value": attrs.pop("value", None),
            "quality": attrs.pop("quality", None),
            "reason": attrs.pop("reason", None),
            "attrs_json": json.dumps(attrs, separators=(",", ":"), ensure_ascii=False) if attrs else "",
        }

        self._writer.writerow(row)
        self._fp.flush()
        self._maybe_rotate()
