"""Parse the decimal prices used by the supported shop."""
import math
import re


def parse_price(text):
    """Return a price or None. Accept 1 299,90 ₽ and metadata such as 1299.90."""
    compact = re.sub(r'\s+', '', text)
    match = re.search(r'(?<![\d.,-])\d+(?:[.,]\d{1,2})?(?![\d.,])', compact)
    if not match:
        return None
    try:
        value = float(match.group().replace(',', '.'))
    except ValueError:
        return None
    return value if math.isfinite(value) else None
