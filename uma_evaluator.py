"""
uma_evaluator.py
ウマ娘のステータス・スキル・適性から、特定コースにおける個体の勝算評価 (S+/S/A+/A/B/C) と
具体的な強み・弱み・スキルアドバイスコメントを生成する物理解析エンジン
"""

import course_database

def evaluate_uma_individual(uma_data: dict, course_key: str = "nakayama_2000") -> dict:
    """
    uma_data 例:
    {
        "uma_name": "トウカイテイオー",
        "leg_style": "先行",
        "stats": {"speed": 1850, "stamina": 1150, "power": 1500, "guts": 1400, "wisdom": 1350},
        "aptitudes": {"distance": "S", "style": "A", "turf": "A"},
        "skills": ["アングリング×スキーミング", "つぼみ、ほころぶ時", "王手", "円弧のマエストロ", "右回り◯", "中山レース場◯"]
    }
    """
    course = course_database.COURSE_DATA.get(course_key, course_database.COURSE_DATA["nakayama_2000"])
    c_dist = course["distance"]
    c_name = course["name"]
    leg = uma_data.get("leg_style", "先行")
    stats = uma_data.get("stats", {})
    
    spd = int(stats.get("speed", 1500))
    sta = int(stats.get("stamina", 1000))
    pwr = int(stats.get("power", 1200))
    gut = int(stats.get("guts", 1100))
    wis = int(stats.get("wisdom", 1100))
    
    skills = uma_data.get("skills", [])
    skills_str = " ".join([str(s) for s in skills])
    
    ap_dist = uma_data.get("aptitudes", {}).get("distance", "A")
    
    # 1. 必要最低限スタミナ計算
    raw_required_sta = int((c_dist / 1000.0) * 450) + 100
    if c_dist >= 3000:
        req_sta_base = raw_required_sta + 200
    elif c_dist >= 2400:
        req_sta_base = raw_required_sta + 150
    else:
        req_sta_base = raw_required_sta + 80
        
    # 金回復スキルの所持数カウント
    heal_count = 0
    for h_name in ["円弧のマエストロ", "好転一息", "食い下がり", "神速", "リフレッシュ", "ブチかまし", "どこ吹く風"]:
        if h_name in skills_str:
            heal_count += 1
            
    effective_sta = sta + (heal_count * 200)
    sta_deficit = req_sta_base - effective_sta
    
    # 2. 有効加速スキルの接続判定
    valid_accel_found = []
    # 各コースで有効な定番加速スキルのチェック
    for accel_name in ["アングリング×スキーミング", "つぼみ、ほころぶ時", "ヴィクトリーショット！", "王手", "迫る影", "直線一気", "ハイボルテージ", "彼方、その先へ", "紅炎ギア"]:
        if accel_name in skills_str:
            # 罠スキルに含まれていないか判定
            inv_list = course.get("invalid_skills", [])
            is_trap = False
            for inv in inv_list:
                inv_name = inv.get("skill") if isinstance(inv, dict) else str(inv)
                if accel_name in inv_name:
                    is_trap = True
                    break
            if not is_trap:
                valid_accel_found.append(accel_name)
                
    # 3. 罠スキルの所持検出
    detected_traps = []
    inv_list = course.get("invalid_skills", [])
    for inv in inv_list:
        inv_name = inv.get("skill") if isinstance(inv, dict) else str(inv)
        inv_reason = inv.get("reason") if isinstance(inv, dict) else ""
        for s in skills:
            if str(s) in inv_name or inv_name in str(s):
                detected_traps.append({"skill": str(s), "reason": inv_reason})

    # 4. 勝算スコア計算 (100点満点)
    score = 60
    
    # スピード評価
    if spd >= 1800: score += 15
    elif spd >= 1600: score += 10
    elif spd < 1400: score -= 15
    
    # スタミナ評価
    if sta_deficit <= 0:
        score += 15
    elif sta_deficit <= 100:
        score += 5
    else:
        score -= min(30, int(sta_deficit / 10)) # スタミナ切れ失速の大打撃
        
    # 距離S評価
    if ap_dist.upper() == "S":
        score += 10
    
    # 加速スキル評価
    if len(valid_accel_found) >= 2:
        score += 15
    elif len(valid_accel_found) == 1:
        score += 8
    else:
        score -= 15 # 有効加速なしは致命的
        
    # 罠スキル減点
    score -= (len(detected_traps) * 5)
    
    score = max(10, min(99, score))
    
    # ランク判定
    if score >= 90: rank, rank_color, win_rate = "S+", "🏆 究極個体", "92% 以上 (優勝候補筆頭)"
    elif score >= 82: rank, rank_color, win_rate = "S", "🥇 超有望個体", "80%〜89% (Aグループ決勝確定級)"
    elif score >= 72: rank, rank_color, win_rate = "A+", "🥈 有望個体", "65%〜79% (決勝進出ライン)"
    elif score >= 60: rank, rank_color, win_rate = "A", "🥉 標準個体", "50%〜64% (勝ち越し目指せる)"
    elif score >= 45: rank, rank_color, win_rate = "B", "⚠️ 育成補強推奨", "30%〜49% (スパート遅延注意)"
    else: rank, rank_color, win_rate = "C", "❌ 再育成推奨", "29% 以下 (スタミナ/加速不足)"

    # 5. コメント生成
    positive_comments = []
    warning_comments = []
    advice_comments = []
    
    # 強み
    if spd >= 1800:
        positive_comments.append(f"🟢 **カンスト級スピード({spd})**: 最高速度のスパート力はトップクラスです！")
    if ap_dist.upper() == "S":
        positive_comments.append("👑 **距離適性『S』確保**: スパート最高速度補正(+10%)が働き勝利への大アドバンテージ！")
    if valid_accel_found:
        positive_comments.append(f"⚡ **最速加速スキル接続OK**: 『{', '.join(valid_accel_found)}』の接続で終盤スパート加速が完璧です！")
    if wis >= 1350:
        positive_comments.append(f"🧠 **高い賢さ({wis})**: スキル安定発動率 93.3% 以上 ＆ 好ポジションをキープできます！")
        
    # 弱み・懸念点
    if sta_deficit > 0:
        warning_comments.append(f"⚠️ **スタミナ不十分 (推定不足: 約-{sta_deficit})**: {c_name}では終盤後半にスタミナ切れを起こし、ラストスパートが遅れるリスクがあります！")
    if not valid_accel_found:
        warning_comments.append(f"⚠️ **最速有効加速の欠如**: {c_name}で最速発動する主要加速スキルが不足しており、他ウマ娘に差し切られる懸念があります。")
    if detected_traps:
        for t in detected_traps:
            warning_comments.append(f"❌ **コース不発スキルの混入**: 『{t['skill']}』は{c_name}では効果が無効化されます ({t['reason']})。")
            
    # 今後のアドバイス
    if sta_deficit > 0:
        advice_comments.append("💡 **アドバイス**: スキルPtが残っていれば『円弧のマエストロ』や『金回復スキル』を最優先で追加習得してください！")
    elif not valid_accel_found:
        advice_comments.append("💡 **アドバイス**: 継承固有（アンスキ/つぼみ/ヴィクトリー）や『王手』等の有効加速スキルを最優先で取得しましょう！")
    else:
        advice_comments.append("💡 **アドバイス**: 基礎ステータス・加速ともに完成度が高いため、残Ptは『右回り◯』『〇〇直線◯』などの緑スキル・速度スキルに回すのが最適です！")

    return {
        "uma_name": uma_data.get("uma_name", "ウマ娘"),
        "course_name": c_name,
        "rank": rank,
        "rank_label": rank_color,
        "win_rate": win_rate,
        "score": score,
        "positive": positive_comments,
        "warning": warning_comments,
        "advice": advice_comments,
        "valid_accel": valid_accel_found,
        "traps": detected_traps
    }

