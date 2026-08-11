# -*- coding: utf-8 -*-
PAST_EVENT_MASTER = {
    # 2026年
    "2026年8月": {"name": "中山 芝 2000m (内回り/皐月賞)", "key": "nakayama_2000", "type": "LOH", "title": "8月LOH 中山2000m"},
    "2026年7月": {"name": "阪神 芝 1600m (外回り/桜花賞)", "key": "hanshin_1600", "type": "チャンミ", "title": "7月チャンミ 阪神1600m (マイル)"},
    "2026年6月": {"name": "東京 芝 2400m (日本ダービー)", "key": "tokyo_2400", "type": "チャンミ", "title": "6月チャンミ 東京2400m (日本ダービー)"},
    "2026年5月": {"name": "東京 芝 1600m (安田記念)", "key": "tokyo_1600", "type": "チャンミ", "title": "5月チャンミ 東京1600m (安田記念)"},
    # 2025年
    "2025年12月": {"name": "中山 芝 3600m (ステイヤーズS)", "key": "nakayama_3600", "type": "チャンミ", "title": "12月チャンミ LONG (長距離)"},
    "2025年7月": {"name": "阪神 芝 1600m (外回り/桜花賞)", "key": "hanshin_1600", "type": "チャンミ", "title": "2025年7月チャンミ 阪神1600m (マイル)"},
    "2025年5月": {"name": "東京 芝 2400m (日本ダービー)", "key": "tokyo_2400", "type": "チャンミ", "title": "2025年5月チャンミ 日本ダービー"},
    # 2024年
    "2024年5月": {"name": "東京 芝 1600m (安田記念)", "key": "tokyo_1600", "type": "チャンミ", "title": "2024年5月チャンミ MILE (東京1600m)"},
    "2024年6月": {"name": "京都 芝 2200m (外回り/宝塚記念)", "key": "kyoto_2200", "type": "チャンミ", "title": "2024年6月チャンミ CLASSIC (京都2200m)"},
}

