"""
Seed script: populates flights.db, hotels.db, and pois.db with realistic mock data.

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

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _uid() -> str:
    return str(uuid.uuid4())[:8]


# ---------------------------------------------------------------------------
# Flights — ~50 rows
# ---------------------------------------------------------------------------

AIRLINES = [
    ("Air France", "AF"),
    ("Delta", "DL"),
    ("United", "UA"),
    ("British Airways", "BA"),
    ("Lufthansa", "LH"),
    ("Emirates", "EK"),
    ("American Airlines", "AA"),
    ("KLM", "KL"),
    ("Singapore Airlines", "SQ"),
    ("Qatar Airways", "QR"),
]

ROUTES = [
    ("JFK", "CDG"),
    ("JFK", "LHR"),
    ("LAX", "CDG"),
    ("ORD", "FRA"),
    ("JFK", "NRT"),
    ("LAX", "SYD"),
    ("JFK", "DXB"),
    ("BOS", "CDG"),
    ("MIA", "LHR"),
    ("SFO", "NRT"),
]


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

    for i in range(52):
        airline, code = random.choice(AIRLINES)
        origin, destination = random.choice(ROUTES)
        depart_date = base_date + timedelta(days=random.randint(0, 90))
        hour = random.randint(5, 22)
        duration = random.randint(360, 840)  # 6–14 hours
        stops = random.choices([0, 1, 2], weights=[50, 35, 15])[0]
        price = round(random.uniform(280, 1800), 2)
        seats = random.randint(1, 30)

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
# Hotels — ~30 rows
# ---------------------------------------------------------------------------

HOTEL_DATA = [
    # (name, city, tier, star, price_per_night)
    ("Le Marais Boutique", "Paris", "upscale", 4.0, 180),
    ("Hôtel de Fleurie", "Paris", "midscale", 3.5, 110),
    ("Budget Inn Montparnasse", "Paris", "budget", 2.0, 65),
    ("Ritz Paris", "Paris", "luxury", 5.0, 950),
    ("The Savoy", "London", "luxury", 5.0, 820),
    ("Premier Inn Waterloo", "London", "budget", 2.5, 75),
    ("Marriott Park Lane", "London", "upscale", 4.5, 280),
    ("citizenM Shoreditch", "London", "midscale", 3.5, 140),
    ("Hotel de Rome", "Berlin", "upscale", 4.5, 220),
    ("Meininger Berlin", "Berlin", "budget", 2.0, 55),
    ("Hotel Adlon Kempinski", "Berlin", "luxury", 5.0, 680),
    ("25hours Hotel", "Berlin", "midscale", 3.5, 120),
    ("Aman Tokyo", "Tokyo", "luxury", 5.0, 1100),
    ("Dormy Inn Asakusa", "Tokyo", "midscale", 3.0, 95),
    ("Khaosan World Kabuki", "Tokyo", "budget", 2.0, 45),
    ("Park Hyatt Tokyo", "Tokyo", "luxury", 5.0, 780),
    ("Sofitel Dubai", "Dubai", "luxury", 5.0, 420),
    ("Ibis Dubai", "Dubai", "budget", 2.5, 70),
    ("JW Marriott Dubai", "Dubai", "upscale", 4.5, 310),
    ("Citymax Hotel Dubai", "Dubai", "midscale", 3.0, 105),
    ("Park Hyatt Sydney", "Sydney", "luxury", 5.0, 580),
    ("Ibis Sydney", "Sydney", "budget", 2.5, 80),
    ("QT Sydney", "Sydney", "upscale", 4.5, 250),
    ("Meriton Suites Sydney", "Sydney", "midscale", 3.5, 130),
    ("The St. Regis New York", "New York", "luxury", 5.0, 900),
    ("Pod 51 Hotel", "New York", "budget", 2.5, 90),
    ("citizenM New York", "New York", "midscale", 3.5, 160),
    ("The Peninsula Chicago", "Chicago", "luxury", 5.0, 560),
    ("Hampton Inn Chicago", "Chicago", "midscale", 3.0, 130),
    ("Freehand Chicago", "Chicago", "budget", 2.5, 85),
]

AMENITIES_POOL = [
    ["WiFi", "Breakfast", "Pool", "Spa", "Gym", "Concierge", "Bar"],
    ["WiFi", "Gym", "Breakfast"],
    ["WiFi", "Parking", "Gym"],
    ["WiFi", "Pool", "Bar", "Room Service"],
    ["WiFi", "Breakfast", "Bar"],
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
        "Paris": (48.8566, 2.3522),
        "London": (51.5074, -0.1278),
        "Berlin": (52.5200, 13.4050),
        "Tokyo": (35.6762, 139.6503),
        "Dubai": (25.2048, 55.2708),
        "Sydney": (-33.8688, 151.2093),
        "New York": (40.7128, -74.0060),
        "Chicago": (41.8781, -87.6298),
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
# POIs — ~100 rows
# ---------------------------------------------------------------------------

POI_DATA = [
    # Paris
    ("Eiffel Tower", "Paris", "landmark", "Iconic iron lattice tower on the Champ de Mars.", 48.8584, 2.2945, 120, 28.0, False),
    ("Louvre Museum", "Paris", "museum", "World's largest art museum and a historic monument.", 48.8606, 2.3376, 180, 17.0, True),
    ("Musée d'Orsay", "Paris", "museum", "Impressionist art in a converted railway station.", 48.8600, 2.3266, 150, 16.0, True),
    ("Notre-Dame Cathedral", "Paris", "religious", "Medieval Catholic cathedral on the Île de la Cité.", 48.8529, 2.3500, 90, 0.0, True),
    ("Luxembourg Gardens", "Paris", "park", "Formal French gardens with fountains and statues.", 48.8462, 2.3372, 60, 0.0, False),
    ("Palace of Versailles", "Paris", "landmark", "Royal château and gardens southwest of Paris.", 48.8049, 2.1204, 240, 18.0, False),
    ("Sacré-Cœur", "Paris", "religious", "White-domed basilica atop the Montmartre hill.", 48.8867, 2.3431, 60, 0.0, False),
    ("Centre Pompidou", "Paris", "museum", "Modern art museum with distinctive architecture.", 48.8607, 2.3522, 120, 15.0, True),
    ("Champs-Élysées", "Paris", "shopping", "Iconic avenue lined with shops and cafés.", 48.8698, 2.3078, 90, 0.0, False),
    ("Seine River Cruise", "Paris", "entertainment", "One-hour boat tour along the Seine.", 48.8583, 2.3404, 75, 15.0, False),
    # London
    ("British Museum", "London", "museum", "World-class collection of human history and culture.", 51.5194, -0.1270, 180, 0.0, True),
    ("Tower of London", "London", "landmark", "Historic castle and home of the Crown Jewels.", 51.5081, -0.0759, 120, 30.0, True),
    ("Hyde Park", "London", "park", "Royal park in central London.", 51.5073, -0.1657, 90, 0.0, False),
    ("Tate Modern", "London", "museum", "Modern and contemporary art in a former power station.", 51.5076, -0.0994, 120, 0.0, True),
    ("Covent Garden", "London", "shopping", "Market and entertainment district.", 51.5117, -0.1240, 90, 0.0, False),
    ("Westminster Abbey", "London", "religious", "Gothic abbey church and royal coronation venue.", 51.4994, -0.1273, 90, 27.0, True),
    ("Buckingham Palace", "London", "landmark", "Official London residence of the monarch.", 51.5014, -0.1419, 60, 0.0, False),
    ("The Shard", "London", "landmark", "Skyscraper with a public viewing gallery.", 51.5045, -0.0865, 60, 32.0, True),
    ("Borough Market", "London", "restaurant", "London's oldest food market.", 51.5055, -0.0910, 60, 0.0, False),
    ("National Gallery", "London", "museum", "Western European paintings from the 13th to 19th centuries.", 51.5089, -0.1283, 120, 0.0, True),
    # Berlin
    ("Brandenburg Gate", "Berlin", "landmark", "Neoclassical triumphal arch, Berlin's symbol.", 52.5163, 13.3777, 45, 0.0, False),
    ("Berlin Wall Memorial", "Berlin", "landmark", "Documentation and memorial site of the former wall.", 52.5351, 13.3904, 90, 0.0, False),
    ("Pergamon Museum", "Berlin", "museum", "Reconstructed ancient architecture including the Pergamon Altar.", 52.5212, 13.3970, 150, 12.0, True),
    ("Tiergarten", "Berlin", "park", "Large urban park in the heart of Berlin.", 52.5145, 13.3501, 90, 0.0, False),
    ("East Side Gallery", "Berlin", "landmark", "Outdoor gallery on a surviving section of the Berlin Wall.", 52.5054, 13.4394, 60, 0.0, False),
    ("Charlottenburg Palace", "Berlin", "landmark", "Baroque palace and gardens.", 52.5206, 13.2956, 120, 12.0, False),
    ("Topography of Terror", "Berlin", "museum", "Documentation centre on Nazi terror and the SS.", 52.5073, 13.3819, 90, 0.0, True),
    ("Berlin Zoo", "Berlin", "entertainment", "One of the world's most popular zoos.", 52.5081, 13.3372, 180, 20.0, False),
    ("Hackescher Markt", "Berlin", "shopping", "Trendy courtyard complex with shops and restaurants.", 52.5227, 13.4018, 90, 0.0, False),
    ("Jewish Museum Berlin", "Berlin", "museum", "History of Jews in Germany over two millennia.", 52.5021, 13.3938, 120, 8.0, True),
    # Tokyo
    ("Senso-ji Temple", "Tokyo", "religious", "Tokyo's oldest temple in Asakusa.", 35.7148, 139.7967, 90, 0.0, False),
    ("Shibuya Crossing", "Tokyo", "landmark", "World's busiest pedestrian crossing.", 35.6595, 139.7005, 30, 0.0, False),
    ("Tokyo National Museum", "Tokyo", "museum", "Japan's oldest and largest museum.", 35.7189, 139.7760, 150, 10.0, True),
    ("Shinjuku Gyoen", "Tokyo", "park", "Large national garden with Japanese, French and English sections.", 35.6852, 139.7100, 90, 5.0, False),
    ("teamLab Borderless", "Tokyo", "entertainment", "Immersive digital art museum.", 35.6254, 139.7753, 180, 32.0, True),
    ("Meiji Shrine", "Tokyo", "religious", "Shinto shrine dedicated to Emperor Meiji.", 35.6764, 139.6993, 60, 0.0, False),
    ("Tsukiji Outer Market", "Tokyo", "restaurant", "Famous fish market with fresh sushi and street food.", 35.6654, 139.7706, 90, 0.0, False),
    ("Akihabara", "Tokyo", "shopping", "Electronics and anime shopping district.", 35.7022, 139.7742, 120, 0.0, False),
    ("Harajuku Takeshita Street", "Tokyo", "shopping", "Youth fashion and street food in Harajuku.", 35.6702, 139.7026, 90, 0.0, False),
    ("Tokyo Skytree", "Tokyo", "landmark", "World's second-tallest structure with observation decks.", 35.7101, 139.8107, 90, 22.0, True),
    # Dubai
    ("Burj Khalifa", "Dubai", "landmark", "World's tallest building with observation decks.", 25.1972, 55.2744, 90, 40.0, True),
    ("Dubai Mall", "Dubai", "shopping", "One of the world's largest shopping centres.", 25.1983, 55.2791, 180, 0.0, True),
    ("Dubai Museum", "Dubai", "museum", "History of Dubai in the Al Fahidi Fort.", 25.2644, 55.2975, 90, 3.0, True),
    ("Palm Jumeirah", "Dubai", "landmark", "Artificial palm-shaped archipelago.", 25.1124, 55.1390, 60, 0.0, False),
    ("Gold Souk", "Dubai", "shopping", "Traditional market for gold jewellery.", 25.2856, 55.3026, 90, 0.0, False),
    ("Desert Safari", "Dubai", "entertainment", "Dune bashing, camel ride, and Bedouin camp dinner.", 24.9000, 55.1000, 360, 85.0, False),
    ("Dubai Aquarium", "Dubai", "entertainment", "One of the world's largest indoor aquariums.", 25.1983, 55.2791, 90, 30.0, True),
    ("Jumeirah Beach", "Dubai", "beach", "White sand beach with views of the Burj Al Arab.", 25.1412, 55.1852, 120, 0.0, False),
    # Sydney
    ("Sydney Opera House", "Sydney", "landmark", "Iconic multi-venue performing arts centre.", -33.8568, 151.2153, 90, 45.0, True),
    ("Bondi Beach", "Sydney", "beach", "Famous surf beach in eastern Sydney.", -33.8908, 151.2743, 120, 0.0, False),
    ("Taronga Zoo", "Sydney", "entertainment", "Harbour-side zoo with Australian wildlife.", -33.8432, 151.2411, 180, 46.0, False),
    ("Royal Botanic Garden", "Sydney", "park", "Living museum adjacent to the Sydney CBD.", -33.8642, 151.2166, 90, 0.0, False),
    ("Australian Museum", "Sydney", "museum", "Natural history and culture museum.", -33.8742, 151.2131, 120, 15.0, True),
    ("The Rocks", "Sydney", "landmark", "Historic district with sandstone buildings and markets.", -33.8599, 151.2090, 90, 0.0, False),
    ("Darling Harbour", "Sydney", "entertainment", "Waterfront precinct with museums, aquarium, and restaurants.", -33.8721, 151.1988, 120, 0.0, False),
    ("Manly Beach", "Sydney", "beach", "Surf beach accessed by ferry from Circular Quay.", -33.7972, 151.2876, 180, 0.0, False),
    # New York
    ("Metropolitan Museum of Art", "New York", "museum", "One of the world's greatest art museums.", 40.7794, -73.9632, 240, 25.0, True),
    ("Central Park", "New York", "park", "843-acre urban park in Manhattan.", 40.7851, -73.9683, 180, 0.0, False),
    ("Statue of Liberty", "New York", "landmark", "Iconic copper statue on Liberty Island.", 40.6892, -74.0445, 180, 24.0, False),
    ("Brooklyn Bridge", "New York", "landmark", "Iconic suspension bridge connecting Manhattan and Brooklyn.", 40.7061, -73.9969, 60, 0.0, False),
    ("MoMA", "New York", "museum", "Museum of Modern Art with an unmatched collection.", 40.7614, -73.9776, 150, 25.0, True),
    ("High Line", "New York", "park", "Elevated linear park on a disused railway line.", 40.7480, -74.0048, 90, 0.0, False),
    ("Times Square", "New York", "landmark", "Neon-lit commercial hub of Midtown Manhattan.", 40.7580, -73.9855, 45, 0.0, False),
    ("One World Observatory", "New York", "landmark", "Observation deck atop One World Trade Center.", 40.7130, -74.0134, 90, 45.0, True),
    # Chicago
    ("Art Institute of Chicago", "Chicago", "museum", "Encyclopedic art museum in Grant Park.", 41.8796, -87.6237, 180, 25.0, True),
    ("Millennium Park", "Chicago", "park", "Iconic park home to Cloud Gate (The Bean).", 41.8827, -87.6233, 90, 0.0, False),
    ("Willis Tower Skydeck", "Chicago", "landmark", "Glass-floor observation deck on the 103rd floor.", 41.8789, -87.6359, 90, 28.0, True),
    ("Navy Pier", "Chicago", "entertainment", "Lakefront entertainment complex.", 41.8917, -87.6086, 120, 0.0, False),
    ("Chicago Riverwalk", "Chicago", "park", "Pedestrian walkway along the Chicago River.", 41.8869, -87.6310, 60, 0.0, False),
    ("Field Museum", "Chicago", "museum", "Natural history museum with the largest T. rex skeleton.", 41.8662, -87.6170, 180, 24.0, True),
    ("Wrigley Field", "Chicago", "sport", "Historic baseball stadium, home of the Cubs.", 41.9484, -87.6553, 180, 40.0, False),
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
            fee,
            1 if indoor else 0,
            round(random.uniform(3.8, 5.0), 1),
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
    print("\n🎉  All databases seeded successfully.")
