import os
import json

GROWTH_DB_FILE = "data/uma_character_growth_rates.json"

def get_uma_growth_rates():
    """
    ウマ娘キャラクターごとのデフォルト成長率ボーナス(%)データベース
    """
    os.makedirs("data", exist_ok=True)
    
    growth_db = {
        "トウカイテイオー": {"speed": 20, "stamina": 10, "power": 0, "guts": 0, "guts_bonus": 0, "wiz": 0, "desc": "スピ20%/スタ10%: スピステが非常に伸びやすくスタミナ補助もあり"},
        "ジェンティルドンナ": {"speed": 15, "stamina": 0, "power": 15, "guts": 0, "wiz": 0, "desc": "スピ15%/パワ15%: スピ・パワがバランス良く伸びるためパワサポ無し構成が主流"},
        "キタサンブラック": {"speed": 20, "stamina": 0, "power": 10, "guts": 0, "wiz": 0, "desc": "スピ20%/パワ10%: スピードカンストが極めて容易"},
        "オルフェーヴル": {"speed": 10, "stamina": 10, "power": 10, "guts": 0, "wiz": 0, "desc": "スピ10%/スタ10%/パワ10%: オールラウンドな10%分散補正"},
        "アーモンドアイ": {"speed": 20, "stamina": 0, "power": 0, "guts": 0, "wiz": 10, "desc": "スピ20%/賢さ10%: スピ・賢さ特化の理想的な成長率"},
        "サイレンススズカ": {"speed": 20, "stamina": 0, "power": 0, "guts": 10, "wiz": 0, "desc": "スピ20%/根性10%: 大逃げ特化のスピ根性ボーナス"},
        "メジロマックイーン": {"speed": 0, "stamina": 20, "power": 10, "guts": 0, "wiz": 0, "desc": "スタ20%/パワ10%: 長距離スタミナ確保に長けた成長率"},
        "スペシャルウィーク": {"speed": 15, "stamina": 15, "power": 0, "guts": 0, "wiz": 0, "desc": "スピ15%/スタ15%: 中長距離万能ボーナス"},
        "シンボリルドルフ": {"speed": 20, "stamina": 10, "power": 0, "guts": 0, "wiz": 0, "desc": "スピ20%/スタ10%: 王道の差し・中長距離ボーナス"},
        "ゴールドシップ": {"speed": 0, "stamina": 20, "power": 10, "guts": 0, "wiz": 0, "desc": "スタ20%/パワ10%: 追込長距離のスタミナ特化"}
    }
    
    with open(GROWTH_DB_FILE, "w", encoding="utf-8") as f:
        json.dump(growth_db, f, ensure_ascii=False, indent=2)
        
    return growth_db

if __name__ == "__main__":
    db = get_uma_growth_rates()
    print(f"[GROWTH DB CREATED] {len(db)} characters growth rates initialized.")
