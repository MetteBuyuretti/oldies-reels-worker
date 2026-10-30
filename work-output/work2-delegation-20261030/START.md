# WORK2 — OLDIES Reels kod ve entegrasyon görevi
30.10.2026 | 03:38 TSİ (UTC+3)
İş kimliği: WORK2-REELS-INTEGRATION-20261030-01
Operasyon sahibi ve teslimi devralacak kişi: mevcut WORK MASTER.
Planlanan uygulayıcı: kurucunun açacağı mevcut Work2 sohbeti. Bu dosyanın hazırlanması Work2'nin görevi aldığı/başladığı anlamına gelmez.
Bağımsız denetçi: mevcut WORK WATCHDOG. Yerel Windows/Jingle uygulayıcısı: mevcut Windows Codex.

## Amaç ve ilk teslim
İngilizce Facebook Reels hattının, önceden kabul edilmiş sakin/enerjik kapanışları doğru seçip gerçekten tüketmesini sağlayan en küçük kod farkını ve anlamlı üretimsiz testini hazırla. Ardından aynı adayda25–30s/doğal süre/kalite kapılarındaki somut uyumsuzluğu ele al. Sadece analiz raporuyla bitirme: kaynak buna elveriyorsa kullanılan çağrı yoluna bağlı dar kod ve test teslim et. Gerçek Windows giriş makbuzu veya medya gerekiyorsa eksik parçayı açık ayır; çevrimdışı yapılabilir kod/test işini bunun yüzünden bekletme.

## Başlangıç ve iletişim
1. GitHub MetteBuyuretti/oldies-reels-worker main üzerindeki AGENTS.md ve control-center/work-state.json dosyalarını oku. Bu talimatı ve yalnız ilgili mevcut çıktıları esas al.
2. İlk gerçek okumada #32'ye “WORK2 ALINDI / BAŞLADI — WORK2-REELS-INTEGRATION-20261030-01” yaz; gerçek TSİ, erişebildiğin araçlar, seçtiğin ref/branch ve ilk10–20dakikalık parçanın gerçekçi kontrol saatini belirt. Erişim yoksa yalnız gerçek eksik yeteneği BLOCKED olarak bildir; başlamış gibi yazma.
3. Sonuçları ve ara checkpoint'leri doğrudan #32'ye ve kendi dalındaki work-output/work2-reels-integration-20261030/ klasörüne yaz. Kullanıcıdan rapor taşımasını isteme. MASTER sonraki aktif okumada buradan devralacak; kayıt başka sohbeti otomatik uyandırmaz.
4. Doğal parçalarda ilerle; kesintide son güvenli checkpoint'ten devam et. Beş saatlik kullanım penceresinin yeniden başlayacağını veya başka sohbetin kotasını bu sohbetten bildiğini varsayma.

## Korunacak kazanımlar
- Commander bağımsız gerçek Work kabulü DONE: #32/6511801783,30Ekim03:25. Mevcut7araç; yeni6proje aracı yalnız3pinnedTumblrkaynağı/3stagingadı/sabitparser. Kurulum/anahtar/refresh/kabul testini tekrarlama. Bu araçlar Jingle/Reels kökü veya genel shell erişimi sağlamaz.
- Tumblr guard/launcher düzeltmesi kabul edildi ve kurulu. Bu görevde yeniden kurma.
- Jingle V3.1 onaylı manuel DJ+müzik referansı korunuyor; J2download→raw→handoff/adapter onarımı mevcut Windows Codex'in işidir. Jingle/Commander kaynaklarına veya Windows staging alanına yazma.
- Reels'in kabul edilmiş iki varlığının kimliği bağımsız kabul edildi. Yeniden üretim, aynı dosyalar için dinleme onayı veya geniş arama yok. Bunlar yalnız istasyon KAPANIŞLARI; bütün haber hikâyesi sesi ya da final film değildir.
- Kullanıcı hedefi25–30s, kaynakla doğrulanmış olaya özgü doğal DJ hikâyesi, gerçek doğru dönem/sanatçı fotoğraflarıdır. PR22'nin eski17spilotu veya18s/17.4s sabitleri bugünkü genel kalite kabulü değildir.59sformat veya bütün kanallara toplu süre değişikliği uygulama.

