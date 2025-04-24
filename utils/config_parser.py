import re

def extract_range(description):
    # Try to match phrases like "Minimum=0 Maximum=1000"
    match = re.search(r"minimum\s*=?\s*(\d+(?:\.\d+)?)\s+maximum\s*=?\s*(\d+(?:\.\d+)?)", description, re.IGNORECASE)
    if match:
        return float(match.group(1)), float(match.group(2))
    # Try to match dash-separated values, e.g., "0 - 1" or "0–1"
    match = re.search(r"(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)", description)
    if match:
        return float(match.group(1)), float(match.group(2))
    return None, None

def parse_config_file(path):
    config = {}
    descriptions = {}
    ranges = {}
    current_comment = []

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith("#"):
                # Accumulate comment text (could be multiple lines)
                current_comment.append(line.lstrip("#").strip())
            elif "=" in line:
                key, value = line.split("=", 1)
                key, value = key.strip(), value.strip()
                config[key] = value
                if current_comment:
                    full_desc = " ".join(current_comment)
                    descriptions[key] = full_desc
                    min_val, max_val = extract_range(full_desc)
                    if min_val is not None and max_val is not None:
                        ranges[key] = (min_val, max_val)
                    current_comment = []  # Reset after use
    return config, descriptions, ranges
