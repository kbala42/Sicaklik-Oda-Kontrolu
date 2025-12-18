import argparse
from itertools import product
from pathlib import Path
import pandas as pd
from src.runner import Scenario, run_scenario

BASE_DIR = Path(__file__).parent / "outputs"

def dataframe_to_html_table(dframe: pd.DataFrame) -> str:
    d = dframe.copy()
    for col in ["IAE","ISE","Overshoot_%","Settling_s","Energy_sum_u2","Violation_s"]:
        if col in d.columns:
            d[col] = d[col].astype(float).round(3)
    return d.to_html(index=False)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--duration", type=int, default=900, help="Simülasyon süresi (s)")
    ap.add_argument("--horizon", type=int, default=12, help="MPC ufku N")
    ap.add_argument("--ambient", nargs="+", type=float, default=[20.0,25.0,30.0])
    ap.add_argument("--mismatch", nargs="+", type=str, default=["nominal","minus20","plus20"])
    ap.add_argument("--profiles", nargs="+", type=str, default=["step","ramp","multistep"])
    args = ap.parse_args()

    records = []
    for prof, Ta, mm in product(args.profiles, args.ambient, args.mismatch):
        scn = Scenario(name=f"{prof}_Ta{int(Ta)}_{mm}", Ta=Ta, mismatch=mm, profile=prof)
        m_pid, _ = run_scenario(scn, controller_type="PID", sim_seconds=args.duration)
        records.append({"Scenario": scn.name, "Controller": "PID", **m_pid})
        m_mpc, _ = run_scenario(scn, controller_type="MPC", sim_seconds=args.duration,
                                mpc_cfg=dict(N=args.horizon, qy=1.0, qdu=0.08, umin=0.0, umax=1.0, du_max=0.06, Ta=Ta))
        records.append({"Scenario": scn.name, "Controller": "MPC", **m_mpc})

    df = pd.DataFrame.from_records(records)
    df.to_csv(BASE_DIR / "results_summary.csv", index=False)
    html = f"""<!DOCTYPE html>
<html lang="tr"><head><meta charset="utf-8"><title>Tam Rapor</title></head>
<body>
<h1>2204-A — Dijital İkiz Tam Rapor (Özet Tablo)</h1>
{dataframe_to_html_table(df)}
</body></html>"""
    (BASE_DIR/"report.html").write_text(html, encoding="utf-8")

if __name__ == "__main__":
    main()
