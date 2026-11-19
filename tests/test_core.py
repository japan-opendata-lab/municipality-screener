"""Core-logic tests for the MCP server, run against tests/fixture.json
(5 real municipalities excerpted from the public dataset).

Run:  SCREENER_DATA_FILE=tests/fixture.json python -m pytest tests/ -q
or simply: python tests/test_core.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mcp'))
os.environ.setdefault('SCREENER_DATA_FILE',
                      os.path.join(os.path.dirname(__file__), 'fixture.json'))

import server  # noqa: E402


def test_search_excludes_missing_values():
    r = server.core_search([{'indicator': 'popchg', 'min': 0.1}], sort_by='popchg')
    names = [x['name'] for x in r['results']]
    assert r['count'] == 2 and '楢葉町' in names and 'つくば市' in names
    assert '双葉町' not in names  # 2020 census population is 0, so no rate


def test_get_carries_sources():
    g = server.core_get('07546')
    assert g['name'] == '双葉町'
    assert g['indicators']['popchg']['value'] is None
    assert g['indicators']['pop']['source']


def test_compare_and_catalog():
    c = server.core_compare(['01100', '08220'], ['pop'])
    assert c['indicators']['pop']['values']['08220'] == 268832
    assert len(server.core_list_indicators()['indicators']) == 51


if __name__ == '__main__':
    test_search_excludes_missing_values()
    test_get_carries_sources()
    test_compare_and_catalog()
    print('all core tests passed')
