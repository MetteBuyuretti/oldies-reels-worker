# FACEBOOK GLOBAL — ENGLISH DJ VOICE READY

Durum: **Yayınsız teknik önizleme başarılı.** Düzeltme test dalında kaydedildi; canlı workflow henüz değiştirilmedi. Facebook ve WordPress yayın çağrısı yapılmadı.

| Kontrol | Sonuç |
|---|---|
| TTS enabled | true |
| voice-over generated | İngilizce, Gemini Charon, 11.112 saniye |
| audio stream detected | AAC, 48000 Hz, 2 kanal, 700 ses paketi |
| silent publish blocked | Aktif; 13/13 Facebook testi geçti |
| diğer otomasyonlar untouched | TR Instagram / Reels / cleanup / retention workflow dosyaları değiştirilmedi; Etsy ve diğer sistemlerde işlem yapılmadı |
| Video | 1080 × 1920, 9:16, 30 fps, 15 saniye |
| FFmpeg ses çıktısı | audio:263kB; audio:0kB yok |
| Ses düzeyi | Ortalama -20.6 dB; tepe -2.9 dB |
| Müzik | Otomatik arka plan müziği eklenmedi; MP4 içinde yalnızca DJ anonsu var |
| Görsel şablon | Mevcut üç fotoğraflı / üç sahneli düzen, fontlar, renkler, alt bant ve geçiş kodu korundu; sahneler görsel olarak incelendi |

Anons metni:

> The Beatles released their debut single ‘Love Me Do’ in Britain. That was on this day in 1962. You're with Oldies Radyo — great records, and the stories behind them.

Yerel, ücretsiz Whisper tiny.en transkripsiyonu:

> The Beatles released their debut single, Love Me Do in Britain. That was on this day in 1962. You're with all these radio, great records, and the stories behind them.

Transkripsiyon, İngilizce hikâyeyi ve kapanış cümlesini çözümledi. İstasyon adını “all these radio” olarak yazdı; bu bir konuşma tanıma belirsizliğidir. Bu ortamda ses doğrudan dinlenemediği için sıcak DJ tonu ve marka telaffuzu için insan dinlemesi henüz doğrulanmış değildir. Ses üretiminde sıcak, doğal, konuşma tarzında DJ istemi kullanıldı.

Ses üretimi başarısız olursa işlem durur. Eksik/boş/çözümlenemeyen ses akışı, tamamen sessiz ses izi ve İngilizce anons bilgisi bulunmayan video teslimat öncesinde reddedilir. Ses kontrolü render sonrasında ve Facebook teslimat fonksiyonunun başında uygulanır. Küçük süre aşımı yalnızca perdeyi değiştirmeyen sınırlı tempo düzeltmesiyle giderilir; kelimeler kesilmez, büyük aşım reddedilir.

Mevcut güvenli Google workload identity, hesap ve TTS çağrısı kullanıldı. Yeni ücretli servis veya anahtar kurulmadı. R2.2 / WordPress publish payload / content_id ve dedupe kodu değişmedi. Diğer workflow dosyalarının ve ortak research / video_factory / requirements dosyalarının değişmediği karşılaştırmayla doğrulandı.

Facebook testleri yerelde ve GitHub çalışmasında **13/13** geçti. Önceki tüm testlerle birlikte **36/37** geçti; tek başarısız test olan Türkçe “unsupported story” testi, değişiklik yapılmamış temel sürümde de başarısızdır. Kullanıcının kapsam sınırlaması nedeniyle bu ayrı konuya müdahale edilmedi.

- Başarılı test: https://github.com/MetteBuyuretti/oldies-reels-worker/actions/runs/37561125079
- Düzeltme: https://github.com/MetteBuyuretti/oldies-reels-worker/pull/22
- Test edilen commit: c9a8350b61f00ea8a240dd8773e1a20b832a58c9
- MP4 SHA-256: f5bb46821a398445806a6259b3871d23a9a9f6cda71f46df833ee9f93adbf380

Canlı publish yapılmadı. Günlük canlı workflow’un bu düzeltmeye geçişi yapılmadı; önizleme incelemesi için hazır.
