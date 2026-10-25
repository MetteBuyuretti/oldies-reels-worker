# OLDIES — mevcut onarımın uygulama devamı
**25.10.2026 | 05:52 TSİ (UTC+3)**
**Sorumlu:** WORK MASTER. **Yerel uygulayıcı:** mevcut Codex oturumu 01a170ae-7e52-7811-b95b-68849537bc0c. **Denetçi:** mevcut WORK WATCHDOG.

## Kısa özet — 25.10.2026 | 05:52 TSİ (UTC+3)
- GERÇEKLEŞEN: Kurucunun tümü çalışana kadar sonuçlandırma emri alındı. Watchdog'a bu aktif turda doğrudan ulaşıldı; incelemesi alındı: #32/6392644686, WD-DIFF-20261025-0549.
- GERÇEKLEŞEN / TEST EDİLDİ: MASTER hedef yayın günü bütçesi için saf hesaplama adayı yazdı; Node24.22.1 ile14/14regresyon geçti. Kod ve test kaynağı bu klasörde. Windows'a uygulanmadı, mevcut allPathsCovered=false korunuyor.
- BEKLEYEN: Yerel tam Verify; hedef zamanın gerçek DOM/schedule semantiği; tüm etkin otomatik yolların ortak atomik rezervasyon/kilidi; yeni içerik stoğu; Jingle10adayın kaynak eşleşmesi ve mevcut handoff doğrulayıcısı.
- PLANLANAN: Aynı Codex aşağıdaki sırayla mevcut işi sürdürmeli; eski düzeltmeleri yeniden kurma yok. Entegrasyon ve gerçek kullanım kabulü ayrı.
- ERİŞİM: Watchdog doğrudan bildirimi aldı. Yerel Codex için bu yeni talimatın alınması henüz teyit edilmedi; GitHub kaydı yerel oturumu kendiliğinden başlatmaz.

## Uygulanacak sıra — 25.10.2026 | 05:52 TSİ (UTC+3)

### 1. Tumblr: kurulu sürümün Verify sonucunu tamamla
Kurulu publisher SHA2563e0913ac6cc9ce637109f05f870133ecb6a475ada44e47046adc06477e88ffe7 ile son güvenli yedek/ledger kimliğini doğrula. Önce kaynaktaki Verify erken çıkışının enqueue/üretim dalına girmediğini göster; sonra mevcut yetki içindeki Verify'ı çalıştır. Verify ledger uzlaştırması yazabildiği için “hiç yazmayan” deme. Komut, parametre, tam log, ledgerpre/posthash, üç gerçek permalink ve güncel envanteri dar kanıt olarak teslim et. Eski hata/yeşil raporu elle değiştirme. İzin veyaCDPkısıtı oluşursa tam hatayı ve mevcut güvenli alternatifi bildir; güvenlik denetimini aşma.

### 2. Tumblr: yayın günü kusurunu gerçek çağrıya bağla
MASTER'ın daily-budget.mjs adayı **üretim eklentisi değildir**; mevcut dailyAdmission fonksiyonunun yeni sözleşmesini sınayan incelenebilir öneridir.
Yeni imza: dailyAdmission(inventory,journal,now,targetAt). targetAt gerçek doğrulanmış yayın/schedule zamanıdır; eksikse hata verir, bugüne varsayılmaz. Dönen day, rezervasyona yazılacak İstanbul günüdür.
Adayın14testi: yarın3dolu/bugünboş→yarına4.ret; bugün3dolu/yarınboş; İstanbul21:00UTCgeceyarısı; eksik kapsam/zaman/hedefte ret; tek postun iki yolda bir kez sayılması; manuel+queue+reservationtoplamı; geçmişbelirsizrezervasyonkoruması; iki güne çelişen kimlik; girdileri değiştirmeme.
Yerel kaynak/testfixture'larla uyarlayıp gerçek caller'ın targetAt sağladığını, reservedDay'in aynı gün olduğunu doğrula. Kuyruk DOM time değerinin yayın saati mi kuyruğa giriş saati mi olduğu kaynak/canlı salt okuma ile kanıtlanmadan kullanılmaz. Otomatik kuyruğun bilinmeyen geleceğini tahminle günlere dağıtma.

