# OLDIES — Tumblr ve Jingle çözüm planı
**25.10.2026 | 00:19 TSİ (UTC+3)**  
**Operasyon sahibi:** WORK MASTER. **Bağımsız denetçi:** mevcut WORK WATCHDOG.  
**Durum:** PLANLANDI; Tumblr uygulaması erişim nedeniyle BEKLEYEN. Jingle analiz teslimi tamam, üretim teyidi erteli.

## Kısa özet — 25.10.2026 | 00:19 TSİ
- GERÇEKLEŞEN: Onaylı V3.0, merkezi durum, önceki ayrıntılı inceleme ve #32'nin son kayıtları yeniden okundu. Güncel kod yaması veya yeni üretim kanıtı yok.
- PLANLANAN: Önce mevcut yetkili yerel Codex'e erişim ve görev alma teyidi; sonra Tumblr'ın güncel hatasına dar düzeltme. 22 Ekim'deki çalışan onarım korunacak.
- PLANLANAN: Jingle'da son çalışan sürüm ve mevcut 19 Ekim track/MP3/Factory zinciri eşlenecek; ilk kopan aşama belirlenecek. Yeni müzik üretilmeyecek.
- BEKLEYEN: Yerel kaynak/komut erişimi. Uygulayıcı görevi almadı; uygulama başlamış sayılmıyor.
- KABUL: Somut değişiklik, hedefli test, gerçek sonuç ve izleyen zamanlı çalışmanın bağımsız kontrolü. Önceki rapor/test sayıları onarım kabulü değil.

## Ayrıntılı plan — 25.10.2026 | 00:19 TSİ

### 1. Ön koşul: mevcut yerel uygulayıcıya erişim
Mevcut Work oturumu Windows'taki kaynakları okuyup değiştirebilen yerel Codex komut kanalına sahip değil. GitHub'da kayıt okumak veya Watchdog'a mesaj göndermek bu yeteneği sağlamıyor. Önceki GitHub ve 260 ZIP metadata araması kaynak paketini bulamadı; yeni kanıt olmadan aynı arama turu tekrarlanmayacak. Kotası dolan Remote Commander yeniden denenmeyecek.

Uygulama için bilgisayardaki mevcut, yetkili Codex oturumuna erişim gerekiyor. Görev alma teyidiyle birlikte güncel dosya yolu/sürüm/hash ve okunabilir hata kaydı ortak kanıta bağlanacak. Kaynaklar yetkili mevcut bir dışa aktarımda erişilebilir olursa MASTER statik yama hazırlayabilir; Windows'a uygulama ayrıca gerçek yerel erişim gerektirir. Yeni kurulum veya izin genişletme bu planın parçası değil.

**Sorumlu:** MASTER. **Teknik uygulayıcı adayı:** mevcut yerel Codex; görev alma ve erişim teyidi bekliyor.  
**Kontrol noktası:** herhangi bir kod değişikliğinden önce. Sonraki aktif kontrol yeni erişim/kaynak kanıtı geldiğinde; takvimli veya arka planda takip kurulmuş değil. Erişim sağlanmadan bitiş saati verilemez.

### 2. Öncelik: Tumblr'ı dar onarımla geri döndürmek
Son doğrudan hesap gözlemi 24 Ekim 17:50'de 23 yayın/11 taslak/0 kuyruktur; 25 Ekim canlı sayımı değildir. Boş kuyruk tek başına kök neden değildir.

İlk kaynak paketi: `run_tumblr_auto.ps1`, `tumblr_auto_news_v3.mjs`, `tumblr_editorial_control_v4.mjs`, ilgili ledger, aynı koşunun tam hata raporu ve 22 Ekim yedek kimliği. 23 Ekim 02:28 yayınsız testteki reconciliation hatası güncel kaynakla eşlenecek; satır numarasından hata türü uydurulmayacak.

