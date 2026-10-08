# OLDIES WATCHDOG v1 — denetim katmanı

Bu sürüm `oldies-reels-worker` deposundaki GitHub Actions iş akışlarını değiştirmeden gözler. Yayın ve otomatik yeniden deneme açısından **salt gözlem** modundadır. Üretim otomasyonlarını yeniden başlatmaz, yeni içerik yayımlamaz veya erişim anahtarlarını değiştirmez. Yalnızca açıkça izlenen üç günlük otomasyonda yeni bir arıza oluşursa GitHub Issue kaydı açabilir.

- Ana dala birleştirilirse, saat başına 37. dakikada zamanlanmış çalışma hedeflenir. GitHub zamanlanmış görevleri geciktirebilir veya atlayabilir.
- Aktif GitHub Actions iş akışlarının son çalışmasını tarar: başarısız, uzun süre takılı kalmış veya kalibre edilmiş sıklığından gecikmiş görevleri raporlar.
- Bulgular GitHub Actions Job Summary'de görünür.
- Son GitHub run başarısı, içeriğin WordPress, Instagram veya Facebook'ta gerçekten yayımlandığının kanıtı değildir.
- `expected_freshness_hours` üç doğrulanmış günlük akış için 36 saat olarak ayarlanmıştır. Diğer manuel/test akışları için gereksiz gecikme alarmı oluşturulmaz. Planlı işleri denetlerken manuel veya push çalışmaları gerçek zamanlanmış görev sonuçlarını maskelemez. Son 48 saatte hata yaşayıp toparlanan işler bilgi amaçlı raporlanır; yeni arıza bildirimi oluşturulmaz.
- `issue_alerts_enabled=true`: GitHub Issues üzerinden mükerrer önlemeli olay kaydı etkin. Yalnızca üç tanımlı günlük iş için başarısızlık, uzun takılma veya gecikmede issue oluşturulur; eski manuel DJ/test hataları ve sonradan düzelmiş günlük hatalar uyarı üretmez. GitHub bildirimlerinin kullanıcıya iletilmesi GitHub Watch/Notifications tercihlerine bağlıdır.
- Yayımlama işlerinde otomatik yeniden deneme **kapalı** kalır. Issue kaydı gerçek yayını doğrulamaz veya kendiliğinden onarım yapmaz.
- Birden fazla GitHub deposu, WordPress ve Meta içi gerçek teslim kontrolü sonraki aşamanın konusudur.

## Yerel test

`cd monitoring && python -m unittest -v test_watchdog.py`

## MASTER STATUS kaydı

`Kontrol tarihi | Akış | Son GitHub sonucu | Gerçek teslim doğrulaması | Hata | Aksiyon | Sonraki kontrol`

## Güvenlik

Mevcut workflow, secrets, yayın ve canlı sistemler değiştirilmez. Tekrar deneme öncesinde mükerrer yayın koruması ve kullanıcı yetkilendirmesi gerekir. Varsayılan GitHub GITHUB_TOKEN kullanılır; ek abonelik öngörülmez ama GitHub Actions kotaları uygulanabilir.
