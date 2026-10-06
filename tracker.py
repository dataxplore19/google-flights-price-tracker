"""Google Flights price tracker.

Searches Google Flights through the Apify Actor data_xplorer/google-flights-scraper,
keeps the cheapest fare of each route in a CSV file, and sends a Telegram message
when a fare goes under your target price or hits a new low.
"""
import csv
import os
from datetime import date
from pathlib import Path

import requests
from apify_client import ApifyClient

ACTOR = "data_xplorer/google-flights-scraper"
HISTORY = Path("price_history.csv")

# One entry per search. Dates can be absolute ("2026-12-26") or relative ("30 days").
SEARCHES = [
    {"from": "CDG", "to": "JFK", "departureDate": "2026-12-26", "returnDate": "2027-01-04"},
    {"from": "LHR", "to": "DXB", "departureDate": "30 days"},
]

# Alert when the cheapest fare of a route is at or below this price.
TARGETS = {("CDG", "JFK"): 450, ("LHR", "DXB"): 300}

# Keep these two fixed, or the price history mixes fares that are not comparable.
CURRENCY = "EUR"
COUNTRY = "FR"


def search_flights():
    client = ApifyClient(os.environ["APIFY_TOKEN"])
    run = client.actor(ACTOR).call(run_input={
        "flights": SEARCHES,
        "currency": CURRENCY,
        "country": COUNTRY,
        "maxStops": "1",
    })
    return list(client.dataset(run["defaultDatasetId"]).iterate_items())


def cheapest_by_route(flights):
    best = {}
    for f in flights:
        if not f.get("price"):
            continue
        key = (f["departureAirport"], f["arrivalAirport"], f["departureDate"])
        if key not in best or f["price"] < best[key]["price"]:
            best[key] = f
    return best


def previous_low(key):
    if not HISTORY.exists():
        return None
    with HISTORY.open() as fh:
        prices = [
            float(row["price"]) for row in csv.DictReader(fh)
            if (row["from"], row["to"], row["departureDate"]) == key
        ]
    return min(prices) if prices else None


def save(key, flight):
    new_file = not HISTORY.exists()
    with HISTORY.open("a", newline="") as fh:
        writer = csv.writer(fh)
        if new_file:
            writer.writerow(["checkedOn", "from", "to", "departureDate", "price", "currency", "airline"])
        writer.writerow([date.today(), *key, flight["price"], flight["currency"], flight["airline"]])


def notify(text):
    token, chat = os.environ.get("TELEGRAM_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        print(text)
        return
    requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat, "text": text},
        timeout=30,
    )


def main():
    flights = search_flights()
    print(f"{len(flights)} flights found")

    for key, flight in cheapest_by_route(flights).items():
        origin, destination, day = key
        price = flight["price"]
        low = previous_low(key)
        target = TARGETS.get((origin, destination))

        reasons = []
        if target and price <= target:
            reasons.append(f"under your target of {target}")
        if low is not None and price < low:
            reasons.append(f"new low (was {low:g})")

        if reasons:
            notify(
                f"{origin} -> {destination} on {day}: {price} {flight['currency']} "
                f"with {flight['airline']} ({', '.join(reasons)})\n{flight['googleFlightsUrl']}"
            )
        save(key, flight)


if __name__ == "__main__":
    main()
