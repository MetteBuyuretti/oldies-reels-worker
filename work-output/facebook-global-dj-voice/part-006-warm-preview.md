# FACEBOOK GLOBAL — ENGLISH DJ VOICE READY

**Sıcak kayıt şablonu v2.0 ve yayınsız test Reel’i hazır.** Yalnızca test dalı güncellendi. Main ve günlük canlı yayın henüz bu sürüme geçirilmedi. Facebook publish, WordPress teslimatı veya GitHub Release video yayını yapılmadı.

| Kontrol | Teknik sonuç |
|---|---|
| TTS enabled | true; mevcut güvenli Gemini / Charon hesabı ve workload identity |
| voice-over generated | İngilizce; ana hikâye 8.472s, ayrı radyo tanıtımı 6.000s; birleşik kayıt 15.55s |
| audio stream detected | AAC, 48000 Hz, stereo, 795 ses paketi |
| silent publish blocked | Render sonrasında ve teslimattan önce zorunlu; sessiz fallback yok |
| diğer otomasyonlar untouched | TR Instagram, Etsy, Zero Cost Reels ve diğer workflow’lar değiştirilmedi |
| Video | 1080 × 1920, 9:16, 30 fps, 17s |
| FFmpeg çıktısı | **audio:336kB**; audio:0kB yok |
| Anons temposu | Tahmini 127.5 kelime/dakika; hızlandırma uygulanmadı |
| Tanıtım arası | **1,1 saniye** dijital sessizlik; son MP4’te aranın merkezi -91.0 dB |
| Ses düzeyi | Ortalama -20.7 dB; tepe -2.2 dB |
| Otomatik müzik | Eklenmedi; kullanıcı Meta müzik kütüphanesinden daha sonra ekleyebilir |
| Görseller | Üç farklı, görüntülenerek incelenmiş 1963/1964/1965 Beatles fotoğrafı; tam kadraj; kırpma/zoom yok |
| Görsel kimlik | Üç sahne, altın/beyaz yazılar, alt bant ve Oldies Radyo imzası korunuyor; yumuşak çözülmeler |
| Kayıt şablonu | Ayrı hikâye ve istasyon tanıtımı; kapanış kaydı SHA256 ile sabitlenerek tekrar kullanılıyor |

## Kayıt

Ana anons:

> The Beatles released their debut single ‘Love Me Do’ in Britain — on this day in 1962.

1,1 saniyelik ayrı dijital sessizlikten sonra radyo tanıtımı:

> Oldies Radio. Timeless music. Listen, enjoy, share.

Daha sakin anlatım, ayrı tanıtım ve son nefes payı nedeniyle bu test 17 saniyedir. Genel hedef yaklaşık 15 saniye; yeni şablonun üst sınırı 18 saniyedir. Süreye yetişmek için kelimeler kesilmez veya ses hızlandırılmaz. Fazla uzun/hızlı kayıt reddedilir.

Ücretsiz yerel Whisper base.en konuşma kontrolü:

> The Beatles released their debut single, Love Me Do, in Britain, on this day in 1962. Oldie's radio, timeless music, listen, enjoy, share.

Hikâye ve kapanış kelimeleri çözümlendi; “Oldie’s radio” yazımı istasyonun fonetik karşılığıdır. Ana anons 127.5 kelime/dakika; tanıtım duraklamalarla daha sakindir. Bu ortamda doğrudan dinleme yapılmadı; sıcak DJ tonu ve son marka telaffuzunun dinleyici değerlendirmesi için MP4 sunuluyor.

## Katı fotoğraf kuralları

Kaynak, tarih, sanatçı, lisans ve tam kompozisyon görüntü üzerinden kontrol edilmeden fotoğraf onaylanmaz. Fotoğraf olay yılına en fazla 3 yıl uzak olabilir. Üç farklı kompozisyon ve SHA256 ile doğrulanmış dosyalar zorunludur. Heykel, tabela, bina, ilgisiz konu, kırpılmış varyant, aynı fotoğrafı çoğaltma ve rastgele arama sonucu yasaktır.

