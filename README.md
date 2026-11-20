# Municipality Screener

Screen all **1,741 Japanese municipalities** by published government statistics — population, households, age structure, income, local finance, commerce, tourism and more — like a stock screener for towns and cities.

Live version: https://jpopendata.jp/screener/ (operated by Japan Open Data Lab / デタマチ)

This repository contains the code only. **The dataset is not bundled**: the UI and the MCP server fetch it at runtime from the public endpoint below, so every user always works on the same published data.

- Dataset endpoint: `https://jpopendata.jp/screener/screener-data.json`
- Dataset: 50 indicators × 1,741 municipalities, compiled from published Japanese government statistics. Per-indicator sources, survey years and formulas are listed in [DATA_SOURCES.md](DATA_SOURCES.md).
- Dataset license: CC BY 4.0 for the compilation (Japan Open Data Lab). Where the terms of an original source differ, the original source prevails.
- Code license: MIT (see [LICENSE](LICENSE)).
- No estimated values and no proprietary indices are included. Ratios are computed only from published numerator/denominator columns, with the formula documented per indicator.

## Web UI

`ui/index.html` is a standalone build of the screener (the live site adds its own page frame around the same logic). Open it from any static host, or just open the file. The data URL can be overridden with a query parameter:

```
ui/index.html?data=https://jpopendata.jp/screener/screener-data.json
```

Features: preset screens (e.g. "municipalities gaining population", "fiscally strong municipalities"), range conditions on any indicator, per-capita conversion (per 10,000 residents), prefecture / population-band / coastal / railway filters, sortable results, shareable condition URLs, and relaxation hints when a screen returns zero matches.

## MCP server

`mcp/server.py` exposes the same dataset to AI clients over MCP (stdio), with four semantic tools. Every response includes the source of each indicator it used, plus the dataset license and version.

| Tool | Purpose |
|---|---|
| `search_municipalities` | Screen municipalities by indicator ranges, prefectures and flags |
| `get_municipality` | Full indicator profile of one municipality (by 5-digit code or name) |
| `compare_municipalities` | Side-by-side comparison of 2–5 municipalities |
| `list_indicators` | The indicator catalog: definitions, units, sources, notes |

Setup:

```bash
cd mcp
pip install "mcp<2"
python server.py
```

Client configuration example: [examples/mcp-config.json](examples/mcp-config.json).

Environment variables: `SCREENER_DATA_URL` (dataset URL override), `SCREENER_DATA_FILE` (read a local dataset file instead — used by tests).

## Tests

`tests/fixture.json` holds 5 real municipalities excerpted from the public dataset (including Futaba-machi, whose 2020 census population is 0, so its population-change rate is legitimately missing). Run:

```bash
python tests/test_core.py
```

## 日本語

全国1,741自治体を、人口・世帯・年齢構成・所得・財政などの公表統計で絞り込む「自治体スクリーナー」の公開コードです。本体は https://jpopendata.jp/screener/ で公開中です。

データは同梱せず、公開エンドポイント（`https://jpopendata.jp/screener/screener-data.json`）から実行時に取得します。指標ごとの出典・調査年・計算式は DATA_SOURCES.md にあります。推計値と独自の指数は含みません。コードは MIT、データ（編集物）は CC BY 4.0 です（原典の条件が優先する場合はそちらに従ってください）。

MCP サーバーは同じデータを AI から使うための受け口で、検索・取得・比較・指標カタログの4ツールを提供し、応答には必ず出典を含みます。
