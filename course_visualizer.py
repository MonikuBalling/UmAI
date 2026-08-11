"""
ウマ娘 プリティーダービー プレミアム・コース物理シミュレーション ビジュアル図面エンジン
(Modern Glassmorphism & Cyberpunk Neon Theme)
"""

import os
import math
from PIL import Image, ImageDraw, ImageFont

def get_japanese_font(size=13, is_bold=False):
    """Windows標準の日本語フォント(メイリオ/MSゴシック)を安全に読み込み"""
    font_paths = [
        "C:\\Windows\\Fonts\\meiryo.ttc",
        "C:\\Windows\\Fonts\\meiryob.ttc" if is_bold else "C:\\Windows\\Fonts\\meiryo.ttc",
        "C:\\Windows\\Fonts\\msgothic.ttc",
        "C:\\Windows\\Fonts\\msyh.ttc"
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                pass
    return ImageFont.load_default()

def draw_rounded_rectangle(draw, xy, corner_radius, fill=None, outline=None, width=1):
    """角丸長方形の描画ヘルパー"""
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle([x1, y1, x2, y2], radius=corner_radius, fill=fill, outline=outline, width=width)

def generate_course_map_image(
    course_name: str,
    total_dist: int,
    final_start_m: int,
    skill_name: str,
    skill_start_m: int,
    skill_end_m: int,
    uphill_list: list = None,
    downhill_list: list = None,
    output_path: str = "course_map.png",
    event_schedule: str = None,
    corner_3_start: int = None,
    corner_3_end: int = None,
    invalid_skills_list: list = None
):
    # キャンバスサイズ (横 1240px, 縦 660px)
    width, height = 1240, 660
    
    # ベースキャンバス（RGBA）
    img = Image.new("RGBA", (width, height), (11, 14, 23, 255)) # 深みのあるネイビーブラック
    
    # レイヤー合成用のオーバーレイ描画
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw_ol = ImageDraw.Draw(overlay)

    # フォント設定
    font_title = get_japanese_font(20, is_bold=True)
    font_section = get_japanese_font(14, is_bold=True)
    font_sub = get_japanese_font(12)
    font_lbl = get_japanese_font(11)
    font_bold = get_japanese_font(12, is_bold=True)
    font_small = get_japanese_font(10)

    # カラー定義
    C_BG_CARD = (20, 27, 41, 230)
    C_BORDER_CARD = (45, 62, 92, 255)
    
    C_PHASE_OPEN = (0, 210, 255, 220)    # ネオンシアン
    C_PHASE_MID = (16, 185, 129, 220)    # エメラルドグリーン
    C_PHASE_FINAL = (244, 63, 94, 220)   # クリムゾンレッド
    
    C_UPHILL = (255, 159, 67, 230)      # アンバーオレンジ
    C_DOWNHILL = (0, 210, 211, 230)     # ターコイズブルー
    C_CORNER = (168, 85, 247, 220)      # パープル

    # 1. バックグラウンドカードパネル
    # 左パネル: 断面プロファイル (x: 20 -> 780)
    draw_rounded_rectangle(draw_ol, [20, 75, 780, 635], 16, fill=C_BG_CARD, outline=C_BORDER_CARD, width=1)
    # 右パネル: JRA公式コース構造 (x: 795 -> 1220)
    draw_rounded_rectangle(draw_ol, [795, 75, 1220, 635], 16, fill=C_BG_CARD, outline=C_BORDER_CARD, width=1)

    # 2. メインヘッダー
    # 左端ゴールドアクセントバー
    draw_rounded_rectangle(draw_ol, [20, 18, 26, 56], 3, fill=(255, 215, 0, 255))
    draw_ol.text((36, 16), f"【{course_name}】 物理高低差プロファイル ＆ JRA公式幾何構造 解析マップ", font=font_title, fill=(255, 255, 255, 255))
    
    # ヘッダーピルバッジ (コース仕様 & イベント開催時期)
    b1_text = f"🏁 全長: {total_dist}m"
    b2_text = f"🎯 終盤開始 (2/3): {final_start_m}m"
    draw_rounded_rectangle(draw_ol, [36, 48, 160, 68], 10, fill=(35, 48, 72, 255), outline=(60, 85, 125, 255))
    draw_ol.text((44, 50), b1_text, font=font_sub, fill=(200, 225, 255, 255))

    draw_rounded_rectangle(draw_ol, [168, 48, 350, 68], 10, fill=(60, 30, 45, 255), outline=(150, 50, 75, 255))
    draw_ol.text((176, 50), b2_text, font=font_sub, fill=(255, 180, 195, 255))

    if event_schedule:
        b3_text = f"📅 開催予定: {event_schedule}"
        draw_rounded_rectangle(draw_ol, [358, 48, 680, 68], 10, fill=(50, 40, 15, 255), outline=(180, 150, 40, 255))
        draw_ol.text((366, 50), b3_text, font=font_sub, fill=(255, 230, 150, 255))

        if any(k in str(event_schedule) for k in ["LOH", "リグヒ", "ヒーロー", "リーグ・オブ・ヒーローズ"]):
            b4_text = "🚫 デバフスキル効果無効・禁止ルール (LOH)"
            draw_rounded_rectangle(draw_ol, [690, 48, 990, 68], 10, fill=(80, 20, 25, 255), outline=(244, 63, 94, 255))
            draw_ol.text((698, 50), b4_text, font=font_sub, fill=(255, 180, 195, 255))

    # パディングとスケール設定 (左パネル内)
    pad_left = 60
    track_width = 680

    def m_to_x(m_val):
        return pad_left + int((m_val / total_dist) * track_width)

    parsed_uphill = []
    for item in uphill_list or []:
        if isinstance(item, dict):
            parsed_uphill.append((int(item.get("start", 0)), int(item.get("end", 0))))
        elif isinstance(item, (tuple, list)) and len(item) >= 2:
            parsed_uphill.append((int(item[0]), int(item[1])))
            
    parsed_downhill = []
    for item in downhill_list or []:
        if isinstance(item, dict):
            parsed_downhill.append((int(item.get("start", 0)), int(item.get("end", 0))))
        elif isinstance(item, (tuple, list)) and len(item) >= 2:
            parsed_downhill.append((int(item[0]), int(item[1])))

    if not parsed_uphill and not parsed_downhill:
        parsed_uphill = [(0, 200), (int(total_dist * 0.9), total_dist)]
        parsed_downhill = [(int(total_dist * 0.3), int(total_dist * 0.5))]

    uphill_list = parsed_uphill
    downhill_list = parsed_downhill

    # 凡例バッジ (左パネル上部)
    draw_ol.text((40, 92), "📊 コース断面図 (スロープ高低差 & ゾーン解析)", font=font_section, fill=(255, 255, 255, 255))
    
    # 凡例カプセルバッジ
    leg_x = 420
    draw_rounded_rectangle(draw_ol, [leg_x, 92, leg_x + 50, 110], 9, fill=(0, 210, 255, 40), outline=C_PHASE_OPEN)
    draw_ol.text((leg_x + 12, 94), "序盤", font=font_small, fill=(150, 235, 255))

    leg_x += 58
    draw_rounded_rectangle(draw_ol, [leg_x, 92, leg_x + 50, 110], 9, fill=(16, 185, 129, 40), outline=C_PHASE_MID)
    draw_ol.text((leg_x + 12, 94), "中盤", font=font_small, fill=(160, 255, 200))

    leg_x += 58
    draw_rounded_rectangle(draw_ol, [leg_x, 92, leg_x + 50, 110], 9, fill=(244, 63, 94, 40), outline=C_PHASE_FINAL)
    draw_ol.text((leg_x + 12, 94), "終盤", font=font_small, fill=(255, 170, 190))

    leg_x += 58
    draw_rounded_rectangle(draw_ol, [leg_x, 92, leg_x + 65, 110], 9, fill=(168, 85, 247, 40), outline=C_CORNER)
    draw_ol.text((leg_x + 10, 94), "コーナー", font=font_small, fill=(225, 185, 255))

    leg_x += 73
    draw_rounded_rectangle(draw_ol, [leg_x, 92, leg_x + 55, 110], 9, fill=(255, 159, 67, 40), outline=C_UPHILL)
    draw_ol.text((leg_x + 8, 94), "↗ 上り坂", font=font_small, fill=(255, 210, 160))

    leg_x += 63
    draw_rounded_rectangle(draw_ol, [leg_x, 92, leg_x + 55, 110], 9, fill=(0, 210, 211, 40), outline=C_DOWNHILL)
    draw_ol.text((leg_x + 8, 94), "↘ 下り坂", font=font_small, fill=(170, 245, 255))

    # ==========================================
    # 【左側/上段】 断面高低差スローププロファイル
    # ==========================================
    track_top_base_y = 200
    thickness_top = 24

    def m_to_y(m_val):
        y_offset = 0.0
        for (d_s, d_e) in downhill_list:
            if d_s <= m_val <= d_e:
                prog = (m_val - d_s) / max(1, (d_e - d_s))
                y_offset += prog * 30.0
            elif m_val > d_e:
                y_offset += 30.0
                
        for (u_s, u_e) in uphill_list:
            if u_s <= m_val <= u_e:
                prog = (m_val - u_s) / max(1, (u_e - u_s))
                y_offset -= prog * 34.0
            elif m_val > u_e:
                y_offset -= 34.0
                
        return int(track_top_base_y + y_offset)

    step_m = 4
    m_points = list(range(0, total_dist + 1, step_m))
    if m_points[-1] != total_dist:
        m_points.append(total_dist)

    x_open_end_m = int(total_dist * (1/6))

    def draw_curved_phase(start_m, end_m, color):
        pts_top = []
        pts_bottom = []
        sub_m = [m for m in m_points if start_m <= m <= end_m]
        if not sub_m:
            return
        if sub_m[0] > start_m:
            sub_m.insert(0, start_m)
        if sub_m[-1] < end_m:
            sub_m.append(end_m)
            
        for m in sub_m:
            x = m_to_x(m)
            y = m_to_y(m)
            pts_top.append((x, y))
            pts_bottom.append((x, y + thickness_top))
            
        poly = pts_top + list(reversed(pts_bottom))
        draw_ol.polygon(poly, fill=color)

    # ベースの3色（序盤・中盤・終盤）を描画
    draw_curved_phase(0, x_open_end_m, C_PHASE_OPEN)
    draw_curved_phase(x_open_end_m, final_start_m, C_PHASE_MID)
    draw_curved_phase(final_start_m, total_dist, C_PHASE_FINAL)

    # 第3コーナーの範囲決定 (指定がない場合は全体距離から自動計算)
    c3_s = corner_3_start if corner_3_start is not None else int(total_dist * 0.60)
    c3_e = corner_3_end if corner_3_end is not None else min(total_dist - 200, c3_s + int(total_dist * 0.15))

    # 第3コーナーのゴールドハイライト描画 (上段断面グラフ)
    draw_curved_phase(c3_s, c3_e, (255, 215, 0, 180))
    xc3_s, yc3_s = m_to_x(c3_s), m_to_y(c3_s)
    yc3_text = yc3_s - 26 if yc3_s > 170 else yc3_s + thickness_top + 6
    draw_rounded_rectangle(draw_ol, [xc3_s, yc3_text, xc3_s + 200, yc3_text + 18], 9, fill=(50, 40, 10, 230), outline=(255, 215, 0), width=1)
    draw_ol.text((xc3_s + 8, yc3_text + 2), f"🚩 最終前 第3コーナー ({c3_s}m~{c3_e}m)", font=font_lbl, fill=(255, 235, 130))

    # 坂道描画＆注釈バッジ
    for (u_s, u_e) in uphill_list:
        draw_curved_phase(u_s, u_e, C_UPHILL)
        xu_s, yu_s = m_to_x(u_s), m_to_y(u_s)
        y_txt = yu_s - 26 if yu_s > 170 else yu_s + thickness_top + 6
        draw_rounded_rectangle(draw_ol, [xu_s, y_txt, xu_s + 210, y_txt + 18], 9, fill=(40, 25, 10, 200), outline=C_UPHILL)
        draw_ol.text((xu_s + 8, y_txt + 2), f"↗ 上り坂 ({u_s}m~{u_e}m | 勾配+2.2%)", font=font_lbl, fill=(255, 220, 170))

    for (d_s, d_e) in downhill_list:
        draw_curved_phase(d_s, d_e, C_DOWNHILL)
        xd_s, yd_s = m_to_x(d_s), m_to_y(d_s)
        draw_rounded_rectangle(draw_ol, [xd_s, yd_s + thickness_top + 6, xd_s + 210, yd_s + thickness_top + 24], 9, fill=(10, 35, 40, 200), outline=C_DOWNHILL)
        draw_ol.text((xd_s + 8, yd_s + thickness_top + 8), f"↘ 下り坂 ({d_s}m~{d_e}m | 省エネ35%)", font=font_lbl, fill=(170, 245, 255))

    # ==========================================
    # 【左側/下段】 コース形状区間 ＆ コーナー・直線帯
    # ==========================================
    track_bot_y = 350
    thickness_bot = 36

    # ベース枠 (序盤/中盤/終盤)
    draw_rounded_rectangle(draw_ol, [m_to_x(0), track_bot_y, m_to_x(x_open_end_m), track_bot_y + thickness_bot], 6, fill=C_PHASE_OPEN)
    draw_rounded_rectangle(draw_ol, [m_to_x(x_open_end_m), track_bot_y, m_to_x(final_start_m), track_bot_y + thickness_bot], 6, fill=C_PHASE_MID)
    draw_rounded_rectangle(draw_ol, [m_to_x(final_start_m), track_bot_y, m_to_x(total_dist), track_bot_y + thickness_bot], 6, fill=C_PHASE_FINAL)

    c1_s, c1_e = int(total_dist * 0.18), int(total_dist * 0.43)
    str_opp_s, str_opp_e = c1_e, c3_s
    c4_s, c4_e = c3_e, int(total_dist * 0.88)
    final_str_s = c4_e

    # コーナー・直線帯の枠
    draw_rounded_rectangle(draw_ol, [m_to_x(c1_s), track_bot_y + 3, m_to_x(c1_e), track_bot_y + thickness_bot - 3], 6, fill=(120, 50, 180, 180), outline=(220, 160, 255))
    draw_ol.text((m_to_x(c1_s) + 6, track_bot_y + 9), f"第1・2コーナー ({c1_s}m~{c1_e}m)", font=font_lbl, fill=(245, 225, 255))

    draw_rounded_rectangle(draw_ol, [m_to_x(str_opp_s), track_bot_y + 3, m_to_x(str_opp_e), track_bot_y + thickness_bot - 3], 6, fill=(35, 45, 65, 180), outline=(180, 200, 230))
    draw_ol.text((m_to_x(str_opp_s) + 6, track_bot_y + 9), f"向正面直線 ({str_opp_s}m~{str_opp_e}m)", font=font_lbl, fill=(230, 240, 255))

    # ★最終前の第3コーナーを黄金ゴールドで超目立つようにハイライト！★
    draw_rounded_rectangle(draw_ol, [m_to_x(c3_s), track_bot_y + 3, m_to_x(c3_e), track_bot_y + thickness_bot - 3], 6, fill=(180, 140, 10, 220), outline=(255, 215, 0), width=2)
    draw_ol.text((m_to_x(c3_s) + 4, track_bot_y + 9), f"🚩 第3コーナー ({c3_s}m~{c3_e}m)", font=font_bold, fill=(255, 235, 130))

    # 第4コーナー
    draw_rounded_rectangle(draw_ol, [m_to_x(c4_s), track_bot_y + 3, m_to_x(c4_e), track_bot_y + thickness_bot - 3], 6, fill=(120, 50, 180, 180), outline=(220, 160, 255))
    draw_ol.text((m_to_x(c4_s) + 4, track_bot_y + 9), f"第4コーナー", font=font_lbl, fill=(245, 225, 255))

    draw_rounded_rectangle(draw_ol, [m_to_x(final_str_s), track_bot_y + 3, m_to_x(total_dist), track_bot_y + thickness_bot - 3], 6, fill=(180, 130, 0, 200), outline=(255, 230, 100))
    draw_ol.text((m_to_x(final_str_s) + 6, track_bot_y + 9), f"最終直線 ({final_str_s}m~)", font=font_lbl, fill=(255, 245, 200))

    # 坂道オーバーレイ
    for (u_s, u_e) in uphill_list:
        draw_rounded_rectangle(draw_ol, [m_to_x(u_s), track_bot_y, m_to_x(u_e), track_bot_y + thickness_bot], 6, fill=C_UPHILL)
        draw_ol.text((m_to_x(u_s) + 4, track_bot_y + 9), f"↗ 上り坂", font=font_lbl, fill=(255, 245, 220))

    for (d_s, d_e) in downhill_list:
        draw_rounded_rectangle(draw_ol, [m_to_x(d_s), track_bot_y, m_to_x(d_e), track_bot_y + thickness_bot], 6, fill=C_DOWNHILL)
        draw_ol.text((m_to_x(d_s) + 4, track_bot_y + 9), f"↘ 下り坂", font=font_lbl, fill=(220, 250, 255))

    # ガイドライン（縦線 & マーカー）
    x_start = m_to_x(0)
    draw_ol.line([(x_start, 150), (x_start, track_bot_y + thickness_bot + 16)], fill=(255, 255, 255, 200), width=2)
    draw_rounded_rectangle(draw_ol, [x_start - 28, track_bot_y + thickness_bot + 20, x_start + 28, track_bot_y + thickness_bot + 38], 8, fill=(35, 45, 60, 220), outline=(180, 200, 230))
    draw_ol.text((x_start - 20, track_bot_y + thickness_bot + 22), "START", font=font_bold, fill=(255, 255, 255))

    x_goal = m_to_x(total_dist)
    draw_ol.line([(x_goal, 150), (x_goal, track_bot_y + thickness_bot + 16)], fill=(255, 215, 0, 220), width=2)
    draw_rounded_rectangle(draw_ol, [x_goal - 55, track_bot_y + thickness_bot + 20, x_goal + 25, track_bot_y + thickness_bot + 38], 8, fill=(60, 50, 15, 220), outline=(255, 215, 0))
    draw_ol.text((x_goal - 48, track_bot_y + thickness_bot + 22), f"GOAL {total_dist}m", font=font_bold, fill=(255, 220, 100))

    x_final_s = m_to_x(final_start_m)
    draw_ol.line([(x_final_s, 140), (x_final_s, track_bot_y + thickness_bot + 16)], fill=(244, 63, 94, 255), width=3)
    draw_rounded_rectangle(draw_ol, [x_final_s - 45, 135, x_final_s + 45, 155], 8, fill=(70, 20, 35, 220), outline=(244, 63, 94))
    draw_ol.text((x_final_s - 38, 137), f"終盤 {final_start_m}m", font=font_bold, fill=(255, 180, 195))

    draw_rounded_rectangle(draw_ol, [x_final_s - 50, track_bot_y + thickness_bot + 20, x_final_s + 50, track_bot_y + thickness_bot + 38], 8, fill=(70, 20, 35, 220), outline=(244, 63, 94))
    draw_ol.text((x_final_s - 42, track_bot_y + thickness_bot + 22), "スパート開始", font=font_bold, fill=(255, 180, 195))

    # スキル発動シミュレーションハイライト
    display_skill = skill_name
    if skill_name == "汎用" or not skill_name:
        display_skill = "最速加速スキル (汎用想定)"

    if skill_start_m >= 0 and skill_end_m > skill_start_m:
        x_sk_s = m_to_x(skill_start_m)
        x_sk_e = m_to_x(min(total_dist, skill_end_m))
        
        # ネオンゴールドの半透明グロー領域 (上段スロープ部)
        draw_rounded_rectangle(draw_ol, [x_sk_s, 160, x_sk_e, 310], 10, fill=(255, 215, 0, 40), outline=(255, 215, 0, 255), width=2)
        
        # 下部解説ガラスカード (文字被りを完全回避して美しく2行配置)
        sk_card_y = 450
        card_w = max(360, x_sk_e - x_sk_s + 120)
        draw_rounded_rectangle(draw_ol, [x_sk_s - 10, sk_card_y, x_sk_s + card_w, sk_card_y + 48], 12, fill=(35, 30, 15, 230), outline=(255, 215, 0, 220), width=1)
        draw_ol.text((x_sk_s + 8, sk_card_y + 6), f"⚡ 【最速スキル発動想定区間】 『{display_skill}』", font=font_bold, fill=(255, 225, 120))
        draw_ol.text((x_sk_s + 24, sk_card_y + 26), f"└─ 発動: {skill_start_m}m 地点  ➔  効果終了: {skill_end_m}m (実効効果中)", font=font_lbl, fill=(240, 230, 180))

    # ==========================================
    # 【右側】 JRA公式本物レース場コース形状ミニマップ
    # ==========================================
    rc_panel_x = 810
    rc_panel_y = 95
    rc_w, rc_h = 395, 525

    draw_ol.text((rc_panel_x + 15, rc_panel_y + 12), f"JRA公式 {course_name}", font=font_section, fill=(255, 215, 0))
    draw_ol.text((rc_panel_x + 15, rc_panel_y + 34), "オーバル構造 ＆ 幾何学グラフィック", font=font_sub, fill=(170, 200, 230))

    center_x = rc_panel_x + 195
    center_y = rc_panel_y + 270
    
    def get_real_jra_track_coord(m_val, is_inner=False):
        frac = m_val / total_dist
        r_base_x = 145 if not is_inner else 112
        r_base_y = 92 if not is_inner else 64

        if frac <= 0.15:
            angle = math.pi/2 - (frac / 0.15) * (math.pi * 0.15)
            x_scale, y_scale = 1.0, 1.0
        elif frac <= 0.43:
            f_local = (frac - 0.15) / (0.43 - 0.15)
            angle = (math.pi/2 - math.pi * 0.15) - f_local * (math.pi * 0.85)
            x_scale, y_scale = 1.15, 0.95
        elif frac <= 0.62:
            f_local = (frac - 0.43) / (0.62 - 0.43)
            angle = -math.pi*0.35 - f_local * (math.pi * 0.3)
            x_scale, y_scale = 1.05, 1.1
        else:
            f_local = (frac - 0.62) / 0.38
            angle = -math.pi*0.65 - f_local * (math.pi * 1.15)
            x_scale, y_scale = 0.95, 1.0

        # 左スロープの高低差標高をそのまま3D標高Z軸にダイナミック変換（うねうねヘビコース）
        z_offset = 0.0
        for (d_s, d_e) in downhill_list:
            if d_s <= m_val <= d_e:
                prog = (m_val - d_s) / max(1, (d_e - d_s))
                z_offset += prog * 38.0  # 下り坂でぐぐーっとダイナミックに沈み込む (うねうね波打ち)
            elif m_val > d_e:
                z_offset += 38.0
                
        for (u_s, u_e) in uphill_list:
            if u_s <= m_val <= u_e:
                prog = (m_val - u_s) / max(1, (u_e - u_s))
                z_offset -= prog * 45.0  # 上り坂で立体的にぐぐーっと大きく浮き上がる (ヘビの波打ち)
            elif m_val > u_e:
                z_offset -= 45.0

        x = center_x + int(r_base_x * x_scale * math.cos(angle))
        y = center_y + int(r_base_y * y_scale * math.sin(angle) + z_offset)
        return x, y

    # サンプル点群の生成 (5mピッチ)
    m_samples = list(range(0, total_dist, 5))
    
    # 1. まずトラックの3D立体側壁（厚み影）を描画し、ヘビのように浮き上がる奥行き感を表現！
    for i in range(len(m_samples) - 1):
        m_curr = m_samples[i]
        m_next = m_samples[i+1]
        
        pt_out_c = get_real_jra_track_coord(m_curr, is_inner=False)
        pt_out_n = get_real_jra_track_coord(m_next, is_inner=False)
        
        # 側面厚みポリゴン (8px下方向へ押出)
        wall_poly = [pt_out_c, pt_out_n, (pt_out_n[0], pt_out_n[1] + 7), (pt_out_c[0], pt_out_c[1] + 7)]
        draw_ol.polygon(wall_poly, fill=(12, 18, 30, 220))

    # 2. 区間ごとに左側グラフと100%完全同期するフェーズカラーでグラデーション塗り分け描画
    for i in range(len(m_samples) - 1):
        m_curr = m_samples[i]
        m_next = m_samples[i+1]
        
        pt_out_c = get_real_jra_track_coord(m_curr, is_inner=False)
        pt_in_c = get_real_jra_track_coord(m_curr, is_inner=True)
        pt_out_n = get_real_jra_track_coord(m_next, is_inner=False)
        pt_in_n = get_real_jra_track_coord(m_next, is_inner=True)
        
        poly_seg = [pt_out_c, pt_out_n, pt_in_n, pt_in_c]
        
        # フェーズカラーの同期判定 (序盤: シアン / 中盤: グリーン / 終盤: クリムゾン)
        if m_curr < x_open_end_m:
            seg_color = (0, 180, 220, 230)
        elif m_curr < final_start_m:
            seg_color = (16, 160, 100, 230)
        else:
            seg_color = (220, 50, 80, 230)
            
        # 第3コーナー・上り坂・下り坂区間のネオンカラー強調
        if c3_s <= m_curr <= c3_e:
            seg_color = (255, 200, 0, 240) # ★第3コーナーはゴールド発光！★
        for (u_s, u_e) in uphill_list:
            if u_s <= m_curr <= u_e:
                seg_color = (255, 140, 30, 240) # 強調オレンジ
        for (d_s, d_e) in downhill_list:
            if d_s <= m_curr <= d_e:
                seg_color = (0, 200, 200, 240) # 強調ターコイズ

        draw_ol.polygon(poly_seg, fill=seg_color, outline=None)

    # 外枠・内枠トラックライン
    outer_pts = [get_real_jra_track_coord(m, is_inner=False) for m in m_samples]
    inner_pts = [get_real_jra_track_coord(m, is_inner=True) for m in m_samples]
    draw_ol.polygon(outer_pts, outline=(240, 245, 255, 220), width=2)
    draw_ol.polygon(inner_pts, outline=(240, 245, 255, 220), width=2)

    # 1. 最終前 第3コーナー マーカー (右側3Dトラック上)
    xc3_j, yc3_j = get_real_jra_track_coord(int((c3_s + c3_e) / 2))
    draw_ol.ellipse([xc3_j - 7, yc3_j - 7, xc3_j + 7, yc3_j + 7], fill=(255, 215, 0), outline=(255, 255, 255), width=2)
    draw_rounded_rectangle(draw_ol, [xc3_j - 65, yc3_j - 26, xc3_j + 65, yc3_j - 6], 7, fill=(50, 40, 10, 230), outline=(255, 215, 0))
    draw_ol.text((xc3_j - 58, yc3_j - 24), f"🚩 第3コーナー ({c3_s}m~)", font=font_bold, fill=(255, 235, 130))

    # 2. 終盤開始位置 マーカー
    xf_j, yf_j = get_real_jra_track_coord(final_start_m)
    draw_ol.ellipse([xf_j - 7, yf_j - 7, xf_j + 7, yf_j + 7], fill=(244, 63, 94), outline=(255, 255, 255), width=2)
    draw_rounded_rectangle(draw_ol, [xf_j - 55, yf_j + 12, xf_j + 55, yf_j + 30], 7, fill=(60, 15, 30, 230), outline=(244, 63, 94))
    draw_ol.text((xf_j - 48, yf_j + 14), f"終盤開始 {final_start_m}m", font=font_lbl, fill=(255, 190, 205))

    # 3. スキル発動位置 マーカー
    if skill_start_m >= 0:
        xs_j, ys_j = get_real_jra_track_coord(skill_start_m)
        draw_ol.ellipse([xs_j - 7, ys_j - 7, xs_j + 7, ys_j + 7], fill=(255, 215, 0), outline=(255, 255, 255), width=2)
        sk_tag = display_skill if len(display_skill) <= 11 else "最速加速スキル"
        lbl_y = ys_j - 28 if ys_j < center_y else ys_j + 14
        draw_rounded_rectangle(draw_ol, [xs_j - 55, lbl_y, xs_j + 55, lbl_y + 20], 7, fill=(50, 40, 10, 230), outline=(255, 215, 0))
        draw_ol.text((xs_j - 48, lbl_y + 3), f"⚡ {sk_tag}", font=font_lbl, fill=(255, 235, 150))

    # 4. 坂位置 マーカー (テキスト重なり回避オフセット)
    for (u_s, u_e) in uphill_list:
        xu_j, yu_j = get_real_jra_track_coord(int((u_s + u_e)/2))
        draw_ol.ellipse([xu_j - 6, yu_j - 6, xu_j + 6, yu_j + 6], fill=(255, 159, 67), outline=(255, 255, 255), width=1)
        draw_rounded_rectangle(draw_ol, [xu_j - 26, yu_j + 16, xu_j + 26, yu_j + 34], 6, fill=(50, 30, 10, 230), outline=(255, 159, 67))
        draw_ol.text((xu_j - 20, yu_j + 18), "↗ 急坂", font=font_bold, fill=(255, 215, 170))

    # 4. コーナー・直線エリアラベル
    draw_ol.text((center_x + 90, center_y - 15), "第1・2コーナー", font=font_lbl, fill=(225, 185, 255))
    draw_ol.text((center_x - 165, center_y - 15), "第3・4コーナー", font=font_lbl, fill=(225, 185, 255))
    draw_ol.text((center_x - 35, center_y - 130), "向正面直線", font=font_lbl, fill=(210, 230, 255))
    
    draw_rounded_rectangle(draw_ol, [center_x - 65, center_y + 125, center_x + 65, center_y + 145], 8, fill=(50, 40, 10, 220), outline=(255, 215, 0))
    draw_ol.text((center_x - 55, center_y + 127), "🏁 最終直線 ＆ GOAL", font=font_bold, fill=(255, 225, 120))

    # 5. 右側パネル下部: 【⚠️ コース構造上 不発・罠スキル 縦一覧カード】
    inv_skills = invalid_skills_list or [
        "最終直線での加速スキル (終盤開始が第3コーナーのため無効)",
        "直線一気/迫る影 (終盤開始が直線でないため無効)",
        "登山家 (序盤の坂で出ると加速効果無効)"
    ]
    
    inv_card_x1, inv_card_y1 = 805, 460
    inv_card_x2, inv_card_y2 = 1210, 630
    draw_rounded_rectangle(draw_ol, [inv_card_x1, inv_card_y1, inv_card_x2, inv_card_y2], 12, fill=(45, 20, 25, 235), outline=(244, 63, 94, 255), width=1)
    
    # 見出しヘッダー
    draw_rounded_rectangle(draw_ol, [inv_card_x1 + 8, inv_card_y1 + 6, inv_card_x2 - 8, inv_card_y1 + 26], 6, fill=(75, 20, 30, 255), outline=(244, 63, 94, 200))
    draw_ol.text((inv_card_x1 + 14, inv_card_y1 + 8), "⚠️ 【コース構造上 不発・罠スキル注意一覧】", font=font_bold, fill=(255, 190, 200))
    
    y_off = inv_card_y1 + 32
    for idx, inv_item in enumerate(inv_skills[:3]):
        if isinstance(inv_item, dict):
            sk_name = inv_item.get("skill", "")
            sk_reason = inv_item.get("reason", "")
        else:
            sk_name = str(inv_item)
            sk_reason = ""
            
        draw_ol.text((inv_card_x1 + 12, y_off), f"❌ {sk_name}", font=font_bold, fill=(255, 175, 185))
        if sk_reason:
            y_off += 16
            r_str = sk_reason if len(sk_reason) <= 26 else sk_reason[:25] + "…"
            draw_ol.text((inv_card_x1 + 24, y_off), f"└─ 理由: {r_str}", font=font_small, fill=(255, 215, 220))
        y_off += 22

    # フッター注記
    draw_ol.text((30, height - 22), "ウマ娘 プリティーダービー 統合物理シミュレーションマップ ｜ Designed by AGY Engine", font=font_small, fill=(100, 125, 155))

    # 画像レイヤーの合成と保存
    final_img = Image.alpha_composite(img, overlay)
    final_img.convert("RGB").save(output_path, "PNG")
    return output_path

if __name__ == "__main__":
    generate_course_map_image("中山 芝 2000m (内回り)", 2000, 1333, "汎用", 1333, 1501, output_path="preview_course_map.png")

