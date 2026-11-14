# OLDIES — Genel sistem kontrolü ve WORK MASTER uygulama planı
**14.11.2026 | 10:14 TSİ — WORK WATCHDOG**
**İş:** GENERAL-CLOSURE-20261114 — PLANLANDI; MASTER alımı henüz doğrulanmadı.
**Kapsam:** Web/TR-EN haber otomasyonu, İngilizce ve Türkçe Reels, Instagram, YouTube, Tumblr/Pinterest, mevcut sistem zamanlamaları ve denetim. Antigravity ve Etsy ilan sistemi tamamen hariç. Yeni Codex işi yok.
**Kurucu isteği:** Önce denetim/plan; uygulama WORK MASTER'da. Kalan Work hakkı kurucu beyanıyla %40; iki güne dengeli yayılacak. Kota bu oturumdan ölçülmedi.

## GERÇEKLEŞEN — 14 Kasım hedefli salt-okunur kontrol
1. Anayasa V3.0 bu konuşmada tam okundu. Merkezi kayıt main SHA 02b3ed0462706dc574dd38ccb512c7081e26638a; updated_at 12 Kasım. Web görevi güncel; Jingle/Reels/sosyal görevlerinin bir kısmı 31 Ekim–1 Kasım'da kalmış. Bu eski durumlar yeni gelişmeleri reddetmek için kullanılamaz.
2. main .github/workflows/reels-worker.yml SHA c0b4a80a7ab6cd8d062425c3ce5819b988164ac9: 12:17 TSİ günlük cron tanımlı, fakat create-draft işi yalnız MANUEL preview_only=true koşulunda çalışabiliyor. Günlük üretim bu girişte karantinada. Cron varlığı çalışıyor demek değil. Başka yeni giriş olup olmadığı araştırılmadan bütün Reels üretimi durmuş denemez.
3. main .github/workflows/facebook-global-en.yml SHA d67a18ec598dc2aeee40fbbc5e07f24a41bc1ab1: 14:23 TSİ cron var; iş if:false ile tamamen kapalı. İngilizce Facebook hattı Instagram/YouTube İngilizce hattıyla aynı sayılmamalı.
4. PR22 halen OPEN/DRAFT, merged=false, mergeable=false; head 9ad08776e882af386f2897ac43e85eaeb28f029e. Eski 17s/38-test açıklaması var. Bu PR'ı doğrudan merge etmek veya eski ses onayını yeniden istemek doğru değil: sonraki kabul edilmiş sesler ve 25–30s teslim çalışmalarıyla uzlaştırılmalı.
5. Canlı WordPress oldies-facebook-global__health: Companion1.0.7-R7; worker_ready/page_configured/token_configured/github_delivery_ready=true; default_dry_run=true. Token mevcudiyeti gerçek geçerli API erişimi/yayın kanıtı değil.
6. Canlı oldies-reels__list-drafts 16 kayıt: 11 DRAFT_REVIEW, 5 READY_FOR_EDITS. En üst kayıt 15 Ekim Four Tops. Dönen kayıtlarda Instagram medya ID'si 0; YouTube success=true 1 kayıt (25 Eylül 1967 olayı, https://www.youtube.com/shorts/jQVOWWK7b5U), ancak youtube_verified_source=false. Bu, Instagram'da hiç yayın yok veya YouTube başarısız demek değildir; platform ile yerel kayıt eşleşmesinin eksik olduğunu gösterir. Platformların güncel profilleri bu taramada okunmadı.
7. #42 halen OPEN: 8 Kasım oluşturulmuş Storage Cleanup failure run42472413273. Sonraki başarılı koşu var mı bu taramada doğrulanmadı; tarihsel tek hata güncel sürekli arıza diye sunulmayacak.
8. Web #41/08-live-head-nav-fix-acceptance-20261112.md okundu: önceki operatör 17 exact301+9 EN RSS onarımını, head-nav-fix0.1.2 active, 5/5 tek description/canonical ve 10/10 çift yön Polylang eşleşmesini kaydetmiş. Bu başarılar yeniden yapılmayacak. Bu oturumda canlı HTML yeniden ölçülmedi.
9. Bekleyen web kanıtları: News Guard1.0.4 gerçek kurulu kaynak/log ve tekrar koruması; Article JSON-LD anlamsal kontrolü; iki yeni pilot; Google yeniden tarama/indeks; WATCHDOG bağımsız kabul. Birden fazla JSON-LD tek başına hata değil. Yedi meşru404 topluca yönlendirilmeyecek.
10. Tumblr/Pinterest son canlı yayınları, Windows görevleri, Jingle son dosyaları, radyo heartbeat ve yedekler bu dar taramada yeniden okunmadı. 5–13 Kasım yeni gelişmelerine eski merkezi kayıt üzerinden HATALI etiketi verilmedi.

