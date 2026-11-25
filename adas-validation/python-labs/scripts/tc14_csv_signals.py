import pandas as pd
from common import DATA, run_cases

def check(filename):
    df = pd.read_csv(DATA / filename)
    assert {"timestamp_ms", "voltage"} <= set(df.columns), "Bad schema"
    assert not df.empty and not df.isna().any().any(), "Missing data"
    assert (df.timestamp_ms.diff().dropna() > 0).all(), "Bad time order"
    bad = ~df.voltage.between(9, 16)
    assert not bad.any(), f"Bad rows: {df.loc[bad].to_dict('records')}"

if __name__ == "__main__":
    raise SystemExit(run_cases("tc14_csv_signals", [
        ("clean", "signals_clean.csv", None),
        ("fault", "signals_fault.csv", AssertionError),
    ], check))
