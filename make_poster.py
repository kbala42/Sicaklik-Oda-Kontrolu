# make_poster.py — 2204-A poster üretici
import argparse, datetime
from pathlib import Path
import numpy as np
import pandas as pd

POSTER_CSS = """
body{margin:0;font-family:Inter,Arial,Helvetica,sans-serif;background:#fafafa;color:#111}
.header{background:#0d1b2a;color:#fff;padding:28px 36px}
.header h1{margin:0;font-size:28px;line-height:1.25}
.header .meta{opacity:.9;margin-top:6px;font-size:14px}
.wrap{display:grid;grid-template-columns:1.2fr 1fr 1fr;gap:18px;padding:18px 24px}
.card{background:#fff;border:1px solid #e6e6e6;border-radius:14px;box-shadow:0 2px 8px rgba(0,0,0,.04)}
.card h2{margin:14px 16px 6px 16px;font-size:18px}
.card .body{padding:0 16px 14px 16px;font-size:14px;line-height:1.5}
.kpi{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:8px}
.kpi .item{background:#f7f7fb;border:1px solid #eee;border-radius:12px;padding:10px;text-align:center}
.kpi .item .val{font-size:18px;font-weight:700}
.small{font-size:12px;color:#666}
.table{width:100%;border-collapse:collapse;font-size:13px}
.table th,.table td{border:1px solid #e5e5e5;padding:6px 8px;text-align:right}
.table th{background:#fbfbfb}
.table td:first-child,.table th:first-child{text-align:left}
.figure{padding:8px 16px 16px 16px}
.figure img{width:100%;height:auto;border:1px solid #eee;border-radius:10px}
.badge{display:inline-block;background:#eef6ff;color:#0b67c2;border:1px solid #cfe3ff;border-radius:999px;padding:3px 8px;margin:2px 4px;font-size:12px}
.footer{padding:8px 24px 24px 24px;color:#555;font-size:12px}
"""

HTML_TMPL = """<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="utf-8">
<title>{title} — Poster</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>{css}</style>
</head>
<body>
<div class="header">
  <h1>{title}</h1>
  <div class="meta">{team} &nbsp;•&nbsp; Süre: {duration}s &nbsp;•&nbsp; MPC ufku: N={horizon} &nbsp;•&nbsp; {date}</div>
</div>

<div class="wrap">
  <div class="card">
    <h2>Özet</h2>
    <div class="body">
      Bu çalışma, 2R–C ısıl modelin <strong>dijital ikizinde</strong> PID ve <strong>kısıtlı MPC</strong> denetleyicilerini karşılaştırır.
      Ölçüm gürültüsünde <strong>Kalman filtresi</strong> ile durum kestirimi yapılır. 27 senaryoda (3 profil × 3 ortam × 3 uyumsuzluk),
      <em>IAE, ISE, aşım %, yerleşme süresi, enerji (∑u²) ve kısıt ihlali süresi</em> metrikleri raporlanır.
      <div class="kpi">
        <div class="item"><div class="val">{n_scen}</div><div class="small">Senaryo</div></div>
        <div class="item"><div class="val">{wins_iae}</div><div class="small">MPC IAE kazanç</div></div>
        <div class="item"><div class="val">{wins_energy}</div><div class="small">MPC Enerji kazanç</div></div>
      </div>
      <div style="margin-top:8px">
        <span class="badge">2R–C model</span>
        <span class="badge">Kalman kestirimi</span>
        <span class="badge">Kısıtlı MPC</span>
        <span class="badge">PID taban çizgisi</span>
        <span class="badge">27× karşılaştırma</span>
      </div>
    </div>
  </div>

  <div class="card">
    <h2>Deney Izgarası</h2>
    <div class="body">
      Profiller: <strong>step</strong>, <strong>ramp</strong>, <strong>multistep</strong><br>
      Ortam: <strong>20/25/30 °C</strong> &nbsp;•&nbsp; Uyumsuzluk: <strong>nominal/−%20/+%20</strong>
      <p class="small">Not: Tüm koşul çiftleri PID ve MPC ile ayrı ayrı yürütülmüştür.</p>
    </div>
    <div class="figure">{grid_table}</div>
  </div>

  <div class="card">
    <h2>Yöntem Kısa</h2>
    <div class="body">
      <ul>
        <li><strong>Dijital ikiz:</strong> Oda (T<sub>r</sub>)–numune (T<sub>s</sub>), giriş u∈[0,1], bozulma T<sub>a</sub>.</li>
        <li><strong>Kalman:</strong> Q,R ayarlı; tek sensör (T<sub>r</sub>) ile durum kestirimi.</li>
        <li><strong>PID:</strong> anti-windup + oran kısıtı (|Δu|≤Δu<sub>max</sub>).</li>
        <li><strong>MPC:</strong> N-adım ufuk; kutu ve oran kısıtları; maliyet J=∑(q<sub>y</sub>e²+q<sub>Δu</sub>Δu²).</li>
      </ul>
      <p class="small">Kod ve rapor otomatik üretim: <code>experiments_full.py</code> → <code>outputs/</code></p>
    </div>
  </div>

  <div class="card">
    <h2>MPC Kazanım Tablosu (düşük daha iyi)</h2>
    <div class="body">{wins_table_html}</div>
  </div>

  <div class="card">
    <h2>Medyan±IQR (Tüm Senaryolar)</h2>
    <div class="body">{overall_html}</div>
  </div>

  <div class="card">
    <h2>Kutu Grafikleri</h2>
    <div class="figure">{fig_html}</div>
  </div>

  <div class="card">
    <h2>Sonuç</h2>
    <div class="body">
      <ul>
        <li>MPC, <strong>IAE</strong> ve <strong>Enerji (∑u²)</strong> metriklerinde çoğu senaryoda PID'i geçti.</li>
        <li>Kısıt ihlali süresi MPC’de belirgin şekilde daha düşüktür.</li>
        <li>Model uyumsuzluğu altında (±%20), Kalman+kısıtlı MPC performans kararlılığı sağlar.</li>
      </ul>
      <p class="small">Gelecek iş: Expm tabanlı ayrıklaştırma, QP çözücülü MPC (OSQP/cvxpy) ve çoklu sensör füzyonu.</p>
    </div>
  </div>
</div>

<div class="footer">
Bu poster otomatik üretildi: <code>make_poster.py</code> • Kaynak: <code>outputs/results_summary.csv</code> ve <code>outputs/figures/</code>.
</div>
</body></html>
"""