COURSE_DATA = {
    "nakayama_2000": {
        "name": "中山 芝 2000m (内回り)",
        "distance": 2000,
        "phase_opening": (0, 333),
        "phase_middle": (333, 1333),
        "phase_final": (1333, 2000),
        "corner_1_start": 300,
        "corner_1_end": 450,
        "corner_2_start": 450,
        "corner_2_end": 600,
        "corner_3_start": 1200,
        "corner_3_end": 1400,
        "corner_4_start": 1400,
        "corner_4_end": 1690,
        "final_straight_start": 1690,
        "final_straight_len": 310,
        "slopes": [
            {"start": 0, "end": 200, "type": "up", "grade": 2.24},
            {"start": 600, "end": 1000, "type": "down", "grade": -1.8},
            {"start": 1800, "end": 2000, "type": "up", "grade": 2.24}
        ],
        "invalid_skills": [
            {"skill": "最終直線での加速スキル", "reason": "終盤開始が第3コーナーのため、直線発動時には加速完了し効果無効"},
            {"skill": "直線一気 / 迫る影", "reason": "終盤開始地点が直線ではなくコーナーのため条件不適合・発動不可"},
            {"skill": "登山家 (序盤発動時)", "reason": "序盤の登り坂で出ると最高速度アップ前に加速終了し効果ゼロ"}
        ]
    },
    "tokyo_2400": {
        "name": "東京 芝 2400m (日本ダービー/ジャパンC)",
        "distance": 2400,
        "phase_opening": (0, 400),
        "phase_middle": (400, 1600),
        "phase_final": (1600, 2400),
        "corner_1_start": 450,
        "corner_1_end": 600,
        "corner_2_start": 600,
        "corner_2_end": 750,
        "corner_3_start": 1350,
        "corner_3_end": 1600,
        "corner_4_start": 1600,
        "corner_4_end": 1875,
        "final_straight_start": 1875,
        "final_straight_len": 525,
        "slopes": [
            {"start": 100, "end": 300, "type": "up", "grade": 1.5},
            {"start": 750, "end": 1100, "type": "down", "grade": -1.2},
            {"start": 1900, "end": 2100, "type": "up", "grade": 2.0}
        ],
        "invalid_skills": [
            {"skill": "最終コーナー後半発動の加速", "reason": "終盤開始が第3コーナー途中のため、最終コーナー後半では遅延し無効"},
            {"skill": "ハイボルテージ", "reason": "マイル限定スキルのため中距離2400mでは条件不適合・発動不可"},
            {"skill": "登山家 (序盤発動時)", "reason": "序盤の坂で出るとスパート開始前に加速が終了し効果ゼロ"}
        ]
    },
    "hanshin_1600": {
        "name": "阪神 芝 1600m (外回り/桜花賞)",
        "distance": 1600,
        "phase_opening": (0, 266),
        "phase_middle": (266, 1066),
        "phase_final": (1066, 1600),
        "corner_3_start": 800,
        "corner_3_end": 1066,
        "corner_4_start": 1066,
        "corner_4_end": 1126,
        "final_straight_start": 1126,
        "final_straight_len": 474,
        "slopes": [
            {"start": 600, "end": 900, "type": "down", "grade": -1.5},
            {"start": 1400, "end": 1550, "type": "up", "grade": 1.8}
        ],
        "invalid_skills": [
            {"skill": "最終コーナー後半発動の加速", "reason": "終盤開始が第3コーナー終わりのため最終コーナー後半では無効"},
            {"skill": "直線一気 / 迫る影", "reason": "終盤開始地点が直線でないため条件不適合・発動不可"},
            {"skill": "王手", "reason": "中距離限定スキルのためマイル1600mでは発動条件外"}
        ]
    },
    "tokyo_1600": {
        "name": "東京 芝 1600m (安田記念/ヴィクトリアM)",
        "distance": 1600,
        "phase_opening": (0, 266),
        "phase_middle": (266, 1066),
        "phase_final": (1066, 1600),
        "corner_3_start": 750,
        "corner_3_end": 1000,
        "corner_4_start": 1000,
        "corner_4_end": 1075,
        "final_straight_start": 1075,
        "final_straight_len": 525,
        "slopes": [
            {"start": 100, "end": 300, "type": "up", "grade": 1.5},
            {"start": 1100, "end": 1300, "type": "up", "grade": 2.0}
        ],
        "invalid_skills": [
            {"skill": "最終コーナー発動の加速スキル", "reason": "終盤開始が第3コーナーのため最終コーナー発動では無効・遅延"},
            {"skill": "アングリング×スキーミング", "reason": "終盤開始がコーナーではなく直線直前のため最速加速にならず無効"},
            {"skill": "王手", "reason": "マイルレースのため中距離限定条件に合致せず発動不可"}
        ]
    },
    "kyoto_2200": {
        "name": "京都 芝 2200m (外回り/エリザベス女王杯)",
        "distance": 2200,
        "phase_opening": (0, 366),
        "phase_middle": (366, 1466),
        "phase_final": (1466, 2200),
        "corner_3_start": 1000,
        "corner_3_end": 1350,
        "corner_4_start": 1350,
        "corner_4_end": 1800,
        "final_straight_start": 1800,
        "final_straight_len": 400,
        "slopes": [
            {"start": 700, "end": 1100, "type": "up", "grade": 2.2},
            {"start": 1100, "end": 1400, "type": "down", "grade": -2.0}
        ],
        "invalid_skills": [
            {"skill": "最終直線発動の加速スキル", "reason": "終盤開始が第3コーナーのため直線発動時には加速終了しており無効"},
            {"skill": "ハイボルテージ", "reason": "マイル限定スキルのため中距離2200mでは発動不可"},
            {"skill": "直線一気 / 迫る影", "reason": "終盤開始地点がコーナーのため条件不適合・発動不可"}
        ]
    },
    "nakayama_3600": {
        "name": "中山 芝 3600m (内〜外/ステイヤーズS/長距離)",
        "distance": 3600,
        "phase_opening": (0, 600),
        "phase_middle": (600, 2400),
        "phase_final": (2400, 3600),
        "corner_3_start": 2100,
        "corner_3_end": 2400,
        "corner_4_start": 2400,
        "corner_4_end": 3290,
        "final_straight_start": 3290,
        "final_straight_len": 310,
        "slopes": [
            {"start": 300, "end": 600, "type": "up", "grade": 2.2},
            {"start": 1500, "end": 1800, "type": "down", "grade": -1.8},
            {"start": 2100, "end": 2400, "type": "up", "grade": 2.0},
            {"start": 3300, "end": 3500, "type": "up", "grade": 2.2}
        ],
        "invalid_skills": [
            {"skill": "つぼみ、ほころぶ時", "reason": "長距離レースのためマイル/中距離限定条件に反し無効"},
            {"skill": "王手", "reason": "長距離レースのため中距離限定条件に反し発動不可"},
            {"skill": "ハイボルテージ", "reason": "マイル限定スキルのため長距離3600mでは発動不可"}
        ]
    },
    "kyoto_3200": {
        "name": "京都 芝 3200m (外〜内/天皇賞春/長距離)",
        "distance": 3200,
        "phase_opening": (0, 533),
        "phase_middle": (533, 2133),
        "phase_final": (2133, 3200),
        "corner_3_start": 1800,
        "corner_3_end": 2133,
        "corner_4_start": 2133,
        "corner_4_end": 2800,
        "final_straight_start": 2800,
        "final_straight_len": 400,
        "slopes": [
            {"start": 700, "end": 1100, "type": "up", "grade": 2.2},
            {"start": 1100, "end": 1400, "type": "down", "grade": -2.0},
            {"start": 2300, "end": 2600, "type": "up", "grade": 2.2},
            {"start": 2600, "end": 2900, "type": "down", "grade": -2.0}
        ]
    }
}

