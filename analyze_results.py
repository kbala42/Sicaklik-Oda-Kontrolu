# analyze_results.py
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

USAGE = "Usage: python analyze_results.py outputs/results_summary.csv"

def boxplot_metric(df, metric, outdir: Path):
    plt.figure()
    data_pid = df[df["Controller"]=="PID"][metric].values
    data_mpc = df[df["Controller"]=="MPC"][metric].values
    plt.boxplot([data_pid, data_mpc], tick_labels=["PID","MPC"])
    plt.ylabel(metric)
    plt.title(f"{metric} — Lower is better")
    plt.tight_layout()
    p = outdir / f"box_{metric}.png"
    plt.savefig(p); plt.close()
    return p

def wins_table(df, metric):
    # daha düşük daha iyi kabulü
    pivot = df.pivot_table(index="Scenario", columns="Controller", values=metric, aggfunc="first")
    wins = (pivot["MPC"] < pivot["PID"]).sum()
    ties = (np.isclose(pivot["MPC"], pivot["PID"])).sum()
    losses = (pivot["MPC"] > pivot["PID"]).sum()
    return wins, ties, losses

def median_iqr(df, by_cols, metric_cols):
    g = df.groupby(by_cols + ["Controller"])[metric_cols]
    med = g.median().rename(columns=lambda c: f"median_{c}")
    q1  = g.quantile(0.25).rename(columns=lambda c: f"q1_{c}")
    q3  = g.quantile(0.75).rename(columns=lambda c: f"q3_{c}")
    out = pd.concat([med,q1,q3], axis=1).reset_index()
    return out

def main():
    if len(sys.argv) != 2:
        print(USAGE); sys.exit(1)
    csv_path = Path(sys.argv[1])
    outdir = csv_path.parent / "analysis"
    (outdir / "figures").mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(csv_path)
    metrics = ["IAE","ISE","Overshoot_%","Settling_s","Energy_sum_u2","Violation_s"]

    # 1) Genel medyan±IQR (tüm senaryolar)
    summary_all = median_iqr(df, by_cols=[], metric_cols=metrics)
    summary_all.to_csv(outdir/"summary_overall.csv", index=False)

    # 2) Profil/ambient/mismatch kırılımları
    # Scenario sütunundan prof/Ta/mm bilgilerini ayıralım:
    parts = df["Scenario"].str.extract(r"(?P<profile>\w+)_Ta(?P<Ta>\d+)\_(?P<mismatch>\w+)")
    dfx = pd.concat([df, parts], axis=1)
    dfx["Ta"] = dfx["Ta"].astype(int)

    summary_by_profile = median_iqr(dfx, ["profile"], metrics)
    summary_by_profile.to_csv(outdir/"summary_by_profile.csv", index=False)

    summary_by_Ta = median_iqr(dfx, ["Ta"], metrics)
    summary_by_Ta.to_csv(outdir/"summary_by_Ta.csv", index=False)

    summary_by_mm = median_iqr(dfx, ["mismatch"], metrics)
    summary_by_mm.to_csv(outdir/"summary_by_mismatch.csv", index=False)

    # 3) Kutu grafikleri (genel)
    figdir = outdir / "figures"
    made = []
    for m in metrics:
        made.append(boxplot_metric(df, m, figdir))

    # 4) Kazanma-tablosu (MPC vs PID) – her metrik için
    rows = []
    for m in metrics:
        w,t,l = wins_table(df, m)
        rows.append({"Metric": m, "MPC_wins": int(w), "Ties": int(t), "MPC_losses": int(l)})
    wins_df = pd.DataFrame(rows)
    wins_df.to_csv(outdir/"wins_table.csv", index=False)

    # 5) Hızlı HTML özet
    html = f"""<!DOCTYPE html>
<html lang="tr"><head><meta charset="utf-8"><title>Analysis Summary</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 24px; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #ccc; padding: 6px; text-align: right; }}
th {{ background: #f7f7f7; }} td:first-child {{ text-align:left; }}
img {{ max-width:100%; height:auto; border:1px solid #ddd; padding:6px; }}
</style></head><body>
<h1>2204-A — Analiz Özeti</h1>
<h2>Genel medyan±IQR</h2>
{summary_all.to_html(index=False)}
<h2>MPC Kazanım Tablosu</h2>
{wins_df.to_html(index=False)}
<h2>Kutu Grafikleri</h2>
{''.join([f'<h3>{Path(p).stem[4:]}</h3><img src="figures/{Path(p).name}">' for p in made])}
</body></html>"""
    (outdir/"analysis.html").write_text(html, encoding="utf-8")
    print(f"✔ Saved: {outdir}")

if __name__ == "__main__":
    main()
