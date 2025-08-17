#!/usr/bin/env python3
"""
scrape_immersive_last200_missing.py
-----------------------------------
Scrape up-to-200 latest spins from CasinoScores (Immersive Roulette) using Selenium,
save them to CSV, and also report which numbers (0..36) did NOT appear at all.

Usage (defaults shown):
    python3 scrape_immersive_last200_missing.py \
        --csv immersive_last200.csv \
        --missing-csv missing_numbers.csv \
        --missing-json missing_numbers.json \
        --max 200 \
        --wait 25 \
        --print

Flags:
    --csv           Output CSV for spins (default immersive_last200.csv)
    --missing-csv   Output CSV listing missing numbers 0..36
    --missing-json  Output JSON with missing numbers + count + timestamp
    --max           Max spins to keep (default 200)
    --wait          Max seconds to wait for content to appear (default 25)
    --print         Also print lists to the console

Requirements:
    - Selenium (pip install selenium)
    - Chromium/Chrome + matching chromedriver accessible in PATH
"""

import re
import csv
import json
import time
import argparse
from datetime import datetime
from typing import List, Tuple, Set

try:
    from zoneinfo import ZoneInfo
except Exception:
    from backports.zoneinfo import ZoneInfo  # type: ignore

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By

ATHENS_TZ = ZoneInfo("Europe/Athens")
TARGET_URL = "https://casinoscores.com/immersive-roulette/"

# Candidate containers and item/field selectors commonly seen on CasinoScores pages
CONTAINER_CSS = [
    ".results", ".history", ".recent", ".tracker", "body"
]
ITEM_CSS = [
    ".results li", ".history li", ".recent .item", ".tracker .item",
    "li.result", "li", ".item"
]
NUMBER_CSS = [".number", ".result", ".ball", ".value", ".num"]
COLOR_CSS  = [".red", ".black", ".green"]

# Single-zero mapping
RED_SET = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
BLACK_SET = set(range(1,37)) - RED_SET

def classify_color(number_text: str, color_text: str) -> str:
    c = (color_text or "").strip().lower()
    if c in ("red", "black", "green"):
        return c
    try:
        n = int(number_text)
        if n == 0: return "green"
        return "red" if n in RED_SET else "black"
    except Exception:
        return ""

def extract_numbers_from_container(container) -> List[Tuple[str,str]]:
    results = []
    seen_texts = set()
    items = []
    for sel in ITEM_CSS:
        try:
            found = container.find_elements(By.CSS_SELECTOR, sel)
            if len(found) > len(items):
                items = found
        except Exception:
            continue
    for it in items:
        number_text = ""
        for nsel in NUMBER_CSS:
            try:
                el = it.find_element(By.CSS_SELECTOR, nsel)
                number_text = el.text.strip()
                if number_text:
                    break
            except Exception:
                continue
        if not number_text:
            try:
                number_text = it.text.strip()
            except Exception:
                number_text = ""
        m = re.search(r'\b([0-9]|[12][0-9]|3[0-6])\b', number_text)
        if not m:
            continue
        number_text = m.group(1)
        color_text = ""
        for csel in COLOR_CSS:
            try:
                el = it.find_element(By.CSS_SELECTOR, csel)
                ctxt = el.text.strip().lower()
                if not ctxt:
                    classes = (el.get_attribute("class") or "").lower()
                    if "red" in classes: ctxt = "red"
                    elif "black" in classes: ctxt = "black"
                    elif "green" in classes: ctxt = "green"
                if ctxt:
                    color_text = ctxt
                    break
            except Exception:
                continue
        row_key = f"{number_text}-{color_text}-{it.id}"
        if row_key in seen_texts:
            continue
        seen_texts.add(row_key)
        results.append((number_text, color_text))
    return results

def compute_missing(seen_nums: Set[int]) -> List[int]:
    all_nums = set(range(0, 37))
    missing = sorted(list(all_nums - seen_nums))
    return missing

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="immersive_last200.csv", help="Output CSV for spins")
    ap.add_argument("--missing-csv", default="missing_numbers.csv", help="Output CSV for missing numbers 0..36")
    ap.add_argument("--missing-json", default="missing_numbers.json", help="Output JSON for missing numbers 0..36")
    ap.add_argument("--max", type=int, default=200, help="Max spins to keep (default 200)")
    ap.add_argument("--wait", type=int, default=25, help="Max seconds to wait for content")
    ap.add_argument("--print", dest="do_print", action="store_true", help="Print lists to stdout")
    args = ap.parse_args()

    options = ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36")

    driver = webdriver.Chrome(options=options)
    try:
        driver.set_page_load_timeout(30)
        driver.get(TARGET_URL)

        # Wait loop for any container
        container = None
        end_time = time.time() + args.wait
        while time.time() < end_time and container is None:
            for sel in CONTAINER_CSS:
                try:
                    container = driver.find_element(By.CSS_SELECTOR, sel)
                    if container:
                        break
                except Exception:
                    continue
            if container is None:
                time.sleep(0.5)

        if container is None:
            raise RuntimeError("Failed to locate results container. Try increasing --wait or updating selectors.")

        pairs = extract_numbers_from_container(container)
        if len(pairs) < 10:
            try:
                body = driver.find_element(By.TAG_NAME, "body")
                pairs = extract_numbers_from_container(body)
            except Exception:
                pass

        pairs = pairs[: args.max]
        now = datetime.now(tz=ATHENS_TZ).isoformat()

        # Build rows & collect seen numbers
        rows = []
        seen_nums: Set[int] = set()
        for num_text, c in pairs:
            col = classify_color(num_text, c)
            try:
                n = int(num_text)
                seen_nums.add(n)
            except Exception:
                pass
            rows.append({"number": num_text, "color": col, "captured_at": now, "source_url": TARGET_URL})

        # Save spins CSV
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["number","color","captured_at","source_url"])
            w.writeheader()
            w.writerows(rows)

        # Compute & save missing numbers
        missing = compute_missing(seen_nums)

        with open(args.missing_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["missing_numbers_0_36"])
            for m in missing:
                w.writerow([m])

        with open(args.missing_json, "w", encoding="utf-8") as f:
            json.dump({"missing_numbers": missing, "count": len(missing), "captured_at": now}, f, ensure_ascii=False, indent=2)

        if args.do_print:
            print("Last spins (numbers only):", [r["number"] for r in rows])
            print("Missing 0..36:", missing)

        print(f"Wrote {len(rows)} spins to {args.csv}")
        print(f"Wrote missing numbers to {args.missing_csv} and {args.missing_json}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
