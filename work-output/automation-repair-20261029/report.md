# Üç otomasyon — ilk uygulama checkpoint'i

29.10.2026 | 14:33 TSİ (UTC+3)

Operasyon sahibi/uygulayıcı: mevcut WORK MASTER, bu Work oturumu. Bağımsız denetçi: mevcut WORK WATCHDOG; bu dosya onun kabul kararı değildir. Dayanak: kurucunun Watchdog planını okuyup çözüme başlama talimatı; WD-THREE-RECHECK-20261029-01.

## Kısa sonuç — 29.10.2026 | 14:33 TSİ

- GERÇEKLEŞEN: Watchdog son kontrolü ve üç görev okundu; main d04f82f, PR33 073e766, PR22 9ad0877 ile karşılaştırıldı. Çözüm sırası benimsendi.
- TEST EDİLDİ: Tumblr'ın iki kip çakışması için gerçek kaynak kesitlerine uygulanabilen staging düzeltmesi yazıldı. 16 odaklı kontrol geçti; iki argüman sırası eski davranışı yeniden üretip adayda ilk main yan etkisinden önce reddediliyor.
- GERÇEKLEŞEN: Reels'in GitHub çağrı yolları ayrıştırıldı. PR33 yerel, hash bağlı sesi tüketiyor; main ve PR22 ses üreticisine ulaşabiliyor. Yerel Windows launcher/ref ve iki kabul edilmiş sesin kimliği hâlâ doğrulanamadı.
- BEKLEYEN: Tumblr adayının bugünkü tam Windows kaynağına hash kontrollü uygulanması ve gerçek giriş doğrulaması; WD-T2 zaman/yazıcı kapsamı; Jingle M05 asıl kayıt ayrımı; Reels yerel sürüm/varlık eşlemesi. Bu Work'e kullanılabilir Windows/tünel araçları sunulmadı; yalnız Remote Desktop Commander ailesi var. Yerel runtime hazır beyanı, bu oturumdan çağrı yeteneği kanıtı sayılmadı.
- PLANLANAN: İlk teslim bağımsız incelemeye sunulur. Kontrol noktası mevcut yerel uygulayıcının güncel preimage ve staging sonucunu teslim ettiği ilk aktif okumadır; otomatik uyandırma veya sürekli arka plan çalışması kurulmadı. Canlı uygulama/gerçek medya/üretim/yayın/süreklilik kabulü yok.

## 1. Tumblr: uygulanabilir dar düzeltme

26 Ekim kaynak paketindeki shouldSubmit yalnız --queue-ready arıyor. main ilk klasör/log yolunu kip ayrımından önce hazırlıyor; iki bayrak birlikte geldiğinde ayrı guard yok. Bu kusur gerçek yayın gerçekleştiğini kanıtlamaz: mevcut allPathsCovered=false ve nextQueueTarget eksikliği gönderimi ayrıca kapatıyor.

Yeni `tumblr/build_candidate.py`, verilen tam publisher'ın SHA256'sını doğrular; bilinen main/argv/shouldSubmit bağlantı noktalarının her birini tekil arar. Şunları ekler:

1. main argv ayrıştırmasından hemen sonra, root/log klasörü/kilit/tarayıcı/envanter/ledger işlemlerinden önce `CONFLICTING_PUBLISHER_MODES` reddi.
2. shouldSubmit içinde eligibility çağrısından önce aynı ret.

Araç yalnız YENİ staging dosyası oluşturur; orijinal dosyaya yazmayı, mevcut çıktının üzerine yazmayı, yanlış hash'i, farklı kaynak yapısını ve tekrar uygulanmayı reddeder. CRLF korunur. Sadece gösterilen bağlantı noktaları eşleşirse aday oluşturulabilir; tüm dosyanın başka bakımdan doğru olduğu sonucu çıkarılmaz. Tam Windows publisher bu oturumda okunamadığından canlı diff/uygulama iddiası yok.

Yerel uygulayıcı, önce güncel tam dosya hash/diff'ini doğrular. Son yayımlanmış kurulu hash `7d817d484608115a44b4e912e2af51bb333dae377299eaac3564cccccdd01279` (26 Ekim) tarihsel karşılaştırma değeridir; bugünün sürümü varsayılmaz. Farklıysa diff incelenmeden yeni hash körlemesine kabul edilmez. Ardından mevcut yetkili staging alanında:

