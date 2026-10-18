"""Append-only, fsync'd event journal plus atomic file writes.

The journal is the single source of truth: on boot the simulator replays it to rebuild
every account (lens 9). A power cut can leave a half-written last line; it is skipped.
"""

import json
import os


class Journal:
    def __init__(self, path):
        self.path = path

    def read(self):
        if not os.path.exists(self.path):
            return []
        events = []
        with open(self.path, "r", encoding="utf-8") as f:
            for n, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except ValueError:
                    # torn write from a power cut; only acceptable on the last line
                    events.append({"e": "corrupt", "line": n})
        while events and events[-1].get("e") == "corrupt":
            events.pop()
        if any(e.get("e") == "corrupt" for e in events):
            raise ValueError("journal %s is corrupt in the middle" % self.path)
        return events

    def append(self, event):
        line = json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n"
        fd = os.open(self.path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
        try:
            os.write(fd, line.encode("utf-8"))
            os.fsync(fd)
        finally:
            os.close(fd)


def write_atomic(path, text):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def append_line(path, text):
    with open(path, "a", encoding="utf-8") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
