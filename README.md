
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
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

`configs/research.json` 保存正式研究設定：三組特徵、60 日視窗、年度切分，以及 seeds 42、43、44。資料快照與結果路徑一律相對於設定檔目錄解析，檢查成功時輸出解析後的絕對路徑；不要求行情已下載。`max_epochs` 與種子數等訓練設定可縮短供後續 smoke test 使用，正式實驗沿用核定設定。

`validate-config` 成功回傳 exit code 0，無效設定回傳 2。help 與設定檢查只使用 Python 標準庫，不載入 TensorFlow，也不連網。

`download --config ...`、`run --config ...`、`report --run-dir ...` 目前只提供 help 與後續介面；執行會明確回報尚未實作並回傳 1，不會下載行情、訓練或產生研究報告。功能依實作計畫的 Commit 2、5、7 接續完成。