```text
python build_candidate.py --source <mevcut-publisher> --output <yeni-staging-publisher.mjs> --expected-sha256 <incelenmiş-güncel-preimage>
node --check <yeni-staging-publisher.mjs>
```

Bu iki komut kurulu sürümü değiştirmez veya çalıştırmaz. Gerçek Windows uygulaması için mevcut yedek/kurulum kilidi, preimage/postimage ve kaynakta başka ilk yan etki bulunup bulunmadığı incelenmeli; iki kip sırası tam girişte yayınsız doğrulanmalıdır. Geri dönüş yalnız ilgili kod farkıdır; eski ledger geri yükleme, lock/claim silme yok. Çakışan girişin ret davranışı yeni latest.json yazmaz; eski dosyanın yeni koşunun sonucu sanılmaması için yerel yürütücü stderr/exit code ve koşu zamanını ayrı teslim etmelidir.

### Gerçek çalıştırılan test

Node v24.22.1 / Python 3.12.14, bu Work'ün izole Linux çalışma alanı. Komut:

```text
node --test work-output/automation-repair-20261029/tumblr/mode_guard.test.mjs
```

16 test, 16 PASS, 0 FAIL, exit 0. Testler repo içindeki onaylı budget-excerpt.mjs ve verify-flow.txt içeriklerini kullanır; ES module syntax çıkarılarak gerçek main/shouldSubmit gövdeleri vm içinde çalıştırılır. Dosya işlemleri gözlemleyen stub ile durdurulur; gerçek tarayıcı veya hesap açılmaz.

Kapsam: eski iki sıra kusur üretimi (2); aday main etkisiz ret (2); aday eligibility öncesi ret (2); tek/varsayılan kipin eski girişini koruma (3); Verify eligibility'ye girmez (1); queue scoped auth reddi (1); queue eligibility sonucu (1); mevcut bütçe/hedef kapıları (1); kaynak koruma/üzerine yazma/hash reddi (1); değişmiş kaynak reddi (1); CRLF ve node --check (1). Bunlar 26 Ekim test sayılarıyla toplanmadı. Üretim bağımlılıklarının top-level import etkileri veya tam Windows launcher bu excerpt testiyle doğrulanmış değildir.

### Düzenli yayın için açık kalanlar

Gerçek platform queue hedef zamanının doğrulanması, otomatik yazıcıların sahipliği/kapsamı ve yeni kabul edilmiş içerik ayrı işlerdir. Bu düzeltme bunları tamamlamaz. allPathsCovered ve yayın kilitleri açılmadı. 26 Ekim contentStock=0 bugünün panel ölçümü sayılmadı; yeni stok var/yok diye hüküm verilmedi. Yeni içeriğe başlanmadan önce yeni teslim olup olmadığı mevcut yerel kayıtlarla kontrol edilmelidir.

## 2. Reels: GitHub R0 çağrı haritası

| Yol | Sabit sürüm | Gerçek kaynak çağrısı | Bugünkü çıkarım/sınır |
|---|---|---|---|
| main TR/EN workflow | d04f82ffeaa13b025768756ee164a426534fa2a6 | workflow → python worker.py → main:1422 → download_voiceover:1465 → eksikse synthesize_google_voice:1468 → build_timeline/render | Ses üreticisi bu kod yolunda ulaşılabilir. Fiilen çalışma ve doğru performans profili kanıtı değildir. |
| main Reels tetik kapısı | Aynı main | create-draft.if yalnız workflow_dispatch + preview_only=true | Schedule atlama kasıtlı kalite kilidi; cron arızası diye düzeltilmeyecek. Main preview önce WP env okur; bunu PR33'ün credentials okumayan preview'siyle karıştırma. |
| main Facebook tetik kapısı | Aynı main | publish-facebook.if=false | İş çalışmaya kapalı; bu tur açılmadı. |
| PR33 preview | 073e7665d9d381e7c8d595fcd60b905a9071490a | worker.main:1111 → prepare_preview → reels_preview.py:63 local_voiceover → hash/script/dil/hız kontrolü → render callback | synthesize_google_voice bu girişte çağrılmıyor. Değişiklik önce doğru packet/ses tüketim yoluna bağlanmalı. |
| PR22 EN | 9ad08776e882af386f2897ac43e85eaeb28f029e | worker.main:1425 → EN dış sesi kullanmaz → synthesize_google_voice:1474 → facebook_global_audio.require_voiceover → facebook_global_visuals.render → audio/media QC | Mevcut 18s/17.4s/1.1s eski sözleşme var. 26 Ekim 25–30s kısa Facebook altgöreviyle uzlaştırılmalı; PR33 veya uzun hikâye profili diye değiştirilemez. |
| Windows launcher | DOĞRULANAMADI | Bu Work'te kaynak/başlatıcı/ref okunabilir değil | GitHub kaynak haritası yerelde aktif sürüm eşlemesinin yerine geçmez. |

