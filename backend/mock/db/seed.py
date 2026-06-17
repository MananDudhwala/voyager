"""
Seed script: populates flights.db, hotels.db, and pois.db with Indian mock data.
All prices are in INR (₹).

Run once before starting the mock API:
    python -m mock.db.seed
"""

from __future__ import annotations

import sqlite3
import random
import uuid
from datetime import date, timedelta
from pathlib import Path

DB_DIR = Path(__file__).parent
DB_DIR.mkdir(parents=True, exist_ok=True)

FLIGHTS_DB = DB_DIR / "flights.db"
HOTELS_DB = DB_DIR / "hotels.db"
POIS_DB = DB_DIR / "pois.db"

random.seed(42)


def _uid() -> str:
    return str(uuid.uuid4())[:8]


# ---------------------------------------------------------------------------
# Flights — Indian domestic + international routes, prices in INR
# ---------------------------------------------------------------------------

AIRLINES = [
    ("IndiGo", "6E"),
    ("Air India", "AI"),
    ("SpiceJet", "SG"),
    ("Vistara", "UK"),
    ("Go First", "G8"),
    ("AirAsia India", "I5"),
    ("Akasa Air", "QP"),
    ("Air India Express", "IX"),
]

# Domestic routes
DOMESTIC_ROUTES = [
    ("DEL", "BOM"),   # Delhi ↔ Mumbai
    ("DEL", "BLR"),   # Delhi ↔ Bangalore
    ("DEL", "MAA"),   # Delhi ↔ Chennai
    ("DEL", "HYD"),   # Delhi ↔ Hyderabad
    ("DEL", "GOI"),   # Delhi ↔ Goa
    ("DEL", "CCU"),   # Delhi ↔ Kolkata
    ("DEL", "JAI"),   # Delhi ↔ Jaipur
    ("DEL", "COK"),   # Delhi ↔ Kochi
    ("BOM", "BLR"),   # Mumbai ↔ Bangalore
    ("BOM", "MAA"),   # Mumbai ↔ Chennai
    ("BOM", "HYD"),   # Mumbai ↔ Hyderabad
    ("BOM", "GOI"),   # Mumbai ↔ Goa
    ("BOM", "JAI"),   # Mumbai ↔ Jaipur
    ("BOM", "COK"),   # Mumbai ↔ Kochi
    ("BLR", "HYD"),   # Bangalore ↔ Hyderabad
    ("BLR", "MAA"),   # Bangalore ↔ Chennai
    ("BLR", "COK"),   # Bangalore ↔ Kochi
]

# Return legs
ALL_ROUTES = DOMESTIC_ROUTES + [(dst, orig) for orig, dst in DOMESTIC_ROUTES]


