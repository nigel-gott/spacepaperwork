from django.db.models import Avg, Max, Min

PRICE_AGG_METHODS = [
    ("average", "average"),
    ("min", "min"),
    ("max", "max"),
    ("latest", "latest"),
]
PRICE_AGG_METHODS_MAP = {
    "average": Avg,
    "min": Min,
    "max": Max,
}
PRICE_TYPES = [
    ("sell", "sell"),
    ("buy", "buy"),
    ("lowest_sell", "lowest_sell"),
    ("highest_buy", "highest_buy"),
]
