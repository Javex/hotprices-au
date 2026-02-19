# hotprices-au

Australian supermarket price scraper and price history tracker. Fetches product and pricing data from Coles and Woolworths on a daily basis, normalises it into a canonical format, and stores it for historical comparison.

A fork of [heissepreise](https://github.com/badlogic/heissepreise), rewritten in Python for the Australian market.

---

## Requirements

- Python 3.11+
- pip

Install Python dependencies:

```bash
pip3 install -r requirements.txt
```

Install Playwright browser binaries (required for Coles):

```bash
playwright install chromium
```

Install camoufox browser profile (required for Coles):

```bash
python3 -m camoufox fetch
```

---

## Usage

All commands are run via `main.py`.

### Scrape a store

```bash
python3 main.py sync <store>
```

`<store>` is one of: `coles`, `woolies`

**Options:**

| Flag | Description |
|------|-------------|
| `--quick` | Fetch only the first category/page (useful for testing) |
| `--category <name>` | Fetch a single category by name or slug |
| `--page <n>` | Fetch a specific page within a category |
| `--request-delay <seconds>` | Delay between page requests to avoid bot protection (default: `2.0`, set to `0` to disable) |
| `--skip-existing` | Skip if output file for today already exists |
| `--print-save-path` | Print the output file path and exit |
| `--output-dir <path>` | Output directory (default: `./output`) |

**Examples:**

```bash
# Full Coles scrape
python3 main.py sync coles

# Quick test (first category only)
python3 main.py sync --quick coles

# Scrape without delay (faster, higher bot-detection risk)
python3 main.py sync coles --request-delay 0

# Scrape a single Woolworths category
python3 main.py sync woolies --category "Fruit & Veg"

# Scrape one page of a Coles category
python3 main.py sync coles --category "Pantry" --page 2
```

### Merge price history

Transforms scraped data and merges it into the canonical price history file:

```bash
python3 main.py analysis
```

**Options:**

| Flag | Description |
|------|-------------|
| `--store <store>` | Limit to one store |
| `--day <YYYY-MM-DD>` | Process a specific date (default: today) |
| `--compress` | Compress per-store output files |
| `--history` | Rebuild full price history from all source files |

**Examples:**

```bash
# Standard daily analysis
python3 main.py analysis

# Rebuild full Coles history from scratch
python3 main.py analysis --store coles --history --compress
```

---

## Output

Scraped data is written to `./output/<store>/` as JSON files. After running analysis, the merged canonical price history is written to `./output/latest-canonical.json.gz`.

### Canonical product format

Each product in the canonical output has the following fields:

| Field | Description |
|-------|-------------|
| `id` | Store product ID |
| `name` | Full product name (brand + name) |
| `price` | Current price in AUD |
| `priceHistory` | Array of `{ date, price }` objects in descending date order |
| `unit` | Unit of measure (e.g. `g`, `ml`, `ea`) |
| `quantity` | Quantity for the given price |
| `isWeighted` | Whether the product is sold by weight |

---

## Scraper notes

### Coles

The Coles scraper uses [camoufox](https://github.com/daijro/camoufox) (a stealth Firefox wrapper built on Playwright) to bypass bot protection. It navigates the Coles homepage on startup to capture a live API key from network traffic, then uses that key for subsequent API requests.

Key behaviours:
- **Top-level categories only** — subcategories are skipped to avoid duplicate products
- **Online-only products excluded** — products not available in physical stores are filtered out
- **Promotional categories excluded** — `down-down`, `back-to-school`, and `bonus-credit-products` are skipped as they duplicate products from real categories
- **Request delay** — a configurable delay (default 2 seconds) is applied between page requests to reduce bot detection; set `--request-delay 0` to disable
- **Auto-reset** — if bot protection is detected mid-scrape, the browser context resets and retries automatically (up to 5 times)

### Woolworths

The Woolworths scraper uses the public HTTP API directly, with no browser automation required.

---

## Docker

```bash
docker build -t hotprices-au .
docker run hotprices-au sync --quick coles
```

---

## Running tests

```bash
pip3 install -r requirements.dev.txt
PYTHONPATH=. pytest -v tests
```

---

## Project structure

```
hotprices_au/
  sites/
    coles.py        # Coles scraper (camoufox + Playwright)
    woolies.py      # Woolworths scraper (HTTP API)
  data/
    coles-categories.json    # Saved category ID mappings
    woolies-categories.json
  analysis.py       # Price history merging and transformation
  categories.py     # Category ID mapping persistence
  output.py         # File save helpers
  request.py        # Shared HTTP session setup
  units.py          # Unit parsing (e.g. price per 100g)
tests/              # pytest test suite
main.py             # CLI entrypoint
requirements.txt    # Runtime dependencies
requirements.dev.txt
Dockerfile
```

---

## Credits

Based on [heissepreise](https://github.com/badlogic/heissepreise) by [@badlogic](https://github.com/badlogic).
