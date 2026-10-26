# Onaylı dar kaynak teslimi

**26.10.2026 | 16:54 TSİ (UTC+3)**

Kurucu, bu yerel oturumda bütçe/Verify fonksiyonları ve Jingle doğrulayıcı/test kaynaklarının `MetteBuyuretti/oldies-reels-worker` deposuna, #32 incelemesi için aktarımına doğrudan **Onaylıyorum** yanıtını verdi. Önceki otomatik inceleme engeli sonrasında istenen açık onay alınmıştır.

Bu teslim yalnız aşağıdaki hazır inceleme kaynaklarını ekler. Ham medya, kimlik bilgisi, özel makbuz, tam ledger, geniş Windows envanteri veya merkezi durum dosyası içermez. Üretim kapısı açılmaz; canlı sistemde bu tur ek kod/ayar/üretim değişikliği yoktur.

| Kaynak | Kapsam |
|---|---|
| budget-excerpt.mjs | Kurulu publisher'daki ilgili bütçe, eligibility, lock, uzlaştırma ve scanner fonksiyonlarının dar kesiti; tarayıcı başlatmaz. |
| verify-flow.txt | Kurulu main içindeki Verify/enqueue ayrımı ve bütçe çağrısı; metin olarak inceleme kesiti. |
| budget.test.mjs / caller.test.mjs | Gerçek hedef gün, rezervasyon günü ve kapalı yayın sınırı testleri. |
| race.test.mjs / scanner.test.mjs | İki sentetik girişin süreç yarışı, dinamik render, sponsor dışlama ve zaman semantiği testleri. |
| manual_music_preflight.py | Üretici/importer/canonical state çağırmayan MANUAL kaynak hazırlığı. |
| test_manual_music_preflight.py | Sentetik girdilerle yedi doğrulayıcı testi. |

Bu klasörde yeniden çalıştırma:

```text
node --test budget.test.mjs caller.test.mjs race.test.mjs scanner.test.mjs
python -B test_manual_music_preflight.py
```

Önceden kaydedilen son sonuçlar: `node-tests.tap` **25/25**, `jingle-tests.txt` **7/7**. Kaynaklar bu onay turunda değiştirilmedi; gereksiz test/üretim tekrarı yapılmadı. Windows'ta Python test geçici dosyaları izinli çalışma alanına yönlendirilmişti.

`report.md` ve #32'deki önceki “kaynak aktarım onayı bekleniyor” notu tarihsel durumdur; bu teslimle kaynak aktarım engeli kapanır. Bütün gerçek yayıncı kapsamı, gerçek queue-preview hedef kanıtı, Jingle'ın kimlikli özgün makbuzu, sonraki doğal çalışma ve bağımsız operasyonel kabul açık kalır. Kaynak paylaşım onayı bu sınırları genişletmez.