## BEKLEYEN — MASTER'ın ilk işi: tek güncel envanter (ilk 15–20 aktif dakika)
Önce bu planı, güncel kurucu talimatlarını ve mevcut çıktılarını oku. Görev alımını #32'ye iş kimliği/TSİ/erişilen araç/ilk kontrol hedefiyle kaydet. Paralel aynı içerik üretme veya yeni altyapı kurma.
Tek tablo çıkar: kanal, aktif giriş/iş kimliği, son gerçek başarılı çıktı URL+TSİ, son doğal koşu, sonraki koşu, içerik stoku, otomatik/manuel, somut engel.
- GitHub son koşu sonuçları + ilgili tek başarısız job logu. SKIPPED/0-step = başarılı üretim değildir.
- Instagram ve YouTube son 3 gerçek içerik; dil, gerçek ses, kaynak film, URL/ID ile WordPress kayıt eşlemesi. Yükleme ile yayın, TR ile EN ayrılacak. Hesap erişimi yoksa tek açık engel olarak kaydet.
- Tumblr son3 yayın ve stok; Pinterest son3 pin, ileri takvim, Trial/Standard Access güncel başvuru durumu. Etsy ilan üretimine girme; mevcut onaylı Pin kaynaklarıyla sınırlı kal.
- Web en yeni 3 TR/EN haber çifti, gerçek HTML, görsel/ALT, canonical/hreflang, sitemap ve son Guard koşusu.
- Windows yalnız ilgili mevcut görevlerin son/sonraki koşusu, hata sonucu ve boş kuyrukta davranışı. Jingle son kabul edilmiş dosyasını ve gerçek üretim kaydını bul; yeni üretim başlatma.
Envanterden sonra en etkili en fazla iki somut engeli düzelt; tüm projeleri aynı anda açma.

## PLANLANAN — öncelikli uygulama ve kabul
| Sıra | Sorumlu | Somut iş | Kabul/koruma |
|---|---|---|---|
| P0 | WORK MASTER | Aktif Reels girişini ve karantina nedenini güncel teslimlerle uzlaştır; EN hattındaki ilk gerçek kopuşu bul. | Mevcut onaylı sesleri koru. Bir EN filmde anlamlı özgün anlatım, olay/dönem/görsel hakları, dil ve gerçek ses QC'si; ilgili güncel kabul süresi. TR25–30s kuralını FB'ye kanıtsız aynen taşıma. |
| P0 | WORK MASTER | Instagram → doğru final film → YouTube aktarım kimliğini eşle; website trafik bağlantısını kontrol et. | En az bir son gerçek içerikte platform ID+URL+zaman+doğru dil/final kaynak. Onaylı Instagram müzik kullanım hakkının YouTube'a geçtiğini varsayma. Yeni yayın için mevcut kapsamı doğrula. |
| P1 | WORK MASTER | Web #41 kalan dar eksikleri kapat; en yeni3 çiftte otomasyon davranışını kontrol et. | İki yetkili staging/draft pilotunda tekrar çağrıda mükerrer yazı yok, TR/EN eşleşme ve görsel/ALT/SEO çıktısı doğru. Google indeks beklemesi teknik işi sonsuza dek açık tutmasın; ayrı izleme kaydı. |
| P1 | WORK MASTER | Tumblr/Pinterest stok→hazırlık→zamanlama→gerçek yayın zincirini güncel olarak doğrula, bulunan en küçük kopuşu onar. | Tumblr3/gün; Pinterest2/gün doğrulanmış temel hedef, yeni artış yok. Renkli konuya uygun hakları belli görsel, ALT, ilgili gerçek site yazısına CTA. Kuyruk bitmeden stok yenileme; yalnız manuel doldurma süreklilik sayılmaz. |
| P1 | WORK MASTER | #42 cleanup son durum ve yalnız ilgili log; boş işte terminal açılması/tekrar tetikleme ve alarm mekanizmasını kontrol et. | Kopya/silinme riski anlaşılmadan retry/silme yok. Toplu görev kapatma yok. Boş kuyruk üretim/ücretli çağrı açmamalı; var olan beş deneme kuralı görev bazında korunmalı. |
| P2 | WORK MASTER | Jingle/radyo ve geri dönüş kontrolünü mevcut çıktıdan güncelle. | Son dosya/çalışan giriş/geri dönüş yolu kaydı; yeni render, kurulum veya yayın yok. Acil gerçek arıza çıkarsa gerekçeli öncelik değiştir. |

