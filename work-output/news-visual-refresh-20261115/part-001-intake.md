# Oldies Radyo — Müzik Haberleri görsel yenileme / İlk teknik denetim

Tarih: 15 Kasım 2026 (Türkiye)
Ana görev: https://github.com/MetteBuyuretti/oldies-reels-worker/issues/43
Koordinasyon: Ana Kumanda #32
Durum: salt-okunur teknik keşif; canlı değişiklik veya yayın yapılmadı.

## Kesinleşen
- Oldies Radyo özel tema: `oldies-radyo-1950s-theme` v7.3.7.1.
- WP haber listesi: `https://oldiesradyo.com/muzik-haberleri/`, sayfa ID 630.
- Sayfada Gutenberg Query Loop, category 786935889, perPage=12, grid=3.
- Kart CSS resim kuralı: `width:100%;aspect-ratio:16/10;object-fit:cover`; fotoğrafa özel `object-position` / blur-fill mimarisi burada görünmüyor.
- 2026 aylık banner tasarım bileşeni sayfa #630 gövdesinde yok; temanın ilgili PHP/CSS bileşenini bulup incelemek gerekiyor.
- WordPress MCP, post/page bloğu ve metadata düzenler; aktif özel temanın kaynak PHP dosyalarını okuyup yama uygulamak için uygun doğrudan araç sağlamıyor. `wpcom_templates_lookup` bu klasik temada 500 döndü.
- Kaynak tasarım: bordo, kömür, krem, altın; plak ve radyo görselleri; aylık görselli başlık. Sohbette 15 Kasım'da beğenilen mockup. İçindeki sanatçı fotoğrafları ve bazı başlık/tarihler görsel örnektir, gerçek haber sayfasına kopyalanmamalı.

## İlk uygulama paketi
1. Canlı tema dosyası / eski `news-monthly-separation-20261025` değişiklikleri / `work2-site-visual-closure-20261031` checkpoint uzlaşması.
2. Haber kartı ortak bileşeni: yatay `cover`; portrede keskin ön fotoğraf + aynı görselin karartılmış/blur arka planı (boş kenarsız); manuel odak pozisyonu. Elvis hatasının gerçek kullanılan medyası ve sayfa ID'si tespit edilmeli.
3. Aylık haber blokları için tek görselli banner şablonu; ay/yıl dinamik, TR/EN ayrı; gerçek ve hakları uygun içerik.
4. 390px mobil + 1200/1440px masaüstü, farklı oranlar, Elvis + 10 örnek görüntü, CLS/LCP, TR/EN, SEO ve yayın otomasyonu regresyon testi.
5. WATCHDOG bağımsız QA, kurucu onayı, sonra sürümlü canlı kurulum ve geri dönüş.

Başlangıç yetkisi: salt-okunur keşif + staging/taslak. Henüz gerçek çalışma kabulü veya canlı sonuç yok.
