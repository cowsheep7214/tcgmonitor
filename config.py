# config.py — TCG Stock Monitor
import os

POLL_INTERVAL = 60
DEFAULT_ZIP = "78701"

DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1480946587541966928/S6skH2cfr_ABqaxQ3jSTlFSov_1hxuSCjtIuU2KVH7_DxTvLvqGsbsN7_LsgZ9saaZPz"

AUSTIN_TARGET_ZIPS = {
    "78702": ("3342",  "Austin Saltillo"),
    "78705": ("3250",  "Austin UT Campus"),
    "78704": ("96",    "Austin South Lamar"),
    "78723": ("1542",  "Austin East"),
    "78749": ("1061",  "Austin SW"),
    "78758": ("95",    "Austin North"),
    "78748": ("2288",  "Austin Southpark"),
    "78759": ("2409",  "Austin Arboretum"),
    "78730": ("1953",  "Four Points"),
    "78738": ("1812",  "Bee Cave"),
    "78717": ("1797",  "Lakeline Mall"),
    "78664": ("1066",  "Round Rock"),
    "78660": ("2495",  "Pflugerville"),
    "78613": ("2342",  "Cedar Park"),
    "78640": ("2725",  "Kyle"),
    "78628": ("1982",  "Georgetown"),
}

PRODUCTS = [
    {"name": "Pokemon Shirt Boys Gray Graphic Tee", "brand": "Pokemon", "tcin": "94900587"},
    {"name": "UNO Elite NFL Red Zone Draft Pack",   "brand": "Other",   "tcin": "94111119"},
    {"name": "LEGO Classic Creative Suitcase 10713","brand": "Other",   "tcin": "52699306"},
]

ENABLED_RETAILERS = {
    "target": True,
    "walmart": False,
    "gamestop": False,
    "bestbuy": False,
    "barnes_nobles": False,
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}
