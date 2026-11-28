# Web sitesi Paket 2 — etkin kaynak kurtarma ve Gemini kod teslimi
**28.11.2026 | 05:08 TSİ — WORK MASTER/root mevcut sohbet.**
Durum: HAZIRLANIYOR; kaynak okuma ve dış operatör teslimi tamam, canlı onarım yok.

## GERÇEKLEŞEN
1. Kurucunun devam talimatıyla yalnız web haber zinciri incelendi. Chrome WordPress yetkili mevcut oturumu çalıştı.
2. Etkin eklentinin gerçek dizini doğrulandı: oldies-instagram-reconnect-175/oldies-radyo-social-automation.php, v1.7.5. Aynı isimdeki diğer kurulu9varyant etkin değil; onların kaynakları kullanılmadı.
3. Etkin dört dosya salt-okunur kod alanından alındı ve baseline altına kaydedildi. Eklenti düzenleyicisinde kod doldurulmadı/kaydedilmedi; etkinlik değişmedi.
4. Gemini görevi gerçekten gönderildi, **ALINDI WEB-GEM-CODE-20261128-02** yanıtı ve aday diff teslimi görüldü. Oturum: https://gemini.google.com/app/9c935cf6a2b266c0 .
5. MASTER aynı öneriyi yalnız haber catch bloğuna uygulayan candidate hazırladı. Runtime'a kurulmadı. Kaynak karşılaştırması yalnız7eklenen/1silinen satır gösteriyor; kilit finally'de korunuyor. İzole4senaryolu PHP harness eklendi, **çalıştırılmadı**: bu executor'da php binary bulunamadı. TeknikPASS verilmedi.

## Haber kesintisinde artık bilinenler
- Orijinal haber ekranı: monitoring ON; auto_publish OFF/taslak.7/12kaynak açık;173toplam haber;0VERIFIED;1NEEDS_REVIEW;1TR/EN published. Bu sayılar pluginin kendi kuyruğu, sitenin tüm yazıları değil.
- Son kaynak taraması panelde **22.09.2026 18:10:55**; en yeni görünen kayıt#173de22Eylül. Kasım yayınlarını bu eski plugin kuyruğunun ürettiği varsayılmayacak.
- Guard ekranı yalnız yayımlanmışTR→ENeşleme/çeviri amaçlı. Lastscan22Sep13:21:08, lasterror22Sep13:21:26 TR4245 'OpenAI API is not configured in Social & News Automation.' Bu tarihsel hata güncel credential durumu/kesinti nedeni kanıtı değildir. Boş password input kayıtlı secret yok demek değildir.
- Yeni AnaKumanda News ekranı 'ACTION BACKEND NOT VERIFIED — Process/Reject/Edit kapalı' gösteriyor; bu wrapper yerine orijinal ekran okundu. Tek kuyruğun manşeti doğruluk/yayın onayı sayılmadı; işlenmedi.
- Etkin Scheduler::handleNewsSourceCheckExecution mevcutThrowable'ı sessizce yutuyor. Bu doğrudan kaynakla kanıtlanmış gözlemlenebilirlik kusurudur, Eylül'denberi taramanın durmasının kesin kök nedeni değildir.
- Plugin::init sürüm farkında scheduleDefaultEvents çağırıyor; scheduler->init içindeki cron_schedules filtresi bundan sonra kayıtlı. oldies_15_minutes recurrence aktivasyon/migration sırasına bağlı olarak henüz kayıtlı olmayabilir. **Hipotez:** event eksik/invalid_schedule. Gerçek eventlist okunmadan 'neden budur' denemez. Routineinit eksiknews eventini herdefasında onarmıyor.
- NewsCoordinator yalnız yeni ingested_ids işler; bütün173pendingkayıdı otomatik yeniden işleme/tekrarüretim önerilmedi.

## Aday değişiklik
candidate/src/Cron/Scheduler.php: hata sınıfı + basename + satır kaydı. Mesaj,trace,URL,anahtar veya token kaydetmez. Gemini önerisidir; MASTER kaynak farkını kontrol etti. Bağımsız WATCHDOG kabulü veya çalışan onarım değildir.
Korunanlar: monitoring/auto_publish ayarları, diğer cronlar, sosyal/Etsy, provider çağrıları, retry politikası ve finally lock cleanup.
Rollback: uygulamaya yetki verildiğinde aynıbaselinehash yeniden doğrulanır; yalnıztekdosya orijinal byte yedeğiyle geri alınır. Bu candidate'ı main'e almak WordPress'e kurmaz; otomatik deploy bağlantısı ayrıca doğrulanmadan kurulmaz.

## Test ve sonraki devir
Work2 görevID WEB-W2-NEWS-DIAG-20261128-01: artık eksik kaynak bahanesi yok; bu4baseline ve aday/harness paketi hazır. Gerçek Work2alımı bu turda yok.
İlk iş: PHP8.1+ ile test-news-diagnostic.php ve php-l çalıştır; sonra mevcutWP-Croneventlistesinde **oldies_news_check_sources_cron** ve recurrence **oldies_15_minutes** varlığını SALT-OKUNUR raporla. Event çalıştırma/oluşturma,cron-reset,publish veya canlı dosyayazma yetkisi yok.
Gemini teslimi code review önerisidir, php test veya bağımsızWatchdog yerine geçmez. Gerekli canlı yetki MASTER'da kalır.

## BEKLEYEN
Gerçek news cron eventlist, recurrence kaydı, provider konfigürasyonunun sır göstermeyen sağlık sonucu; PHPfixture yürütmesi; bağımsız review; canlıya alma.429neden/Google4xxeşleştirme Paket1'deki ayrı iş.
Kontrolzamanı: sonraki darpaketbaşlangıcı. Arkaplançalışma veya yeniotomasyon kurulmadı.

## Kaynak SHA256
baseline oldies-radyo-social-automation.php c20e47a808bcb2c87838e56089949dad1beead1c16aa70a4ec10d32f484d1498
baseline src/Cron/Scheduler.php bff75a15cc4953801cdcfb1220769b0f08d14411ff17b9d0557bf3654c1e2b0e
baseline src/Plugin.php 43786f2eb6e6ec24b78ddce153b1d1f18564e9a61a53fea5035d2ffe35fb8ade
baseline src/News/NewsCoordinator.php d8dfcb3cada7e3750da89ffadca65db0f7bc932587841d635f1be9aa8f8f70b6
candidate src/Cron/Scheduler.php db7ef8183ae73dfd70754c53f370eb5ffb0b869f60016ccbc810034653113a4f
