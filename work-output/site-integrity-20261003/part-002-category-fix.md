# Site Integrity — canonical EN research filing

Verified EN Polylang languages and reciprocal pairs before changes.

- Post 4343: added existing category 786982547; retained 786978945.
- Post 4286: added existing category 786982547; retained 786978945.
- No categories created, deleted or renamed. No title, slug, image, menu or player changes.

Rollback: set categories to [786978945] on each of 4343 and 4286 using an authenticated category update. Original metadata is in part-001-backup.json.

Frontend root cause: HFCM Snippet #1 constructs a two-card research strip in browser JavaScript with hardcoded links to TR posts 4274 and 4308. It has no category query and no language branch. TR Belgium 4457 is absent; this snippet also appears on EN homepage. The Features pages do not link the priority research posts in fetched server HTML. Active classic PHP theme v7.3.7.1 is not inspectable through the current connector. Custom plugin upload is not offered by plugin.install (marketplace/WP.org only).
