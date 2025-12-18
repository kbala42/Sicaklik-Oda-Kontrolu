# experiments_full.py  —  ANALİZ GÖMÜLÜ SÜRÜM
import argparse, time
from itertools import product
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from src.runner import Scenario, run_scenario

BASE_DIR = Path(__file__).parent / "outputs"
FIG_DIR  = BASE_DIR / "figures"
BASE_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

METRICS = ["IAE","ISE","Overshoot_%","Settling_s","Energy_sum_u2","Violation_s"]

def dataframe_to_html_table(dframe: pd.DataFrame) -> str:
    d = dframe.copy()
    for col in METRICS:
        if col in d.columns:
            d[col] = d[col].astype(float).round(3)
    return d.to_html(index=False)

def wins_table(df: pd.DataFrame, metric: str):
    # "düşük daha iyi" varsayımı
    pvt = df.pivot_table(index="Scenario", columns="Controller", values=metric, aggfunc="first")
    wins   = int((pvt["MPC"] < pvt["PID"]).sum())
    ties   = int(np.isclose(pvt["MPC"], pvt["PID"]).sum())
    losses = int((pvt["MPC"] > pvt["PID"]).sum())
    return wins, ties, losses

def median_iqr(df: pd.DataFrame, by_cols, metric_cols):
    g = df.groupby(by_cols + ["Controller"])[metric_cols]
    med = g.median().rename(columns=lambda c: f"median_{c}")
    q1  = g.quantile(0.25).rename(columns=lambda c: f"q1_{c}")
    q3  = g.quantile(0.75).rename(columns=lambda c: f"q3_{c}")
    return pd.concat([med,q1,q3], axis=1).reset_index()

def boxplot_metric(df: pd.DataFrame, metric: str, outpng: Path, title: str):
    plt.figure()
    d_pid = df[df["Controller"]=="PID"][metric].values
    d_mpc = df[df["Controller"]=="MPC"][metric].values
    # Matplotlib 3.9+: labels->tick_labels
    plt.boxplot([d_pid, d_mpc], tick_labels=["PID","MPC"])
    plt.ylabel(metric)
    plt.title(title)
    plt.tight_layout()
    plt.savefig(outpng)
    plt.close()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--duration", type=int, default=900, help="Simülasyon süresi (s)")
    ap.add_argument("--horizon", type=int, default=12, help="MPC ufku N")
    ap.add_argument("--ambient", nargs="+", type=float, default=[20.0,25.0,30.0])
    ap.add_argument("--mismatch", nargs="+", type=str, default=["nominal","minus20","plus20"])
    ap.add_argument("--profiles", nargs="+", type=str, default=["step","ramp","multistep"])
    args = ap.parse_args()

    combos = list(product(args.profiles, args.ambient, args.mismatch))
    total = len(combos)
    print(f"▶ Running {total} scenarios | duration={args.duration}s, horizon N={args.horizon}")

    t0 = time.perf_counter()
    records = []

    for i, (prof, Ta, mm) in enumerate(combos, start=1):
        scn = Scenario(name=f"{prof}_Ta{int(Ta)}_{mm}", Ta=Ta, mismatch=mm, profile=prof)

        t_start = time.perf_counter()
        print(f"[{i:>2}/{total}] {prof:10s} | Ta={Ta:>4.1f}°C | mismatch={mm} -> PID ", end="", flush=True)
        m_pid, _ = run_scenario(scn, controller_type="PID", sim_seconds=args.duration)
        print("✓", flush=True)

        print(f"    ... MPC (N={args.horizon}) ", end="", flush=True)
        m_mpc, _ = run_scenario(
            scn, controller_type="MPC", sim_seconds=args.duration,
            mpc_cfg=dict(N=args.horizon, qy=1.0, qdu=0.08, umin=0.0, umax=1.0, du_max=0.06, Ta=Ta)
        )
        print(f"✓  ({time.perf_counter()-t_start:.1f}s)", flush=True)

        records.append({"Scenario": scn.name, "Controller": "PID", **m_pid})
        records.append({"Scenario": scn.name, "Controller": "MPC", **m_mpc})

    df = pd.DataFrame.from_records(records)
    (BASE_DIR / "results_summary.csv").write_text(df.to_csv(index=False), encoding="utf-8")

    # ---------- GÖMÜLÜ ANALİZ ----------
    # 1) wins tablosu
    rows = []
    for m in METRICS:
        w,t,l = wins_table(df, m)
        rows.append({"Metric": m, "MPC_wins": w, "Ties": t, "MPC_losses": l})
    wins_df = pd.DataFrame(rows)

    # 2) medyan±IQR (genel + profile kırılımı)
    overall = median_iqr(df, by_cols=[], metric_cols=METRICS)
    parts = df["Scenario"].str.extract(r"(?P<profile>\\w+)_Ta(?P<Ta>\\d+)_(?P<mismatch>\\w+)")
    dfx = pd.concat([df, parts], axis=1)
    dfx["Ta"] = dfx["Ta"].astype(int)
    by_profile = median_iqr(dfx, ["profile"], METRICS)

    # 3) kutu grafikleri (seçili 3 metrik)
    figs = []
    sel = [("IAE","IAE — düşük daha iyi"),
           ("Energy_sum_u2","Enerji (∑u²) — düşük daha iyi"),
           ("Violation_s","Kısıt ihlali (s) — düşük daha iyi")]
    for metric, title in sel:
        outpng = FIG_DIR / f"box_{metric}.png"
        boxplot_metric(df, metric, outpng, title)
        figs.append(outpng.name)

    # ---------- RAPOR ----------
    html = f"""<!DOCTYPE html>
<html lang="tr"><head><meta charset="utf-8"><title>2204-A — Dijital İkiz Tam Rapor</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 24px; }}
h1, h2, h3 {{ margin-top: 1.1em; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #ccc; padding: 6px; text-align: right; }}
th {{ background: #f7f7f7; }}
td:nth-child(1), td:nth-child(2) {{ text-align: left; }}
img {{ max-width: 100%; height: auto; border:1px solid #ddd; padding:6px; }}
</style></head>
<body>
<h1>2204-A — Dijital İkiz Tam Rapor</h1>
<p><strong>Toplam senaryo:</strong> {total} &nbsp; | &nbsp;
<strong>Simülasyon süresi:</strong> {args.duration}s &nbsp; | &nbsp;
<strong>MPC ufku:</strong> N={args.horizon}</p>

<h2>Özet Tablo (Tüm Senaryolar)</h2>
{dataframe_to_html_table(df)}

<h2>MPC vs PID — Kazanım Tablosu (düşük daha iyi)</h2>
{wins_df.to_html(index=False)}

<h2>Medyan±IQR (Genel)</h2>
{overall.to_html(index=False)}

<h2>Medyan±IQR (Profile göre)</h2>
{by_profile.to_html(index=False)}

<h2>Kutu Grafikleri</h2>
{"".join([f'<img src="figures/{n}">' for n in figs])}

<p>Oluşturulma süresi: {time.perf_counter()-t0:.1f} s</p>
</body></html>"""
    (BASE_DIR / "report.html").write_text(html, encoding="utf-8")

    print(f"✅ Done → outputs/results_summary.csv & outputs/report.html (+figures/*)")

if __name__ == "__main__":
    main()
