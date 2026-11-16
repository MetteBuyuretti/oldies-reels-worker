# İki çalışma — somut teslim ve kalan kaynak

16.11.2026 | 22:19:52 TSİ — WORK MASTER

**İngilizce sesli inceleme filmi teslim edildi. Instagram → YouTube son üç aktarımı final kaynak dosyalarını bekliyor. İki işin tümü DONE değildir.**

## GERÇEKLEŞEN — İngilizce Reels

[29,33 saniyelik sesli inceleme videosunu aç](https://chatgpt.com/library?file_id=libfile_ae24933f96988191b5254c1e72f66121&account_id=personal) · [Gerçek videodan üç kare](https://chatgpt.com/library?file_id=libfile_1a28e4a495508191a006344f5e0dffaa&account_id=personal) · [Özgün Charon hikâye kaydı](https://chatgpt.com/library?file_id=libfile_da23dd6cff70819191b98a8ab5767e3f&account_id=personal)

Yeni konu: **With The Beatles — 22 Kasım 1963**. Önceki reddedilmiş Beatles 1964 filmi kullanılmadı. Mevcut onaylı bankadan üç ayrı 1963 fotoğrafı; olayla yıl farkı 0, tam kadraj, crop/zoom yok. Önceki altın/beyaz üç sahneli kimlik korundu. Tarih, bugüne aitmiş gibi gösterilmedi.

Olgu kaynakları: [resmî albüm sayfası](https://www.thebeatles.com/beatles) ve [resmî olay kaydı](https://www.thebeatles.com/22-november-1963-beatles-released). Bunlar aynı yabancı yayıncının iki ayrı sayfasıdır; bağımsız iki yayıncı iddiası yok. Hikâyenin son cümlesi dinleyiciye hayal etme çağrısıdır.

| Kontrol | Gerçek ölçüm / sonuç |
|---|---|
| Film | 1080×1920, H.264, 30 fps, 880 kare |
| Süre | 29.333333 sn; 25–30 sn kapısı PASS |
| Ses | AAC stereo 48kHz, 1375 paket; tam decode PASS |
| Hikâye | Yeni Charon kaydı 20.850958 sn; yaklaşık 123.7 sözcük/dk |
| Kapanış | Kabul edilmiş sakin kayıt: 6.720 sn; özgün MP3 kaynak hash'i aynı |
| Ara | 1.1 sn; merkez örnekte tepe −91 dBFS |
| Ses seviyesi | −16.5 LUFS; true peak −2.0 dBFS; LRA 5.0 LU |
| Hız / fon | Hızlandırma veya germe yok; fon müziği eklenmedi |
| Boyut | 1,944,078 bayt |
| Film SHA256 | 25fb5ee531dc52b14308e62680658602b8f9619860dfed1bb836f303abfcd1d1 |

Hikâye Google AI Studio'da **gemini-2.5-flash-preview-tts / Charon** ile ücretsiz üretildi. No API key selected durumu korundu; ücretli anahtar, abonelik veya faturalandırma seçilmedi. Bu gerçek UI kaydı, otomasyonun Cloud Pro modelinin değiştirildiği anlamına gelmez. Kabul edilmiş kapanış yeniden üretilmedi.

Özgün WAV: 1,000,890 bayt; PCM16 mono 24kHz; SHA256 ed960e671cf2d1be7ff69023e4acacbde7976a813586ce2da1cb3835c3518f93. Windows Downloads/Generated Audio November 16, 2026 - 10_04PM.wav ile aktarılan Work dosyası birebir. İndirme zamanı yerel dosya kaydından 16.11.2026 22:04:46.950 TSİ.

### Düzeltilen iki İngilizce hata

1. build_dj_parts çok cümleli hikâyeyi ilk cümleye kesiyordu. Gerçek tekrar, yeni metni 18 tahmini sözcük / 16.86 sn tahmini videoya düşürdü. Tam metin korunuyor; açık dj_story_text aynen tüketiliyor; uygunsuz süre sağlayıcı çağrısından önce reddediliyor.
2. İlk gerçek FFmpeg7 renderı xfade girişinde 1/0 kare hızı nedeniyle durdu. Açık fps=30 düzeltmesiyle ikinci gerçek render ve medya QC PASS. Boş ilk çıktı teslim edilmedi.

62 Python testi PASS (49 ses/görsel/kapanış/metin + 5 giriş + 8 spiker). Kare hızı değişikliği sonrası aynı 17 görsel test tekrar PASS; yeni 17 test diye sayılmadı. İkinci gerçek film renderı teknik entegrasyon kanıtıdır; insanın dinlemesi veya bağımsız WATCHDOG kabulü sayılmadı.

## GERÇEKLEŞEN — Instagram → YouTube kaynak sorgusu

Mevcut Reels Bridge eklentisi **2.3.8-YT11-SOURCE** olarak güncellendi. Yeni eklenti yok. Salt-okunur son-video tablosu ve tekil kaynak kontrolü var. Tekil sorgunun reddettiği media_audio_type alanı iki Graph sorgusundan çıkarıldı. Native PHP lint PASS; 8/8 offline kaynak testi PASS; kaydedilen canlı kaynak tam içerik olarak adayla aynı.

[Canlı panel ekran kanıtı](live-source-inspector.jpg) · [Kurulu kaynak](bridge.readback.php) · [Değişiklik öncesi geri alma kaynağı](bridge.before.php) · [Kaynak testleri](test-instagram-source.php)

| Gerçek Instagram paylaşımı | Medya kimliği | Düzeltilmiş tekil API sonucu |
|---|---|---|
| [1–7 Kasım / 11 Kasım paylaşımı](https://www.instagram.com/reel/Dfm96scpYxb/) | 18149541115603460 | instagram_final_media_missing |
| [26–31 Ekim / 2 Kasım paylaşımı](https://www.instagram.com/reel/DfPw8yDNQmB/) | 18128567308910933 | instagram_final_media_missing |
| [Adriano Celentano / 25 Ekim](https://www.instagram.com/reel/De67RaiJCyt/) | 18446999791133929 | instagram_final_media_missing |

Kimliği doğrulanmış üç tekil GET de media_url vermedi. Eski Chris Isaak videolarında URL geliyor; genel bağlantı/token arızası değil. Boş ses türü lisanslı müzik nedeni kanıtı sayılmadı. İlk paylaşım sahibinin web arayüzünde 59.375 sn / 1080×1920; video blob kaynağında, gönderiyi yönet menüsünde indirme yok. Eski 16 taslak başlık benzerliğiyle eşleştirilmedi; ham videoya dönülmedi. Yeni YouTube yüklemesi/yayını **0**.

## BEKLEYEN

- İngilizce: kurucunun gerçek filmi dinleyip metin/ses uyumunu değerlendirmesi; gerekli bağımsız inceleme. Otomatik üretim/yayın sistemi tamamlandı iddiası yok.
- Instagram → YouTube: yukarıdaki üç yayının **Edits'ten/Instagram'dan dışa aktarılmış final MP4 dosyaları** veya sağlayıcıdan indirilebilir final adresi. Bu kaynaklar olmadan olumlu yayın sonucu uydurulamaz.
- [PR44](https://github.com/MetteBuyuretti/oldies-reels-worker/pull/44) taslak/açık; güncel dal commit'i 354d4afd6e83cec67575fabf81913d3891c56c19. Merge, karantina açma, scheduler veya yeni yayın yapılmadı.

## PLANLANAN — ilk eksik adım

İngilizce hazır filmi yeniden üretmeden dinleme/bağımsız kabulü al. Yetkili kurulum kararında PR44'ü değerlendir. Instagram final dosyaları geldiğinde gerçek kimlik + dosya hash'i bağını kur, mevcut YouTube dispatcher'ına tekil/idempotent aktar ve dönen gerçek görünürlük/işlenme makbuzunu doğrula. Aynı üç boş kaynak sorgusunu gerekçesiz tekrarlama.

Kod tekrar çalıştırılacaksa PR44 kaynak ağacı, mevcut Python bağımlılıkları ve FFmpeg gereklidir. build_storyboard.py/render_review.py yalnız yerel inceleme üretir; yayın yapmaz. candidate.json ve manifest.json ölçülmüş teslim kimliğini saklar. Kabul edilmiş sesleri yeniden arama veya üretme.

Saat düzeltmesi: iki ara ilerleme notundaki 22:02/22:09 ibareleri saat ölçümünden ilerideydi. Bu nihai kayıt, doğrudan ölçülen gerçek TSİ saatlerine ve dosya zamanına dayanır. Önceki checkpoint geçmişi Git commitlerinde korunmuştur.
