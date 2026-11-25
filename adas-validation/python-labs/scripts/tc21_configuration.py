import json
from common import DATA, TestError, run_cases

class ConfigurationError(TestError):
    pass

def check(filename):
    config = json.loads((DATA / filename).read_text(encoding="utf-8"))
    if not isinstance(config, dict) or not config.get("ecu_id"):
        raise ConfigurationError("Missing ECU ID")
    timeout = config.get("timeout_ms")
    if type(timeout) is not int or timeout <= 0:
        raise ConfigurationError("Invalid timeout")

if __name__ == "__main__":
    raise SystemExit(run_cases("tc21_configuration", [
        ("valid", "config_valid.json", None),
        ("invalid", "config_invalid.json", ConfigurationError),
        ("bad JSON", "config_broken.json", json.JSONDecodeError),
    ], check))