Uygulama sırası:
1. Güncel sürümü ve yedeği doğrula; 22 Ekim launcher/timeout/güncel sonuç düzeltmelerinin korunmasını kontrol et.
2. Hatalı ifade ile giriş kaydını eşleştir; yalnız kanıtlanan kusuru düzelt.
3. Önce yayımlamayan örnek kayıtlarla özgün hata, aynı postun tekrar eşleştirilmesi, belirsiz yayın cevabı, eşzamanlılık ve İstanbul gece yarısı sınırını kontrol et.
4. Gerçek diff ve sonuçları WATCHDOG'a sun; mevcut yetki sınırları içindeki gerçek çalışma sonucunu ayrı doğrula.

**Korunacaklar:** tüm yayın yollarında İstanbul takvim günü başına birleşik 3 sınırı; gerçek postID/permalink ile eşleştirme; belirsiz işlemi yeniden yayımlamama. Kod/config geri alınabilir; ledger eski yedeğe kör döndürülemez. Mevcut 11 taslak topluca kuyruğa alınmayacak.

**Kapanış:** kaynak/QA'sı doğrulanmış işin tek gerçek platform kaydıyla doğru eşleşmesi, güncel raporun doğru sonucu vermesi, günlük limitin korunması ve izleyen doğal koşuda aynı davranış. Bu adımlar henüz uygulanmadı.

### 3. Ardından Jingle: mevcut çıktının zincirini tamamlamak
Önce son kabul edilmiş otomatik DJ MASTER'ın run/sürümü bulunacak; 19 Ekim'de kullanıcı tarafından görülen track'in mevcut MP3 ve Factory girdisiyle ilişkisi kontrol edilecek. Güncel fiziksel dosya okunmadan “MP3 yok” veya “tek sorun Gemini” sonucu çıkarılmayacak.

Ayrı kontrol alanları: sağlayıcıda iş sonucu; dosyanın indirilip teslimi; Factory durum/API 6–7 mutabakatı ve ses QC; müzikten DJ'li MASTER'a gerçek çağrı zinciri. Önceki staging yamalarının canlı sürüme uygulanmış olduğu varsayılmayacak. Son çalışan sürümle fark bulunup ilk kopan aşamaya müdahale önerilecek.

Mevcut MP3/WAV, claim/lock ve işlem geçmişi korunur. V3.1 −4.0 dB ve DJ sonrası temiz kapanış sabittir. Pilot teyidi erteli olduğundan bu plan yeni submit, indirme, miks, TTS/API, render veya zamanlayıcı başlatmaz. Üretim adımı mevcut erteleme kaldırıldığında kendi yetkisiyle yürütülür.

**Kapanış ölçütü:** kimliği doğrulanmış DJ'li MASTER dosyası, dosya/süre/teknik inceleme ve tam dinleme; ardından ayrı zamanlı uçtan uca çalışma ve bağımsız kabul. Sadece ham müzik veya CAPCUT_READY sonucu yeterli değil.

### 4. Yönetim ve Watchdog
MASTER sorumluluğu sürdürür. WATCHDOG mevcut dar yaklaşımı incelemiş, 24 Ekim 18:46'da şartlarını teslim etmiş ve MASTER 18:50'de yanıtlamıştır. Bu tur yeni denetim görevi gönderilmedi veya yeni kabul alınmadı. Uygulama sonrası kaynak diff'i, test sonuçları ve gerçek çıktı kanıtı yeni incelemeye sunulacak. Ortak kayıt otomatik Codex/Watchdog uyandırması sayılmaz.

**Risk:** erişim açığını çözmeden talimatı tekrar etmek onarımı ilerletmez; gerçek uygulayıcı ve kaynak teyidi birinci kapıdır. Yeni altyapı veya ek maliyet önerilmedi.

## Dayanak
- [Önceki ayrıntılı inceleme](https://github.com/MetteBuyuretti/oldies-reels-worker/blob/main/work-output/work-master-system-takeover-20261024/part-007.md)
- [Watchdog'un kaynak, günlük limit ve geri dönüş şartları](https://github.com/MetteBuyuretti/oldies-reels-worker/issues/32#issuecomment-6386220827)
- [MASTER'ın doğrudan okuma ve yanıt teyidi](https://github.com/MetteBuyuretti/oldies-reels-worker/issues/32#issuecomment-6386261483)