SKILL_RULES = {
    "つぼみ、ほころぶ時": {
        "type": "corner",
        "base_duration": 4.0,
        "base_pt": 180,
        "effect": "加速 0.40m/s² (継承固有は0.20m/s²)",
        "sources": "ニシノフラワー固有継承"
    },
    "王手": {
        "type": "final_corner",
        "base_duration": 0.9,
        "base_pt": 180,
        "effect": "加速 0.40m/s²",
        "sources": "SSRエルコンドルパサー / SSRオルフェーヴル"
    },
    "アングリング×スキーミング": {
        "type": "corner",
        "base_duration": 4.0,
        "base_pt": 180,
        "effect": "加速 0.40m/s² (継承固有は0.20m/s²)",
        "sources": "セイウンスカイ固有継承"
    },
    "迫る影": {
        "type": "straight",
        "base_duration": 0.9,
        "base_pt": 180,
        "effect": "加速 0.40m/s²",
        "sources": "覚醒スキル/SSRヒシアマゾン"
    },
    "ハイボルテージ": {
        "type": "final_corner",
        "base_duration": 1.8,
        "base_pt": 180,
        "effect": "加速 0.40m/s²",
        "sources": "SSRゴールドシチー / SSRヤマニンゼファー"
    },
    "レースの真髄・体": {
        "type": "spurt",
        "base_duration": 3.0,
        "base_pt": 150,
        "effect": "目標速度 0.25m/s UP (※持久力2.0%消耗！)",
        "sources": "URAファイナルズ / 因子継承"
    },
    "レースの真髄・力": {
        "type": "speed",
        "base_duration": 4.0,
        "base_pt": 150,
        "effect": "目標速度 0.15m/s UP (持続4.0秒)",
        "sources": "URAファイナルズ / 因子継承"
    },
    "レースの真髄・速": {
        "type": "speed",
        "base_duration": 2.0,
        "base_pt": 150,
        "effect": "目標速度 0.15m/s UP",
        "sources": "URAファイナルズ / 因子継承"
    },
    "レースの真髄・根": {
        "type": "acceleration",
        "base_duration": 1.2,
        "base_pt": 150,
        "effect": "加速 0.20m/s² UP",
        "sources": "URAファイナルズ / 因子継承"
    }
}

