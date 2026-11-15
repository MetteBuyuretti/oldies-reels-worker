# WORK MASTER UYGULAMA TALİMATI — Müzik Haberleri Kalıcı Görsel Sistemi
Tarih: 16 Kasım 2026
Ana görev: https://github.com/MetteBuyuretti/oldies-reels-worker/issues/43
Ana Kumanda bildirimi: https://github.com/MetteBuyuretti/oldies-reels-worker/issues/32#issuecomment-6899603302
Ön keşif: work-output/news-visual-refresh-20261115/part-001-intake.md

## Hedef
Kullanıcının onayladığı bordo / kömür / altın / krem editorial tasarımını oldiesradyo.com'un gerçek Müzik Haberleri sayfasına, TR/EN sayfalara ve Ekim/Kasım/gelecek ay arşivlerine kalıcı, bakım yapılabilir biçimde uygulamak. Örnek görseldeki hayali haberleri, tarihler ve lisansı belirsiz yüz fotoğraflarını yayımlamak YASAK.

## Başlamadan önce
- AGENTS.md, work-state.json, WORK_CONTINUITY_PROTOCOL.md ve #43'ü oku. WORK MASTER “ALINDI” geri bildirimi versin.
- Aktif tema sürümünü, sürüm kontrolünü ve hedef dosyaları salt-okunur envantere al. Son teyit: özel tema oldies-radyo-1950s-theme v7.3.7.1; haberler sayfası ID 630.
- Haber listesinin mevcut dinamik Gutenberg Query Loop yapısını koru (kategori 786935889, 12 yazı, 3 sütun). /en/music-news/ ve aylık arşiv bileşenlerini ayrıca keşfet.
- news-monthly-separation-20261025 ve work2-site-visual-closure-20261031 ile çakışma olmadığını doğrula.
- Kaynak dosyaların yedeğini, canlı mevcut görünüm ekran görüntülerini ve geri alma komutunu kaydet.

## Paket 1 — Haber görselleri / portre sistemi
- Gerçek kart bileşenine sınırlı CSS ve gerekirse progressive-enhancement JS ekle. Önce kaynak dosya/markup ile uyuştuğunu test et.
- Kart resim oranı sabit (mevcut 16/10 kabul edilebilir; kullanıcı mockup'ındaki 4/3 tercihi QA karşılaştırmasıyla kararlaştırılacak), yükseklik bütün kartlarda tutarlı.
- Yatay/kompozisyon açısından güvenli görsellerde cover; görselin yüzünü kesen dikey/kare fotoğraflarda aynı görselin koyulaştırılmış ve bulanıklaştırılmış arka katmanı + keskin, ortalanmış ön resim (contain). Boş beyaz/siyah bant yok.
- Ön görselin yüksekliğini CSS ile kutunun yüksekliğine bağla, resim oranından kaynaklanan taşma/CLS oluşturma. `<img>` alt metin ve erişilebilir bağlantı yapısı korunsun; ayrı tekrarlı dekoratif resim `aria-hidden` veya CSS background olsun.
- Portre otomatik algılama eşikleri kaynak görselin yönüne dayanabilir, fakat **Elvis hatası yön algısından farklı bir odak sorunu olabilir**: Elvis ve istisnalar için medya/post-ID bazlı manuel odak seçeneği veya per-card sınıfı ekle. Elvis'in gerçek id ve gerçek görsel URL'si kanıtlanmadan başarı iddia etme.
- Bant genişliği ve performans: ekstra tam çözünürlüklü görsel indirmeden, srcset/thumbnail'ları koruyarak aynı görüntüden blur üret; lazy loading, alt, srcset, boyutları bozma. CSS arka planı img.currentSrc'den uygulanacaksa yüklenme ve responsive srcset testleri şart.
- Site geneline rastgele `img { object-fit:... }` yazma; yalnız ilgili haber kartı sınıflarında değişiklik yap.

## Paket 2 — Kalıcı aylık banner
- Tema içindeki aylık arşiv rendering yolunu/partial'ını bul. Ay/yıl otomatik güncellenen TEK ortak bileşen geliştir; TR + EN etiketleri diline göre değişsin. İçerik mevcut yayın verisinden gelsin.
- Bordo ana yüzey, krem güçlü tipografi, altın detay; plak/radyo/vintage illüstrasyon veya lisansı uygun gerçek sanatçı fotoğraflarıyla zenginleştir. Yalnız düz gradient banner kabul edilmez.
- Banner ve kartlarda görsel seçimi ile metin overlay kontrastı ayrı doğrulansın. Ekim/Kasım iki örnek, geçişte Aralık için de dinamik davranış test edilsin.
- Photoshop/AI tasarım örneği statik bir mockup'tır. Koddan üretilen gerçek responsive sonuç ile kıyasla; navigasyon, site fontu/tema kimliği ve gerçek yayın başlıkları korunacak.

## Paket 3 — Kanıt ve güvenlik
- Staging/taslak ortamı, ya da yalnız yöneticinin göreceği önizleme ile önce test.
- 1440px, 1200px, 768px ve 390px ekranlarda ekran görüntüsü; en az 10 gerçek kart (Elvis, yatay fotoğraflar, dikey, kare, eksik görsel) ve Ekim/Kasım banner.
- Tüm haber linkleri, Query Loop filtresi, Polylang TR/EN, meta/canonical/hreflang, newsletter, sitemap, eski arşiv URL'leri ve otomasyon olumsuz regresyon yok.
- Gerekirse önce WP #630 üzerinde sınırlı style düzenlemesi yapılabilir; ancak **kalıcı çözümü tema ortak bileşenine** koy, sayfaya geçici JS ekleyip bütünüyle çözüldü sayma.
- Ekran görüntüsü önce/sonra, dosya diff, uygulanmış sürüm, rollback planı ve WATCHDOG bağımsız QA raporunu #43'e ekle.
- Kurucu nihai görsel ve CANLI yayın onayını ayrıca versin; güvenli önizleme PASS, canlıya alınmış sayılmaz.
- Canlı değiştirilirse uygulanmış sürümü ve her ekranın tarayıcı kanıtını raporla.

## Görev devir durumu
Bu talimat işin başlamasına ve staging geliştirmesine yöneliktir. WORK MASTER'ın iş alımı kendiliğinden gerçekleşmez. Canlı değişiklik veya dağıtım henüz onaylı değildir.
