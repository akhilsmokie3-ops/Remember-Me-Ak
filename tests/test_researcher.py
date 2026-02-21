import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# Mock requests and bs4
sys.modules['requests'] = MagicMock()
sys.modules['bs4'] = MagicMock()

# Add src to path
sys.path.append(os.path.abspath("src"))

from remember_me.agents.researcher import SovereignSearch

class TestSovereignSearch(unittest.TestCase):
    def setUp(self):
        self.searcher = SovereignSearch()

    @patch('requests.get')
    def test_search_basic(self, mock_get):
        # Mocking the first response (opensearch)
        mock_opensearch_res = MagicMock()
        mock_opensearch_res.status_code = 200
        mock_opensearch_res.json.return_value = [
            "query",
            ["Title 1"],
            ["Desc 1"],
            ["https://url1"]
        ]

        # Mocking the extract responses
        mock_extract_res = MagicMock()
        mock_extract_res.status_code = 200
        mock_extract_res.json.return_value = {
            "query": {
                "pages": {
                    "123": {"title": "Title 1", "extract": "Extract for Title 1"}
                }
            }
        }

        def side_effect(url, params=None, **kwargs):
            if params.get('action') == 'opensearch':
                return mock_opensearch_res
            return mock_extract_res

        mock_get.side_effect = side_effect

        results = self.searcher.search("test query", max_results=1)
        self.assertEqual(len(results), 1)
        self.assertIn("Title 1", results[0])
        self.assertIn("Extract for Title 1", results[0])

    @patch('requests.get')
    def test_search_fallback(self, mock_get):
        # Force a failure in Strategy A
        mock_get.side_effect = Exception("API Down")

        results = self.searcher.search("lion mane")
        self.assertTrue(any("Lion's Mane" in r for r in results))

if __name__ == "__main__":
    unittest.main()