def calculate_skill_timing(course_key: str = "nakayama_2000", skill_name: str = "つぼみ、ほころぶ時", wisdom: int = None, leg_style: str = None, event_schedule: str = None) -> str:
    course = COURSE_DATA.get(course_key, COURSE_DATA["nakayama_2000"])

    c_dist = course["distance"]
    final_start = course["phase_final"][0]
    str_s = course["final_straight_start"]

    target_wis = wisdom if (wisdom and isinstance(wisdom, int) and wisdom > 0) else 1200
    act_rate = max(0.0, min(100.0, 100.0 - (9000.0 / float(target_wis))))

    rule = SKILL_RULES.get(skill_name, {
        "type": "speed",
        "base_duration": 3.0,
        "base_pt": 160,
        "effect": "目標速度アップ (0.35m/s)",
        "sources": "固有スキル/覚醒スキル/各種サポカ"
    })

    base_dur = rule.get("base_duration", 3.0)
    eff_dur = base_dur * (c_dist / 1000.0)

    chosen_leg_str = leg_style if leg_style else "先行"

    c3_s = course.get("corner_3_start", int(c_dist * 0.60))
    c3_e = course.get("corner_3_end", int(c_dist * 0.75))

    res = f"📐 **【{course['name']} 物理シミュレーション解析】**\n\n"
    if event_schedule:
        res += f"📅 **【開催予定日時】**: **`{event_schedule}`**\n"
        if any(k in str(event_schedule) for k in ["LOH", "リグヒ", "ヒーロー", "リーグ・オブ・ヒーローズ"]):
            res += "🚫 **【特殊ルール注意】**: **`リーグ・オブ・ヒーローズ (LOH) ルール適用`**\n"
            res += "   └─ ⚠️ **相手へのデバフスキル(独占力/八重の帯/スタミナデバフ等)は効果無効・発動禁止対象です！** 自ウマ娘の速度・加速・回復スキルを重視しましょう！\n"
        res += "\n"
    res += f"🧮 **【公式物理パラメータ】**\n"
    res += f"・**終盤開始位置**: `全距離 {c_dist}m × (2/3) = {final_start}m 地点`\n"
    res += f"・🚩 **最終前 第3コーナー**: **`{c3_s}m 地点 〜 {c3_e}m 地点`** (終盤直前/ポジション争い要所)\n"
    res += f"・**最終直線開始**: `{str_s}m 地点` (最終直線の長さ: `{course.get('final_straight_len', 310)}m`)\n"
    res += f"・**賢さ({target_wis})スキル発動率**: **`{act_rate:.1f}%`**\n"
    res += f"・**実効持続時間**: **`{eff_dur:.2f} 秒間`** (基準{base_dur}秒 × {c_dist}/1000)\n\n"
    
    inv_list = course.get("invalid_skills", [])
    if inv_list:
        res += "⚠️ **【コース構造上 不発・無効化される罠スキル注意一覧】**\n"
        for inv in inv_list:
            if isinstance(inv, dict):
                res += f"・❌ **`{inv.get('skill')}`**\n"
                res += f"   └─ ⚠️ **理由**: {inv.get('reason')}\n"
            else:
                res += f"・❌ **`{inv}`**\n"
        res += "\n"

    res += f"📊 **【おすすめ育成目標ステータス ＆ 戦略アドバイス】**\n"
    res += f"・**脚質**: **`{chosen_leg_str}`**\n"
    res += f"・**スピード**: **`1800〜2100`** (最優先・最高速度の基本値)\n"
    res += f"・**スタミナ**: **`1100〜1200 以上`** (スパート遅延防衛)\n"
    res += f"・**パワー**: **`1500〜1700`** (坂での減速防衛＆加速力)\n"
    res += f"・**根性**: **`1400〜1600`** (最終直線の追い比べ競り合い勝利の要！)\n"
    res += f"・**賢さ**: **`1350〜1500`** (スキル安定発動率 93.3%以上)\n"

    return res

