import re 
def normalize_fg(obj):
    if isinstance(obj, dict):
        if "#text" in obj and len(obj) <= 2:
            return obj["#text"]
        return {k: normalize_fg(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [normalize_fg(x) for x in obj]
    else:
        return obj
    


def extract_text(value):
    """Recursively extract readable text from FG formatted structures."""
    if isinstance(value, str):
        return value

    if isinstance(value, dict):
        # Prefer #text if present
        if "#text" in value:
            return value["#text"]

        # Otherwise recursively extract from values
        return " ".join(extract_text(v) for v in value.values())

    if isinstance(value, list):
        return " ".join(extract_text(v) for v in value)

    return ""


def clean_item_description(desc_elem):
    if not desc_elem:
        return ""

    paragraphs = desc_elem.get("p", [])
    if not isinstance(paragraphs, list):
        paragraphs = [paragraphs]

    raw = " ".join(extract_text(p) for p in paragraphs)

    # Normalize whitespace
    raw = re.sub(r"\s+", " ", raw).strip()

    return raw

def extract_link_text(item):
    desc = item.get("description", {})
    linklist = desc.get("linklist")

    if not linklist:
        return []

    # Ensure we always work with a list of linklist entries
    if isinstance(linklist, dict):
        linklists = [linklist]
    elif isinstance(linklist, list):
        linklists = linklist
    else:
        return []

    result = []

    for ll in linklists:
        links = ll.get("link")
        if not links:
            continue

        # Single link dict
        if isinstance(links, dict):
            text = links.get("#text")
            if text:
                result.append(text)

        # Multiple link dicts in list
        elif isinstance(links, list):
            for link in links:
                text = link.get("#text")
                if text:
                    result.append(text)

    return result
