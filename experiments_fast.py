from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from src.runner import Scenario, run_scenario

BASE_DIR = Path(__file__).parent / "outputs"
FIG_DIR = BASE_DIR / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

def save_plot_time(tr, filepath: Path, title: str):
    import matplotlib.pyplot as plt
    plt.figure()
    plt.plot(tr["y"], label="y")
    plt.plot(tr["r"], linestyle="--", label="r")
    plt.xlabel("Zaman (s)")
    plt.ylabel("Sıcaklık (°C)")
    plt.title(title)
    plt.legend()
    plt.tight_layout()
    plt.savefig(filepath)
    plt.close()

def save_boxplot(df, metric, filepath: Path, title: str):
    import matplotlib.pyplot as plt
    plt.figure()
    data_pid = df[df["Controller"]=="PID"][metric].values
    data_mpc = df[df["Controller"]=="MPC"][metric].values
    plt.boxplot([data_pid, data_mpc], tick_tick_labels=["PID","MPC"])
    plt.ylabel(metric)
    plt.title(title)
    plt.tight_layout()
    plt.savefig(filepath)
    plt.close()

def dataframe_to_html_table(dframe):
    d = dframe.copy()
    for col in ["IAE","ISE","Overshoot_%","Settling_s","Energy_sum_u2","Violation_s"]:
        if col in d.columns:
            d[col] = d[col].astype(float).round(3)
    return d.to_html(index=False)

def main():
    scenarios = [Scenario(name=f"{p}_Ta25_nominal", Ta=25.0, mismatch="nominal", profile=p) for p in ["step","ramp","multistep"]]
    records = []
    example_figs = []

    for scn in scenarios:
        m_pid, tr_pid = run_scenario(scn, controller_type="PID", sim_seconds=300)
        records.append({"Scenario": scn.name, "Controller": "PID", **m_pid})
        m_mpc, tr_mpc = run_scenario(scn, controller_type="MPC", sim_seconds=300)
        records.append({"Scenario": scn.name, "Controller": "MPC", **m_mpc})

        f1 = FIG_DIR / f"{scn.profile}_PID.png"
        f2 = FIG_DIR / f"{scn.profile}_MPC.png"
        save_plot_time(tr_pid, f1, f"{scn.profile.upper()} — PID")
        save_plot_time(tr_mpc, f2, f"{scn.profile.upper()} — MPC")
        example_figs += [f1, f2]

    import pandas as pd
    df = pd.DataFrame.from_records(records)
    df.to_csv(BASE_DIR / "results_fast_slice.csv", index=False)

    save_boxplot(df, "IAE", FIG_DIR / "box_IAE.png", "IAE — düşük daha iyi")
    save_boxplot(df, "Energy_sum_u2", FIG_DIR / "box_Energy.png", "Enerji (∑u²) — düşük daha iyi")
    save_boxplot(df, "Violation_s", FIG_DIR / "box_Violation.png", "Kısıt ihlali süresi — düşük daha iyi")

    html = f"""<!DOCTYPE html>
<html lang="tr"><head><meta charset="utf-8"><title>Hızlı Rapor</title></head>
<body>
<h1>Dijital İkiz — Hızlı Çalışan İlk Rapor</h1>
<h2>Toplu Metrikler</h2>
{dataframe_to_html_table(df)}
<h2>Örnek Zaman Yanıtları</h2>
{''.join([f'<img src="figures/{p.name}">' for p in example_figs])}
<h2>Kutu Grafikleri</h2>
<img src="figures/box_IAE.png">
<img src="figures/box_Energy.png">
<img src="figures/box_Violation.png">
</body></html>"""
    (BASE_DIR/"report_fast_slice.html").write_text(html, encoding="utf-8")

if __name__ == "__main__":
    main()
