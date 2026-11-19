
# LSTM Stock_Trend_Prediction

Analyze the stock trend prediction of 台積電(2330.TW) by constructing an LSTM model.

## Authors

- [@PoDa](https://github.com/v016604z)

## Code references

- [@AUSTIN2526](https://github.com/AUSTIN2526/learn-AI-in-30-days-book-version/tree/main)'s Ch.05 LSTM principle introduction and Keras implementation
- [@Docat0209]LSTM_Stock_Prediction_v1 co-producer

## LSTM 比較研究環境

新增的 `src/lstm_comparison/` 為獨立研究套件，使用 Python 3.11 與 CPU 版 TensorFlow。舊版 Notebook 與 `src/Trading/` 保留原用途；其舊相依套件清單不適用於本研究。研究設計與工作切分請見 [8 個 Commit 實作計畫](./docs/單變量與多變量%20LSTM%20股票價格預測績效比較｜實作計畫.md)。

研究相依套件由 `pyproject.toml` 宣告，`uv.lock` 鎖定直接及傳遞依賴。安裝基線為 Windows x64、Python 3.11、CPU；其他平台尚未驗收。

### 建立專案內環境

以下 PowerShell 指令在專案根目錄執行，使用 [uv 0.13.9 官方 standalone ZIP](https://github.com/astral-sh/uv/releases/download/0.13.9/uv-x86_64-pc-windows-msvc.zip)，以官方 SHA256 驗證後解壓至 `.tools/uv/`。不修改全域 PATH 或 Windows registry。

```powershell
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Path .tools -Force | Out-Null
$uvUrl = 'https://github.com/astral-sh/uv/releases/download/0.13.9/uv-x86_64-pc-windows-msvc.zip'
Invoke-WebRequest -Uri $uvUrl -OutFile .tools/uv.zip -UseBasicParsing
Invoke-WebRequest -Uri "$uvUrl.sha256" -OutFile .tools/uv.zip.sha256 -UseBasicParsing
$expectedHash = ((Get-Content .tools/uv.zip.sha256 -Raw).Trim() -split '\s+')[0]
if ((Get-FileHash .tools/uv.zip -Algorithm SHA256).Hash -ne $expectedHash) { throw 'uv SHA256 mismatch' }
Expand-Archive -LiteralPath .tools/uv.zip -DestinationPath .tools/uv -Force
$env:UV_CACHE_DIR = Join-Path (Get-Location) '.uv-cache'
$env:UV_PYTHON_INSTALL_DIR = Join-Path (Get-Location) '.tools/python'
.\.tools\uv\uv.exe python install 3.11 --no-bin --no-registry
.\.tools\uv\uv.exe sync --locked
```

`.tools/`、`.uv-cache/`、`.venv/` 皆為本地環境，不納入版本控制。在新 PowerShell 視窗重新執行 uv 指令前，需再次設定上面兩個環境變數。也可直接使用 `.venv/Scripts/python.exe` 執行下列已安裝模組的指令，不需啟用虛擬環境。

### 本階段可用指令

```powershell
.\.venv\Scripts\python.exe -m lstm_comparison --help
.\.venv\Scripts\python.exe -m lstm_comparison validate-config --config configs/research.json
.\.venv\Scripts\python.exe -m lstm_comparison download --config configs/research.json
.\.venv\Scripts\python.exe -m lstm_comparison load-snapshot --config configs/research.json
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

`configs/research.json` 保存正式研究設定：三組特徵、60 日視窗、年度切分，以及 seeds 42、43、44。資料快照與結果路徑一律相對於設定檔目錄解析，檢查成功時輸出解析後的絕對路徑；不要求行情已下載。`max_epochs` 與種子數等訓練設定可縮短供後續 smoke test 使用，正式實驗沿用核定設定。

`validate-config` 成功回傳 exit code 0，無效設定回傳 2。help 與設定檢查只使用 Python 標準庫，不載入 TensorFlow，也不連網。

`download` 會下載新行情快照；若快照已存在，會離線檢查並重用，不重新連線或覆寫。`load-snapshot` 僅離線檢查。來源或快照驗證失敗回傳 1，設定錯誤回傳 2。`run --config ...`、`report --run-dir ...` 尚未實作，執行會回傳 1；模型訓練與研究報告依 Commit 5、7 接續完成。

### 行情快照與交易日完整性

預設快照由以下三個檔案組成，納入版本控制：

- `res/research/2330.TW_2015-2025.csv`：固定欄位 `Date,Open,High,Low,Close,Volume`；Date 為台北交易日的 ISO 日期。
- `res/research/2330.TW_2015-2025.sessions.csv`：研究期間預期的交易日。
- `res/research/2330.TW_2015-2025.metadata.json`：下載 UTC 時間、完整來源參數、Python／套件版本、筆數、日期邊界，以及行情與交易日 CSV 的 SHA256。

行情使用 yfinance 的 `auto_adjust=True`，保留來源成交量，不進行額外價格修復、補值或刪除缺值列。資料檢查拒絕空結果、重複日期或欄位、多股票混入、缺欄位、缺值、非有限數值、非正價格、不合理 High/Low，以及非正整數成交量。本研究要求有效交易日 `Volume > 0`；已知 Yahoo 存在 TWSE 實際有成交卻回傳零量的日期，因此不能將零量樣本視為正常行情。

預期交易日使用鎖定的 [exchange_calendars 4.13.3 XTAI](https://pypi.org/project/exchange_calendars/4.13.3/)，加上經 TWSE 官方資料核實的明列修正，研究區間共 **2,679 個預期交易日**：

- 額外休市：2022/02/04（[春節公告](https://www.twse.com.tw/staticFiles/news/news/tsecnews/ff8080817d22b9cb017e3336c4e203e3.pdf)）、2023/01/18（[當月市場成交資料](https://www.twse.com.tw/rwd/zh/afterTrading/FMTQIK?date=20230101&response=json)顯示 01/17 後至 01/30 才恢復交易）、2024/10/31（[康芮颱風公告](https://wwwc.twse.com.tw/staticFiles/news/news/tsecnews/8a8216d69236c2e30192dd523eb10329.pdf)）。
- 額外開市：2016/01/30、2016/06/04、2016/09/10、2017/02/18、2017/06/03；各日均由下表 TWSE 個股資料確認有正成交量及有效 OHLC，不能因落在週六而排除。

每筆修正的日期、原因與官方來源列於 `data.py`，成功凍結時一併寫入 metadata。行情的起訖及中間每個交易日都必須與預期日期完全相同；不使用單純工作日推測休市，也不根據 Yahoo 缺資料的日期自行刪除預期交易日。

交易日 CSV 與日曆來源版本一同凍結。後續離線讀取核對凍結日期及 hash，不因目前安裝的日曆版本不同而改寫歷史。來源資料仍受 Yahoo 的歷史資料修訂及日曆規則正確性限制，任何日期差異都應查明原因後再建立新快照。

快照先在同目錄暫存，完整寫入後以不覆寫的方式發布；metadata 最後發布，作為完整快照標記。一般寫入錯誤只清理本次建立的檔案，程序中斷可能留下部分檔案；讀取時會明確拒絕這類殘留，不將它當成成功快照，也不自動刪除或修復。遇到不完整或損壞快照，先保留檔案查明原因，或在設定中使用新的 `snapshot_path` 重新下載，沒有 `--force` 覆寫選項。

搬移快照時需一併搬移三個同名檔案，並更新設定中的 `snapshot_path`。離線檢查只比對資料來源參數，不綁定原始絕對路徑或模型訓練參數。CSV 固定使用 LF；`.gitattributes` 僅針對 `res/research/*.csv` 保留 LF，避免 Windows 換行轉換破壞 SHA256。搬移到其他版控目錄時，也需保留此換行規則。

### 真實來源驗收狀態

**Commit 2 的下載與離線快照程式已實作；正式行情快照尚未完成。** 使用者已選擇維持 Yahoo 與嚴格檢核，先交付程式；不以其他來源或補值繞過資料品質問題。

2026/11/19 實際向 Yahoo 取得 **2,682 筆**，起訖為 2015/01/05–2025/12/31，但無法通過獨立交易日與數值檢查。相對於 2,679 個預期交易日，來源缺少 2 日、多出 5 個非交易日；另有 6 個有效交易日 OHLC 全為 NaN，以及 1 個有效交易日為平價零量。缺少或價量異常的有效交易日合計 **9 日**，不含那 5 個非交易占位日。

| 日期 | Yahoo 狀況 | TWSE 官方個股證據 |
| --- | --- | --- |
| 2019/09/09 | 缺少該日 | [2019 年 9 月](https://www.twse.com.tw/rwd/zh/afterTrading/STOCK_DAY?date=20190901&response=json&stockNo=2330)：17,317,833 股，OHLC 265.50／266.00／263.50／265.00 |
| 2021/04/06 | 缺少該日 | [2021 年 4 月](https://www.twse.com.tw/rwd/zh/afterTrading/STOCK_DAY?date=20210401&response=json&stockNo=2330)：37,664,216 股，OHLC 615／616／608／610 |
| 2016/01/30 | OHLC 全 NaN、Volume 0 | [2016 年 1 月](https://www.twse.com.tw/rwd/zh/afterTrading/STOCK_DAY?date=20160101&response=json&stockNo=2330)：11,865,065 股，OHLC 142.50／143.00／141.00／142.00 |
| 2016/06/04 | OHLC 全 NaN、Volume 0 | [2016 年 6 月](https://www.twse.com.tw/rwd/zh/afterTrading/STOCK_DAY?date=20160601&response=json&stockNo=2330)：2,631,269 股，OHLC 160／160／159.50／160 |
| 2016/09/10 | OHLC 全 NaN、Volume 0 | [2016 年 9 月](https://www.twse.com.tw/rwd/zh/afterTrading/STOCK_DAY?date=20160901&response=json&stockNo=2330)：15,470,223 股，OHLC 177／179／176／178 |
| 2017/02/18 | OHLC 全 NaN、Volume 0 | [2017 年 2 月](https://www.twse.com.tw/rwd/zh/afterTrading/STOCK_DAY?date=20170201&response=json&stockNo=2330)：3,517,102 股，OHLC 190／190.50／189.50／189.50 |
| 2017/06/03 | OHLC 全 NaN、Volume 0 | [2017 年 6 月](https://www.twse.com.tw/rwd/zh/afterTrading/STOCK_DAY?date=20170601&response=json&stockNo=2330)：1,535,230 股，OHLC 209／209／208／209 |
| 2025/08/01 | OHLC 全 NaN、Volume 0 | [2025 年 8 月](https://www.twse.com.tw/rwd/zh/afterTrading/STOCK_DAY?date=20250801&response=json&stockNo=2330)：45,352,225 股，OHLC 1,145／1,150／1,130／1,140 |
| 2021/08/17 | OHLC 全相同、Volume 0 | [2021 年 8 月](https://www.twse.com.tw/rwd/zh/afterTrading/STOCK_DAY?date=20210801&response=json&stockNo=2330)：31,845,499 股，OHLC 580／582／578／580 |

Yahoo 多出的非交易占位日為 2015/07/10、2015/09/29、2016/07/08、2016/09/27、2016/09/28，皆為平價零量。已核對 TWSE 市場月成交資料：[2015 年 7 月](https://www.twse.com.tw/rwd/zh/afterTrading/FMTQIK?date=20150701&response=json)、[2015 年 9 月](https://www.twse.com.tw/rwd/zh/afterTrading/FMTQIK?date=20150901&response=json)、[2016 年 7 月](https://www.twse.com.tw/rwd/zh/afterTrading/FMTQIK?date=20160701&response=json)、[2016 年 9 月](https://www.twse.com.tw/rwd/zh/afterTrading/FMTQIK?date=20160901&response=json)。程式仍拒絕這些列，不自動刪除來使資料過關。

針對 2019/09/09、2021/04/06、2021/08/17、2025/08/01，再以有界短日期區間比較 Yahoo `download` 與 `Ticker.history`，結果均重現同一異常。上述 TWSE 未調整價格僅作查證證據，沒有拿來補入調整後行情。下載指令會明確非零拒絕並列出缺日、多日與無效日期，因此 `res/research/` 下沒有正式行情、sessions 或 metadata 三檔；診斷回應僅留在被忽略的 `.tools/diagnostics/`。
