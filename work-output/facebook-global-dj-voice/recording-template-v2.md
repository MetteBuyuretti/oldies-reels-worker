# Oldies Radyo — Facebook Global kayıt ve fotoğraf şablonu v2.0

Yalnızca Facebook Global English Reels için geçerlidir. Canlı yayın onayı yerine geçmez.

## Kayıt düzeni

| Bölüm | Sabit kural |
|---|---|
| Ana anons | İngilizce; doğrudan konuya giren, doğrulanmış kaynaktan kısa hikâye. En fazla 25 kelime. |
| Ses | Mevcut güvenli Gemini TTS / Charon. Sıcak müzik radyosu DJ’i: tek bir dinleyiciyle sohbet eden, rahat ve gülümseyen ton. |
| Tempo | Hedef yaklaşık 128 kelime/dakika; tahmini üst sınır 138. Cümleler nefes almalı, kelimeler yutulmamalı. |
| Anons ile reklam arası | Ayrı kayıtlardan sonra dijital olarak eklenen **1,1 saniye sessizlik**. Reklam ana anonsa yapışmaz. |
| Sondaki radyo tanıtımı | **“Oldies Radio. Timeless music. Listen, enjoy, share.”** Aynı sıcak DJ, yumuşak istasyon tanıtımı. Görselde oldiesradyo.com/en/ bulunur. |
| Tekrar kullanım | Onaylı kapanış kaydı sabit dosya ve SHA256 ile tekrar kullanılır. Ana hikâye her Reel için üretilir. |
| Süre | Normal hedef yaklaşık 15 saniye. Sakin anlatım ve ayrı tanıtım gerektirdiğinde 18 saniye üst sınır. |
| Hız müdahalesi | **Hızlandırma yasak.** Gerekirse perdeyi değiştirmeyen sınırlı yavaşlatma. Fazla hızlı veya uzun kayıt reddedilir; metin kısaltılıp yeniden kaydedilir. |
| Arka plan | Müzik otomatik eklenmez. MP4 içinde DJ hikâyesi ve ayrı radyo tanıtımı bulunur. Kullanıcı Meta müzik kütüphanesinden daha sonra müzik ekleyebilir. |

Ana anons kayıt istemi:

> English only. Be a warm, unhurried music-radio DJ speaking personally to one listener. A friendly smile in your voice; intimate and conversational, with gentle natural inflection. Read at approximately 128 words per minute. Let each phrase breathe. Start directly with the music story. Read the supplied words exactly once. No added words, music, singing or effects. Avoid a newsreader or robotic delivery.

Tanıtım kaydı için ek yönlendirme:

> This is a separate soft station promotion after the story. Say Oldies Radio clearly: old-eez ray-dee-oh. Keep the same warm, unhurried DJ delivery.

Örnek kayıt:

**ANA ANONS:** The Beatles released their debut single ‘Love Me Do’ in Britain — on this day in 1962.

**ARA:** 1,1 saniye dijital sessizlik.

**RADYO TANITIMI:** Oldies Radio. Timeless music. Listen, enjoy, share.

## Fotoğraf seçimi — zorunlu kurallar

1. Gerçek sanatçının veya grubun gerçek dönem fotoğrafı kullanılmalı. Tarih yalnızca dosya adından tahmin edilmez; kaynak açıklaması/arşiv kaydıyla doğrulanır.
2. Fotoğraf yılı olay yılından en fazla 3 yıl uzak olabilir. Başka bir döneme ait veya güncel fotoğrafla boşluk doldurulmaz.
3. Orijinal kompozisyon insan tarafından görüntülenerek onaylanır. Grup fotoğrafında tüm üyeler ve yüzler görülebilmeli; ilgisiz konu, zayıf kadraj veya düşük kalite reddedilir.
4. Heykel, anıt, tabela, bina, bilet, logo, çizim, kolaj veya sanatçıyı taklit eden grup kullanılamaz.
5. Kullanılabilir lisans, kaynak URL’si, fotoğraf tarihi, fotoğrafçı, kompozisyon kimliği ve dosya SHA256’sı kaydedilir. Onaydan sonra değişen dosya tekrar onay gerektirir.
6. Üç sahne için üç farklı, onaylı fotoğraf gerekir. Aynı fotoğrafı kırpıp çoğaltmak veya farklı dosya adıyla tekrar kullanmak yasaktır.
7. **Kaynak fotoğrafın tamamı görünür kalır.** Fotoğraf 9:16 tuvale oranı korunarak sığdırılır. Sağdan/soldan kesme, otomatik doldur-kırp, zoom/pan ve bulanık kırpılmış arka plan yasaktır.
8. Fotoğraf ile yazı alanı ayrıdır; yazı yüzleri ve kadrajı örtmez. Fotoğrafın arşiv yılı ayrıca gösterilir. Dönem görseli olayın gerçekleştiği anın fotoğrafıymış gibi sunulmaz.
9. Otomatik arama sonuçları kendiliğinden onaylanmaz. Yeterli onaylı dönem fotoğrafı yoksa aday atlanır; uygun başka aday da yoksa job fail olur.

Başlangıçtaki onaylı havuz Beatles için 1963 tanıtım, 1964 Ed Sullivan prova ve 1965 grup portresidir. Başka sanatçılar için aynı görsel inceleme sürecinden geçen fotoğraflar havuza eklenmelidir. Otomasyon kuralları gevşeterek boşluğu doldurmaz.

## Yayın öncesi kapılar

TTS başarısızsa, İngilizce voice-over oluşmazsa, audio stream boş/yok/sessizse, kayıt şablonu/reklam arası geçersizse veya fotoğraf kuralları sağlanmazsa teslimat engellenir. Kontroller gerçek MP4 üzerinde ffprobe/FFmpeg ile yapılır. `audio:0kB` kabul edilmez.

1080 × 1920, 9:16, üç sahne, mevcut alt bant, altın/beyaz yazılar ve Oldies Radyo imzası korunur. Fotoğraflar sabittir; sahneler yumuşak çözülmeyle geçer. Türkçe Instagram, Etsy, Zero Cost Reels, diğer workflow’lar ve mevcut R2.2/WordPress publish/dedupe gövdesi bu şablonun kapsamı dışındadır.
