# Hak ve gerçek görsel ön incelemesi — WORK2-TR-INTEGRATION-20261031-02

**Aktör:** WORK2 / üretici ön incelemesi. Bağımsız WATCHDOG veya kurucu kabulü değildir.
**Gerçek erişim:** Beş LOC özgün TIFF taraması indirildi, açılıp görüldü; bytes/SHA256/çözünürlük ölçüldü. Kaynak TIFF dosyaları değiştirilmedi. İnceleme kopyaları/contact sheet ve 1080×1920 contain örnekleri bu özgünlerden üretildi. Yeni ses/film yok.

## Aday kararları

| Aday / özgün kayıt | Görülen gerçek içerik | Work2 kararı |
|---|---|---|
| P3 / LOC ppmsca.41592 / item 2016646493 | Yakın dört kişilik grup; yüzler açık ve fotoğrafa hakim. Soldan sağa Harrison, Starr, McCartney, Lennon ile görsel olarak tutarlı. | En güçlü grup adayı; bağımsız yüz/kadro teyidi ve hak kabulü bekliyor. |
| P1 / ppmsca.41593 / 2016646494 | Mikrofonlu, daha uzaktan grup; sağda ek görevli/kişi. P3 ile aynı ortam; telefon yerleşiminde yüzler daha küçük. | Yedek; P3'ten zayıf. Aynı olaydan iki kareyi çeşitlilik diye otomatik kabul etme. |
| P2 / ppmsca.41598 / 2016646499 | Arkadan sahne; davul, ışık ve sırtlar baskın. Dört üyenin yüzü anlatı için kurulamaz. | Bu storyboard için RED. Fotoğrafın yüksek çözünürlüğü kompozisyon kusurunu gidermiyor. |
| A1 / ppmsca.41596 / 2016646497 | Merkezde Ringo ile tutarlı yakın kişi, hayranlar/görevli. Grup dörtlüsü veya gitar tekniği karesi değil. | Koşullu tek-üye alternatifi; tek başına S2 gitar hikâyesini karşılamıyor. Arşiv kaydı üyeyi tek tek adlandırmıyor. |
| A2 / ppmsca.41597 / 2016646498 | Seyirci yüzleri; grup yok. | Sanatçı karesi yerine RED. |

Tüm kayıtların tarihi arşivde **11 Şubat 1964**, bağlamı **Washington** olarak veriliyor. Bunlar 18 Ekim EMI stüdyo görüntüsü değildir. Jimmie Nicol'lü Haziran turnesi karesi kullanılmadı. Eski reddedilmiş Harrison/Anefo veya Gotfryd dosyaları geri getirilmedi; yeni dosyalar T1'in gerçek LOC kaynak kayıtları ve aynı koleksiyondaki açık alternatiflerdir.

## Birincil hak dayanağı

- Kayıt bazındaki hak açıklaması: **No known restrictions on publication.**
- https://www.loc.gov/rr/print/res/078_usnw.html
- https://guides.loc.gov/us-news-and-world-report-photograph-collection/rights-reproductions
- https://findingaids.loc.gov/repositories/31/resources/6529

LOC, kurumun bağış sırasında personel fotoğraflarında sahip olduğu hakları kamuya bıraktığını açıklar; Marion S. Trikosko personel listesinde yer alır. Personel dışı eserler ve kişilik/tanıtım hakları ayrı tutulur. Bu belge **CC0 değildir**; bu ön inceleme TR/GB/US için kesin hukuki/bölgesel izin ilan etmez. Manifestte doğrulanmış bölgeler boş ve runtime_license=null bırakıldı.

Kurumsal hak sayfasının HTML kopyası alındı; SHA256 **85207ee6b8e6ad5502d217b40e8ab9d27ea794e884cfb6d02e8186f511336d74**. wwws adresi 403 verdi; www.loc.gov adresinden gerçek içerik alındı. Bazı düşük çözünürlüklü JPEG adresleri de 403 verdi; arşiv JSON'undaki özgün TIFF adresleri çalıştı. Bu erişim farkları gizlenmedi.

## Görüntü ve mobil yerleşim

Özgünler yaklaşık 5.4K×3.7–3.9K'dır; ölçümler ve tam hashler ASSET-MANIFEST.json'dadır. Negatif kenar/sprocket izleri bilinçli korundu. 1080×1920 contain yerleşimi tüm kaynak çerçevesini tutuyor; görüntü düzeniyle yüz kesilmedi. Arşiv fotoğrafındaki mevcut örtülmeler/cisimler giderilmedi.

Başlık/ana altyazı örnekleri fotoğrafın altındadır; 56–64px caption politikası ses/film olmadan gerçek Pillow yerleşiminde kontrol edildi. Kredi küçük alt satırdadır: tam kredi/yer/hak kaydı paket manifestinde de bulunur; nihai telefonda bağımsız okunurluk kabulü verilmedi. P3'te yüzlerin görünümü P1'den belirgin güçlü; P2/A2'de contain yapmak eksik sanatçı/yüz bilgisini düzeltemez.

İlk toplu PNG contact sheet, dosya doğrulamasında bozuk checksum nedeniyle elendi. Yeniden oluşturulan JPEG overview ve mobil föy hem görüntülenip hem dosya olarak doğrulandı; başarısız PNG teslim paketine alınmadı. Bu, kaynak TIFF bytes'ını değiştirmedi.

## Kalan kesin girdi

**B-VISUAL-PACKET:** Üç farklı hikâye-gerekçeli fotoğrafın bağımsız kadro/kompozisyon ve TR/GB/US hak değerlendirmesi. Mevcut P3 güçlü, P1 yedek ve A1 koşullu; iyi bir gitar/çalışma bağlamlı S2 karesi hâlâ eksik. ppmsca.41599 için item JSON ve özgün TIFF erişimi timeout oldu; görülmeyen bu kareye PASS verilmedi. İlgili dosya/URL/denenen yol/sahip manifestte kayıtlıdır.

Tamamlanmış yayınlık üçlü üretildi denmiyor. Bu görsel seti mevcut fotoğraf kapısını atlatmak için image_credits'e otomatik yazılmadı. Sorumlu: MASTER'ın atadığı hak/görsel bağımsız inceleyici. Work2'nin kod/test/Windows devri bu açık girdi nedeniyle bekletilmedi.