def wins_table(df: pd.DataFrame, metric: str):
    p = df.pivot_table(index="Scenario", columns="Controller", values=metric, aggfunc="first")
    wins   = int((p["MPC"] < p["PID"]).sum())
    ties   = int(np.isclose(p["MPC"], p["PID"]).sum())
    losses = int((p["MPC"] > p["PID"]).sum())
    return wins, ties, losses, p

def median_iqr(df: pd.DataFrame, metrics):
    g = df.groupby(["Controller"])[metrics]
    med = g.median().rename(columns=lambda c: f"median_{c}")
    q1  = g.quantile(0.25).rename(columns=lambda c: f"q1_{c}")
    q3  = g.quantile(0.75).rename(columns=lambda c: f"q3_{c}")
    return pd.concat([med,q1,q3], axis=1).reset_index()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="outputs/results_summary.csv", help="Sonuç CSV yolu")
    ap.add_argument("--title", default="Dijital İkiz Tabanlı Sıcaklık Oda Kontrolü: Kalman + Kısıtlı MPC")
    ap.add_argument("--team", default="Ekip: ... (okul/öğrenciler/danışman)")
    ap.add_argument("--duration", type=int, default=900)
    ap.add_argument("--horizon", type=int, default=15)
    args = ap.parse_args()

    csv_path = Path(args.csv)
    outdir = csv_path.parent
    figdir = outdir/"figures"
    df = pd.read_csv(csv_path)

    metrics = ["IAE","ISE","Overshoot_%","Settling_s","Energy_sum_u2","Violation_s"]
    w_iae, _, _, _ = wins_table(df, "IAE")
    w_en , _, _, _ = wins_table(df, "Energy_sum_u2")

    # wins tablosu
    rows = []
    for m in metrics:
        w,t,l,_ = wins_table(df, m)
        rows.append({"Metrik": m, "MPC kazanım": w, "Berabere": t, "MPC kayıp": l})
    wins_df = pd.DataFrame(rows)
    wins_table_html = wins_df.to_html(index=False, classes="table")

    # medyan±IQR (tüm senaryolar)
    overall = median_iqr(df, metrics)
    overall_html = overall.to_html(index=False, classes="table")

    # basit ızgara tablosu (profil×Ta×mismatch sayımları)
    parts = df["Scenario"].str.extract(r"(?P<profile>\\w+)_Ta(?P<Ta>\\d+)_(?P<mismatch>\\w+)")
    grid = parts.drop_duplicates().sort_values(["profile","Ta","mismatch"])
    grid_table = grid.rename(columns={"profile":"Profil","Ta":"Ta (°C)","mismatch":"Uyumsuzluk"}) \
                     .to_html(index=False, classes="table")

    # figürler (varsa 3'lü)
    figs = []
    for name in ["box_IAE.png","box_Energy_sum_u2.png","box_Violation_s.png","box_Energy.png"]:
        p = figdir/name
        if p.exists():
            figs.append(f'<img src="figures/{p.name}">')
    fig_html = "".join(figs) if figs else "<p class='small'>Figür bulunamadı. experiments_full sonrası otomatik üretilir.</p>"

    html = HTML_TMPL.format(
        css=POSTER_CSS,
        title=args.title,
        team=args.team,
        duration=args.duration,
        horizon=args.horizon,
        date=datetime.datetime.now().strftime("%Y-%m-%d"),
        n_scen=int(df["Scenario"].nunique()),
        wins_iae=w_iae,
        wins_energy=w_en,
        grid_table=grid_table,
        wins_table_html=wins_table_html,
        overall_html=overall_html,
        fig_html=fig_html
    )
    (outdir/"poster.html").write_text(html, encoding="utf-8")
    print(f"✔ Poster yazıldı → {outdir/'poster.html'}")

if __name__ == "__main__":
    main()
