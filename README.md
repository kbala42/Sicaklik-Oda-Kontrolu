# Dijital İkiz Tabanlı Sıcaklık Oda Kontrolü (Kalman + Kısıtlı MPC)

Bu depo, 2R–C ısıl sistemin **dijital ikizinde** PID ve **kısıtlı MPC-lite (PGD)** denetleyicilerini
27 senaryo (3 profil × 3 ortam T × 3 uyumsuzluk) üzerinde karşılaştırmak için hazırlanmıştır.

## Hızlı Başlangıç (GitHub Codespaces)
1. **Code → Create codespace on main** deyin.
2. Terminalde:
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Hızlı deney (3 profil × 2 denetleyici, 5 dk sim):
   ```bash
   python experiments_fast.py
   ```
4. Çıktılar `outputs/` altında oluşur. `report_fast_slice.html` dosyasını editörde açabilirsiniz.

## Tam Izgara (27 senaryo)
```bash
python experiments_full.py --duration 900 --horizon 15   --ambient 20 25 30 --mismatch nominal minus20 plus20 --profiles step ramp multistep
```
Rapor ve grafikler `outputs/` altında üretilecektir.