## Kesin ses kimlikleri
| Profil | Bilinen kaynak | Bytes/süre | SHA256 |
|---|---|---|---|
| calm | PR22 assets/facebook/en-warm-signoff-radyo-v3.mp3 |26880 /6.720s|1dc358ef0cea5a3a6d9fe20d9934358fed5ccd0009ba0838a60bba9f28bb9d9c|
| energetic | Mevcut Oldies-Radyo-DJ-Energetic-Preview.mp3; özgün kayıt Librarylibfile_9aa7cad7f33881918c27603206b19a44 |21120 /5.280s|a2df71619290530249fbacbc02c546caceeecaf3c05d265bd8321ebfeefb4ac8|

İkisi24kHz/mono; önceki gerçek bytes/hash/ffprobe/decode doğrulaması kapalı.1.25xkarşılaştırma kabul edilmiş energetic değildir.
Onay kaynağı: OLDIES_WATCHDOG_INGILIZCE_REELS_SES_RAPORU_20261026_0506.md (Librarylibfile_a3a2acadd7148191b747aa665130c310).
Makinece okunur kimlik ve sınır:
https://github.com/MetteBuyuretti/oldies-reels-worker/blob/e1c87bd0616ca763a2362282ff4d878aab3f02f4/work-output/local-exec-20261029/review/reels-signoff-identities.json
Bağımsız kabul:
https://github.com/MetteBuyuretti/oldies-reels-worker/issues/32#issuecomment-6509320201
Repo public; yeni ham ses/özel kaynak/credential yükleme. Enerjik varlığın gerçek Windows kopyası için yerel Codex eşlemesi hâlâ ayrı girdidir. Onay kaydını kullan; approver/tarih uydurma veya yayın/final-media onay bayraklarını otomatik açma.

## Dal ve dosya sahipliği
- İlk okumada PR22'nin güncel head'ini doğrula.03:34kontrolünde OPEN/DRAFT/unmerged ve9ad08776e882af386f2897ac43e85eaeb28f029e idi.
- Facebook aday kodu için bu sabitPR22ref'inden ayrı work2/reels-integration-20261030 dalı kullan; aynı isim mevcutsa sahibini ve son checkpoint'i kontrol et, kör reset/overwrite yapma.
- facebook_global_audio.py, ilgili Facebook template/consumer ve gerçekten gerekli odaklı testler yalnız kendi dalında değişebilir. Güncel main ve PR33'ü karşılaştırma girdisi olarak oku; PR22/PR33/main/PR35 üzerinde doğrudan kod değişikliği yapma.
- Uygunsa kendi dalından mevcut PR22dalına karşı DRAFT PR aç; bağımlılığı açık yaz. Bu, PR22'nin main'e alınması veya çalışır Windows sürümü değildir.
- Merkezi main work-state.json'un koordinasyonu MASTER'dadır. AGENTS checkpoint gereğini kendi dalındaki kendi görev kaydın ve çıktılarınla karşıla; başkalarının kayıtlarını silme. Aynı dosyaya ikinci uygulayıcı yönlendirilmedi.

## Paket R1 — kabul edilmiş dosyanın gerçek tüketimi
Önce main/PR22/PR33 için workflow/giriş/ref→worker→ses tüketim yolunu kısa tabloda ayır. PR33 preview local_voiceover tüketir; synthesize_google_voice aynı preview yolu değildir. GitHub'da görülen giriş ile bilinmeyen Windows aktif girişini karıştırma.

PR22/9ad içindeki facebook_global_audio.py doğrudan incelendi: validate_template tek warm path'i kilitliyor; require_approved_signoff tek hash/meta kullanıyor; synthesize_dj cache şartı sağlanmazsa preview'da advert üretimine gidebiliyor. Bu gözlemi kaynakta doğrula; başka sürüme varsayma.

