import unittest

import zero_cost


class ArtistEntitySourceTests(unittest.TestCase):
    def test_eagles_uses_band_page_title(self):
        self.assertEqual(zero_cost.artist_page_title("Eagles"), "Eagles (band)")

    def test_eagles_never_falls_back_to_eagle_animal(self):
        animal = {
            "title": "Eagle",
            "wikibase_item": "Q2092297",
            "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/Eagle"}},
        }
        band = {
            "title": "Eagles (band)",
            "wikibase_item": "Q189635",
            "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/Eagles_(band)"}},
        }

        selected = zero_cost._page_for_artist({"pages": [animal, band]}, "Eagles")
        self.assertEqual(selected["wikibase_item"], "Q189635")
        self.assertEqual(selected["title"], "Eagles (band)")

        self.assertEqual(zero_cost._page_for_artist({"pages": [animal]}, "Eagles"), {})

    def test_unambiguous_artist_still_matches_normally(self):
        lennon = {"title": "John Lennon", "wikibase_item": "Q1203"}
        selected = zero_cost._page_for_artist({"pages": [lennon]}, "John Lennon")
        self.assertEqual(selected["wikibase_item"], "Q1203")


if __name__ == "__main__":
    unittest.main()
