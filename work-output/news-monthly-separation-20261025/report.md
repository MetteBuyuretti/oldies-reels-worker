# Yeni Haberler — aylık ve ay içi ayrımı
**Kısa özet — 25.10.2026 | 05:31 TSİ (UTC+3)**
- GERÇEKLEŞEN: Eylül TR4817/EN4818 taslaktan yayıma alındı; dosyalar kayıp değildi, taslak olduğu için görünmüyordu.
- CANLIDA: TR Yeni Haberler ve EN Music News ekranları aylık derlemeler / tekil haberler olarak ayrıldı. Aylık dosyalar tekil akışta tekrar gösterilmiyor.
- KORUNAN: Mevcut kategoriler, menü URL'leri, haber gövdeleri, fotoğrafları ve TR/EN eşleşmesi. Yeni kategori açılmadı.
- DOĞRULAMA: İki dilde canlı DOM ve anonim HTTP yanıtlarında iki bölüm ve Eylül bağlantısı görüldü. TR aylık bölümünde 3 kart (Eylül, güncel Ağustos ve eski Ağustos dosyası); EN'de 2 kart.
- SINIR: Bu işlem içeriklerin haber doğruluğunu yeniden araştıran bir editoryal denetim değildir; mobil veya bağımsız Watchdog PASS verilmedi.

**Ayrıntılı rapor — 25.10.2026 | 05:31 TSİ (UTC+3)**

Operasyon sahibi WORK MASTER. Kurucunun “Eylül dosyası Yeni Haberler içinde olmalı; aylık ve ay içi haberler ayrı olmalı” talimatı uygulandı. Önce merkezi durum ve mevcut WordPress kayıtları okundu. Yeni Haberler menüsü /muzik-haberleri/ sayfasına gidiyordu; 224 ve2753 numaralı eski Yeni Haberler sayfaları ana menünün hedefi değildi. Bu eski sayfalar değiştirilmedi.

TR630 içeriğini değiştirmek sonucu etkilemiyordu: canlı listeyi tema page-muzik-haberleri.php ve oldies_latest_news_items() üretiyordu. Aktif dosya editörün görünür textarea'sından okundu ve before.json içinde yedeklendi. functions.php yalnız okundu, değiştirilmedi.

Yeni kategori oluşturma işlemi “Mimari kilitli. Önce değişiklik önerisi, önizleme ve kullanıcı onayı gerekir.” yanıtıyla reddedildi. Ayrı araçla kategori kilidi aşılmadı; ayrım mevcut kategorileri değiştirmeyen görünüm düzenlemesiyle yapıldı.

page-muzik-haberleri.php, aynı kart biçimini koruyarak iki bölüm ve erişilebilir bölüm bağlantıları sunar. Aylık dosyalar mevcut slug standardındaki aylik-haber / monthly-news ve eski agustos-2026-oldies-music-haberleri anahtarıyla tanınır. Gelecek aylık dosyalarda bu standart korunmalıdır. TR veri kaynağı ve mevcut 40 yayın sınırı aynı kaldı; aylık arşiv bu mevcut sorgu kapsamıyla sınırlıdır. Ayların tamamını süresiz listeleyen yeni arşiv sistemi kurulmadı.

EN1714'ün kayıtlı şablonu page-muzik-haberleri.php olarak ayarlandı. İlk denemede legacy English katmanının template_include filtresi bütün native EN sayfalarını index.php'ye zorladığı görüldü. inc/ai-english.php canlı kaynağı ayrıca ai-english-before.php olarak yedeklendi. Yalnız bu açıkça seçilmiş haber şablonuna izin veren tek koşul eklendi; diğer sayfaların yönlendirmesi korunur. Tema düzenleyicisi iki dosya kaydını “Dosya düzenlendi” olarak doğruladı. Yerel PHP CLI olmadığı için php -l çalıştırıldı iddiası yok; gerçek PHP render'ı iki dilde başarılı oldu.

Eylül4817/4818 yalnız status=publish ile güncellendi. İçerik gövdeleri, öne çıkan görsel ve kategoriler geri okumada öncekiyle aynı doğrulandı; yeni içerik yazılmadı. Yayın tarihi 25 Ekim2026; içerik kapsadığı ay Eylül2026'dır.

Kanıtlar:
- TR arşiv: https://oldiesradyo.com/muzik-haberleri/
- EN arşiv: https://oldiesradyo.com/en/music-news/
- TR Eylül: https://oldiesradyo.com/2026/10/25/eylul-2026-muzik-efsaneleri-aylik-haber/
- EN Eylül: https://oldiesradyo.com/en/2026/10/25/september-2026-music-legends-monthly-news/
- Yedek: before.json ve ai-english-before.php, bu klasörde.
- Uygulanan ana şablon: page-muzik-haberleri.php, bu klasörde.

Geri dönüş: page-muzik-haberleri.php'yi before.json içindeki özgün metne; inc/ai-english.php'yi ai-english-before.php'ye; EN1714 template değerini boş dizgeye döndür. Gerekiyorsa Eylül durumlarını draft'a al; bu yayın URL'lerini tekrar görünmez yapar. İçerik gövdelerine dokunma. Otomasyonları, güvenlik veya maliyet ayarlarını değiştirme.

Kapanış: Talep edilen görünür ayrım ve Eylül dosyasının erişimi CANLIDA doğrulandı. Sonraki kontrol kullanıcı görünüm değerlendirmesi veya yeni aylık dosya eklendiğinde slug standardının doğrulanmasıdır; otomatik takip kurulmadı.
