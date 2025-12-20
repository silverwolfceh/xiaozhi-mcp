import requests
from typing import Any, Dict, List, Optional
from response_format import return_error_response, return_success_response, send_progress_notification
import json
from bs4 import BeautifulSoup
import logging
from utils import load_env, envvarsenum
import asyncio
logger = logging.getLogger(__name__)

def decode_hex_escaped(s: str) -> str:
    # turns r"\x3c" into "<"
    return bytes(s, "utf-8").decode("unicode_escape")


def parse_doji_table(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    result = {
        "updated_at": None,
        "items": []
    }

    # update time
    time_el = soup.select_one(".update-time")
    if time_el:
        result["updated_at"] = time_el.get_text(strip=True).replace("Cập nhập lúc:", "").strip()

    # table rows
    rows = soup.select("table.goldprice-view tbody tr")
    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 3:
            continue

        name = cols[0].select_one(".title")
        unit = cols[0].select_one(".sub-title")

        buy = cols[1].get_text(strip=True)
        sell = cols[2].get_text(strip=True)

        result["items"].append({
            "name": name.get_text(strip=True) if name else None,
            "unit": unit.get_text(strip=True) if unit else None,
            "buy": int(buy.replace(",", "")) if buy else None,
            "sell": int(sell.replace(",", "")) if sell else None
        })

    return result

def get_doji_gold_price_tool(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    {
        "name": "get_doji_gold_price",
        "description": "Get the current DOJI gold price.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "goldtype": {
                    "type": "string",
                    "enum": ["tael", "ring"],
                    "description" : "The type of gold."
                }
            },
            "required": []
        }
    }
    """
    goldtype = arguments.get("goldtype", "tael").lower()
    if goldtype not in ["tael", "ring", ""]:
        logger.error("Invalid goldtype argument: %s", goldtype)
        return return_error_response("[Error] Invalid goldtype. Must be 'tael' or 'ring'.")
    typemap = {
        "tael": 'AVPL/SJC - BÁN LẺ', # Type name
        "ring": 'NHẪN TRÒN 9999 (HƯNG THỊNH VƯỢNG - BÁN LẺ)'
    }
    try:
        url = "https://giavang.doji.vn/?q=doji/get/json/gia_vang_quoc_te"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        text = resp.content.decode("utf-8-sig")
        data = json.loads(text)
        if "main_price" not in data:
            logger.error("DOJI response missing 'main_price': %s", json.dumps(data))
            return return_error_response("[Error] Failed to retrieve gold prices from DOJI.")
        html_content = data["main_price"]
        html_decoded = decode_hex_escaped(html_content)
        parsed_data = parse_doji_table(html_decoded)
        for item in parsed_data["items"]:
            expected_type_name = typemap.get(goldtype)
            if goldtype == "" or item.get("name") == expected_type_name:
                buy_price = item.get("buy")
                sell_price = item.get("sell")
                gold_type_name = "Tael" if item.get("name") == typemap["tael"] else "Ring"
                logger.info("Retrieved DOJI gold price for %s: Buy %d, Sell %d", gold_type_name, buy_price, sell_price)
                return return_success_response(f"DOJI Gold Price ({gold_type_name}): Buy Price: {buy_price} VND, Sell Price: {sell_price} VND")
        logger.error("Specified gold type not found in DOJI prices: %s", goldtype)
        return return_error_response("[Error] Specified gold type not found in DOJI prices.")
    except requests.RequestException as e:
        logger.error("Network error occurred while fetching DOJI gold prices: %s", str(e))
        return return_error_response(f"[Error] Network error occurred: {str(e)}")

def get_sjc_gold_price_tool(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    {
        "name": "get_sjc_gold_price",
        "description": "Get the current SJC gold price.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "goldtype": {
                    "type": "string",
                    "enum": ["tael", "ring"],
                    "description" : "The type of gold."
                }
            },
            "required": []
        }
    }
    """
    goldtype = arguments.get("goldtype", "tael").lower()
    if goldtype not in ["tael", "ring", ""]:
        return return_error_response("[Error] Invalid goldtype. Must be 'tael' or 'ring'.")
    typemap = {
        "tael": 1, # Type id
        "ring": 33
    }
    try:
        url = "https://sjc.com.vn/GoldPrice/Services/PriceService.ashx"
        data = {
            "method": "GetCurrentGoldPricesByBranch",
            "BranchId": "1" # Ho Chi Minh City branch
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://sjc.com.vn/gia-vang-online"
        }
        resp = requests.post(url, data=data, headers=headers, verify=False)
        resp.raise_for_status()
        data = resp.json() # Reuse the data variable for JSON response
        if "success" not in data or not data["success"]:
            return return_error_response("[Error] Failed to retrieve gold prices from SJC.")
        prices = data.get("data", [])
        if not prices:
            return return_error_response("[Error] No price data available from SJC.")
        for p in prices:
            expected_type_id = typemap.get(goldtype)
            if goldtype == "" or p.get("Id") == expected_type_id:
                buy_price = int(p.get("BuyValue", 0))
                sell_price = int(p.get("SellValue", 0))
                gold_type_name = "Tael" if p.get("Id") == 1 else "Ring"
                return return_success_response(f"SJC Gold Price ({gold_type_name}): Buy Price: {buy_price} VND, Sell Price: {sell_price} VND")
        logger.error("Specified gold type not found in SJC prices: %s", goldtype)
        return return_error_response("[Error] Specified gold type not found in SJC prices.")
    except Exception as e:
        logger.error("Network error occurred while fetching SJC gold prices: %s", str(e))
        return return_error_response(f"[Error] Network error occurred: {str(e)}")
    
def get_crypto_price_tool(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    {
        "name": "get_crypto_price",
        "description": "Get the current cryptocurrency price from CoinMarketCap.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description" : "The symbol of the cryptocurrency (e.g., BTC, ETH)."
                }
            },
            "required": ["symbol"]
        }
    }
    """
    symbol = arguments.get("symbol", "").upper()
    notification = arguments.get("notification", None)
    if not symbol:
        return return_error_response("[Error] 'symbol' argument is required.")
    # await send_progress_notification(notification, "Fetching cryptocurrency price...", 10)

    api_key = load_env().get(envvarsenum.CMC_API_KEY)
    if not api_key or api_key.strip() == "":
        logger.error("CoinMarketCap API key is not set.")
        return return_error_response("[Error] CoinMarketCap API key is not configured.")
    # await send_progress_notification(notification, "Contacting CoinMarketCap API...", 50)
    try:
        url = f"https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest?symbol={symbol.upper()}&CMC_PRO_API_KEY={api_key}&convert=usd"
        headers = {
            "Accepts": "application/json",
            "X-CMC_PRO_API_KEY": api_key,
        }
        resp = requests.get(url, headers=headers)
        # await send_progress_notification(notification, "Processing response...", 80)
        resp.raise_for_status()
        data = resp.json()
        if "data" not in data or symbol not in data["data"]:
            return return_error_response(f"[Error] Cryptocurrency symbol '{symbol}' not found.")
        crypto_data = data["data"][symbol][0]
        price = crypto_data["quote"]["USD"]["price"]
        # await send_progress_notification(notification, f"Current price of {symbol} is ${price:.2f} USD.", 100)
        return return_success_response(f"Current price of {symbol} is ${price:.2f} USD.")
    except Exception as e:
        logger.error("Error occurred while fetching cryptocurrency price: %s", str(e))
        return return_error_response(f"[Error] Network error occurred: {str(e)}")