İncelenen main ağaçta tek MP3 yolu assets/john-lennon-pro-one-take.mp3 olarak görünüyor; dosya adı beğenilmiş iki Charon varlığını kanıtlamaz. 26 Ekim raporu kabul beyanını korur ama iki örneğin fiziksel kimliğini içermiyor. PR22 varlıklarının tamamı veya özel Windows diski için yokluk iddiası yok. Yeni TTS veya aynı seslere yeniden kullanıcı onayı talebi yok.

Bu yüzden süre/closing/pause kuralları bu tur topluca değiştirilmedi. Sonraki dar giriş: ilgili yerel iş/launcher/ref, calm/energetic dosya/hash ve mevcut kabul eşlemesi. Ardından yalnız seçilmiş aktif profile yama. Mevcut 10s ret, görsel kimlik/lisans, script ve bağımsız manifest kapıları korunur.

## 3. Jingle: kanıt ve şema ayrımının sınırı

manual_music_preflight.py gerçekten hem receipt hem original_metadata içinde aynı MANUAL/track_id/source_date/sha256/bytes alanlarını ister. Bu, yalnız tutarlılık sözleşmesidir. M05 için yayımlanan adayda related_existing_records=1 yazıyor; asıl kaydın türü, alanları ve dosya bağı yok. Bu nedenle ne 'kaynak kesin kayıp' ne de 'sadece şema hatası' sonucu çıkarılabilir. Alan adlarını tahmin ederek adapter veya sağlayıcı makbuzu üretilmedi.

Mevcut yerel uygulayıcının ilk görevi yalnız zaten işaretli M05 kaydını inceleyip kayıt türü/tarih, sağlayıcı kimliği mi yerel rezervasyon mu, dosya/indirme bağı ve gerçek alan eşlemesini teslim etmektir. Geniş on dosya/disk taraması tekrarlanmayacak. Kurtarılamazsa tarihsel kurtarma parçası 'kanıt bulunamadı' olarak kapanabilir; bütün Factory onarımı kapanmaz. Importer/state/lock/recovery → DJ miks çağrı yolu üretimsiz kaynak incelemesi ayrı ilerler. Asıl importer/Factory kaynakları bu main ağacında bulunmadığı ve Windows'a erişim olmadığı için bu oturumda incelenmiş sayılmadı.

7/7 preflight ve 10/10 eski test yeniden koşturulup ilerleme sayılmadı. State/lock/18 Ekim slotu, V3.1 ve pilot ertelemesi korunuyor. Gerçek MASTER, tam dinleme ve planlı süreklilik hâlâ bekliyor.

## Kaynak ve izlenebilirlik

- Watchdog son karar: https://github.com/MetteBuyuretti/oldies-reels-worker/issues/32#issuecomment-6495376317
- Reels sürüm düzeltmesi: https://github.com/MetteBuyuretti/oldies-reels-worker/issues/31#issuecomment-6495357982
- Jingle J1/J2: https://github.com/MetteBuyuretti/oldies-reels-worker/issues/27#issuecomment-6485720411
- Tumblr budget excerpt blob: 6b654b9a66f9a8c7f5bd05e3204218c97953c07d; verify-flow ve report sabit main d04f82f üzerinden doğrudan okundu.
- PR33 worker blob: 554421fa99c57b221a3fa6a469a7b0b9fdbbf0ca; reels_preview: 4c9886faf9d807f6d68b383bff6b7823dfa5fce2.
- PR22 worker blob: 01a12d2671246d302b47a1de13b81911d74c53cd; facebook_global_audio: 8529ee73f79b6d3097c8eabe56f2cea16480d888.

Görev ALINDI/BAŞLADI: bu Work'te kaynak inceleme ve staging kod işi fiilen yapıldı. Ayrı Windows Codex'in bu yeni işi aldığı veya başladığı doğrulanmadı. GitHub kaydı otomatik uyandırma değildir. Üretim/merge/deploy/publish/dispatch/ücretli API/yeni kurulum yapılmadı. Genel OPERASYONEL PASS ve WATCHDOG kabulü verilmedi.
