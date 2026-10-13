# WORK-2 — Jingle Factory / Watchdog teknik teslim

Durum: **KISMİ TEST EDİLDİ / ERİŞİM VE CANLI ENTEGRASYON BEKLİYOR**.
Bu rapor üretim sisteminin kalıcı olarak onarıldığı anlamına gelmez.
Takip: [Issue #27](https://github.com/MetteBuyuretti/oldies-reels-worker/issues/27),
[taslak PR #26](https://github.com/MetteBuyuretti/oldies-reels-worker/pull/26).

## A. Kök neden ve kanıt

| Bulgu | Doğrulama | Sonuç |
|---|---|---|
| PR26/main çakışması | PR26 `mergeable=false`; yerel merge tek çakışmayı `watchdog.py` içinde üretti | Jingle audit başlangıcı ile PR28 current-run dışlama değişikliği birlikte korunmalı |
| Jingle testleri CI dışında | Workflow yalnız `test_watchdog.py` çalıştırıyordu | Jingle regresyonları CI yeşilken kaçabiliyordu |
| NaN süre kabulü | Eski `abs(NaN-target)>tolerance` koşulu false; negatif testte kabul | Sonlu sayı kontrolü eklendi |
| Eksik dosya tarihi denetimi çökertiyor | `file["modified_at"]` KeyError üretiyor | Eksik tarih kontrollü redde dönüştü |
| Geçersiz SHA kabulü | Yalnız 64 karakter uzunluğu kontrol ediliyordu | Hexadecimal SHA-256 doğrulaması eklendi |
| Hatalı/eksik aşama zinciri | Araya ERROR eklenmesi finali engellemiyor; CAPCUT_READY izi o aşamaya ulaşmayabiliyordu | Hata içeren COMPLETE ve duruma ulaşmayan iz reddediliyor |
| Telemetri metninin rapora taşınması | Job/provider/status/task-run alanlarına yol/satır sonu konulan fixture rapora sızıyordu | Job biçimi sınırlandı; durum/provider izin listesi ve tarih normalizasyonu eklendi |

Yeni 11 test eski PR26 hizmet koduna karşı çalıştırıldı: **9 assertion failure,
1 error** (subtestler dahil). Düzeltme sonrası birleşik **61 test geçti**.
Ham kayıtlar: `regressions-before.txt`, `regressions-after.txt`.

Issue27 geçmiş yorumları tarayıcı kapanması, indirmede ENOENT, aynı parçayı
yeniden indirme ve eksik MASTER zincirini belgeliyor. Bunlar bu oturumda
orijinal Windows loglarından yeniden doğrulanmadı. AUTH_REQUIRED, profil/port,
GOOGLE_HTTP_503, yeniden başlatma ve 13 Ekim çıktısının mevcut kök nedeni
**doğrulanamadı**. Cihazın şu anda OFFLINE olması geçmiş arızanın nedeni değildir.

## B. Uygulanan düzeltmeler

- Mevcut PR26 dalına main `359b90712fec7abdfa60821781f950e8c62aa3d5`
  birleştirildi. PR28 merge `b2365d9edb3fe9d54b2f72899624fc2769acb4a5`
  korunuyor; main'e PR26 birleştirilmedi.
- `monitoring/watchdog.py`: ortak zaman damgası/Jingle audit ile
  `GITHUB_RUN_ID` dışlama birlikte çalışır.
- `.github/workflows/oldies-watchdog.yml`: bütün `monitoring/test_*.py`
  testleri keşfedilir; PR koşusunda canlı audit adımı çalışmaz.
- `monitoring/jingle_service.py`: yukarıdaki telemetri ve aşama doğrulamaları;
  açık STALE etiketi; Windows dosya raporunun GitHub tarafından doğrudan
  dosya incelemesi olmadığına dair doğru çıktı.
- `monitoring/test_jingle_robustness.py`: olumsuz veri, HTTPS/auth,
  yönlendirme reddi, yanıt boyutu, bozuk JSON, iki saat sınırı ve dedupe testleri.

Bu kod düzeltmeleri yalnız taslak test dalındadır. Canlıya geçici bir müdahale
yapılmadı. Üretici FINAL kilidi henüz uygulanmadı; observer reddi bunun yerine geçmez.

## C. Regresyon ve kabul matrisi

| İstenen senaryo | Bu oturumda kanıt |
|---|---|
| Normal üretim | Yalnız sentetik tam kanıt fixture; gerçek üretim yapılmadı |
| İnternet kesintisi | Mock TimeoutError, kimlikli telemetry hata ayrımı |
| Gemini erişim hatası | Hata durumu fixture; gerçek Gemini erişimi sınanmadı |
| Oturum kaybı | AUTH_REQUIRED fixture; gerçek Chrome oturumu sınanmadı |
| Eksik/bozuk müzik | Yerel probe mock testleri ve bozuk telemetri redleri |
| Eski jingle | Eski tarih ve duplicate source/master fixture redleri |
| Yanlış job ID | Aşama/dosya/QC iş kimliği redleri |
| DJ sesi yok | voice_mixed=false reddi; işitsel inceleme yok |
| Yanlış V3.1 seviyesi | -12/-4.8 dB QC fixture redleri; ses ölçümü yapılmadı |
| Hatalı/doğrulanmamış kapanış | Kapanış/dinleme kanıtı fixture redleri |
| WordPress heartbeat kesintisi | Mock timeout ve eksik server receipt ayrımı; canlı POST yok |
| PC kapalı/heartbeat eski | 7200 saniye sınırı ve 7201 saniye STALE fixture; gerçek receipt okunamadı |
| GitHub zamanlama gecikmesi | PR28 current-run/schedule-gap regresyonları korunup geçti |
| Tekrarlanan otomasyon | Aynı stale olayına iki audit/tek Issue offline testi; üretim tekrar kilidi sınanmadı |
| Yetkisiz FINAL/yayın geçişi | Observer QC redleri; üretici/yayın kapısının canlı testi **yok** |

61/61 Python unittest; workflow YAML ayrıştırma ve `git diff --check` başarılı.
Reels/ Facebook workflow dosyaları main ile aynı; saatler ve concurrency korunuyor.
Windows PowerShell/Node testleri, gerçek FFprobe/SHA ve işitsel QC yapılmadı.

## D. Gerçek üretim doğrulaması

Yeni Gemini isteği **0**, gerçek yeni MASTER **doğrulanmadı**, yayın **0**.
Onaylı V3.1 dosyası ve referans ses değiştirilmedi, yeniden onay istenmedi.
13 Ekim 62 saniyelik ham müzik/10 saniyelik çıktılar talimatın bildirimidir;
dosyalara erişim olmadığı için bu oturumun doğrulanmış üretim kanıtı değildir.
İki Windows uygulamasının canlı/test rolü kaynak ve görev komutları okununca belirlenecek.

## E. Watchdog entegrasyonu

WordPress araç keşfi başarılı; 47 sunulan yetenek içinde heartbeat okuma,
eklenti PHP kaynağı veya seçenek kaydı okuma yeteneği bulunmuyor.
Dolayısıyla gerçek alıcı kodu, sunucu kayıt yeri ve son alınma zamanı doğrulanmadı.
Ayrı okuma tokenı oluşturulmadı; gönderim anahtarı yeniden kullanılmadı.
GitHub'daki authenticated HTTPS istemcisi test edildi; canlı WordPress köprüsü
bağlanmadı. Gerçek uzak heartbeat denetimi **NOT MONITORED / entegrasyon bekliyor**.
GitHub Windows dosyalarını doğrudan incelemiyor.

Yeni durumlar `MASTER_QC_PENDING`, `MASTER_VERIFIED`, `PUBLICATION_APPROVED`
üreticiye eklenmedi. Eski sözleşme kontrollü korunuyor; bu durumların geçiş
kuralları gerçek üretici/alıcı incelendikten sonra sürümlü uyumlulukla tamamlanmalı.
V3.1 observer mevcut denge/kapanış kanıtını kontrol ediyor; 1.3/0.1/0.4/1.8/1.5
saniyelik miks parametrelerinin gerçek miks motorunda uygulanması doğrulanmadı.

## F. Geri dönüş, erişim ve sonraki adım

Git geçmişi önceki PR26 başını (`2ab9f6b`) ve alınan main'i koruyor.
Canlı dosya/görev değiştirilmediğinden canlı geri dönüş gerekmiyor.
Test dalı düzeltmeleri normal revert ile geri alınabilir; main'de revert yapılmamalı.
Gelecek Windows/WP kritik düzenlemelerinde önce gerçek dosya ve görev yedeği alınmalı.

En küçük sonraki adım: **Mete-DELL-2025 ve mevcut Desktop Commander bağlantısı
çevrimiçi olsun**. Sonra görev XML'i, durum/loglar, mevcut Node/Python/miks ve
heartbeat kodları, referans/QC ve arşiv okunmalı. WordPress alıcı PHP'sinin
mevcut yetkili yönetim erişimi veya özel kaynak kopyası da gerekli; sırlar
sohbete/GitHub'a taşınmamalı.

Bu kanıtlar gelince mevcut üreticiye job/hash/QC bağlı FINAL kilidi, güvenli
devam etme ve mevcut WordPress bileşenine sınırlı okuma köprüsü hazırlanabilir.
Canlı entegrasyon/kabul tamamlanmadan main/WordPress dağıtım onayı istenmemeli.
Onay sonrası en az üç ardışık doğal üretim gözlemi gerekir; şu an **0/3**.
Gelecek gözlem görevi kurulmadı; bağlantı olmadan izleniyor iddiası yok.

## Master Status (beş madde)

1. **GERÇEKLEŞEN:** PR26/main uzlaştırması, telemetri redleri ve tüm jingle testlerinin CI'a alınması; test dalında.
2. **TEST EDİLDİ:** 61/61 yerel test; YAML ve diff kontrolleri. Gerçek MASTER/E2E kanıtı yok.
3. **ONAY BEKLİYOR:** Main/WordPress canlı değişiklikleri henüz kabul koşullarını sağlamıyor; dağıtım yapılmadı.
4. **BEKLEYEN:** Windows/receiver erişimi, üretici FINAL kilidi, gerçek MASTER, kimlikli köprü ve üç doğal koşu.
5. **HATALI:** Mevcut günlük üretim arızalarının güncel kök nedeni yerel log erişimi olmadığı için doğrulanamadı; kalıcı onarım tamamlandı denemez.
