#!/usr/bin/env python3
"""Municipality Screener MCP server (Japan Open Data Lab).

Serves four semantic tools over a published-statistics dataset of all 1,741
Japanese municipalities. The dataset is NOT bundled: it is fetched from the
public endpoint (default https://jpopendata.jp/screener/screener-data.json)
or read from a local file when SCREENER_DATA_FILE is set (used by tests).

Environment:
  SCREENER_DATA_URL   dataset URL (default: the public endpoint above)
  SCREENER_DATA_FILE  local dataset JSON path; overrides the URL when set

Every tool response carries the source and note of each indicator it used,
plus the dataset license, as required by the lab's MCP policy.
"""
import json
import os
import urllib.request

DATA_URL = os.environ.get(
    'SCREENER_DATA_URL', 'https://jpopendata.jp/screener/screener-data.json')
DATA_FILE = os.environ.get('SCREENER_DATA_FILE')

_cache = None


def load_data():
    global _cache
    if _cache is not None:
        return _cache
    if DATA_FILE:
        with open(DATA_FILE, encoding='utf-8') as f:
            _cache = json.load(f)
    else:
        req = urllib.request.Request(DATA_URL, headers={'User-Agent': 'municipality-screener-mcp/1.0'})
        with urllib.request.urlopen(req, timeout=30) as r:
            _cache = json.loads(r.read().decode('utf-8'))
    return _cache


def _idx(data):
    return {m['id']: i for i, m in enumerate(data['indicators'])}


def _meta(data, iid):
    m = data['indicators'][_idx(data)[iid]]
    return {'source': m['src'], 'note': m['note'], 'unit': m['unit'], 'label': m['label']}


def _attribution(data, indicator_ids):
    return {
        'dataset': data.get('dataset'),
        'version': data.get('version'),
        'generated_at': data.get('generated_at'),
        'license': data.get('license'),
        'indicators': {iid: {'source': _meta(data, iid)['source'],
                             'note': _meta(data, iid)['note']} for iid in indicator_ids},
    }


def _value(row, data, iid):
    return row[5 + _idx(data)[iid]]


def core_search(conditions=None, prefectures=None, coastal_only=False,
                railway_only=False, sort_by='pop', descending=True, limit=50):
    """conditions: list of {indicator, min, max, per_capita} dicts."""
    data = load_data()
    conditions = conditions or []
    used = [c['indicator'] for c in conditions] + [sort_by]
    pop_i = 5 + _idx(data)['pop']
    out = []
    for row in data['rows']:
        if prefectures and row[1] not in prefectures:
            continue
        if coastal_only and not row[3]:
            continue
        if railway_only and not row[4]:
            continue
        ok = True
        values = {}
        for c in conditions:
            v = _value(row, data, c['indicator'])
            if v is None:
                ok = False
                break
            if c.get('per_capita'):
                v = v / row[pop_i] * 10000
            if c.get('min') is not None and v < c['min']:
                ok = False
                break
            if c.get('max') is not None and v > c['max']:
                ok = False
                break
            values[c['indicator']] = v
        if not ok:
            continue
        values[sort_by] = _value(row, data, sort_by)
        out.append({'code': row[0], 'name': row[2], 'prefecture': row[1], 'values': values})
    out.sort(key=lambda r: (r['values'][sort_by] is None, -(r['values'][sort_by] or 0) if descending else (r['values'][sort_by] or 0)))
    return {'count': len(out), 'results': out[:limit],
            'attribution': _attribution(data, sorted(set(used)))}


def core_get(code_or_name):
    data = load_data()
    for row in data['rows']:
        if row[0] == code_or_name or row[2] == code_or_name:
            indicators = {}
            for m in data['indicators']:
                indicators[m['id']] = {
                    'label': m['label'], 'value': _value(row, data, m['id']),
                    'unit': m['unit'], 'source': m['src'], 'note': m['note'],
                }
            return {'code': row[0], 'name': row[2], 'prefecture': row[1],
                    'coastal': bool(row[3]), 'railway': bool(row[4]),
                    'indicators': indicators,
                    'attribution': _attribution(data, [])}
    return {'error': f'municipality not found: {code_or_name}'}


def core_compare(codes, indicators=None):
    data = load_data()
    indicators = indicators or [m['id'] for m in data['indicators'] if m['tier'] == 0]
    by_code = {r[0]: r for r in data['rows']}
    municipalities = []
    for c in codes:
        r = by_code.get(c)
        if r is None:
            return {'error': f'municipality code not found: {c}'}
        municipalities.append({'code': r[0], 'name': r[2], 'prefecture': r[1]})
    rows = {}
    for iid in indicators:
        m = _meta(data, iid)
        rows[iid] = {'label': m['label'], 'unit': m['unit'], 'source': m['source'],
                     'note': m['note'],
                     'values': {c: _value(by_code[c], data, iid) for c in codes}}
    return {'municipalities': municipalities, 'indicators': rows,
            'attribution': _attribution(data, indicators)}


def core_list_indicators():
    data = load_data()
    return {'indicators': [
        {'id': m['id'], 'label': m['label'], 'unit': m['unit'],
         'source': m['src'], 'note': m['note'], 'per_capita_available': m['percap'],
         'min': m['min'], 'max': m['max'], 'median': m['p50']}
        for m in data['indicators']],
        'attribution': _attribution(data, [])}


def build_server():
    from mcp.server.fastmcp import FastMCP
    from mcp.types import ToolAnnotations

    # All four tools are read-only lookups over a published dataset:
    # they never modify anything, the same arguments give the same
    # result for a given dataset version, and answers are computed
    # from a public endpoint fetched at runtime.
    _READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False,
                                 idempotentHint=True, openWorldHint=True)
    srv = FastMCP('municipality-screener')

    @srv.tool(annotations=_READ_ONLY)
    def search_municipalities(conditions: list[dict] | None = None,
                              prefectures: list[str] | None = None,
                              coastal_only: bool = False,
                              railway_only: bool = False,
                              sort_by: str = 'pop',
                              descending: bool = True,
                              limit: int = 50) -> dict:
        """Screen all 1,741 Japanese municipalities by published statistics.

        conditions: list of {"indicator": <id from list_indicators>,
        "min": number|null, "max": number|null, "per_capita": bool}.
        Returns matching municipalities with the values used, plus the
        source of every indicator."""
        return core_search(conditions, prefectures, coastal_only,
                           railway_only, sort_by, descending, limit)

    @srv.tool(annotations=_READ_ONLY)
    def get_municipality(code_or_name: str) -> dict:
        """Full published-statistics profile of one municipality, by its
        5-digit municipality code or Japanese name. Every value carries its
        source."""
        return core_get(code_or_name)

    @srv.tool(annotations=_READ_ONLY)
    def compare_municipalities(codes: list[str],
                               indicators: list[str] | None = None) -> dict:
        """Compare 2-5 municipalities side by side on the chosen indicators
        (default: the headline set). Every indicator carries its source."""
        return core_compare(codes, indicators)

    @srv.tool(annotations=_READ_ONLY)
    def list_indicators() -> dict:
        """The indicator catalog: definitions, units, sources and notes for
        every statistic available to the screener."""
        return core_list_indicators()

    return srv


if __name__ == '__main__':
    build_server().run()


def main():
    build_server().run()