## İki gün ve Work bütçesi
Bunlar kesin platform ölçümü değil, harcama önceliğidir. Kurucunun toplam kotasındaki kalan40 yüzde puanının yaklaşık 32'sini kullan; 8'ini acil durum ve bağımsız kabul için bırak.
- Ortak envanter ve bu önkontrol dahil4 puan.
- Reels/Instagram/YouTube12 puan.
- Web8 puan.
- Tumblr/Pinterest6 puan.
- Sistem/cleanup2 puan.
- Rezerv8 puan.
14 Kasım: envanter, en etkili iki engel, geri dönüş ve ilk somut çıktı. 15 Kasım: sonraki doğal koşu/gerçek platform sonucu ve dar regresyon; yeni proje açma.
10–20 dakikalık çalışma birimi sonunda bir checkpoint; her tıklamayı raporlama. Beklerken Work oturumunu açık tutma. Planlanan sonraki doğal koşuyu kaydet; sürekli polling ve aynı kaynağı tekrar okuma yok.
Bir erişim hatası için en fazla iki hedefli deneme, sonra mevcut yetkili alternatif veya somut engel. Bu, Gemini'nin geçici üretim retleri için onaylı beş deneme kuralını değiştirmez.
Mevcut kod/test/kabulü tekrar oluşturma. Ücretli GSC yenilemesi, yeni servis/API maliyeti, yeni zamanlama veya kritik canlı açılış bu planla otomatik onaylanmış değildir.

## Teslim ve denetim
Her düzeltilen engelde: önceki kanıt → değişiklik/sürüm → hedefli test → gerçek sonuç → sonraki doğal kontrol → geri dönüş. MASTER uygulama sahibi, WATCHDOG bağımsız inceleme sahibi.
İlk kontrol: MASTER'ın gerçek alımından15–20 dakika sonra envanter+tek seçilmiş engel; ikinci kontrol ilgili birim sonunda somut değişiklik/çıktı veya açık engel.
Merkezi kaydı yeni kanıtla güncelle; Ekim verilerini güncel başarı gibi taşıma. Kapanışta en fazla5 maddelik GERÇEKLEŞEN/BEKLEYEN/PLANLANAN özeti ve kanıt bağlantıları.
Bu dosyanın yazılması MASTER oturumunu uyandırmaz. ALINDI/BAŞLADI makbuzu görülmeden uygulama başladı denmez.

## Dayanaklar
- https://github.com/MetteBuyuretti/oldies-reels-worker/blob/main/control-center/work-state.json
- https://github.com/MetteBuyuretti/oldies-reels-worker/blob/main/.github/workflows/reels-worker.yml
- https://github.com/MetteBuyuretti/oldies-reels-worker/blob/main/.github/workflows/facebook-global-en.yml
- https://github.com/MetteBuyuretti/oldies-reels-worker/pull/22
- https://github.com/MetteBuyuretti/oldies-reels-worker/issues/31
- https://github.com/MetteBuyuretti/oldies-reels-worker/issues/42
- https://github.com/MetteBuyuretti/oldies-reels-worker/blob/main/work-output/oldies-news-seo-bilingual-20261105/08-live-head-nav-fix-acceptance-20261112.md
- WordPress canlı read-only ability sonuçları: oldies-facebook-global__health; oldies-reels__list-drafts (14 Kasım10:11–10:14 TSİ kontrol penceresi; dosya düzenleme saati üsttedir).
