# Warframe Relic Tracker
alecaframe alternative for relic drop value tracking

relic-price-overlay/
│
├── config/
│   └── settings.yaml          # screen regions, thresholds, cache TTL, hotkeys
│
├── data/
│   └── items_cache.json       # cached list of WFM item names/slugs (auto-refreshed)
│
├── src/
│   ├── __init__.py
│   ├── capture.py             # mss-based screen grabbing + trigger detection
│   ├── preprocess.py          # OpenCV cleanup (grayscale, threshold, upscale)
│   ├── ocr.py                 # pytesseract wrapper, image -> raw string
│   ├── matcher.py             # rapidfuzz matching against items_cache
│   ├── market_api.py          # requests calls to warframe.market, price calc
│   ├── cache.py                # simple TTL cache for price lookups
│   ├── overlay.py             # Tkinter overlay window
│   └── orchestrator.py        # ties everything together, main loop
│
├── debug/
│   └── captures/              # dumped images for calibration (gitignored)
│
├── logs/
│   └── app.log                # unmatched items, OCR failures, API errors
│
├── main.py                    # entry point — just calls orchestrator
├── requirements.txt
├── .gitignore                 # ignore debug/, logs/, __pycache__, data/items_cache.json
└── README.md
