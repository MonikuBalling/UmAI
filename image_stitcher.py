"""
image_stitcher.py
ウマ娘の複数枚スクショから重複領域（スクロールで被っているスキル枠・ヘッダー部分）を
画像特徴テンプレートマッチングで自動検出・カットし、完璧に重ならないシームレスな「1枚の縦長ロング画像（因子レシート）」を合成するモジュール
"""

from PIL import Image, ImageChops
import io

def find_overlap_offset(img1: Image.Image, img2: Image.Image) -> int:
    """
    img1の下部とimg2の上部をテンプレート比較し、スクロールによる重複領域の高さ(px)をミリ単位で自動検出
    """
    w1, h1 = img1.size
    w2, h2 = img2.size
    
    # 横幅を合わせる
    if w1 != w2:
        ratio = w1 / float(w2)
        img2 = img2.resize((w1, int(h2 * ratio)), Image.Resampling.LANCZOS)
        w2, h2 = img2.size

    # 重複探索範囲: 高さの10%〜80%
    min_search = int(h2 * 0.05)
    max_search = int(min(h1, h2) * 0.85)
    
    best_offset = 0
    min_diff = float("inf")
    
    # 比較エリア（中央の80%幅）
    crop_x1 = int(w1 * 0.1)
    crop_x2 = int(w1 * 0.9)
    
    # スライドサーチ
    for offset in range(min_search, max_search, 2):
        crop1 = img1.crop((crop_x1, h1 - offset, crop_x2, h1))
        crop2 = img2.crop((crop_x1, 0, crop_x2, offset))
        
        diff = ImageChops.difference(crop1, crop2)
        # 画像差分の平均値を算出
        stat = sum(sum(pixel) for pixel in diff.getdata()) / float(crop1.width * crop1.height * 3)
        
        if diff_val := stat < min_diff:
            min_diff = stat
            best_offset = offset
            
        if stat < 5.0: # ほぼ完全一致
            return offset
            
    # 一致度が低い場合（重複なしと判定）
    if min_diff > 25.0:
        return 0
        
    return best_offset

def stitch_images_vertically(image_bytes_list: list[bytes], header_title: str = "") -> bytes:
    """
    複数枚のスクショから重複しているスキル表示枠やヘッダーを自動識別して切り落とし、
    一切被りのない綺麗に繋がった1枚の縦長ロング画像（因子レシート）を生成
    """
    if not image_bytes_list:
        return b""
        
    pil_images = []
    for img_bytes in image_bytes_list:
        try:
            im = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
            pil_images.append(im)
        except Exception as e:
            print(f"Error opening image for stitching: {e}")
            
    if not pil_images:
        return b""
        
    base_width = pil_images[0].width
    
    # 全画像の横幅をリサイズ統一
    normalized_images = []
    for im in pil_images:
        if im.width != base_width:
            ratio = base_width / float(im.width)
            new_h = int(im.height * ratio)
            im_resized = im.resize((base_width, new_h), Image.Resampling.LANCZOS)
        else:
            im_resized = im
        normalized_images.append(im_resized)
        
    if len(normalized_images) == 1:
        out_buf = io.BytesIO()
        normalized_images[0].convert("RGB").save(out_buf, format="PNG", quality=98)
        return out_buf.getvalue()

    # 1枚目をベースにし、2枚目以降の重複領域(overlap)を検出して自動トリミング接続
    cropped_slices = [normalized_images[0]]
    
    for i in range(len(normalized_images) - 1):
        prev_img = normalized_images[i]
        next_img = normalized_images[i+1]
        
        overlap_h = find_overlap_offset(prev_img, next_img)
        
        if overlap_h > 15:
            # 重複している上部(overlap_h px)をカットして新しいスライスとする
            w, h = next_img.size
            crop_next = next_img.crop((0, overlap_h, w, h))
            cropped_slices.append(crop_next)
        else:
            cropped_slices.append(next_img)

    # 最終キャンバスの長さを計算
    total_height = sum(im.height for im in cropped_slices)
    canvas = Image.new("RGBA", (base_width, total_height))

    # 隙間・被り0ピクセルでピタッと縦に連結
    current_y = 0
    for im in cropped_slices:
        canvas.paste(im, (0, current_y), im)
        current_y += im.height

    out_buf = io.BytesIO()
    canvas.convert("RGB").save(out_buf, format="PNG", quality=98)
    return out_buf.getvalue()
