name: Auto Update Stock Prices

on:
  schedule:
    - cron: '30 6 * * 1-5'
  workflow_dispatch:

permissions:
  contents: write

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install requests
      - run: python update_pms.py
      - run: |
          git config --global user.name "github-actions[bot]"
          git config --global user.email "github-actions[bot]@users.noreply.github.com"
          git add index.html
          git commit -m "Auto update prices" || exit 0
          git push
```eof

### 🛠️ 操作建議：
1. 先確認 **Settings** 內的寫入權限已經儲存（`Read and write permissions`）。
2. 進入 `.github/workflows/update.yml` 貼上上方最新的設定內容並 **Commit changes**。
3. 回到 **Actions** 點擊 **`Run workflow`** 再次測試！
