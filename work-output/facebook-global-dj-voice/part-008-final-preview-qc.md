# OLDIES RADYO — Facebook Global final locked preview / QC

7 Ekim 2026. PR #22, `fix/facebook-global-dj-voice`. Canlı Facebook yayını yapılmadı; WordPress taslağı ve R2 teslimatı da yapılmadı. Yeni test dosyası: **Oldies-Facebook-English-DJ-Beatles-Test.mp4**.

**Teknik testler başarılı. Yeni kapanışın sahibi tarafından dinleme onayı bekleniyor. Production onayı ve SHA256 kilidi henüz verilmedi; tam LOCK READY etiketi kullanılmıyor.**

## GitHub Actions kanıtı

- [Başarılı Actions çalışması 37566151737](https://github.com/MetteBuyuretti/oldies-reels-worker/actions/runs/37566151737)
- Test/render commit: `47cb8d20ecf829c686ae9b72f5c292032c111899`.
- Güncel Facebook testleri: **38/38 PASS**, Actions üzerinde 5,442 saniye. Local testler de 38/38; nihai kanıt Actions çalışmasıdır.
- Ayrı render adımı başarılı. `OLDIES_PREVIEW_ONLY=true`; sonuç `success=true, preview_only=true, voiceover=true`.
- Log: `Preview-only render completed; WordPress draft upload was intentionally skipped.`

| İstenen durum | Sonuç |
|---|---|
| TTS enabled | PASS — `OLDIES_TTS_ENABLED=true` |
| voice-over generated | PASS — mevcut güvenli Gemini 2.5 Pro TTS / Charon / en-US; iki ayrı gerçek kayıt |
| audio stream detected | PASS — AAC, 48.000 Hz, stereo, 798 paket; MP4 içine gömülü |
| silent publish blocked | PASS — eksik/boş/sessiz/çözülemeyen audio ve başarısız TTS testleri geçiyor; fallback=false |
| diğer otomasyonlar untouched | PASS — bu düzeltme Facebook dosyaları ve ilgili checkpoint ile sınırlı; diğer workflow’lar değiştirilmedi |

## Gerçek MP4 audio QC

| Kontrol | Ölçüm / sonuç |
|---|---|
| Video | **1080×1920, 9:16, 30 FPS, 17,000 s** |
| FFmpeg render | `video:954kB audio:347kB`; bu MP4 için `audio:0kB` yok |
| Anons | 8,472 s; tahmini **127,5 WPM** |
| Radyo tanıtımı | Ayrı kayıt, 6,720 s; tüm kayıt süresi üzerinden 62,5 WPM; doğal duraklar bu ölçüme dahildir |
| Ara | 1,100 s dijital sessizlik; tanıtım 9,572 s’de başlıyor |
| Ara ses seviyesi | Orta 0,4 saniyelik bölümde peak **−91,0 dB** |
| MP4 ses seviyesi | Mean −20,2 dB; peak −1,9 dB; FFmpeg decode başarılı |
| Bölüm ses seviyesi | Ana anons mean −18,9 / peak −2,5 dB; tanıtım mean −21,1 / peak −1,9 dB |
| Hızlandırma / müzik | İkisi de yok. Ana anons ve kapanış tempo_factor=1,0 |
| İngilizce anlaşılırlık | Yerel Whisper base.en, gerçek MP4’den Beatles / Love Me Do / Britain / 1962 hikâyesini doğru çıkardı. Ayrı kapanışın İngilizce çağrısı da multilingual base/en ile çıkarıldı |
| Marka telaffuzu | **Dinleme onayı bekliyor.** ASR özel marka adını genel İngilizce sözcüğe normalleştiriyor; marka telaffuzunu otomatik onaylamak için yeterli değil |
| Sıcak DJ tonu | İngilizce sıcak, sohbet eden müzik radyosu DJ yönlendirmesi uygulanmış. Öznel ton ve marka telaffuzu sahibi tarafından dinlenerek onaylanmalı |

Kayıttaki sabit metin:

**Ana anons:** The Beatles released their debut single ‘Love Me Do’ in Britain — on this day in 1962.

**1,1 saniye sessizlik.**

**Ayrı kapanış:** Oldies Radyo. Timeless music. Listen, enjoy, share.

Telaffuz yönlendirmesi: Oldies = OLD-eez; Radyo = RAH-dyoh, iki hece, ilk ünlü “ah”. Marka yazımı değişmiyor. Önceki kapanış MP3’ü production havuzundan silindi ve yeniden kullanılmıyor.

Yeni dosya: **Oldies-Radyo-English-DJ-Signoff-Preview.mp3**. Dosyanın mevcut SHA256’sı aşağıdadır. Bu, teslim edilen kaydın kimliğidir; production onayı yerine geçmez:

`1dc358ef0cea5a3a6d9fe20d9934358fed5ccd0009ba0838a60bba9f28bb9d9c`

Sahibi bu kaydı dinleyip onayladıktan sonra aynı dosya production `advert_sha256` alanına bağlanacak, onaylayan/tarih/telaffuz doğrulaması kaydedilecek. Şu anda `advert_approved=false`, `advert_sha256=""`; production hem kayıt öncesinde hem teslimat öncesinde kapalı. Sessiz fallback veya eski kayda dönüş yok.

MP4 SHA256: `a78e4038f9082cb51bac296e98fd4e2b73d0b3551f1599c4b7c9b6464e65461f`.

## 1962 önce araştırıldı; üç farklı 1963 (+1) fotoğraf

1962 Commons kategorisi ve dosyaları önce tarandı. [Cavern fotoğrafı](https://commons.wikimedia.org/wiki/File:The-True-Story-of-the-Beatles-1.jpg) 711×501 ve aktif telif/silme itirazına sahip olduğu için reddedildi. Diğer adaylar kapak, sergi, modern tabela veya replika niteliğindeydi. Üç uygun, lisansı doğrulanabilir yüksek çözünürlüklü 1962 fotoğraf seti bulunamadı. Bu sonuç tüm dünyada 1962 fotoğrafı bulunmadığı iddiası değildir; incelenen kaynaklardan uygun set doğrulanamadı.

İzin verilen **+1 yıl** uygulandı. 1964/1965’e otomatik geçilmedi; ±2 kullanılmadı. Araştırma kaynakları: [1962 kategorisi](https://commons.wikimedia.org/wiki/Category:The_Beatles_in_1962), [1963 kategorisi](https://commons.wikimedia.org/wiki/Category:The_Beatles_in_1963), yukarıdaki Cavern dosyası. Araştırma ve görsel inceleme: Codex, 7 Ekim 2026; gerekçe fotoğraf havuzunda kayıtlı.

| Sıra / fotoğraf | Yıl kanıtı | Kaynak çözünürlük | Kaynak / fotoğrafçı | Kaynakta belirtilen kullanım statüsü |
|---|---|---|---|---|
| 1 — Dört Beatles tanıtım portresi | 1963; UK yayımı 29 Kasım, US yayımı 26 Aralık 1963 | 3621×2817 | [Commons tam kare](https://commons.wikimedia.org/wiki/File:The_Beatles_1963_Dezo_Hoffman_Capitol_Records_press_photo_2.jpg); Dezo Hoffmann / Capitol Records | PD-US-no notice + PD-scan; **ABD kamu malı**. Sayfa diğer kaynak ülkelerde telifin devam ettiğini açıkça belirtiyor |
| 2 — Hötorgscity’de dört üye zıplarken | Ekim 1963 | 1446×1607 | [Commons tam kare](https://commons.wikimedia.org/wiki/File:The_Beatles_i_H%C3%B6torgscity_1963.jpg); Scanpix, fotoğrafçı belirtilmemiş | PD-Sweden + PD-US-not renewed; İsveç/ABD kamu malı beyanları, diğer ülkeler için kaynakta sınırlama notu var |
| 3 — Stockholm grup fotoğrafı | Kaynak açıklamasında 1963 | 2003×1600 | [Commons tam kare](https://commons.wikimedia.org/wiki/File:Beatles_Trenter_1963_cleaned_up_3_jpg.jpg); Bo Trenter | PD-Sweden; **İsveç kamu malı** beyanı. Bu sayfada ayrı ABD gerekçesi yok |

Bu statüler kaynakların belirttiği coğrafi kapsamla kaydedildi; dünya çapında koşulsuz lisans olarak gösterilmiyor. Hoffmann kaynağı arka plan/ton düzeltmesi yapılmış gerçek fotoğraf olarak açıklanıyor. Kullanılan görseller kapak tasarımı veya kapak kırpımı değil, tam fotoğraf dosyalarıdır; bizim işlemimiz yalnızca oranı koruyan boyutlandırma/JPEG kaydıdır.

| Kullanılan dosya | Saklanan çözünürlük | SHA256 |
|---|---|---|
| beatles-1963-hoffmann.jpg | 1800×1400 | `0ce328f1a4daefb00aee1f7de6571e2e3f04ff3bea0a8b2b7d9077e707528ddc` |
| beatles-1963-hotor-full.jpg | 1446×1607 | `8cd12e16ecbec19d5c84cdfb054b10f87a285931d5c51f9327369b625003acba` |
| beatles-1963-trenter-full.jpg | 1800×1438 | `01e0cb0b8b4bfee8b5126cfda01381010fe52c05e23487594e507926b9f84aea` |

Üçü de gerçek Beatles fotoğrafı, John/Paul/George/Ringo kadrosu, erken saç/suit görünümü. İlk ve üçüncü karede konuk yok. Sokak karesindeki küçük arka plan kişileri gruba eşit ağırlık taşımıyor; dört üye büyük ön plan öznesi. Pasta sahne içi bir nesne; misafir veya kapak tasarımı değil. Kaynak görüntüler ve MP4’den 2 / 7 / 13 saniye kareleri görsel olarak incelendi.

**Crop yok; zoom yok; üç farklı kompozisyon; bütün kaynak kadrajları görünür.** Arşiv yılı her sahnede 1963 olarak yazıyor; 1962 olay anı fotoğrafıymış gibi sunulmuyor. Mevcut siyah, altın/beyaz üç sahneli şablon, metin alanı, alt bant ve OLDIES RADYO imzası korunuyor.

## Katı kapılar ve kapsam

Sıra: olay yılı → yeterli kaliteli kare yoksa ±1 → gerçekten zorunluysa olay/fotoğraf SHA256’sına bağlı manuel ±2 onayı. ±2 için saç, kıyafet, kadro ve sahne uyumu açıklanmış olmalı; boş not veya boolean onay yeterli değil. ±3 ve sonrası daima yasak. Sanatçı-baskın kompozisyon, doğru görünüm, lisans/kaynak/tarih, tam kadraj ve dosya SHA256’sı zorunlu. Eksik uygun set job fail; kaliteyi başka döneme geçerek tamamlamak yok.

Testler eksik/sessiz audio, TTS hatası, yanlış marka metni, değişen/onaysız kapanış, hızlı kayıt, gerçek reklam arası, aynı yıl önceliği, gerekçesiz ±1, onaysız/başka olaya ait ±2, ±3, eşit ağırlıklı misafir, yanlış görünüm, kapak/crop/telif itirazı, değişen fotoğraf hash’i, aynı fotoğraftan üç kopya ve teslimattan önce blok davranışını kapsıyor.

Facebook Global R2.2 / WordPress payload, yayın ve dedupe gövdesi korunuyor; yalnızca önüne zorunlu onay kapısı eklendi. Türkçe Instagram, Etsy, Zero Cost Reels ve diğer workflow’lar bu düzeltmede değiştirilmedi. **CANLI FACEBOOK PUBLISH YAPILMADI.**

Oldies-Facebook-Photo-and-Audio-QC.zip içinde kullanılan tam kare JPEG’ler, kaynak/lisans/yıl/hash kaydı, ffprobe, audio QC, kayıt bilgisi ve ham ASR sonucu bulunur. Yeniden kullanılabilir katı şablon ayrıca Oldies-Facebook-DJ-Recording-Template.md dosyasında.