Seçilen gerçek aday consumer üzerinde calm/energetic seçimi→dosya/hash/onay kanıtı→gerçek tüketim→dj_recording metadata bağını kuran en küçük farkı hazırla. Çağrılmayan bağımsız yeni yardımcı üretip işi bitmiş sayma. Üretim/onay kapıları korunsun; eksik/değişmiş dosya veya bilinmeyen profil fail closed olsun. Aynı kabul edilmiş kapanış sessizce yeniden TTS'e düşmesin. İki kapanışın kabulü tam hikâye/MP4 kabulü olarak işaretlenmesin.

Gerçek API/provider/Windows dosyasına dokunmayan fixture ve stub'larla anlamlı regresyon göster: seçilen profil doğru dosya/kimlikle tüketiliyor; yanlış hash/eksik dosya/bilinmeyen profil veya yanlış recording bağı reddediliyor; kabul edilmiş cached kapanış yeniden üretilmiyor. Onay metadata'sı eksikse sahte kişi/tarih üretme; var olan kanıt referansı ile gerçekten eksik alanı ayrı teslim et.

## Paket R2 —25–30s ve doğal süre kapısı
R1'i kendi başına checkpoint'le, sonra süre işine geç. Eski18s/17.4s/25kelime varsayımının25–30shedefiyle çeliştiği kullanılan Facebook consumer/render/gate noktalarını belirle. Yalnız aynı Facebook adayında doğal hikâye süresi + seçilmiş kapanışın gerçek süresi + mevcut ayrım aralığıyla tutarlı, metni/finali hızlandırmayan en küçük kod farkını hazırla. TRpreview veya diğer kanalları değiştirme; eski çıktıyı kabul edildi diye yeniden etiketleme.

Var olan görsel kimlik/lisans/dönem, gerçek fotoğraf, tam kadraj ve bağımsız medya kabul kapıları korunur. Tek global sabit değiştirip bütün akışı düzelmiş sayma. Süre/recording/render kapısı uyumu anlamlı çevrimdışı testlerle gösterilsin; gerçek25–30sMP4/yaratıcı kabul ve Windows uygulaması henüz yapılmadı diye ayrı raporlansın. Kod yolu için gerekli kanıt yoksa bir somut eksik girdi belirt; tahminle başka sürüme yama yapma.

## Yetki ve sınırlar
Mevcut üretimsiz kod/diff/test ve draftPR işi. Merge/deploy, canlı scheduler/yayın, yeni ücretli API/TTS/provider, yeni gerçek ses/MP4, indirme/import/miks, claim/lock reset, genel Commander kapsamı veya anahtar/hesap ayarı yok. Testlerin stub/fixture olduğu açık olsun. Tam kurulu özel config/env/ham ses dışa aktarılmaz. Eski başarılı testleri yeni test sayısına ekleme; yalnız değişikliğin etkilediği anlamlı kontrolleri çalıştır. Başka uygulayıcının dosya değişikliğini görürsen preimage/ref ile uzlaştır.

## Teslim biçimi — MASTER'ın tek yerden devralması
Kendi dalında:
- RESULT.md: problem→son davranış, yapılan kod farkı, gerçek test komutu/ortam/sonuç, kapsam ve kalan tek sonraki girdi.
- HANDOFF.json: job_id, actor, received_at_TSI, base_ref, branch, head_commit, changed_files, tested_commands/results, limits, remaining_blocker, next_step.
- Gereken gizlisiz diff/test kaydı; test edilmemiş bölümü PASS sayma.

#32'ye aynı iş kimliğiyle kısa teslim + sabit commit/PR/RESULT bağlantısı yaz. Hazır/alındı/başladı/teslim/test/uygulama/kabul ayrı olsun. En az R1somut kod+test teslimi ver; R2bloklanırsa R1'i bekletme. MASTER bu kayıtları doğrudan okuyup sürüm/hash/kod/test tutarlılığını denetleyecek ve gereken yerel uygulama parçasını mevcut Windows Codex'e devredecek. Otomatik sohbet tetikleme veya arka planda sürekli çalışma iddiası yok.
