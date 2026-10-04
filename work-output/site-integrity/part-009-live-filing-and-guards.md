# Site Integrity — checkpoint 009, live v0.2.1 and targeted filing

Approved installation completed; WordPress plugin active. Tested follow-up source fixes applied through native plugin editor; both file-update receipts observed.

Verified: meaningful default News category no longer falsely categorized as missing; source guard remains active if baseline option disappears. Ana Kumanda panel now exposes finite review queues, readonly audit JSON, real daily schedule and nonmutating runtime filter probes.

Live runtime probe: invalid publish returns oldies_publish_gate (422), missing image/category/translation reported; menu REST write returns oldies_architecture_locked; menu insertion blocked. No test content published.

Targeted category assignments only: TR4300 [786935112] -> [786935889]; EN4286 [786982547,786978945] -> [786982547,786982544]; EN4343 [786982547,786978945] -> [786982547]. Editor reload verified all remain published, body/title/excerpt unchanged. Existing categories retained; no term deletion/creation, slug, player, menu or Polylang settings changed.

Rollback: pre-change exact theme/plugin/HFCM source and menu baseline in approved package version3; fresh targeted body/category backups captured locally and will be added to final package. Reassign the arrays above to roll back filing. Deactivating this isolated plugin restores original theme/HFCM output; baseline options survive. No full hosting database snapshot available on current plan.

PHP8.3.33 lint clean for all3 PHP files;47 behavioral tests pass. Logged-in TR/EN homepage Research modules each show correct language and 3 valid cards, including Belgium. EN canonical archive verified. WordPress.com Clear All cache action submitted; pending fresh anonymous HTTP checks.

Remaining: finish fresh native all-publication audit, 8 priority frontend validations, visitor cache verification, final package/checkpoint/report. Current historical score47% contains568 template reviews and is not a proven frontend failure rate.
