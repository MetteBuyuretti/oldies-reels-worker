# UYGULAMA TALİMATI — Müzik Haberleri görsel sistemi v1.0

**Tarih:** 16 Kasım 2026 (TR)  
**Ana görev:** https://github.com/MetteBuyuretti/oldies-reels-worker/issues/43  
**Koordinasyon:** ANA KUMANDA / WORK MASTER; WordPress desteği mevcut sohbet; WATCHDOG bağımsız QA; **canlı onay sahibi kullanıcı**  
**Durum:** TALİMAT HAZIR. Kod canlıya uygulanmadı; WORK MASTER'ın işi aldığını gösteren kayıt henüz yok.

## 0. İşin sınırları

Kullanıcının 15 Kasım'da beğendiği tasarım yönü: Oldies Radyo'nun bordo, krem, kömür siyahı ve antik altın kimliği; plak/radyo estetiği; görselli aylık banner; aynı boyda ve dolu haber görsel kutuları; portrelerde yüzü kesmeyen keskin fotoğraf + aynı fotoğrafın bulanık/karartılmış kenar dolgu katmanı. Mockup **gerçek haber kaynağı değildir**, içindeki Elvis ve diğer temsilî haberler/görseller **yayımlanamaz**.

**Kritik:** Güncel canlı `https://oldiesradyo.com/muzik-haberleri/` sayfasının ID'si **630**; 16 Kasım kontrolünde `modified=2026-08-28T21:53:20`. Aktif tema `oldies-radyo-1950s-theme` **v7.3.7.1**. Sayfa Gutenberg Query Loop kategori `786935889`, `perPage=12`, 3 sütun; fotoğraf `16/10` ve `object-fit:cover`. Bu sayfanın içinde **aylık görselli banner yok**: Ekim/Kasım arşiv komponentini tema kaynaklarında ayrıca bul.

## 1. Ön kontrol (salt-okunur)

1. Önce `AGENTS.md`, `control-center/WORK_CONTINUITY_PROTOCOL.md`, `control-center/work-state.json`, önceki #43 ve `part-001-intake.md` dosyalarını oku.
2. `news-monthly-separation-20261025`, `work2-site-visual-closure-20261031`, SEO #41 görevleriyle kapsam çakışmasını kontrol et. Mevcut kategori, slug, TR/EN akışını ve Query Loop'u koru.
3. Aktif tema dosya haritasında `muzik-haberleri` veya `music-news` için `page-*.php`, `archive*.php`, `template-parts`, `assets/css` ve özel bileşenleri bul. Yalnız sayfa #630 CSS'siyle tüm arşivleri düzelmiş sayma.
4. Elvis ve diğer hatalı kartların **gerçek post ID, featured media ID, kaynak görsel boyutu ve liste içindeki HTML yapısını** tespit et. "Fotoğraf kötü" diyerek asıl medya dosyasını körlemesine değiştirme.

## 2. Kalıcı haber kartı görsel düzeni

**Görsel kabul sözleşmesi**

- Tüm liste kartlarının medya çerçevesi sabit **4:3**; manşet/hero oranı **16:9**. Var olan `16/10` kullanılan yerlerde responsive kırılma ve CLS kontrollü geçiş.
- Fotoğrafın yüzü kesilmiyor; kart kenarında beyaz/boş bant görünmüyor.
- `cover` yalnız geniş, odağı güvenle kesilebilen görsellerde. Portre, dikey arşiv ve riskli kadrajda **blur-fill**.
- Blur-fill: `position:absolute; inset:0` arka foto, `background-size:cover`, `filter:blur(20px) brightness(.5)`, `transform:scale(1.08)`; üzerine **keskin** ana foto `object-fit:contain`, tam kutu yüksekliğinde. Alt metin tek ana `<img>` üzerinde; arka plan dekoratif.
- Önce sunucu tarafında `getimagesize` / WP attachment metadata ile aspect-ratio al. Ancak sanatçı kadrajı yalnız oranla belirlenemez: her post veya medya için manuel `fit=blurfill|cover` ve `object-position` opsiyonu olmalı. Elvis gibi sorunlu görseller bu override ile güvenle düzeltilmeli. Bozuk/yok görseller için markalı fallback.
- CSS/HTML yalnız haber sayfaları ve bloklarıyla sınırlandırılmalı (örn. `oldies-news-card`, `oldies-news-image`), diğer WordPress kapaklarını etkilemesin. Inline JS ile kart HTML'sini sonradan zorla değiştirmeyi kalıcı çözüm sayma.

**Örnek bileşen sözleşmesi** (doğrudan canlıya yapıştırılacak kod değil):

```html
<figure class="oldies-news-image is-blurfill" style="--news-photo:url('SAFE_IMAGE_URL');--news-focal:50% 20%">
  <span class="oldies-news-image__backdrop" aria-hidden="true"></span>
  <img src="SAFE_IMAGE_URL" alt="HABERE UYGUN GERÇEK ALT AÇIKLAMA"
       width="900" height="1200" loading="lazy" decoding="async">
</figure>
```

