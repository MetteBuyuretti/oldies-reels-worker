# Tumblr yazıcı kapsamı — 26.10.2026 | 15:55 TSİ

Operasyon sahibi WORK MASTER; yerel inceleme aynı Codex oturumunda. Bu dar kaynak incelemesi izin veya zamanlayıcı değişikliği değildir.

| Yol | Kanıt / açık durum |
|---|---|
| run_tumblr_auto.ps1 → tumblr_auto_news_v3.mjs | Son doğal Run ve bu tur iki Verify bu yolu gerçekten kullanıyor. Mevcut publisher.lock içinde envanter→uzlaştırma; enqueue kapısı kapalı. |
| tumblr_editorial_control_v4.mjs | Browser/queue/publication çağrısı yok; sağlık ve yerel editorial kayıtları. Yayın yazıcısı değil. |
| tumblr_auto_share.mjs | draftPost ile taslak kaydı; doğrudan yayın/kuyruk yok. Bu nedenle publication bütçesi kapsamı olarak sayılmadı. |
| tumblr_auto_news.mjs / tumblr_auto_news_v2.mjs | queuePost fonksiyonlarıyla eski kuyruk yazıcıları; ortak publisher lock/bütçe yok. Güncel görevli/çağrılmıyor kabulünü kanıtlayan yetkili scheduler sonucu yok. Devre dışı varsayılmadı, değiştirilmedi. |
| tumblr_queue_two_evergreen.mjs / tumblr_queue_five_current.mjs | Bağımsız queue click yardımcıları; ortak protokol yok. Elle çağrılabilirler; güncel etkinlik durumu doğrulanamadı. |
| tumblr_start_here_draft_then_publish.mjs | Taslak oluşturma sonrası Gönder/confirmation yolu var; ortak protokol yok. Eski yardımcı yeni üretim için çalıştırılmadı. |
| tumblr_create_start_here.mjs | Ayrı Gönder/confirmation yardımcısı; ortak publication bütçesi doğrulanmadı. Güncel etkinliği bilinmediğinden kapsam dışında varsayılmadı. |
| Doğrudan kullanıcı arayüzü / başka API yazıcıları | Genel erişim kapatılamaz ve bu yerel kodun kilidine girdiği iddia edilemez. Bu tur böyle bir yayın yapılmadı. |

**Karar:** `allPathsCovered=false` korunur; diğer potansiyel yazıcılar bilinmeden bayrak true yapılmaz. İki süreçli sentetik yarış testi paylaşılan kilit+bütçe+rezervasyon sırasını sınar; bütün gerçek girişlerin bu protokole bağlandığını ispatlamaz. Bu aşamada legacy yardımcıların sessizce değiştirilmesi veya geniş erişim taraması yapılmadı.

**İşletim penceresi taslağı — etkinleştirilmedi:** Önce mevcut otomatik yazıcı sahipliği, pencere başı gerçek manuel/planlı kayıtlar ve hedef schedule semantiği doğrulanır. Ardından sınırlandırılmış tek otomatik yazıcı penceresinde aynı kilit altında taze envanter→gerçek hedef gün→kalıcı rezervasyon→tek gönderim→gerçek ID uzlaştırması uygulanır. İnsan kullanımını sessizce kilitlemek/izinlerini değiştirmek yok. Plan dışı manuel yazım görülürse envanter yeniden uzlaştırılmadan admission durur. Bu taslak tek başına yayın yetkisi veya kapsam kanıtı değildir.