def calculate_minimum_required_stats(course_query: str = "", leg_style: str = "先行", is_pvp: bool = True) -> str:
    """目標イベント・目標レース・コースから、完走・勝利のために『最低限必要な目標ステータス（下限値）』を精密計算"""
    dist = 2000
    if "3200" in course_query or "天皇賞春" in course_query or "長距離" in course_query:
        dist = 3200
    elif "3000" in course_query or "菊花賞" in course_query:
        dist = 3000
    elif "2500" in course_query or "有馬記念" in course_query:
        dist = 2500
    elif "2400" in course_query or "日本ダービー" in course_query or "ジャパン" in course_query or "オークス" in course_query:
        dist = 2400
    elif "1600" in course_query or "マイル" in course_query or "桜花賞" in course_query or "安田記念" in course_query:
        dist = 1600
    elif "1200" in course_query or "スプリンターズ" in course_query or "短距離" in course_query or "高松宮" in course_query:
        dist = 1200
        
    raw_stamina = int((dist / 1000.0) * 450) + 100
    
    if dist >= 3000:
        min_sta_no_heal = raw_stamina + 200
        min_sta_gold_heal = min_sta_no_heal - 200
        min_sta_2gold_heal = min_sta_no_heal - 400
    elif dist >= 2400:
        min_sta_no_heal = raw_stamina + 150
        min_sta_gold_heal = min_sta_no_heal - 200
        min_sta_2gold_heal = min_sta_no_heal - 350
    elif dist >= 2000:
        min_sta_no_heal = raw_stamina + 100
        min_sta_gold_heal = min_sta_no_heal - 200
        min_sta_2gold_heal = min_sta_no_heal - 300
    else:
        min_sta_no_heal = raw_stamina
        min_sta_gold_heal = max(600, min_sta_no_heal - 150)
        min_sta_2gold_heal = 600

    if is_pvp:
        min_sp = 1600
        min_pow = 1400
        min_guts = 1300
        min_wis = 1350
    else:
        min_sp = 1000
        min_pow = 900
        min_guts = 700
        min_wis = 800

    c_name = f"距離 {dist}m" if not any(w in course_query for w in ["有馬", "ダービー", "天皇賞", "桜花賞", "菊花賞"]) else course_query

    res = f"🧮 **【目標コース・G1レース別 最低必須目標ステータスライン (精密計算)】**\n\n"
    res += f"🎯 **対象レース/コース**: **`{c_name}`** | **想定脚質**: **`{leg_style}`**\n\n"
    res += f"📊 **【最低でも絶対必要なステータス下限値 (完走・スパート遅延防止)】**\n"
    res += f"・⚡ **スピード**: **`{min_sp} 以上`** (スパート最高速度の基礎！上限突破を優先)\n"
    res += f"・🍵 **スタミナ (最低必要ライン)**:\n"
    res += f"   ├─ **回復スキルなしの場合**: 最低 **`{min_sta_no_heal} 以上`**\n"
    res += f"   ├─ **金回復1個所持の場合**: 最低 **`{min_sta_gold_heal} 以上`** (`スタミナ+200相当`)\n"
    res += f"   └─ **金回復2個所持の場合**: 最低 **`{min_sta_2gold_heal} 以上`** (`スタミナ+400相当`)\n"
    res += f"・⛰️ **パワー**: **`{min_pow} 以上`** (上り坂の減速無効化 ＆ 加速度の親ステータス)\n"
    res += f"・🔥 **根性**: **`{min_guts} 以上`** (最終直線「追い比べ」で競り勝つための下限)\n"
    res += f"・🧠 **賢さ**: **`{min_wis} 以上`** (スキル発動率 `{100 - 9000/min_wis:.1f}%` ＆ 出遅れ防止)\n"

    return res
