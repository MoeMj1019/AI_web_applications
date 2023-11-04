from urllib.parse import urljoin

def get_full_urls(base_url, urls:list):
    standarized_urls = []
    for url in urls:
        absolute_url = urljoin(base_url, url)
        standarized_urls.append(absolute_url)
    return standarized_urls

def convert_time_units(time_delta, from_unit, to_unit):
    units_in_seconds = {
        "seconds": 1,
        "s": 1,
        "minutes": 60,
        "m": 60,
        "hours": 3600,
        "h": 3600,
        "days": 86400,
        "d": 86400,
    }
    return time_delta * units_in_seconds[from_unit] / units_in_seconds[to_unit]

def normalize_time_units(time_delta, time_unit):
    return convert_time_units(time_delta, time_unit, "seconds")
