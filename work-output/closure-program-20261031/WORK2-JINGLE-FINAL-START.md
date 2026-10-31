# WORK2 — Jingle Factory'yi gerçek çıktı ve günlük işleyişe tamamla
**Düzenleme: 01.11.2026 | 01:26 TSİ (UTC+3)**  
**İş:** WORK2-JINGLE-FINAL-20261101-01  
**Sorumlu:** Harici Work2. **Yönetim/kabul:** MASTER; bağımsız inceleme mevcut WATCHDOG.  
**Durum:** HAZIR — Work2 alımı/başlangıcı henüz yok. Codex'e yeni iş verilmez.

## Hedef ve dayanak
Kurucunun bu sohbet mesajı: “Şu Jingle Factory'yi artık tamamla bitsin… Codex'i artık yüklenmeyelim, limitimiz bitiyor… Work2'ye ver.”
Hedef yeni bir analiz veya test paketi değil: mevcut Gemini müzik üretimi → gerçek indirme → doğrulanmış handoff → mevcut onaylı DJ anonsuyla V3.1 miks → dinlenebilir DJ MASTER → günlük otomatik çalışma zincirinin tamamlanmasıdır. Kurucunun bu açık tamamlama talebini güncel işin yetki dayanağı olarak kaydet; eski “hiçbir üretim yapılmaz” hazırlık sınırında tekrar bekleme. Yeni ödeme/abonelik veya ayrıca ücret doğuran API kullanımı yetkisi verilmiş değildir. Kod ve güvenlik kapılarını atlatma.

## Önce erişim ve tek uygulayıcı
- Kurucu onaylı V3.0: work-output/master-work2-intake-20261031/FOUNDER-APPROVED-CONSTITUTION-V3.0.txt; AGENTS.md ve control-center/work-state.json.
- Work2 önce mevcut Windows bağlantısıyla gerçek dar erişim makbuzu al: Factory proje kimliği, ilgili süreçler ve görevlerin durumu. Mevcut Remote Desktop Commander genel komut/dosya bağlantısı veya gerçekten geniş araçları etkin Oldies Commander kullanılabilir. Mevcut dar Oldies Commander'ın yedi Tumblr/staging aracı Jingle komutu çalıştıramaz; bunu yeterli sanma. Harici Work2'nin bağlantısını bu kayıt tek başına kanıtlamaz.
- Mevcut ücret/kota içindeki bağlantıları kullan; yeni ücretli servis açma. Windows komut erişimi yoksa tek gerçek denemeden sonra eksik bağlantı katmanını açıkça bildir; GitHub raporunu Windows işlemi sayma. Aynı erişim engelini genel Commander'ı yeniden tasarlayarak çözmeye çalışma.
- Windows Jingle işi bu göreve geçer; Codex aynı dosyalara paralel yazmaz. Commander 07 ve Tumblr bu görevde değiştirilmez. Merkez state yazarı MASTER kalır; Work2 çıktı/#32 üzerinden teslim eder.

