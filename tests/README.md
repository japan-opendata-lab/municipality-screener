# Test fixture

`fixture.json` is a **test fixture**: 5 municipalities excerpted from the public dataset at https://jpopendata.jp/screener/screener-data.json (dataset version 1.0, generated 2026-11-19, compiled from published Japanese government statistics; see the repository's DATA_SOURCES.md for the source of every indicator). It exists only so the MCP core logic can be tested offline. The full dataset is never bundled with this repository.

Municipalities included:

| Code | Municipality | Why it is in the fixture |
|---|---|---|
| 01100 | 札幌市 (Sapporo) | Large city baseline |
| 08220 | つくば市 (Tsukuba) | Fast-growing city (population change +11.2%) |
| 07542 | 楢葉町 (Naraha) | Fastest population growth rate in the fixture (+22.3%) |
| 07546 | 双葉町 (Futaba) | Edge case: the 2020 census population is 0, so the population-change rate is legitimately missing (null) |
| 13402 | 青ヶ島村 (Aogashima) | Smallest municipality in Japan (population 168) |

Run the tests with:

```bash
python tests/test_core.py
```
