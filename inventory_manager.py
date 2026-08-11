# -*- coding: utf-8 -*-
import os
import json
import datetime

INVENTORY_FILE = os.path.join(os.path.dirname(__file__), "user_inventories.json")

def load_inventories():
    if os.path.exists(INVENTORY_FILE):
        try:
            with open(INVENTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_inventories(data):
    try:
        with open(INVENTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving inventories: {e}")

def update_user_cards(user_id: str, card_list: list):
    """
    card_list: [{"name": "オルフェーヴル", "type": "根性", "rarity": "SSR", "limit_break": 4}, ...]
    """
    data = load_inventories()
    u_id = str(user_id)
    if u_id not in data:
        data[u_id] = {
            "cards": {},
            "updated_at": ""
        }
    
    existing_cards = data[u_id].get("cards", {})
    for c in card_list:
        c_name = c.get("name")
        if c_name:
            existing_cards[c_name] = {
                "name": c_name,
                "type": c.get("type", "不明"),
                "rarity": c.get("rarity", "SSR"),
                "limit_break": int(c.get("limit_break", 0))
            }
            
    data[u_id]["cards"] = existing_cards
    data[u_id]["updated_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_inventories(data)
    return len(existing_cards)

def get_user_cards_summary(user_id: str) -> str:
    data = load_inventories()
    u_id = str(user_id)
    if u_id not in data or not data[u_id].get("cards"):
        return "登録済みの所持サポートカードはありません。"
    
    cards = data[u_id]["cards"]
    res = f"📋 **【登録済みサポートカード一覧】** (最終更新: {data[u_id].get('updated_at', '不明')})\n"
    sorted_cards = sorted(cards.values(), key=lambda x: (x.get("rarity", ""), x.get("limit_break", 0)), reverse=True)
    
    for c in sorted_cards:
        lb = c.get("limit_break", 0)
        lb_str = "完凸(4凸)" if lb == 4 else f"{lb}凸"
        res += f"・**[{c.get('rarity', 'SSR')}] {c.get('name')}** ({c.get('type', '汎用')}) ➔ **`{lb_str}`**\n"
        
    return res
