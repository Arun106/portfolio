from common import TestError, run_cases

class ECUConnectionError(TestError):
    pass

class SimulatedECU:
    def __init__(self, connected):
        self.connected = connected

    def probe(self):
        if not self.connected:
            raise ECUConnectionError("No ECU response")
        return b"READY"

def check(connected):
    ecu = SimulatedECU(connected)
    assert ecu.probe() == b"READY", "Unexpected ECU reply"

if __name__ == "__main__":
    raise SystemExit(run_cases("tc01_ecu_connectivity", [
        ("online", True, None),
        ("offline", False, ECUConnectionError),
    ], check))
