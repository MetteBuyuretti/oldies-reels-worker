# AGENTS.md — Oldies Radyo Kesintiye Dayanıklı Çalışma Standardı

Bu repository üzerinde çalışan ChatGPT Work / Codex / başka bir ajan, uzun bir göreve başlamadan önce aşağıdaki kuralları uygular.

## Zorunlu başlangıç
1. Önce `control-center/work-state.json` dosyasını oku.
2. İlgili görev kaydı varsa tamamlanmış adımları tekrar yapma.
3. `next_step` alanından veya ilk tamamlanmamış adımdan devam et.
4. Durum çelişkiliyse önce mevcut çıktı dosyalarını kontrol et; yalnızca eksik kısmı üret.

## Parçalama
- Tek parça uzun çalışma yapma.
- Görevi yaklaşık 10–20 dakikalık veya doğal teslimat parçalarına böl.
- Her parça bağımsız kaydedilebilir olmalı.
- 100 maddelik işlerde varsayılan paket: 20 madde.
- Çok ülkeli işlerde varsayılan paket: ülke başına 1 çıktı.

## Checkpoint
Her anlamlı parça tamamlandığında:
1. Çıktıyı kalıcı bir dosyaya yaz.
2. `control-center/work-state.json` içindeki ilgili görevi güncelle.
3. `last_checkpoint`, `completed_units`, `next_step` ve kısa `note` alanlarını güncelle.
4. Ancak bundan sonra sonraki parçaya geç.

## Kesinti / yeniden bağlanma
- Oturum, ağ veya araç bağlantısı kesildiyse görevi sıfırdan başlatma.
- Yeniden açıldığında önce durum dosyasını ve mevcut çıktıları oku.
- Son güvenli checkpoint'ten sonraki ilk eksik parçadan devam et.
- Tamamlanmış dosyaları gereksiz yere yeniden yazma.

## Durum değerleri
Kullanılacak ana durumlar:
- `queued`
- `in_progress`
- `checkpointed`
- `needs_reconcile`
- `blocked`
- `done`

## Güvenlik
- Token, parola, API anahtarı veya kişisel gizli veri bu durum dosyalarına yazılmaz.
- Canlı yayınlama / harcama / geri döndürülemez işlem, ayrıca yetki verilmedikçe yapılmaz.
- Var olan çalışan otomasyon bozulmamalıdır.

Detaylı açıklama: `control-center/WORK_CONTINUITY_PROTOCOL.md`
