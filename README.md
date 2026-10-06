# Google Flights Price Tracker (Python)

Track flight prices from Google Flights in Python and get a Telegram alert when a fare drops.

Google has no public Google Flights API. This script gets the data through the [Google Flights Scraper](https://apify.com/data_xplorer/google-flights-scraper) Actor on Apify, which works as a Google Flights API alternative: you send routes and dates, you get every flight as JSON.

What the script does on each run:

1. searches Google Flights for your routes and dates,
2. keeps the cheapest fare of each route in `price_history.csv`,
3. sends a Telegram message when a fare is under your target price or hits a new low.

Step-by-step tutorial: [Build a Google Flights Price Tracker in Python](https://dev.to/data_xplorer/build-a-google-flights-price-tracker-in-python-no-official-api-needed-2o1a).

## Quick start

You need Python 3.9+ and an [Apify](https://apify.com) account (the free plan includes monthly credits).

```bash
git clone https://github.com/dataxplore19/google-flights-price-tracker.git
cd google-flights-price-tracker
pip install -r requirements.txt
export APIFY_TOKEN="your_apify_token"
python tracker.py
```

Telegram alerts are optional. Without the two variables below, alerts are printed to the console.

```bash
export TELEGRAM_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"
```

## Configuration

Edit the top of `tracker.py`:

```python
SEARCHES = [
    {"from": "CDG", "to": "JFK", "departureDate": "2026-12-26", "returnDate": "2027-01-04"},
    {"from": "LHR", "to": "DXB", "departureDate": "30 days"},
]

TARGETS = {("CDG", "JFK"): 450, ("LHR", "DXB"): 300}

CURRENCY = "EUR"
COUNTRY = "FR"
```

- `from` and `to` take airport codes (`CDG`), city codes (`PAR`) or city names (`Paris`).
- Dates are absolute (`2026-12-26`) or relative (`30 days`). Relative dates suit a daily job: each run looks the same distance ahead.
- Leave `returnDate` out for a one-way flight.
- Keep `CURRENCY` and `COUNTRY` fixed. Fares differ by country of search, so changing them breaks the price history.

## Example output

Console, when a fare drops:

```
185 flights found
CDG -> JFK on 2026-12-26: 440 EUR with Delta (under your target of 450, new low (was 521))
https://www.google.com/travel/flights/search?tfs=...
```

`price_history.csv`:

```csv
checkedOn,from,to,departureDate,price,currency,airline
2026-10-06,CDG,JFK,2026-12-26,521,EUR,Delta
2026-10-06,LHR,DXB,2026-11-05,410,EUR,Royal Jordanian
```

## Data returned for each flight

The script only uses the price, but each flight comes with much more:

| Data | Fields |
| --- | --- |
| Price | `price`, `currency`, `isCheapest` |
| Flights | `airline`, `flightNumbers`, `legs` |
| Schedule | `departureDate`, `departureTime`, `arrivalTime`, `duration`, `durationMinutes` |
| Route | `departureAirport`, `arrivalAirport`, `stops`, `layovers` |
| Environment | `co2EmissionsKg`, `typicalCo2EmissionsKg`, `emissionsVsTypicalPercent` |
| Links | `googleFlightsUrl` |

Useful options to add to `run_input` in `search_flights()`:

- `"priceCalendar": true`: the cheapest price of each departure date around your date, up to 330 days
- `"bookingOptions": true`: every seller (airline or travel agency) with its price and booking link
- `"maxPrice"`, `"airlines"`, `"excludeAirlines"`, `"maxDurationHours"`, `"checkedBags"`: filters

The full list is on the [Actor's input page](https://apify.com/data_xplorer/google-flights-scraper/input-schema).

## Run it every day

With cron, every morning at 8:00:

```bash
0 8 * * * cd /path/to/google-flights-price-tracker && APIFY_TOKEN=your_apify_token /usr/bin/python3 tracker.py
```

## Cost

The scraper is billed per result, from $0.75 to $1.50 per 1,000 flights depending on your Apify plan. The example above (2 searches, 185 flights) costs about $0.28 on the free plan's rate.

## FAQ

### Is there an official Google Flights API?

No. Google closed its QPX Express API in 2018 and has not released a replacement.

### Is scraping Google Flights legal?

The data is public and contains no personal information. Rules depend on your country and use case, so check what applies to you.

## Disclosure

I am the author of the Google Flights Scraper Actor used by this script.

## License

MIT
