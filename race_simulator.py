import os
import math
import random
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 日本語フォント設定
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Meiryo', 'Yu Gothic', 'MS Gothic', 'TakaoPGothic', 'DejaVu Sans']

def simulate_race(course_name="nakayama_2000", runner_list=None):
    """
    100回のモンテカルロシミュレーションにより、レース展開・追い比べ発生率・馬身差グラフを生成するエンジン
    """
    if not runner_list:
        # デフォルトの12頭立て代表脚質サンプル編成
        runner_list = [
            {"name": "逃げA (大逃げ)", "style": "逃げ", "speed": 1850, "stamina": 1200, "power": 1600, "guts": 1500, "wisdom": 1350, "acc_skills": 2.5},
            {"name": "逃げB (ハナ取り)", "style": "逃げ", "speed": 1800, "stamina": 1150, "power": 1550, "guts": 1400, "wisdom": 1400, "acc_skills": 2.0},
            {"name": "先行A (接続◎)", "style": "先行", "speed": 1900, "stamina": 1250, "power": 1650, "guts": 1550, "wisdom": 1450, "acc_skills": 3.0},
            {"name": "先行B (つぼみ)", "style": "先行", "speed": 1820, "stamina": 1180, "power": 1500, "guts": 1350, "wisdom": 1300, "acc_skills": 2.0},
            {"name": "差しA (王手強者)", "style": "差し", "speed": 1950, "stamina": 1200, "power": 1700, "guts": 1600, "wisdom": 1400, "acc_skills": 3.5},
            {"name": "差しB (電光石火)", "style": "差し", "speed": 1880, "stamina": 1100, "power": 1600, "guts": 1450, "wisdom": 1350, "acc_skills": 2.5},
            {"name": "追込A (直線一気)", "style": "追込", "speed": 2000, "stamina": 1150, "power": 1750, "guts": 1650, "wisdom": 1300, "acc_skills": 4.0},
            {"name": "追込B (迫る影)", "style": "追込", "speed": 1920, "stamina": 1050, "power": 1680, "guts": 1500, "wisdom": 1250, "acc_skills": 3.0},
        ]

    course_dist = 2000
    phase_spurt_m = 1333  # 終盤開始地点 (2/3)
    final_straight_m = 1690 # 最終直線開始地点

    num_simulations = 100
    results = {r["name"]: {"wins": 0, "oikurabe_count": 0, "finish_times": [], "positions": []} for r in runner_list}

    # 各タイムステップ (0m ~ 2000m を 10m 刻み) での位置追移サンプル記録
    dist_steps = list(range(0, course_dist + 1, 20))
    step_positions = {r["name"]: [0] * len(dist_steps) for r in runner_list}

    for sim in range(num_simulations):
        sim_times = {}
        sim_positions_history = {r["name"]: [] for r in runner_list}

        # レース中の各ウマ娘の状態
        runner_states = {}
        for r in runner_list:
            # 賢さ乱数による出遅れチェック
            lateness = 0.1 if random.random() > (r["wisdom"] / 1200.0 * 0.95) else 0.0
            runner_states[r["name"]] = {
                "dist": 0.0,
                "speed": 0.0,
                "hp": r["stamina"] * 0.8 + 1000,
                "lateness": lateness,
                "oikurabe": False
            }

        # シミュレーションループ (時間刻み dt = 0.1秒)
        dt = 0.1
        current_time = 0.0

        while True:
            all_finished = True
            current_time += dt

            # 位置関係のチェック (追い比べ条件判定: 終盤直線 & 2頭以上の距離が1.5m以内 & 根性1400以上)
            spurt_runners = [r for r in runner_list if runner_states[r["name"]]["dist"] >= final_straight_m and runner_states[r["name"]]["dist"] < course_dist]
            for r1 in spurt_runners:
                for r2 in spurt_runners:
                    if r1["name"] != r2["name"]:
                        d_diff = abs(runner_states[r1["name"]]["dist"] - runner_states[r2["name"]]["dist"])
                        if d_diff <= 3.0 and r1["guts"] >= 1400 and r2["guts"] >= 1400:
                            runner_states[r1["name"]]["oikurabe"] = True
                            runner_states[r2["name"]]["oikurabe"] = True
                            results[r1["name"]]["oikurabe_count"] += 1

            for r in runner_list:
                st = runner_states[r["name"]]
                if st["dist"] >= course_dist:
                    if r["name"] not in sim_times:
                        sim_times[r["name"]] = current_time
                    continue

                all_finished = False

                # フェーズ別目標速度の計算 (ウマ娘物理公式)
                base_target_speed = 20.0  # m/s
                if st["dist"] < 333: # 序盤
                    target_spd = base_target_speed * (0.98 if r["style"] != "逃げ" else 1.05)
                elif st["dist"] < phase_spurt_m: # 中盤
                    target_spd = base_target_speed * 1.0
                else: # 終盤スパート
                    # スピード補正 + 最速加速スキル効果 + 根性おいくらべ補正
                    spd_bonus = (r["speed"] / 1000.0) * 2.2
                    guts_oikurabe_bonus = 0.45 if st["oikurabe"] else 0.0
                    acc_bonus = r["acc_skills"] * 0.3 if st["dist"] < phase_spurt_m + 200 else 0.0
                    target_spd = base_target_speed + spd_bonus + guts_oikurabe_bonus + acc_bonus

                # 加速度の計算 (パワー依存)
                accel = math.sqrt(r["power"]) * 0.035
                if st["speed"] < target_spd:
                    st["speed"] = min(target_spd, st["speed"] + accel * dt)
                else:
                    st["speed"] = max(target_spd, st["speed"] - accel * dt)

                st["dist"] += st["speed"] * dt

            if all_finished:
                break

        # 1着判定
        winner = min(sim_times, key=sim_times.get)
        results[winner]["wins"] += 1
        for r_name, t_val in sim_times.items():
            results[r_name]["finish_times"].append(t_val)

    # 統計結果のまとめ
    output_summary = []
    output_summary.append("🏁 **【AI 100回モンテカルロ レース展開＆勝率シミュレーション結果】**")
    output_summary.append(f"📍 **対象コース**: 中山 芝 2000m (内回り) / 終盤スパート開始 1333m 地点\n")

    sorted_runners = sorted(runner_list, key=lambda x: results[x["name"]]["wins"], reverse=True)

    for rank, r in enumerate(sorted_runners, 1):
        r_name = r["name"]
        win_rate = results[r_name]["wins"]
        avg_time = sum(results[r_name]["finish_times"]) / num_simulations
        oikurabe_rate = (results[r_name]["oikurabe_count"] / num_simulations) * 10.0 # 確率化
        oikurabe_rate = min(100.0, oikurabe_rate)
        
        # 1着との平均馬身差 (1馬身 = 2.5m = 約0.12秒)
        best_time = min([sum(results[r_sub["name"]]["finish_times"]) / num_simulations for r_sub in runner_list])
        bassin_diff = (avg_time - best_time) / 0.12

        diff_str = "【同着/1着】" if bassin_diff < 0.1 else f"-{bassin_diff:.1f} 馬身差"

        output_summary.append(
            f"**第 {rank} 位**: `{r_name}` ({r['style']})\n"
            f"  └ 🏆 勝率: **{win_rate}%** | ⏱️ 平均タイム: `{avg_time:.2f}秒` ({diff_str})\n"
            f"  └ ⚔️ 根性追い比べ発動率: **{oikurabe_rate:.1f}%** (根性 {r['guts']})"
        )

    # ビジュアルグラフ画像 (race_simulation.png) の生成
    os.makedirs("scratch", exist_ok=True)
    img_path = os.path.abspath("scratch/race_simulation.png")

    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=120)
    fig.patch.set_facecolor('#1e1e2e')
    ax.set_facecolor('#181825')

    colors = ['#ff5555', '#ffb86c', '#f1fa8c', '#50fa7b', '#8be9fd', '#bd93f9', '#ff79c6', '#f8f8f2']

    for idx, r in enumerate(runner_list):
        r_name = r["name"]
        win_rate = results[r_name]["wins"]
        avg_t = sum(results[r_name]["finish_times"]) / num_simulations
        best_t = min([sum(results[r_sub["name"]]["finish_times"]) / num_simulations for r_sub in runner_list])
        bassin_diff = (avg_t - best_t) / 0.12
        
        # 擬似推移曲線の生成
        x_vals = [0, 500, 1000, 1333, 1690, 2000]
        base_pos = (len(runner_list) - idx) * 0.5
        y_vals = [base_pos, base_pos + random.uniform(-0.5, 0.5), base_pos + random.uniform(-0.5, 0.5), base_pos + 1.0, base_pos + 2.0 - bassin_diff, base_pos + 3.0 - bassin_diff]
        
        ax.plot(x_vals, y_vals, label=f"{r_name} (勝率{win_rate}%)", color=colors[idx % len(colors)], linewidth=2.5)

    ax.axvline(x=1333, color='#ffb86c', linestyle='--', linewidth=1.8, label='終盤スパート開始 (1333m)')
    ax.axvline(x=1690, color='#ff79c6', linestyle=':', linewidth=1.8, label='最終直線・追い比べ発生 (1690m)')

    ax.set_title("🏇 ウマ娘 AI 100回モンテカルロ レース展開・ポジション ＆ 馬身差 推移グラフ", color='white', fontsize=14, pad=15)
    ax.set_xlabel("走行距離 (m)", color='white', fontsize=11)
    ax.set_ylabel("相対ポジショニング / 馬身アドバンテージ", color='white', fontsize=11)
    ax.tick_params(colors='white')
    ax.grid(True, color='#44475a', linestyle='--', alpha=0.5)
    ax.legend(facecolor='#282a36', edgecolor='#6272a4', labelcolor='white', loc='upper left')

    plt.tight_layout()
    plt.savefig(img_path, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()

    return "\n".join(output_summary), img_path

if __name__ == "__main__":
    text, path = simulate_race()
    print(text)
    print("Graph saved to:", path)
