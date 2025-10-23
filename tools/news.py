import requests
from typing import Any, Dict, List, Optional
from response_format import *
import xml.etree.ElementTree as ET
import re


_TAG_RE = re.compile(r"<[^>]+>")


def strip_html(text: Optional[str]) -> str:
    """Remove HTML tags and extra whitespace from a string. Returns empty string for None."""
    if not text:
        return ""
    # Remove HTML tags
    no_tags = _TAG_RE.sub("", text)
    # Remove common image urls and data URIs
    no_images = re.sub(r"https?://\S+\.(?:png|jpg|jpeg|gif|svg)\S*", "", no_tags, flags=re.IGNORECASE)
    no_images = re.sub(r"data:image/[^;\s]+;base64,[A-Za-z0-9+/=]+", "", no_images, flags=re.IGNORECASE)
    # Collapse whitespace
    return " ".join(no_images.split())


def parse_xml_to_dict(xml_text: str) -> Dict[str, Any]:
    """Parse a simple XML string into a nested dictionary structure.

    The parser produces a mapping where element tags map to either:
    - a string for text-only elements,
    - a dict for elements with children or attributes,
    - a list when multiple sibling elements share the same tag.

    This is intentionally lightweight (built on xml.etree) and avoids
    external dependencies.
    """
    root = ET.fromstring(xml_text)

    def elem_to_dict(elem: ET.Element) -> Any:
        # collect children
        children = list(elem)
        if not children:
            text = elem.text.strip() if elem.text and elem.text.strip() else ""
            # include attributes if any
            if elem.attrib:
                data = {"_text": text} if text else {}
                data.update({f"@{k}": v for k, v in elem.attrib.items()})
                return data
            return text

        result: Dict[str, Any] = {}
        # include attributes on element
        for k, v in elem.attrib.items():
            result[f"@{k}"] = v

        for child in children:
            child_val = elem_to_dict(child)
            tag = child.tag
            if tag in result:
                # convert to list or append
                if not isinstance(result[tag], list):
                    result[tag] = [result[tag]]
                result[tag].append(child_val)
            else:
                result[tag] = child_val

        return result

    return {root.tag: elem_to_dict(root)}


def extract_rss_items(parsed: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract RSS items from the parsed XML dict into a list of simplified dicts."""
    # navigate rss->channel->item or feed->entry for Atom
    items: List[Dict[str, Any]] = []
    # support both rss and feed
    if "rss" in parsed:
        channel = parsed["rss"].get("channel", {})
        raw_items = channel.get("item", [])
    elif "feed" in parsed:
        raw_items = parsed["feed"].get("entry", [])
    else:
        # fallback: search for any 'item' key at top level
        raw_items = parsed.get("item", [])

    if isinstance(raw_items, dict):
        raw_items = [raw_items]

    for it in raw_items:
        simple: Dict[str, Any] = {}
        if isinstance(it, dict):
            for k, v in it.items():
                # unwrap simple containers and strip HTML from text-like fields
                val: Any
                if isinstance(v, dict) and "_text" in v and len(v) == 1:
                    val = v["_text"]
                else:
                    val = v

                # For common textual fields, strip HTML and images
                if k.lower() in {"title", "description", "content", "summary", "encoded", "content:encoded"}:
                    if isinstance(val, str):
                        simple[k] = strip_html(val)
                    else:
                        simple[k] = strip_html(str(val))
                else:
                    # For other fields, keep as-is but strip if it's a plain string
                    if isinstance(val, str):
                        simple[k] = strip_html(val)
                    else:
                        simple[k] = val
        else:
            # if item is a string
            simple["content"] = strip_html(str(it))
        items.append(simple)

    return items


def get_latest_news_tool(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    {
        "name": "get_latest_news",
        "description": "Fetch the latest news articles from VNExpress.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description" : "The RSS feed URL to fetch news from."
                }
            },
            "required": []
        }
    }
    """
    url = arguments.get("url", "https://vnexpress.net/rss/tin-moi-nhat.rss")
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
    except Exception as e:
        return return_error_response(f"Failed to fetch RSS feed: {e}")

    try:
        results = []
        parsed = parse_xml_to_dict(res.text)
        items = extract_rss_items(parsed)
        for i in items:
            news = {
                "title": i.get("title", "No Title"),
                "link": i.get("link", ""),
            }
            results.append(news)
        return return_success_response({"items": results})
    except ET.ParseError as e:
        return return_error_response(f"XML parse error: {e}")
    except Exception as e:
        return return_error_response(str(e))


if __name__ == "__main__":
    # Example usage
    result = get_latest_news_tool({})
    print(result)