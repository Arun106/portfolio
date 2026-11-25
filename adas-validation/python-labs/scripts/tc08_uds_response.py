from common import TestError, run_cases

class DiagnosticError(TestError):
    pass

def check(response):
    if response[:1] == b"\x7f":
        raise DiagnosticError(f"Negative response: {response.hex()}")
    assert response[:3] == bytes.fromhex("62 F1 90"), "Bad header"
    vin = response[3:].decode("ascii")
    assert len(vin) == 17 and vin.isalnum(), "Invalid VIN payload"

if __name__ == "__main__":
    good = bytes.fromhex("62 F1 90") + b"WVWZZZ12345678901"
    raise SystemExit(run_cases("tc08_uds_response", [
        ("positive", good, None),
        ("negative", bytes.fromhex("7F 22 31"), DiagnosticError),
        ("truncated", bytes.fromhex("62 F1 90"), AssertionError),
    ], check))