```css
.oldies-news-image {position:relative;aspect-ratio:4/3;overflow:hidden;margin:0;background:#1c1114;}
.oldies-news-image img {position:relative;display:block;width:100%;height:100%;object-fit:cover;object-position:var(--news-focal,50% 30%);}
.oldies-news-image.is-blurfill .oldies-news-image__backdrop {position:absolute;inset:-12px;background:var(--news-photo) center/cover no-repeat;filter:blur(20px) brightness(.55);}
.oldies-news-image.is-blurfill img {object-fit:contain;z-index:1;}
```

**Kritik test:** `figure` içindeki `img` hem ekran okuyucu için doğru ALT içermeli, hem kartın `<a>` bağlantısı mevcutsa tıklanabilirlik/odak erişilebilirliği korunmalı. Arka plan URL'leri WordPress tarafından sanitize/escape edilmeli; HTML string concat ile kontrolsüz kaynak koyma.

## 3. Aylık görselli banner sistemi

- Öncelikle **gerçekte kullanılan** Ekim/Kasım arşiv template bileşenini bul. Tasarım tek reusable bileşen veya tema template-part olarak uygulanmalı; her ay manuel sabit banner HTML çoğaltılmamalı.
- TR başlık `EKİM 2026 / KASIM 2026 — MÜZİK HABERLERİ`; EN eşleri `OCTOBER 2026 / NOVEMBER 2026 — MUSIC NEWS`. Ay/yıl **arşiv sorgusu veya ilgili aylık post metadata'sından dinamik** türetilmeli; bugün tarihini kullanıp geçmiş arşivin adını bozma.
- Görsel: eski radyo ve plak için orijinal tasarım/izinli varlıklar; eğer sanatçı fotoğrafları eklenecekse telif/atıf ve fotoğrafın hangi olaya ait olduğu net. Yıldızların aynı anda sahnede gibi gösteren yanıltıcı kolaj yok.
- Başlık görsel altı okunurluğu, mobilde odak ve kontrast öncelikli. Metni görselin içine bitmap olarak yakma; semantik `h1/h2` olarak HTML'de kalsın.
- Banner üzerindeki birinci görsel ağırsa WebP/AVIF ve kaynak boyutları; lazy load ilk ekranın LCP görseline uygulanmamalı.
- Tek komponente dayalı kalıcı aylık şablon, TR/EN metinleri ve gelecek aylarda otomatik tarih dönüşümü; sayfa #630 içine sabit "KASIM 2026" eklemek KABUL DEĞİL.

## 4. Değişiklik stratejisi / geri dönüş

- Önce tema snapshot, aktif CSS, sayfa #630 içeriği ve kritik arşiv PHP dosyalarının hash/backup kayıtlarını al.
- Özgün temanın bütün ZIP'ini gelişigüzel overwrite etme; tercihen izole child theme ya da sürümlü küçük companion plugin/tema patch'i; aktif site ve eklenti altyapısına uyumluluk kontrolü.
- Kodun otomatik testleri ve görsel çıktıları ayrı staging ortamında doğrulansın. Aylık/tekil kategori ayrımı, Polylang eşleşmeleri, sitemap/canonical/hreflang, RSS, sayfa açılma hızı ve haber otomasyonu bozulmamalı.
- **Canlı deploy kilitli:** Bağımsız WATCHDOG kabulü + kurucunun mobil/masaüstü görsel onayı olmadan canlı değişiklik ve yayın yok.
- Geri alma: hangi dosya/sürüm, hangi geri yükleme komutu, en fazla kaç dosya etkilendiği, eski görünümün kanıtı yazılsın. WordPress teması değiştirme/kurulumu otomatik yapılmasın.

## 5. Zorunlu kabul matrisi

| Test | Kriter |
| --- | --- |
| Elvis (gerçek post) | yüz kırpılmamış, kenarlarda boşluk yok, blurfill düzgün |
| Diğer 9 gerçek haber | hem portre hem geniş görsel hem eksik medya fallback |
| Ekim/Kasım banner | gerçek dönem / ay başlığı, görselli, TR ve EN |
| 390 px mobil | yatay taşma yok, metin okunur, kart boyları tutarlı |
| 1200 ve 1440 px | grid düzgün, görsel oranları eşit |
| Erişilebilirlik | ALT, link odağı, dekoratif arka katmanın gizlenmesi |
| SEO / arşiv | canonical/hreflang/kategori/URL ve sorgu sırası korunmuş |
| Performans | LCP/CLS ölçümü, önce/sonra kıyas; kritik bozulma yok |
| Yayın | haber otomasyonuna ve newsletter'a yanlış tetikleme yok |
| Geri dönüş | test edilen rollback, kanıt dosyası |

## 6. İlk talep ve rapor biçimi

**WORK MASTER'dan beklenen**: `ALINDI / ERİŞİM / TEMA DOSYA HARİTASI / ELVIS HATA KÖK NEDENİ / İLK STAGING PİLOTU / ENGEL` bilgisini #43 altında kaydetmesi. Yalnız görevin GitHub'a yazılması, çalışmanın otomatik başladığı anlamına gelmez.

İlk kalıcı çıktı: `work-output/news-visual-refresh-20261115/part-003-theme-mapping.md`. Canlı uygulama ancak sonraki ayrı onay/kabul evresidir.