Tam kaynak kadrajı oranı korunarak 9:16 tuvale sığdırılır; kenarlar kesilmez, zoom/pan yapılmaz, yazı fotoğrafı örtmez. Dönem fotoğraflarının gerçek arşiv yılı gösterilir. Son MP4’ün 2, 7 ve 14. saniye kareleri incelendi; tüm üyeler ve fotoğraf kenarları görünür.

Başlangıç havuzu şu anda Beatles için hazırdır. Başka sanatçılar için aynı incelemeden geçen fotoğraflar havuza eklenmelidir. Üç uygun fotoğraf yoksa aday atlanır; uygun aday yoksa job fail olur. Kalite kuralını aşan görsel fallback yoktur.

| Fotoğraf | Tarih | Fotoğrafçı / lisans | Kaynak |
|---|---|---|---|
| The Beatles 1963 Dezo Hoffman Capitol Records press photo 2.jpg | 1963 | Dezo Hoffmann, Distributed by Capitol Records / Public domain | [Arşiv](https://commons.wikimedia.org/wiki/File:The_Beatles_1963_Dezo_Hoffman_Capitol_Records_press_photo_2.jpg) |
| The Beatles, The Ed Sullivan Show group photo.jpg | 1964 | Bernard Gotfryd / Public domain | [Arşiv](https://commons.wikimedia.org/wiki/File:The_Beatles,_The_Ed_Sullivan_Show_group_photo.jpg) |
| The Beatles pose for a portrait (1965).jpg | 1965 | EMI. / Public domain | [Arşiv](https://commons.wikimedia.org/wiki/File:The_Beatles_pose_for_a_portrait_(1965).jpg) |

## Doğrulama ve kapsam

- **26/26 Facebook testi yerelde geçti.** Gerçek TTS önizlemesinin GitHub çalışmasında 24/24 test geçti. Sabit kapanışın tekrar kullanımı ve bozulmuş dosyanın engellenmesi için eklenen 2 test de yerelde geçti.
- Gerçek hikâye kaydı ve sabit kapanış dosyasıyla çevrimdışı yeniden birleştirme başarılı; ikinci TTS çağrısı gerekmiyor. 1,1 saniyelik sessiz ara tekrar ölçüldü.
- TTS hatası, eksik/boş audio stream, sessiz ses izi, yanlış dil/oran, aşırı süre/tempo, geçersiz reklam arası, fotoğraf onayı/tarihi/kadrajı veya dosya hash’i yayın öncesinde engelleniyor.
- Tüm eski testlerle yapılan kapsam kontrolü 47/48 geçti. Tek hata olan Türkçe test_unsupported_story_is_rejected, değişmemiş temel sürümde de başarısızdır; ayrı otomasyona müdahale edilmedi.
- Değişen tek workflow: facebook-global-en.yml. Ortak Türkçe görsel arama/render fonksiyonları korunuyor. Mevcut Facebook R2.2/WordPress publish payload, content_id, delivery ve dedupe gövdesi AST karşılaştırmasında aynıdır; başına kalite kapıları eklendi.
- Yeni ücretli servis veya API anahtarı kurulmadı.

Test çalışması: https://github.com/MetteBuyuretti/oldies-reels-worker/actions/runs/37562928093

Düzeltme taslağı: https://github.com/MetteBuyuretti/oldies-reels-worker/pull/22

Gerçek TTS/MP4 testi commit’i: 9cd677e8dd05e7edb0aae5d0331b4d35f513df4a

MP4 SHA256: bad2bfe06deab170e0c99a3ab8699c704f1e67ff3b4ec75b7aaf077a825f24f0

Canlı publish yapılmadı. Önizleme ve kayıt/fotoğraf şablonu incelemeye hazır.

## Güncel ana dal ile uyum

Son kontrol sırasında ana dalda ae09f0d sürümünün eklendiği görüldü. Bu sürümün mevcut İngilizce TTS değişiklikleri test dalına birleştirilerek korundu; Facebook’a özel kayıt/fotoğraf kapıları ve ayrı DJ motoru test dalında kaldı. Güncel kodla 26/26 Facebook testi ve 49/50 tüm test geçti; tek başarısız Türkçe test önceki temel sürümde de başarısızdır. Bu çalışma ana dala merge edilmedi ve canlı yayın başlatmadı. Sunulan MP4’ün gerçek TTS testi 37562928093 numaralı çalışmadır.
