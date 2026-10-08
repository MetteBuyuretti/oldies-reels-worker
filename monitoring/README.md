# OLDIES WATCHDOG v1 — denetim katmanı

Bu sürüm `oldies-reels-worker` deposundaki GitHub Actions iş akışlarını değiştirmeden gözler. Şimdilik **salt raporlama** modunda. Üretim otomasyonlarını yeniden başlatmaz, yeni içerik yayımlamaz, erişim anahtarlarını değiştirmez veya issue açmaz.

- Ana dala birleştirilirse, saat başına 37. dakikada zamanlanmış çalışma hedeflenir. GitHub zamanlanmış görevleri geciktirebilir veya atlayabilir.
- Aktif GitHub Actions iş akışlarının son çalışmasını tarar: başarısız, uzun süre takılı kalmış veya kalibre edilmiş sıklığından gecikmiş görevleri raporlar.
- Bulgular GitHub Actions Job Summary'de görünür.
- Son GitHub run başarısı, içeriğin WordPress, Instagram veya Facebook'ta gerçekten yayımlandığının kanıtı değildir.
- `expected_freshness_hours` alanı bilerek boştur. Önce gerçek cron/sıklık envanteri yapılmalıdır; manuel işleri yanlış alarm olarak işaretlememeliyiz.
- İstenirse sonraki güvenli sürümde `issue_alerts_enabled` kontrollü olarak `true` yapılır ve workflow izni `issues: write` seviyesine çıkarılır. Yayımlama işlerinde otomatik yeniden deneme **kapalı** kalır.
- Birden fazla GitHub deposu, WordPress ve Meta içi gerçek teslim kontrolü sonraki aşamanın konusudur.

## Yerel test

`cd monitoring && python -m unittest -v test_watchdog.py`

## MASTER STATUS kaydı

`Kontrol tarihi | Akış | Son GitHub sonucu | Gerçek teslim doğrulaması | Hata | Aksiyon | Sonraki kontrol`

## Güvenlik

Mevcut workflow, secrets, yayın ve canlı sistemler değiştirilmez. Tekrar deneme öncesinde mükerrer yayın koruması ve kullanıcı yetkilendirmesi gerekir. Varsayılan GitHub GITHUB_TOKEN kullanılır; ek abonelik öngörülmez ama GitHub Actions kotaları uygulanabilir.
