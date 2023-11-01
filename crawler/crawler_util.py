from urllib.parse import urljoin , urlparse

IGNORED_WORDS = set([
            "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", 
            "yours", "yourself", "yourselves", "he", "him", "his", "himself", "she", 
            "her", "hers", "herself", "it", "its", "itself", "they", "them", "their", 
            "theirs", "themselves", "what", "which", "who", "whom", "this", "that", 
            "these", "those", "am", "is", "are", "was", "were", "be", "been", "being", 
            "have", "has", "had", "having", "do", "does", "did", "doing", "a", "an", 
            "the", "and", "but", "if", "or", "because", "as", "until", "while", "of", 
            "at", "by", "for", "with", "about", "against", "between", "into", "through", 
            "during", "before", "after", "above", "below", "to", "from", "up", "down", 
            "in", "out", "on", "off", "over", "under", "again", "further", "then", "once"
        ])

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