### 3. Tumblr: bütün yolları tek bütçeye bağla
Yalnız mevcut hesaba yayın/kuyruk yazabilen etkin launcher/controller/legacy/API girişlerinin ilgili fonksiyonlarını çıkar. Aynı kilit içinde envanteryenileme→hedefgünbütçe→atomikrezervasyon→işlem→gerçekIDuzlaştırması yürüsün. İki farklı giriş son kontenjanı birlikte alamamalı. Kullanılmayan yol için mevcut kapalı/çağrılmıyor kanıtı yeterli.
Manuel dış yazım ortak rezervasyona giremiyorsa bütün insan eylemlerinin her zaman kilitlendiği iddia edilmez. Mevcut3/gün sınırına uygun, otomasyonun tek yazıcı olduğu açık işletim penceresi ve pencere başı platform kontrolü taslağını sun; insan izinlerini veya görevleri kendiliğinden değiştirme.
allPathsCovered elle true yapılmaz; kanıtla türetilir. Entegrasyon/kapsam doğrulanmadan yeni gönderi yok. Ledger eski yedeğe dönmez.
Ayrıca onaylı eski3hikâyenin stok0olduğunu koru: mevcut11taslaktan kullanılacak içerik varsa doğruluk/görsel/sitefooter/QCile tek tek hazırla; hassas/asılsız vefat iddiasını otomatik kuyruğa koyma. Yeni içerik hazırlığı ile yayın yetkisi ayrı kaydedilir.

### 4. Jingle: mevcut dosyayla ilerle
Mevcut10MP3 ve mevcut19Ekimtrack/indirme metadata/receipt arasında dar kaynak eşleştirmesi yap. Yeniden geniş envanter tarama veya tüm MP3'leri dışarı yükleme yok. Gerçek kimlik+hash+mevcutmakbuz bağını göster; ad/tarih/sesbenzerliği yeterli değil.
Mevcut web_music_handoff içindeki kimlik/receipt doğrulama ve importer çağrı bölümlerini incele. Mevcut üretimsiz doğrulama varsa onu kullan; eksikse yalnız izinli workspace'te üretici çağırmayan/canonicalstate'e yazmayan validator adayı ve fixture hazırla. Eksik provenans UNRESOLVED döndürsün; hazırlık manifesti gerçek receipt yerine geçmesin.
Eski18Ekimslot/claimi19Ekimdosyasıyla doldurma. Çalışanvenv/kurulu4yamayı yeniden kurma. Yeni Gemini submit, yeni maliyet,claimreset,zamanlayıcı ve ertelenmişpilot/E2E başlatma bu talimatla yetkilendirilmiyor. Dosya bulma ve bağlantı hazırlığı için “pilot erteli” genel durdurma gerekçesi değildir.

### 5. Kabul ve kontrol
Tumblr kapanışı: kurulu sürümde doğru Verify; bütün-yol/gelecek-gün/iki-yazıcıyarışı negatif testleri; onaylı içeriğin mevcut yetkiyle tek gerçek platform kaydı ve sonraki doğal koşu. Jingle kapanışı: kimlikli kaynak→gerçekDJMASTER kalite/dinleme ve izinli doğal üretim kabulü. Yalnız test logu kapanış değildir.
İlk teslim, bu aktif yerel turdaki Verify veya tam bir somut engel + hedefli kaynak parçaları olmalı; doğal koşunun saatini beklemek diğer güvenli düzeltmeleri durdurmaz.
Bu Work'ten yerel Codex'i uyandırma kanalı yok. Görev alma teyidi olmadan “bu yeni devam başladı” deme. MASTER doğrudan Watchdog yanıtını almış ve kendi14test adayını üretmiştir; yerel entegrasyon henüz yapılmamıştır.
