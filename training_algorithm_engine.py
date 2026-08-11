import math

def calculate_training_algorithm_scores(speed, stamina, power, guts, wiz, skill_pt, rank_eval, junior_desc="", classic_desc="", senior_desc="", scenario_info=""):
    """
    トレーナーのトレーニング踏み方傾向を【数学的アルゴリズム ＆ 5次元ベクトルスコア】に変換・分類する数理計算エンジン
    """
    # 1. 絆・序盤優先度スコア (Bond Priority Score)
    bond_score = 85
    if any(k in junior_desc for k in ["絆", "早期", "メイクデビュー", "お出かけ"]):
        bond_score += 10
    bond_score = min(100, max(50, bond_score))

    # 2. スピード偏重比率 (Speed Bias Ratio)
    total_main = speed + stamina + power + guts + wiz
    speed_bias = round(speed / max(1, total_main), 3)

    # 3. サブステバランス度 (SubStat Balancing Score)
    sub_stats = [stamina, power, guts, wiz]
    avg_sub = sum(sub_stats) / 4.0
    variance = sum((x - avg_sub) ** 2 for x in sub_stats) / 4.0
    std_dev = math.sqrt(variance)
    substat_balance_score = round(max(0, 100 - (std_dev / 5.0)), 1)

    # 4. 夏合宿爆発効率 (Summer Camp Efficiency Index)
    camp_efficiency = 80
    if any(k in classic_desc for k in ["夏合宿", "ダブル", "トリプル", "集中"]):
        camp_efficiency += 15
    camp_efficiency = min(100, max(60, camp_efficiency))

    # 5. スキルPt最適化係数 (Skill-Pt Optimization Factor)
    skill_pt_factor = round(skill_pt / 2000.0, 2)

    # 6. トレーナータイプ分類アルゴリズム (Trainer Archetype Classification)
    archetype = "🛡️ 安定バランスビルド型 (Solid Base Builder)"
    if skill_pt >= 3700 and wiz >= 1300:
        archetype = "🧠 スキルPt最大化・賢さ頭脳派型 (Skill-Pt Maximizer)"
    elif camp_efficiency >= 90 and speed >= 1600:
        archetype = "⚡ 夏合宿一撃ハイローラー型 (High-Roll Specialist)"
    elif "ラーメン" in scenario_info or "博多" in scenario_info or "北海道" in scenario_info:
        archetype = "🍜 ラーメン職人・地域仕込み完全最適化型 (Ramen Synergy Master)"

    return {
        "archetype": archetype,
        "bond_score": bond_score,
        "speed_bias": speed_bias,
        "substat_balance_score": substat_balance_score,
        "camp_efficiency": camp_efficiency,
        "skill_pt_factor": skill_pt_factor
    }

def format_algorithm_report(alg_data):
    """アルゴリズム解析結果を美しく表示用テキストにフォーマット"""
    return (
        f"⚙️ **【トレーナー踏み方傾向アルゴリズム化スコア】**\n"
        f"🏷️ **トレーナー属性分類**: `{alg_data['archetype']}`\n"
        f"📊 **踏み方5次元アルゴリズムベクトル**:\n"
        f"・👶 **絆早期MAX・基礎固めスコア**: `{alg_data['bond_score']} / 100`\n"
        f"・⚡ **スピード配分偏重比率**: `{alg_data['speed_bias']} (全体比)`\n"
        f"・⚖️ **サブステ安定バランス度**: `{alg_data['substat_balance_score']} / 100`\n"
        f"・🔥 **夏合宿爆発立ち回り効率**: `{alg_data['camp_efficiency']} / 100`\n"
        f"・✨ **スキルPt最適化生成力**: `x{alg_data['skill_pt_factor']}`\n"
    )
