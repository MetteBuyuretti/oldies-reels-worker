# T2 aday sözleşme farkı ve odaklı test önerisi — UYGULANMADI

İş: WORK2-TR-PREPRODUCTION-20261031-01. Bu not **T1 sabit checkpoint'inden sonra** yazıldı.
T1 içerik: 2be10a68dd7f904a5b99b55fda79d81fc722b181; T1 RESULT/HANDOFF manifesti: 0daf1b0bac3fe3b976f4d497dab1cc03c1b4c5d5; #32/6536332197.
Önceki somut kontrol ve yaratıcı sınırları tekrar açmaz.

## Tek kanıtlanan boşluk

PR33 worker main → prepare_preview → render_preview yolu kullanılıyor. 27s **stub** için gerçek build_timeline sekiz caption bölümü oluşturuyor; make_timeline_scenes bunlara modül içindeki gerçek modulo ifadesiyle üç fotoğrafı döndürüyor. Bu paket üç hikâye fotoğraf sahnesi planlıyor. Mevcut tüketici, caption bölümlerini fotoğraf sahnesi saydığı için bu planı kullanamıyor.

Önerilen dar fark **caption zamanları ile fotoğraf sahnelerinin ayrılmasıdır**. TTS promptu, ses modeli, 59s normu, 25–30s genel limiti veya sessizlik eşiği değişikliği bu boşluğu çözmez.

## Aday veri sözleşmesi

VISUAL-CONTRACT-CANDIDATE.json yalnız bu işte tartışılan bir taslaktır; PR33 bunu okumuyor. status=DESIGN_ONLY_NOT_CONSUMED. Script SHA tam T1 metnine bağlıdır. Üç sahnenin söz aralıkları 0–24, 24–35, 35–56 (başlangıç dahil, bitiş hariç); bunlar ses zaman damgası değildir. Fotoğraf hashleri null'dır; null bir kaynak hiçbir uygulamada onaylı sayılmamalıdır.

- Süre profili aynı legacy_short_25_30 kalır. Ayrı visual_plan_version yalnız bu yeni planı seçer; yeni genel yayın profili yaratmaz.
- Kelime aralıkları sıralı, çakışmasız ve tam metni kapsar; referanslar source/script/packet hashleriyle bağlanır.
- P1/P2/P3 yalnız fotoğraf aday kimliğidir. Gerçek image_credits hash/kimlik/dönem/lisans/bölge kanıtı tamamlanmadan renderer'a geçilmez.
- Caption aynı fotoğraf sahnesi içinde değişebilir. Fotoğraf kaynağı caption sayacından modulo ile seçilmez. Aynı fotoğrafın türev crop'unu yeni kimlik saymak yoktur.
- Bilinmeyen sürüm, eksik map, hash farkı, süre aralığı boşluğu veya kaynak fotoğraf eksikliği kapalı durur. Yeni plan istendiğinde sessizce legacy modulo'ya düşülmez.
- Eski kabul kapıları ve eski reddedilmiş medya korunur; planlı kapanış/hız/fotoğraf onayı dosya alanlarıyla uydurulmaz.

## Koordinatöre önerilen dosya sahipliği — en çok dört modül

| PR33 modülü | Dar değişiklik önerisi / kullanılan çağrı |
|---|---|
| reels_preview.py | Yeni görsel plan seçilmişse check_script/check_photo_evidence sonrasında hash-bağlı planı doğrulayıp gerçek render callable'ına aktar. Üretici veya TTS çağrısı ekleme. |
| worker.py | main içindeki render_preview ile make_timeline_scenes'in gerçek yolunda açık foto-sahne eşlemesini tüket. Sadece çağrılmayan yardımcı ekleyerek bitirme. |
| video_factory.py | Caption zamanlarını fotoğraf sahne aralıklarından ayrı taşı; gerçek renderer bu aralıkları tüketmeli. final_reel_duration ve kısa profil/10s ret davranışı aynen kalsın. |
| editorial_quality_gate.py | Yeni görsel plan için script/photo hashleri, kapsama, sıra ve çeşitlilik kontrolünü mevcut kaynak/fotoğraf/bağımsız kabul kapısına bağla; hiçbir korumayı kaldırma. |

source_evidence.py ve media_evidence.py bu dar kapsamda değişmemeli: 56 kelimelik metin zaten mevcut yapısal script kapısından geçti; süre/sessizlik değişikliği gerekçesi yok. Değişiklik ihtiyacı ortaya çıkarsa ayrı somut kanıtla kapsam uzlaştırılır.

**Dosya sahipliği henüz teyit edilmedi.** Bu Work2 gerçek Windows girişine veya farklı worker/gate bytes'ına yama uygulamaz. Koordinatör PR33 sabit tabanı ve yalnız bu dört modülün tek yazarlığını doğrulamadan kök dosya diff'i uygulanmaz. Bu not çalışmış kod/test veya kurulmuş uygulama değildir.

## Sonraki aday için odaklı test önerisi — YAZILMADI / NOT RUN

1. Gerçek preview callable → render consumer yolunda hash-bağlı üç sahneli fixture; sekiz caption olsa da fotoğraf geçişleri yalnız S1/S2/S3 planını izlemeli.
2. Yanlış script SHA, fotoğraf SHA, bilinmeyen plan sürümü veya eksik plan, renderer/provider/delivery çağrısından önce durmalı.
3. Çakışan veya eksik kelime/zaman aralığı ve sahne atlaması reddedilmeli; tüm metin ve kapanış görünür kapsamda kalmalı.
4. Reddedilmiş fotoğraf, aynı bytes veya crop türevinin farklı kimlikle sunulması çeşitlilik sayılmamalı.
5. Mevcut kısa profilin 10s ve >30s reddi korunmalı; bu test sonuçları burada koşulmuş diye raporlanmamalı.
6. Kaynak/kimlik/lisans/bağımsız tam medya kabulü eksikse yeni görsel plan hiçbir yayın bayrağını açmamalı.

Bunlar sonraki dar adayın test tasarımıdır; T1'de gerçekten çalışmış beş kontrolle birleştirilip PASS toplamı yapılmaz.

## Devir

T1 yaratıcı/görsel ön incelemesi ve B-VISUAL-PACKET mevcut tek somut girdi olarak sürer. Koordinatör bu notu aynı paketten okuyarak sahiplik ve uygulama parçasını ayırabilir. Yeni genel analiz/kurulum/onay turu, başka sohbete otomatik komut veya kullanıcıdan rapor taşıma gereği oluşturulmadı.
