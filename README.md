# Oldies Radyo Reels Draft Worker

Bu işçi her gün 12:00 Europe/Istanbul saatine karşılık gelen 09:00 UTC'de çalışır. Yabancı kaynaklarla müzik tarihinde bugün araştırması yapar, en iyi adayı kalite puanıyla seçer, özgün 9:16 sessiz MP4 üretir ve WordPress'teki **inceleme kuyruğuna** yükler. Ayrıca Instagram uygulamasında seçilecek gerçek şarkıyı ve önerilen 10–15 saniyelik bölümü kaydeder. Instagram'a doğrudan yayın yapamaz.

## GitHub ayarları

Repository secrets:

- `OPENAI_API_KEY`
- `OLDIES_WP_BEARER`

Repository variables:

- `OLDIES_WP_BASE_URL=https://oldiesradyo.com`
- `REELS_AUTOMATION_ENABLED=false` (ilk testten sonra `true`)
- `OPENAI_RESEARCH_MODEL=gpt-5.4`
- `OPENAI_IMAGE_MODEL=gpt-image-2`

İlk çalışma `workflow_dispatch` ile elle başlatılmalıdır. WordPress panelinde taslak önizlenir, Meta Dry Run yapılır ve ancak bundan sonra “yayına hazır” olarak işaretlenebilir. Canlı yayın anahtarı bu paketin dışında ve varsayılan olarak kapalıdır.
