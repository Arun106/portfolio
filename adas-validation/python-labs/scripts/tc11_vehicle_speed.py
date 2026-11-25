import pandas as pd
from common import run_cases

def check(rows):
    df = pd.DataFrame(rows, columns=["reference", "actual"])
    assert not df.empty and not df.isna().any().any(), "Missing data"
    delta = (df.actual - df.reference).abs()
    bad = delta > 2
    assert not bad.any(), f"Bad samples: {df.loc[bad].to_dict('records')}"

if __name__ == "__main__":
    raise SystemExit(run_cases("tc11_vehicle_speed", [
        ("within tolerance", [(0, 0), (80, 81.5)], None),
        ("deviation", [(80, 84)], AssertionError),
        ("missing", [(80, None)], AssertionError),
    ], check))
