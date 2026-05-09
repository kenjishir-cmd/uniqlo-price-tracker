name: UNIQLO Price Tracker

on:
  schedule:
    - cron: '0 1 * * *'
  workflow_dispatch:

jobs:
  check:
    runs-on: ubuntu-latest
    permissions:
      contents: write

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install requests playwright
          playwright install chromium
          playwright install-deps chromium

      - name: Run price checker
        env:
          TG_TOKEN: ${{ secrets.TG_TOKEN }}
          TG_CHAT_ID: ${{ secrets.TG_CHAT_ID }}
        run: python check_price.py

      - name: Save price history
        run: |
          git config user.name "github-actions"
          git config user.email "actions@github.com"
          git add prices.json
          git diff --staged --quiet || git commit -m "Update prices $(date +'%Y-%m-%d')"
          git push