def seed_flights() -> None:
    conn = sqlite3.connect(FLIGHTS_DB)
    conn.execute("DROP TABLE IF EXISTS flights")
    conn.execute(
        """
        CREATE TABLE flights (
            flight_id TEXT PRIMARY KEY,
            airline TEXT,
            flight_number TEXT,
            origin TEXT,
            destination TEXT,
            depart_date TEXT,
            depart_time TEXT,
            arrive_time TEXT,
            duration_minutes INTEGER,
            stops INTEGER,
            travel_class TEXT,
            price_per_person REAL,
            available_seats INTEGER,
            baggage_included INTEGER
        )
        """
    )

    rows = []
    base_date = date.today() + timedelta(days=30)

    for i in range(60):
        airline, code = random.choice(AIRLINES)
        origin, destination = random.choice(ALL_ROUTES)
        depart_date = base_date + timedelta(days=random.randint(0, 90))
        hour = random.randint(5, 22)
        # Domestic Indian flights: 1.5–3 hours
        duration = random.randint(90, 180)
        stops = random.choices([0, 1], weights=[75, 25])[0]
        # INR prices: ₹2,500 – ₹15,000 per person
        price = round(random.uniform(2500, 15000), 0)
        seats = random.randint(1, 40)

        rows.append((
            _uid(),
            airline,
            f"{code}{random.randint(100, 999)}",
            origin,
            destination,
            depart_date.isoformat(),
            f"{hour:02d}:00",
            f"{(hour + duration // 60) % 24:02d}:{duration % 60:02d}",
            duration,
            stops,
            "economy",
            price,
            seats,
            1,
        ))

    conn.executemany(
        """INSERT INTO flights VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        rows,
    )
    conn.commit()
    conn.close()
    print(f"✅  Seeded {len(rows)} flights → {FLIGHTS_DB}")


# ---------------------------------------------------------------------------
# Hotels — Indian cities, prices in INR per night
# ---------------------------------------------------------------------------

HOTEL_DATA = [
    # (name, city, tier, star, price_per_night_inr)
    # Goa
    ("The Leela Goa", "Goa", "luxury", 5.0, 18000),
    ("Taj Holiday Village Goa", "Goa", "luxury", 5.0, 22000),
    ("Novotel Goa Resort", "Goa", "upscale", 4.0, 8500),
    ("La Calypso Baga", "Goa", "midscale", 3.0, 3200),
    ("OYO Rooms Calangute Beach", "Goa", "budget", 2.0, 1200),
    # Jaipur
    ("Rambagh Palace", "Jaipur", "luxury", 5.0, 35000),
    ("Taj Jai Mahal Palace", "Jaipur", "luxury", 5.0, 28000),
    ("ITC Rajputana", "Jaipur", "upscale", 4.5, 9500),
    ("Sarovar Portico Jaipur", "Jaipur", "midscale", 3.5, 3800),
    ("Hotel Pearl Palace", "Jaipur", "budget", 2.5, 1500),
    # Udaipur
    ("The Oberoi Udaivilas", "Udaipur", "luxury", 5.0, 55000),
    ("Taj Lake Palace", "Udaipur", "luxury", 5.0, 42000),
    ("Radisson Blu Udaipur", "Udaipur", "upscale", 4.0, 7200),
    ("Hotel Mahendra Prakash", "Udaipur", "midscale", 3.0, 2800),
    ("Zostel Udaipur", "Udaipur", "budget", 2.0, 800),
    # Manali
    ("The Himalayan Manali", "Manali", "luxury", 5.0, 15000),
    ("Sterling Manali", "Manali", "upscale", 4.0, 6500),
    ("Snow Valley Resorts", "Manali", "midscale", 3.0, 3000),
    ("Zostel Manali", "Manali", "budget", 2.0, 700),
    ("Hotel Rockway Manali", "Manali", "budget", 2.5, 1200),
    # Kerala (Kochi)
    ("CGH Earth Brunton Boatyard", "Kochi", "luxury", 5.0, 16000),
    ("Taj Malabar Resort", "Kochi", "luxury", 5.0, 20000),
    ("Holiday Inn Kochi", "Kochi", "upscale", 4.0, 6800),
    ("Fort House Hotel Kochi", "Kochi", "midscale", 3.5, 3200),
    ("Zostel Kochi", "Kochi", "budget", 2.0, 900),
    # Varanasi
    ("Taj Ganges Varanasi", "Varanasi", "luxury", 5.0, 18000),
    ("Ramada Plaza Varanasi", "Varanasi", "upscale", 4.0, 6000),
    ("Brijrama Palace", "Varanasi", "upscale", 4.5, 12000),
    ("Hotel Surya Varanasi", "Varanasi", "midscale", 3.0, 2200),
    ("BrownBread Hostel Varanasi", "Varanasi", "budget", 2.0, 600),
]

AMENITIES_POOL = [
    ["WiFi", "Pool", "Spa", "Gym", "Restaurant", "Room Service", "Bar"],
    ["WiFi", "Breakfast", "Pool", "Gym"],
    ["WiFi", "Restaurant", "Parking", "Gym"],
    ["WiFi", "Room Service", "Bar", "Laundry"],
    ["WiFi", "Breakfast"],
]


def seed_hotels() -> None:
    conn = sqlite3.connect(HOTELS_DB)
    conn.execute("DROP TABLE IF EXISTS hotels")
    conn.execute(
        """
        CREATE TABLE hotels (
            hotel_id TEXT PRIMARY KEY,
            name TEXT,
            city TEXT,
            tier TEXT,
            star_rating REAL,
            price_per_night REAL,
            amenities TEXT,
            cancellation_policy TEXT,
            available INTEGER,
            latitude REAL,
            longitude REAL
        )
        """
    )

    CITY_COORDS = {
        "Goa": (15.2993, 74.1240),
        "Jaipur": (26.9124, 75.7873),
        "Udaipur": (24.5854, 73.7125),
        "Manali": (32.2432, 77.1892),
        "Kochi": (9.9312, 76.2673),
        "Varanasi": (25.3176, 82.9739),
    }

    rows = []
    for name, city, tier, star, ppn in HOTEL_DATA:
        lat, lon = CITY_COORDS[city]
        available = random.choices([1, 0], weights=[85, 15])[0]
        amenities = "|".join(random.choice(AMENITIES_POOL))
        rows.append((
            _uid(),
            name,
            city,
            tier,
            star,
            ppn,
            amenities,
            "Free cancellation up to 48h before check-in",
            available,
            round(lat + random.uniform(-0.05, 0.05), 6),
            round(lon + random.uniform(-0.05, 0.05), 6),
        ))

    conn.executemany(
        "INSERT INTO hotels VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        rows,
    )
    conn.commit()
    conn.close()
    print(f"✅  Seeded {len(rows)} hotels → {HOTELS_DB}")


# ---------------------------------------------------------------------------
# POIs — Indian destinations, entry fees in INR
# ---------------------------------------------------------------------------

POI_DATA = [
    # Goa
    ("Baga Beach", "Goa", "beach", "Lively beach known for water sports and shacks.", 15.5560, 73.7518, 180, 0, False),
    ("Calangute Beach", "Goa", "beach", "The Queen of Beaches — Goa's largest and most popular.", 15.5440, 73.7528, 150, 0, False),
    ("Basilica of Bom Jesus", "Goa", "religious", "UNESCO World Heritage church housing St. Francis Xavier's remains.", 15.5009, 73.9116, 60, 0, True),
    ("Fort Aguada", "Goa", "landmark", "17th-century Portuguese fort overlooking the Arabian Sea.", 15.4947, 73.7760, 90, 50, False),
    ("Dudhsagar Falls", "Goa", "landmark", "One of India's tallest waterfalls on the Goa-Karnataka border.", 15.3139, 74.3140, 240, 400, False),
    ("Saturday Night Market Arpora", "Goa", "shopping", "Vibrant flea market with Indian crafts, food, and live music.", 15.5560, 73.7630, 120, 0, False),
    ("Goa State Museum", "Goa", "museum", "Exhibits on Goa's cultural heritage and history.", 15.4975, 73.8278, 90, 10, True),
    ("Casino Goa", "Goa", "entertainment", "Floating casino on the Mandovi River.", 15.4921, 73.8148, 180, 2000, True),
    ("Anjuna Flea Market", "Goa", "shopping", "Famous Wednesday market with antiques and clothing.", 15.5789, 73.7409, 120, 0, False),
    ("Chapora Fort", "Goa", "landmark", "Hilltop fort offering panoramic views — made famous by Dil Chahta Hai.", 15.6009, 73.7392, 60, 0, False),
    # Jaipur
    ("Amber Fort", "Jaipur", "landmark", "Magnificent hilltop Rajput fort with mirror palace.", 26.9855, 75.8513, 180, 100, False),
    ("City Palace Jaipur", "Jaipur", "landmark", "Royal palace complex in the heart of the Pink City.", 26.9258, 75.8237, 120, 200, True),
    ("Hawa Mahal", "Jaipur", "landmark", "Palace of Winds — iconic five-storey pink sandstone façade.", 26.9239, 75.8267, 60, 50, False),
    ("Jantar Mantar Jaipur", "Jaipur", "landmark", "UNESCO-listed 18th-century astronomical observatory.", 26.9247, 75.8242, 90, 50, False),
    ("Jaipur Literature Festival Venue", "Jaipur", "entertainment", "World's largest free literary festival at Diggi Palace.", 26.8894, 75.8028, 120, 0, True),
    ("Albert Hall Museum", "Jaipur", "museum", "Oldest museum of Rajasthan with artefacts and Egyptian mummy.", 26.9037, 75.8193, 120, 150, True),
    ("Johari Bazaar", "Jaipur", "shopping", "Traditional market for gems, jewellery, and fabrics.", 26.9178, 75.8242, 90, 0, False),
    ("Nahargarh Fort", "Jaipur", "landmark", "Hilltop fort with sunset views of Jaipur city.", 26.9427, 75.8084, 120, 50, False),
    ("Birla Mandir Jaipur", "Jaipur", "religious", "Lakshmi Narayan temple made of white marble.", 26.8936, 75.8119, 60, 0, True),
    ("Chokhi Dhani", "Jaipur", "entertainment", "Ethnic Rajasthani village experience with folk arts.", 26.7773, 75.8567, 180, 700, False),
    # Udaipur
    ("City Palace Udaipur", "Udaipur", "landmark", "Largest palace complex in Rajasthan, overlooking Lake Pichola.", 24.5752, 73.6830, 180, 300, True),
    ("Lake Pichola", "Udaipur", "landmark", "Scenic artificial lake with island palaces — boat ride included.", 24.5744, 73.6807, 90, 400, False),
    ("Jagdish Temple", "Udaipur", "religious", "Largest temple in Udaipur, dedicated to Lord Vishnu.", 24.5775, 73.6827, 60, 0, True),
    ("Saheliyon Ki Bari", "Udaipur", "park", "Garden of the Maidens with fountains and lotus pools.", 24.5878, 73.6801, 60, 25, False),
    ("Fateh Sagar Lake", "Udaipur", "landmark", "Man-made lake with a small island garden.", 24.5970, 73.6735, 60, 0, False),
    ("Bagore Ki Haveli", "Udaipur", "museum", "18th-century haveli with royal artifacts and puppet shows.", 24.5757, 73.6843, 90, 100, True),
    ("Shilpgram Crafts Village", "Udaipur", "shopping", "Rural arts and crafts complex showcasing tribal culture.", 24.6026, 73.6672, 120, 50, False),
    # Manali
    ("Solang Valley", "Manali", "landmark", "Scenic valley known for skiing, zorbing, and paragliding.", 32.3177, 77.1527, 240, 0, False),
    ("Rohtang Pass", "Manali", "landmark", "High mountain pass with snow even in summer.", 32.3744, 77.2504, 300, 550, False),
    ("Hadimba Temple", "Manali", "religious", "Unique wooden temple dedicated to Goddess Hadimba in cedar forest.", 32.2337, 77.1760, 60, 0, True),
    ("Mall Road Manali", "Manali", "shopping", "Main shopping street for woolens, artifacts, and street food.", 32.2432, 77.1892, 90, 0, False),
    ("Beas River", "Manali", "entertainment", "River rafting and riverside walks.", 32.2390, 77.1915, 120, 600, False),
    ("Museum of Himachal Culture", "Manali", "museum", "Cultural artifacts and exhibits on Himachali life.", 32.2418, 77.1881, 60, 20, True),
    ("Vashisht Hot Springs", "Manali", "landmark", "Natural sulphur hot springs in a traditional village.", 32.2572, 77.2017, 60, 0, False),
    # Kochi
    ("Chinese Fishing Nets", "Kochi", "landmark", "Iconic cantilevered fishing nets on Fort Kochi waterfront.", 9.9646, 76.2432, 60, 0, False),
    ("Mattancherry Palace", "Kochi", "museum", "16th-century Portuguese palace with Kerala murals.", 9.9569, 76.2596, 90, 5, True),
    ("Jewish Synagogue Mattancherry", "Kochi", "religious", "Oldest active synagogue in the Commonwealth.", 9.9553, 76.2609, 60, 5, True),
    ("Fort Kochi Beach", "Kochi", "beach", "Serene beach with views of container ships and backwaters.", 9.9626, 76.2422, 90, 0, False),
    ("Backwater Houseboat Cruise", "Kochi", "entertainment", "Half-day houseboat experience through Kerala backwaters.", 9.9312, 76.2673, 240, 1500, False),
    ("Kerala Folklore Museum", "Kochi", "museum", "Three-storeyed museum with 4,000+ antique artefacts.", 9.9890, 76.2943, 90, 100, True),
    ("Spice Market Ernakulam", "Kochi", "shopping", "Wholesale spice market with cardamom, pepper, and more.", 9.9826, 76.2880, 60, 0, False),
    # Varanasi
    ("Dashashwamedh Ghat", "Varanasi", "landmark", "Main ghat and site of spectacular nightly Ganga Aarti.", 25.3067, 83.0107, 120, 0, False),
    ("Kashi Vishwanath Temple", "Varanasi", "religious", "One of India's holiest Shiva temples on the banks of the Ganges.", 25.3109, 83.0107, 90, 0, True),
    ("Sarnath", "Varanasi", "landmark", "Deer Park where Buddha gave his first sermon — Buddhist pilgrimage site.", 25.3795, 83.0239, 150, 20, False),
    ("Manikarnika Ghat", "Varanasi", "landmark", "Sacred cremation ghat on the Ganges, burning 24/7.", 25.3097, 83.0125, 60, 0, False),
    ("Bharat Kala Bhavan Museum", "Varanasi", "museum", "Museum at BHU with textiles, paintings, and antiquities.", 25.2677, 82.9913, 120, 30, True),
    ("Morning Boat Ride on Ganges", "Varanasi", "entertainment", "Sunrise boat ride past the ghats — mystical experience.", 25.3067, 83.0107, 90, 500, False),
    ("Vishwanath Lane Market", "Varanasi", "shopping", "Narrow lanes with silk sarees, religious items, and sweets.", 25.3109, 83.0107, 90, 0, False),
    ("Tulsi Manas Temple", "Varanasi", "religious", "Modern marble temple dedicated to Lord Rama.", 25.3073, 83.0010, 45, 0, True),
]


def seed_pois() -> None:
    conn = sqlite3.connect(POIS_DB)
    conn.execute("DROP TABLE IF EXISTS pois")
    conn.execute(
        """
        CREATE TABLE pois (
            poi_id TEXT PRIMARY KEY,
            name TEXT,
            city TEXT,
            category TEXT,
            description TEXT,
            latitude REAL,
            longitude REAL,
            estimated_duration_minutes INTEGER,
            entry_fee_usd REAL,
            is_indoor INTEGER,
            rating REAL
        )
        """
    )

    rows = []
    for name, city, cat, desc, lat, lon, dur, fee, indoor in POI_DATA:
        rows.append((
            _uid(),
            name,
            city,
            cat,
            desc,
            lat,
            lon,
            dur,
            fee,   # entry fee in INR (stored in the "entry_fee_usd" column, now represents INR)
            1 if indoor else 0,
            round(random.uniform(3.9, 5.0), 1),
        ))

    conn.executemany(
        "INSERT INTO pois VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        rows,
    )
    conn.commit()
    conn.close()
    print(f"✅  Seeded {len(rows)} POIs → {POIS_DB}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    seed_flights()
    seed_hotels()
    seed_pois()
    print("\n🎉  All databases seeded successfully (Indian routes, ₹ prices).")