## Başlangıç — yapılmışı tekrarlama
Proje: C:\Users\METE\Oldies-Jingle-Factory.
Son sabit teslim: [68d2a2db RESULT](https://github.com/MetteBuyuretti/oldies-reels-worker/blob/68d2a2db8abe017bb8676418055702afd8f2bbed/work-output/jingle-tumblr-apply-20261101/RESULT.md).
Canonical scripts/Run-Factory.ps1 SHA256: 21a6c0ea568a3fad76e7e33a843204f41eb7054d28cdca9a3fa7b8d84b5cc2f4.
STAGE manifest SHA256: 8520b954029103e4259c16175a698da903125f1ef6d5b2cb9f63191c2a8005e1.
İkisi KURULU, gerçek candidate.verify PASS; yedek ve çift geri dönüş mevcut. Bunları tekrar yazma/test paketi diye sunma. Üç Jingle görevi kapalı.
Son bilinen activation/daily pencere 18 Ekim'e bağlı, factory_provider_calls_authorized=false; 01 Kasım işi/gerçek handoff/final çıktı yok. Eski 18 Ekim claim/receipt'i silme, yeniden tarihleme veya yeni işe kopyalama.
V3.1'in daha önce kabul edilmiş 14.18 saniyelik manuel DJ+müzik referansı ve özgün anons girdileri korunacak.

## Tek görevde sırasıyla bitir
1. **Güncel üretim girdilerini tamamla.** Mevcut gerçek giriş/producer/importer şemasını oku. Bu iş için benzersiz kimlik, gerçek tarih/saat, desteklenen slot, bağlı mevcut prompt, kullanılan hesap/yol ve yalnız gerekli activation alanlarını güncel kurucu talebine bağlayarak oluştur. Hazırlanacak bir iş tanımını geçmişte gerçekleşmiş provider receipt'i gibi gösterme. Yeni tarih girişi yazılabilir; eski claim'e dokunulmaz. Sonraki günlük hedef mevcut 19:00 Europe/Istanbul planıdır; saat gelmeden geçmiş/gelecek slot kontrolünü kandırma. İlk deneme mevcut desteklenen manuel/doğrulama yolu üzerinden gerçek başlangıç saatiyle yapılır; kaynak böyle bir yol sağlamıyorsa en küçük açık ve geri alınabilir uyarlamayı yap, gizli bypass ekleme.
2. **Gerçek Gemini müziğini üret ve indir.** Önce mevcut STAGE producer/Gemini web akışını, mevcut oturum ve onaylı prompt/rotasyonla kullan. Gemini sohbetindeki bir yanıtı veya kaynakta duran promptu üretim başarısı sayma. Mevcut aboneliğe dahil yol önceliklidir; ücretli API'ye sessizce geçme. Tek iş için kontrollü bir ilk üretim; belirsiz indirme/sonuçta yeni üretime basmadan job durumunu uzlaştır. Gerçek dosya bytes, decode/süre, kaynak-job eşlemesi ve SHA256 kaydı gerekir. Sahte ses veya sentetik test verisiyle gerçek üretim kabulü verme.
3. **Mevcut aktarım ve miks zincirini çalıştır.** Gerçek producer job/status/raw çıktısını mevcut importer'a ver; aynı gün/slot/job/hash bağlı gerçek handoff ve receipt'i oluştur. Yeni miks mimarisi kurma. Kurulu launcher'ın MusicHandoff iletimini kullanarak canonical Factory'yi mevcut V3.1 ayarları ve hash'i doğrulanmış onaylı anonsla çalıştır. Eksik arşiv girdisini kullanıcıya tekrar kaydettirmek yerine önce yereldeki bilinen onaylı kaynağı bul. Karşılaştığın kusuru zincirin o adımında dar düzelt; yedek/hash/geri dönüşü koru. İki başarısız aynı yöntemin ardından yeni kanıtla yöntem değiştir; sonsuz tekrar veya toplu yeniden üretim yok.
4. **Dinlenebilir son dosyayı teslim et.** Final MASTER'ın gerçekten mevcut, açılır ve doğru müzik+anonsu içerdiğini doğrula. Referans ton/dengesi korunsun: enstrümantal müzik, sert başlangıç, DJ groove üzerinde, kısa fade-out ve 1.5–2 saniye müzik kuyruğu; clipping, sessizlik, kesilmiş anons ve tekrarlayan yaklaşık 11. saniye gitar kusurunu kontrol et. Önceki kabul edilmiş V3.1 miks ayarlarını sırf test için değiştirme. Süre, peak/clipping/sessizlik ölçümleri ve SHA kaydet; dinlemediysen dinledim veya insan QC geçti deme. Son ses dosyasını Work2'den erişilebilir ek/kalıcı dosya olarak sun, yalnız Windows yolu verme. Medyayı izinsiz public GitHub'a yükleme; hassas kaynak URL/anahtarları kayda çıkarma.
5. **Günlük otomatik çalışmayı tamamla.** Mevcut görev/launcher zincirini kullan; ikinci zamanlayıcı oluşturma. Yerel görev yedeği, güncel iş/rotasyon/izin penceresi, mükerrer üretim kilidi, hata/eksik dosyada durma ve sonraki 19:00 tetikleme eşleşmesini doğrula. İnsan ending incelemesi veya bağımsız kabul mevcut gerçek kodda zorunluysa o kapıyı taklit ederek açma: dinlenebilir finali ve etkinleştirilmeye hazır tam paketi önce teslim et; kalan tek insan kararı somut dosya üstünden alınsın. Geçerli kabul tamamlanınca kurucunun bu günlük tamamlama talebi kapsamında yalnız mevcut ilgili görev etkinleştirilir; alakasız scheduler/üretim/yayın açılmaz. İlk gerçek zamanlayıcı koşusu ve üç gün süreklilik, kendi zamanları gelmeden PASS sayılmaz.

## Çıkış ölçütü / teslim
- Bir gerçek yeni müzik dosyası, doğrulanmış aktarım/handoff ve anonslu dinlenebilir final; kullanılan kimlikler/dosyalar/hash ve başarısız adım varsa tam hata.
- Kurulu düzeltme, gerçek üretim, miks, dinleme/insan QC, scheduler hazır/etkin, sonraki tetikleme ve süreklilik ayrı etiketlerle.
- work-output/work2-jingle-final-20261101/RESULT.md + HANDOFF.json; özel ham dosya/yedekler yerelde, final medya erişilebilir uygun dosya kanalında.
- #32'ye gerçek ALINDI/BAŞLADI, erişim kanıtı ve alımdan itibaren ilk20dk kontrol noktası. Her doğal20dk parçada gerçek çıktı veya tek somut engel ve çözüm adımını kaydet; bekleme/aralıksız arka plan çalışması varmış gibi yazma.
- Yalnız “aday/testler geçti” diye işi kapatma. Bir erişim veya zorunlu insan kabulü eksikliği işi durdurursa bağımsız bütün hazırlanabilir parçaları bitir; eksikliği tek somut karar/girdi olarak teslim et. MASTER ve WATCHDOG kabulü otomatik var sayılmaz.
