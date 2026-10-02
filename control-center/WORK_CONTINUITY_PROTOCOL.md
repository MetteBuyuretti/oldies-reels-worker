# Work Continuity Protocol — Oldies Radyo

Amaç: ChatGPT Work, tarayıcı, ağ veya araç bağlantısı kesilse bile uzun işlerin baştan başlamasını engellemek.

## Temel ilke
**Sohbet hafıza değildir; GitHub kalıcı çalışma hafızasıdır.**

Her uzun iş üç parçadan oluşur:
1. Görev kaydı
2. Parça parça çıktı
3. Checkpoint sonrası güncellenen durum

## Standart iş akışı

### A. Başlarken
- `control-center/work-state.json` dosyasını oku.
- İlgili görevin mevcut durumunu bul.
- Daha önce oluşturulmuş çıktı dosyalarını kontrol et.
- Tamamlanan kısımları atla.
- `next_step` ile devam et.

### B. Çalışırken
Görevleri küçük teslimat paketlerine böl:
- Ülke serisi: her ülke ayrı paket.
- 100 soru/cevap: 001–020, 021–040, 041–060, 061–080, 081–100.
- Web / otomasyon kurulumu: araştırma, kod, test, yayın öncesi kontrol ayrı paketler.
- Jingle / medya: kaynak hazırlama, miks, kalite kontrol, final ayrı paketler.

Her paketin sonunda çıktı kalıcı dosyaya yazılır. Önerilen yapı:

```
work-output/<task-id>/
  part-001.md
  part-002.md
  ...
```

### C. Checkpoint
Her paket tamamlanınca `work-state.json` güncellenir:
- status
- last_checkpoint
- completed_units
- next_step
- note

Bir sonraki pakete ancak checkpoint sonrasında geçilir.

### D. Kesinti sonrası
1. Durum dosyasını oku.
2. İlgili çıktı klasörünü kontrol et.
3. Son tamamlanmış birimi belirle.
4. İlk eksik birimden devam et.
5. Önceki tamamlanmış işi yeniden üretme.

## Çakışma önleme
Aynı görevi iki ajan aynı anda yürütüyorsa:
- Biri `in_progress` durumundaysa ikinci ajan önce son checkpoint'i kontrol eder.
- Yeni ajan aynı parçayı tekrar üretmez.
- Gerekirse durum `needs_reconcile` yapılır ve mevcut çıktılar karşılaştırılır.

## Kullanıcıya kısa durum
Uzun iş sırasında kullanıcıya gerektiğinde yalnızca şu formatta bilgi ver:
- Tamamlanan:
- Şu an:
- Sıradaki:
- Engel:

## Başarı ölçütü
Bağlantı kopması halinde kayıp, en fazla son checkpoint'ten sonraki tamamlanmamış küçük paket kadar olmalıdır; tüm görev kaybolmamalıdır.