def format_evaluation_message(eval_res: dict) -> str:
    """評価結果辞書からユーザーに返信する綺麗なMarkdownテキストを生成"""
    res = f"🏇 **【{eval_res['uma_name']} 個体勝算 AI精密診断レポート】**\n\n"
    res += f"🎯 **【対象コース】**: **`{eval_res['course_name']}`**\n"
    res += f"👑 **【勝算評価ランク】**: **`【{eval_res['rank']}】 {eval_res['rank_label']}`** (総合スコア: `{eval_res['score']}点`)\n"
    res += f"📈 **【想定勝率】**: **`{eval_res['win_rate']}`**\n\n"
    
    if eval_res["positive"]:
        res += "✨ **【個体の強み・高評価ポイント】**\n"
        for p in eval_res["positive"]:
            res += f"  {p}\n"
        res += "\n"
        
    if eval_res["warning"]:
        res += "⚠️ **【課題・辛口弱点チェック】**\n"
        for w in eval_res["warning"]:
            res += f"  {w}\n"
        res += "\n"
        
    if eval_res["advice"]:
        res += "💡 **【育成アドバイス・今後の対策】**\n"
        for a in eval_res["advice"]:
            res += f"  {a}\n"
        res += "\n"
        
    res += "📊 **【全国ガチ勢対戦基準 (判定ランクの定義)】**\n"
    res += "・`S+ (90点~)`: ルマチ連勝・96傑狙える完璧個体 (最速加速複数+距離S+スタミナ完備)\n"
    res += "・`S  (82点~)`: Aグループ決勝確定級 (主要加速と十分なステ)\n"
    res += "・`A  (60点~)`: Aグループ進出ライン (一部加速欠除や距離Aなど)\n"
    res += "・`B/C(59点以下)`: 再育成推奨 (スタミナ切れ・罠スキル混入あり)\n\n"
    res += "🏷️ `#本育成評価` `#個体勝算AI診断` `#ウマ娘` `#ファン活` `#リグヒ`"
    return res
