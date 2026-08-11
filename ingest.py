import os
import sys
import argparse
import datetime
import re
import time
import random
from dotenv import load_dotenv

# print時のエンコーディングエラーを回避（Windows向け）
sys.stdout.reconfigure(encoding='utf-8')

from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or YOUTUBE_API_KEY

if not YOUTUBE_API_KEY or not GEMINI_API_KEY:
    print("Error: YOUTUBE_API_KEY or GEMINI_API_KEY is missing in .env file.")
    exit(1)

def search_youtube_videos(query, max_results=5):
    """YouTubeで動画を検索し、動画IDのリストを返す"""
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    request = youtube.search().list(
        q=query,
        part='snippet',
        type='video',
        order='date',
        maxResults=max_results
    )
    response = request.execute()
    
    videos = []
    for item in response.get('items', []):
        videos.append({
            'video_id': item['id']['videoId'],
            'title': item['snippet']['title'],
            'channel': item['snippet']['channelTitle'],
            'published_at': item['snippet']['publishedAt']
        })
    return videos

def transcribe_audio_with_gemini(video_id):
    """字幕がない動画の音声をダウンロードし、Gemini APIで文字起こしする"""
    import yt_dlp
    import google.generativeai as genai
    import tempfile

    temp_dir = tempfile.mkdtemp()
    audio_path = None

    try:
        # 1. yt-dlpで音声をダウンロード（FFmpeg不要な形式、動画でもGeminiは可）
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio/ba/best',
            'outtmpl': os.path.join(temp_dir, f'{video_id}.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f'https://www.youtube.com/watch?v={video_id}', download=True)
            # ダウンロードされたファイルを特定
            for f in os.listdir(temp_dir):
                if f.startswith(video_id):
                    audio_path = os.path.join(temp_dir, f)
                    break

        if not audio_path or not os.path.exists(audio_path):
            print(f"  -> 音声ファイルのダウンロードに失敗しました")
            return None

        print(f"  -> 音声ダウンロード完了: {os.path.basename(audio_path)} ({os.path.getsize(audio_path) // 1024}KB)")

        # 2. Gemini APIで文字起こし
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.0-flash')

        print(f"  -> Gemini APIに音声をアップロード中...")
        uploaded_file = genai.upload_file(audio_path)

        response = model.generate_content([
            "この音声を日本語で文字起こししてください。"
            "話している内容をそのまま書き起こしてください。"
            "挨拶や前置きは不要で、文字起こしのみを出力してください。",
            uploaded_file
        ])

        # アップロードしたファイルを削除
        try:
            genai.delete_file(uploaded_file.name)
        except Exception:
            pass

        text = response.text.strip()
        if text:
            print(f"  -> Gemini文字起こし完了 ({len(text)}文字)")
            return text
        return None

    except Exception as e:
        print(f"  -> 音声文字起こしエラー: {e}")
        return None
    finally:
        # 一時ファイルを削除
        import shutil
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass

def get_transcript(video_id):
    """動画IDから字幕を取得する（日本語優先、自動生成・英語にフォールバック、最終手段で音声文字起こし）"""
    api = YouTubeTranscriptApi()
    
    # 1. 日本語 → 英語の順でフォールバック（手動・自動生成の両方を含む）
    try:
        transcript_list = api.fetch(video_id, languages=['ja', 'en'])
        full_text = " ".join([t.text for t in transcript_list])
        if full_text.strip():
            return full_text
    except Exception:
        pass
    
    # 2. 利用可能な字幕を何でも取得
    try:
        available = api.list(video_id)
        for t in available:
            try:
                fetched = t.fetch()
                full_text = " ".join([snippet.text for snippet in fetched])
                if full_text.strip():
                    print(f"  -> フォールバック: {t.language_code} の字幕を取得しました")
                    return full_text
            except Exception:
                continue
    except Exception:
        pass
    
    # 3. 字幕が全く取れない場合、音声から文字起こし（最終手段）
    print(f"  -> 字幕なし。音声から文字起こしを試みます...")
    return transcribe_audio_with_gemini(video_id)

def parse_iso8601_duration(duration_str):
    """ISO 8601 形式の動画時間 (e.g. PT1H25M30S, PT15M10S) を秒数に変換する"""
    import re
    if not duration_str:
        return 0
    hours = re.search(r'(\d+)H', duration_str)
    minutes = re.search(r'(\d+)M', duration_str)
    seconds = re.search(r'(\d+)S', duration_str)
    
    total_sec = 0
    if hours:
        total_sec += int(hours.group(1)) * 3600
    if minutes:
        total_sec += int(minutes.group(1)) * 60
    if seconds:
        total_sec += int(seconds.group(1))
    return total_sec

def is_livestream_or_long_video(item):
    """配信・生放送・アーカイブおよび30分以上の長尺配信動画を判定してスキップする"""
    snippet = item.get('snippet', {})
    title = snippet.get('title', '').lower()
    
    # 1. 生配信メタデータのチェック
    if 'liveStreamingDetails' in item or snippet.get('liveBroadcastContent') in ['live', 'upcoming']:
        return True, "生配信または配信アーカイブ"
        
    # 2. タイトルの配信キーワードチェック
    stream_keywords = ['配信', '生放送', 'ライブ', 'live', 'アーカイブ', '参加型', '作業用', '雑談', '初見さん大歓迎', 'メン限', 'メンバー限定', '同時視聴']
    if any(k in title for k in stream_keywords):
        return True, "配信タイトルキーワード該当"
        
    # 3. 再生時間のチェック（30分 = 1800秒 以上は長尺配信とみなしてスキップ）
    content_details = item.get('contentDetails', {})
    duration_str = content_details.get('duration', '')
    duration_sec = parse_iso8601_duration(duration_str)
    if duration_sec >= 1800:
        return True, f"30分以上の長尺動画 ({duration_sec // 60}分)"
        
    return False, ""

def extract_video_ids(text):
    """テキストから全てのYouTube動画IDを抽出する"""
    matches = re.finditer(r'(?:v=|youtu\.be/)([^&\s\?]+)', text)
    ids = []
    for m in matches:
        vid = m.group(1)
        if vid not in ids:
            ids.append(vid)
    return ids

def resolve_channel_videos(youtube, channel_id=None, handle=None, username=None):
    """チャンネル識別子から最新の動画IDリスト（最大5件）を取得する"""
    try:
        kwargs = {'part': 'contentDetails'}
        if channel_id:
            kwargs['id'] = channel_id
        elif handle:
            kwargs['forHandle'] = handle
        elif username:
            kwargs['forUsername'] = username
        else:
            return []
            
        res = youtube.channels().list(**kwargs).execute()
        if not res.get('items'):
            return []
            
        uploads_id = res['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        
        pl_res = youtube.playlistItems().list(
            part='snippet',
            playlistId=uploads_id,
            maxResults=5
        ).execute()
        
        vids = []
        for item in pl_res.get('items', []):
            vids.append(item['snippet']['resourceId']['videoId'])
        return vids
    except Exception as e:
        print(f"Error resolving channel videos: {e}")
        return []

def resolve_playlist_videos(youtube, playlist_id, max_results=10):
    """再生リスト(プレイリスト)IDから動画IDのリストを取得する"""
    try:
        pl_res = youtube.playlistItems().list(
            part='snippet',
            playlistId=playlist_id,
            maxResults=max_results
        ).execute()
        
        vids = []
        for item in pl_res.get('items', []):
            resource = item['snippet'].get('resourceId', {})
            if resource.get('kind') == 'youtube#video' and resource.get('videoId'):
                vids.append(resource['videoId'])
        return vids
    except Exception as e:
        print(f"Error resolving playlist videos: {e}")
        return []

def get_top_comments(youtube, video_id, max_results=5):
    """動画のトップコメントを取得する"""
    try:
        res = youtube.commentThreads().list(
            part='snippet',
            videoId=video_id,
            maxResults=max_results,
            order='relevance',
            textFormat='plainText'
        ).execute()
        comments = []
        for item in res.get('items', []):
            text = item['snippet']['topLevelComment']['snippet']['textDisplay']
            likes = item['snippet']['topLevelComment']['snippet'].get('likeCount', 0)
            comments.append({"text": text[:200], "likes": likes})
        return comments
    except Exception:
        return []

def rate_video(title, channel, view_count, like_count, comments, transcript_preview):
    """Gemini API枠を100%質問応答用に残すため、再生数・いいね数から即座におすすめ度★を判定する"""
    try:
        views = int(view_count) if str(view_count).isdigit() else 0
        likes = int(like_count) if str(like_count).isdigit() else 0
        
        if views >= 10000 or likes >= 300:
            return "★★★★★ 高評価攻略動画"
        elif views >= 3000 or likes >= 100:
            return "★★★★☆ 実用的な攻略解説"
        elif views >= 1000:
            return "★★★☆☆ 関連攻略情報"
        else:
            return "★★★☆☆ 新着検証情報"
    except Exception:
        return "★★★★☆ おすすめ攻略情報"

def ingest_manual_videos(text_input, progress_callback=None):
    """テキストに含まれる複数のYouTube URL(動画・チャンネル・再生リスト)から字幕を取得し、1動画ずつChromaDBに追加する（メモリ安全版）"""
    import gc

    def report(msg):
        """進捗をコールバックとコンソールに報告"""
        print(msg)
        if progress_callback:
            try:
                progress_callback(msg)
            except Exception:
                pass

    try:
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        
        report("🔍 URLを解析中...")
        video_ids = extract_video_ids(text_input)
        
        # チャンネルURLおよび再生リストURLの抽出と解決
        handle_matches = re.finditer(r'youtube\.com/(@[^&\s\?\/]+)', text_input)
        channel_id_matches = re.finditer(r'youtube\.com/channel/(UC[^&\s\?\/]+)', text_input)
        user_matches = re.finditer(r'youtube\.com/user/([^&\s\?\/]+)', text_input)
        playlist_matches = re.finditer(r'list=([a-zA-Z0-9_-]+)', text_input)
        
        for m in handle_matches:
            report(f"🔍 チャンネル {m.group(1)} の動画を取得中...")
            video_ids.extend(resolve_channel_videos(youtube, handle=m.group(1)))
        for m in channel_id_matches:
            report(f"🔍 チャンネルの動画を取得中...")
            video_ids.extend(resolve_channel_videos(youtube, channel_id=m.group(1)))
        for m in user_matches:
            video_ids.extend(resolve_channel_videos(youtube, username=m.group(1)))
        for m in playlist_matches:
            playlist_id = m.group(1)
            report(f"🔍 再生リストの動画を取得中...")
            video_ids.extend(resolve_playlist_videos(youtube, playlist_id=playlist_id, max_results=10))
            # 今後の自動巡回用に playlists.txt に登録保存
            try:
                playlists_file = "playlists.txt"
                existing_pl = set()
                if os.path.exists(playlists_file):
                    with open(playlists_file, "r", encoding="utf-8") as pf:
                        existing_pl = set([l.strip() for l in pf if l.strip()])
                full_pl_url = f"https://www.youtube.com/playlist?list={playlist_id}"
                if full_pl_url not in existing_pl and playlist_id not in existing_pl:
                    with open(playlists_file, "a", encoding="utf-8") as pf:
                        pf.write(f"{full_pl_url}\n")
                    report(f"✨ 新しい再生リストを自動巡回リスト (playlists.txt) に追加登録しました！")
                else:
                    report(f"ℹ️ この再生リストはすでに自動巡回リストに登録済みです。")
            except Exception as pe:
                print(f"Error saving to playlists.txt: {pe}")
            
        # 重複削除
        video_ids = list(dict.fromkeys(video_ids))
        
        if not video_ids:
            return False, "入力されたテキストから動画URL、チャンネルURL、再生リストURLを見つけられませんでした。"

        if len(video_ids) > 10:
            video_ids = video_ids[:10]

        processed_file = "processed_videos.txt"
        processed_ids = set()
        if os.path.exists(processed_file):
            with open(processed_file, "r", encoding="utf-8") as f:
                processed_ids = set([line.strip() for line in f if line.strip()])

        # 未学習のIDのみに絞り込む
        new_video_ids = [vid for vid in video_ids if vid not in processed_ids]
        
        if not new_video_ids:
            return False, "指定された動画（またはチャンネル・再生リストの動画）はすべて既に学習済みでした！"



        if len(video_ids) > 10:
            video_ids = video_ids[:10]

        processed_file = "processed_videos.txt"
        processed_ids = set()
        if os.path.exists(processed_file):
            with open(processed_file, "r", encoding="utf-8") as f:
                processed_ids = set([line.strip() for line in f if line.strip()])

        # 未学習のIDのみに絞り込む
        new_video_ids = [vid for vid in video_ids if vid not in processed_ids]
        
        if not new_video_ids:
            return False, "指定された動画（またはチャンネルの最新動画）はすべて既に学習済みでした！"

        # 動画情報を取得
        request = youtube.videos().list(
            part='snippet,statistics,contentDetails,liveStreamingDetails',
            id=','.join(new_video_ids)
        )
        response = request.execute()
        
        items = response.get('items', [])
        if not items:
            return False, "動画情報の取得に失敗しました。"

        report(f"📋 {len(items)}件の動画が見つかりました。1つずつゆっくり処理します...")

        # Embeddingsモデルを1回だけ読み込む
        report("🧠 AIモデルを準備中...")
        embeddings = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-small")
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

        added_videos_info = []
        all_documents_for_summary = []
        success_count = 0
        skip_count = 0

        # === 1動画ずつ処理（メモリに余裕を持たせてゆっくり） ===
        for idx, item in enumerate(items, 1):
            video_id = item['id']
            title = item['snippet']['title']
            
            # --- 配信・生放送・アーカイブ・30分以上の長尺配信のスキップチェック ---
            is_stream, stream_reason = is_livestream_or_long_video(item)
            if is_stream:
                report(f"⏭️ [{idx}/{len(items)}] 「{title}」→ {stream_reason}のためスキップ")
                skip_count += 1
                continue

            channel = item['snippet']['channelTitle']
            published_at = item['snippet']['publishedAt']
            like_count = item['statistics'].get('likeCount', '0')
            view_count = item['statistics'].get('viewCount', '0')
            date_str = published_at[:10]
            
            # --- 詳細ログ表示 ---
            report(
                f"🔄 [{idx}/{len(items)}] 処理中...\n"
                f"📺 タイトル: {title}\n"
                f"👤 投稿者: {channel}\n"
                f"📅 投稿日: {date_str}\n"
                f"👁️ 再生数: {int(view_count):,}\n"
                f"👍 いいね: {int(like_count):,}"
            )
            
            # IPブロック対策の待機（最初の1件目以外）
            if idx > 1:
                time.sleep(8)
            
            # コメント取得
            comments = get_top_comments(youtube, video_id)
            time.sleep(2)  # API呼び出し間隔
            
            transcript_text = get_transcript(video_id)
            if not transcript_text:
                desc = item['snippet'].get('description', '').strip()
                if desc:
                    transcript_text = f"（概要欄情報）{desc}"
                    report(f"ℹ️ [{idx}/{len(items)}] 「{title}」→ 字幕/音声不可のため動画の概要欄から学習します")
                else:
                    report(f"⏭️ [{idx}/{len(items)}] 「{title}」→ 字幕/音声/概要欄取得不可。スキップ")
                    skip_count += 1
                    gc.collect()
                    time.sleep(3)
                    continue
            
            # ★おすすめ度をGeminiが評価
            report(f"⭐ [{idx}/{len(items)}] おすすめ度を評価中...")
            rating = rate_video(title, channel, view_count, like_count, comments, transcript_text[:500])
            time.sleep(2)  # API呼び出し間隔
            
            report(
                f"📊 [{idx}/{len(items)}] 評価結果\n"
                f"📺 「{title}」\n"
                f"⭐ おすすめ度: {rating}"
            )
            
            text_with_date = f"[投稿日: {date_str} | 再生数: {view_count} | いいね数: {like_count}] {transcript_text}"
            
            # この1動画分のチャンクを作成
            chunks = text_splitter.split_text(text_with_date)
            meta = {
                "source": f"https://www.youtube.com/watch?v={video_id}",
                "title": title,
                "channel": channel,
                "date": date_str,
                "views": view_count,
                "likes": like_count
            }
            meta_list = [meta] * len(chunks)
            
            # この1動画分をChromaDBに保存
            report(f"💾 [{idx}/{len(items)}] 「{title}」をAIに学習させています...")
            Chroma.from_texts(
                texts=chunks,
                embedding=embeddings,
                metadatas=meta_list,
                persist_directory="./chroma_db"
            )
            
            # 学習履歴ログの記録
            try:
                log_file = "learned_knowledge_log.json"
                log_data = []
                if os.path.exists(log_file):
                    with open(log_file, "r", encoding="utf-8") as lf:
                        log_data = json.load(lf)
                
                log_entry = {
                    "video_id": video_id,
                    "title": title,
                    "channel": channel,
                    "date": date_str,
                    "learned_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "rating": rating,
                    "url": f"https://www.youtube.com/watch?v={video_id}"
                }
                log_data.append(log_entry)
                with open(log_file, "w", encoding="utf-8") as lf:
                    json.dump(log_data, lf, ensure_ascii=False, indent=2)
            except Exception as log_e:
                print(f"Error logging learned video: {log_e}")

            added_videos_info.append(f"・{title}\n  {rating}")
            all_documents_for_summary.append(text_with_date[:5000])  # 要約用に一部だけ保持
            processed_ids.add(video_id)
            success_count += 1
            
            # 処理済みIDを即座に保存（途中クラッシュ対策）
            with open(processed_file, "w", encoding="utf-8") as f:
                for vid in processed_ids:
                    f.write(f"{vid}\n")
            
            # メモリ解放
            del transcript_text, text_with_date, chunks, meta_list, comments
            gc.collect()
            
            report(f"✅ [{idx}/{len(items)}] 「{title}」→ 学習完了！")
            
            # 次の動画の前にメモリ回復待ち（余裕を持たせる）
            time.sleep(5)

        if success_count == 0:
            return False, "動画は見つかりましたが、いずれも字幕・音声が取得できませんでした。"

        info_str = "\n".join(added_videos_info)
        
        # AI要約の生成
        summary_text = ""
        try:
            report("📝 AIが学習内容を要約中...")
            llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.7)
            prompt = ChatPromptTemplate.from_template(
                "あなたはウマ娘の熟練アシスタントです。以下のYouTube動画の文字起こしデータを元に、今回新しく学習した内容のざっくりとした要約を箇条書きで3〜4行で作成してください。\n"
                "挨拶や前置きは不要で、要約のみを出力してください。\n\n"
                "【動画内容】\n{text}"
            )
            chain = prompt | llm | StrOutputParser()
            combined_text = "\n\n".join(all_documents_for_summary)[:30000]
            summary_text = chain.invoke({"text": combined_text})
        except Exception as e:
            print(f"Error generating summary: {e}")
            summary_text = "（要約の生成中にエラーが発生しました）"

        # 要約もログに保存
        try:
            log_file = "learned_knowledge_log.json"
            if os.path.exists(log_file):
                with open(log_file, "r", encoding="utf-8") as lf:
                    log_data = json.load(lf)
                for entry in log_data:
                    if entry.get("video_id") in [item['id'] for item in items]:
                        entry["summary"] = summary_text
                with open(log_file, "w", encoding="utf-8") as lf:
                    json.dump(log_data, lf, ensure_ascii=False, indent=2)
        except Exception as log_summary_e:
            print(f"Error updating summary in log: {log_summary_e}")
        
        # 要約用データを解放
        del all_documents_for_summary
        gc.collect()
            
        return True, (info_str, summary_text)
        
    except Exception as e:
        print(f"Error in ingest_manual_videos: {e}")
        return False, f"処理中にエラーが発生しました: {e}"

def ingest_videos(base_query="ウマ娘", max_results=5):
    """動画を検索し、字幕を取得してChromaDBに保存する（YouTube API クォータ保護設計）"""
    try:
        processed_file = "processed_videos.txt"
        processed_ids = set()
        if os.path.exists(processed_file):
            with open(processed_file, "r", encoding="utf-8") as f:
                processed_ids = set([line.strip() for line in f if line.strip()])

        videos = []
        seen_video_ids = set()

        # 1. 登録再生リスト (playlists.txt) から優先巡回（たった1ユニットで超軽量）
        playlists_file = "playlists.txt"
        if os.path.exists(playlists_file):
            try:
                youtube_client = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
                with open(playlists_file, "r", encoding="utf-8") as pf:
                    pl_lines = [l.strip() for l in pf if l.strip()]
                for pl_line in pl_lines:
                    if len(videos) >= 4:
                        break
                    pl_match = re.search(r'list=([a-zA-Z0-9_-]+)', pl_line)
                    pl_id = pl_match.group(1) if pl_match else pl_line
                    print(f"Fetching registered playlist: {pl_id}...")
                    pl_vids = resolve_playlist_videos(youtube_client, pl_id, max_results=4)
                    
                    pl_count = 0
                    for vid in pl_vids:
                        if vid not in seen_video_ids and vid not in processed_ids:
                            seen_video_ids.add(vid)
                            videos.append({
                                'video_id': vid,
                                'title': '再生リスト動画',
                                'channel': '',
                                'published_at': ''
                            })
                            pl_count += 1
                            if pl_count >= 2:
                                break
            except Exception as ple:
                print(f"Error fetching registered playlists: {ple}")

        # 2. 未学習動画が少ない場合のみキーワード検索を少量実行
        if len(videos) < 2:
            try:
                keyword_file = "keywords.txt"
                keywords = ["チャンミ"]
                if os.path.exists(keyword_file):
                    with open(keyword_file, "r", encoding="utf-8") as f:
                        lines = [line.strip() for line in f if line.strip()]
                        if lines:
                            keywords = lines[:1]
                for kw in keywords:
                    search_query = f"{base_query} {kw}".strip()
                    print(f"Searching for '{search_query}'...")
                    results = search_youtube_videos(search_query, 2)
                    for v in results:
                        if v['video_id'] not in seen_video_ids and v['video_id'] not in processed_ids:
                            seen_video_ids.add(v['video_id'])
                            videos.append(v)
            except Exception as se:
                print(f"Search quota check: {se}")
                    
        # 1回の自動巡回での全体取得件数を最大4件に安全制限
        if len(videos) > 4:
            videos = videos[:4]


        
        if not videos:
            print("No new videos found.")
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open("ingest.log", "a", encoding="utf-8") as log_file:
                log_file.write(f"[{now_str}] 新しい動画は見つかりませんでした。\n")
            return [], ""

        # Fetch like counts and live status for the new videos
        print("Fetching like counts and checking live status...")
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        video_ids = [v['video_id'] for v in videos]
        
        # We can request up to 50 IDs at once
        like_counts = {}
        view_counts = {}
        is_live = {}
        snippets = {}
        for i in range(0, len(video_ids), 50):
            batch_ids = video_ids[i:i+50]
            request = youtube.videos().list(
                part='snippet,statistics,contentDetails,liveStreamingDetails',
                id=','.join(batch_ids)
            )
            response = request.execute()
            for item in response.get('items', []):
                vid = item['id']
                like_counts[vid] = item['statistics'].get('likeCount', '0')
                view_counts[vid] = item['statistics'].get('viewCount', '0')
                snippets[vid] = item.get('snippet', {})
                
                # 生配信・アーカイブ・長尺配信（30分以上）の完全スキップ判定
                is_st, reason = is_livestream_or_long_video(item)
                is_live[vid] = is_st
                if is_st:
                    print(f"Skipping stream/archive video ({reason}): {item['snippet'].get('title', '')}")
                
        # Filter out livestreams and apply details
        filtered_videos = []
        for v in videos:
            vid = v['video_id']
            if is_live.get(vid, False):
                continue
            snip = snippets.get(vid, {})
            v['title'] = snip.get('title', v['title'])
            v['channel'] = snip.get('channelTitle', v['channel'])
            v['published_at'] = snip.get('publishedAt', v['published_at'])
            v['like_count'] = like_counts.get(vid, '0')
            v['view_count'] = view_counts.get(vid, '0')
            filtered_videos.append(v)


        documents = []
        metadatas = []

        for video in filtered_videos:
            print(f"Fetching transcript for: {video['title']} ({video['video_id']})")
            time.sleep(12.0)  # Gemini API クォータ消費を抑えるため12秒の安全インターバル
            text = get_transcript(video['video_id'])
            if not text:
                snip = snippets.get(video['video_id'], {})
                desc = snip.get('description', '').strip()
                if desc:
                    text = f"（概要欄情報）{desc}"
            if text:
                # 日付といいね情報、再生数をテキストの先頭に付与してチャンク分割に備える
                date_str = video['published_at'][:10]
                like_str = video.get('like_count', '0')
                view_str = video.get('view_count', '0')
                text_with_date = f"[投稿日: {date_str} | 再生数: {view_str} | いいね数: {like_str}] {text}"
                documents.append(text_with_date)
                metadatas.append({
                    "source": f"https://www.youtube.com/watch?v={video['video_id']}",
                    "title": video['title'],
                    "channel": video['channel'],
                    "date": date_str,
                    "views": view_str,
                    "likes": like_str
                })
        
        if not documents:
            print("No transcripts could be extracted.")
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open("ingest.log", "a", encoding="utf-8") as log_file:
                log_file.write(f"[{now_str}] 新しい動画は見つかりましたが、文字起こしが取得できませんでした。\n")
            return [], ""

        print("Splitting texts...")
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        
        docs_to_embed = []
        meta_to_embed = []
        
        for doc, meta in zip(documents, metadatas):
            chunks = text_splitter.split_text(doc)
            docs_to_embed.extend(chunks)
            meta_to_embed.extend([meta] * len(chunks))

        # Initialize HuggingFace Embeddings
        print("Initializing HuggingFace embeddings (intfloat/multilingual-e5-small)...")
        embeddings = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-small")
        
        # ChromaDBに保存 (ローカルディレクトリ 'chroma_db' に永続化)
        Chroma.from_texts(
            texts=docs_to_embed,
            embedding=embeddings,
            metadatas=meta_to_embed,
            persist_directory="./chroma_db"
        )
        
        # 処理完了した動画IDを保存
        with open(processed_file, "a", encoding="utf-8") as f:
            for vid in seen_video_ids:
                f.write(f"{vid}\n")
                
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("ingest.log", "a", encoding="utf-8") as log_file:
            # 重複を排除しつつ、必要な情報を全てまとめた文字列を作成
            added_videos_info = []
            seen_titles = set()
            for m in metadatas:
                if m['title'] not in seen_titles:
                    seen_titles.add(m['title'])
                    info_str = f"{m['title']} (投稿者: {m['channel']} | 投稿日: {m['date']} | 再生数: {m['views']} | いいね: {m['likes']})"
                    added_videos_info.append(info_str)
            
            log_file.write(f"[{now_str}] 情報収集が完了しました。新たに {len(added_videos_info)} 件の動画データを追加学習しました:\n")
            for info in added_videos_info:
                log_file.write(f"  - {info}\n")
                
        # --- AI要約の生成 ---
        summary_text = ""
        if documents:
            try:
                print("Generating AI summary of new videos...")
                llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.7)
                prompt = ChatPromptTemplate.from_template(
                    "あなたはウマ娘の熟練アシスタントです。以下のYouTube動画の文字起こしデータ（複数）を元に、今回新しく学習した内容（最新メタや育成のコツなど）のざっくりとした要約を箇条書きで3〜4行で作成してください。\n"
                    "挨拶や前置きは不要で、要約のみを出力してください。文字数が多すぎないように注意してください。\n\n"
                    "【動画内容】\n{text}"
                )
                chain = prompt | llm | StrOutputParser()
                # APIの文字数制限対策として、先頭から50000文字程度に制限
                combined_text = "\n\n".join(documents)[:50000]
                summary_text = chain.invoke({"text": combined_text})
                print(f"Generated summary:\n{summary_text}")
            except Exception as e:
                print(f"Error generating summary: {e}")
                summary_text = "（要約の生成中にエラーが発生しました）"

        print("Done! Data ingested into ChromaDB.")
        return added_videos_info, summary_text

    except Exception as e:
        print(f"Error during ingestion: {e}")
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("ingest.log", "a", encoding="utf-8") as log_file:
            log_file.write(f"[{now_str}] エラーが発生しました: {e}\n")
        return [], ""

def categorize_video_title(title):
    """動画タイトルからウマ娘の攻略テーマカテゴリを自動判定する"""
    t = title.lower()
    categories = []
    
    if any(k in t for k in ['リグヒ', 'loh', 'チャンミ', 'チャンピオンズ', 'リーグオブヒーローズ', '皐月賞', '東京2400', '中山']):
        categories.append("🏆 チャンミ/リグヒ攻略")
    if any(k in t for k in ['因子', '相性', '親因子', '青因子', '周回', '厳選']):
        categories.append("🧬 因子厳選/周回")
    if any(k in t for k in ['サポカ', 'サポート', 'ssr', 'ガチャ', '引くべき', '性能', '完凸']):
        categories.append("🎴 サポカ/ガチャ評価")
    if any(k in t for k in ['育成', '立ち回り', 'スキル', '解説', '編成', 'ローテーション']):
        categories.append("🏇 育成論/スキル解説")
    if any(k in t for k in ['ぱかライブ', 'ぱかまとめ', 'アプデ', '最新情報', '新シナリオ', '新キャラ', '公式']):
        categories.append("🎬 最新情報/ぱかライブ")
        
    if not categories:
        categories.append("📌 その他/総合攻略")
        
    return categories

def get_learned_videos_list():
    """ChromaDBから学習済みの動画タイトルと情報のリスト（カテゴリ付き）を取得する"""
    try:
        if not os.path.exists("./chroma_db"):
            return []
            
        embeddings = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-small")
        vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
        data = vectorstore.get()
        metadatas = data.get("metadatas", [])
        
        seen_sources = set()
        learned_videos = []
        
        for meta in metadatas:
            if not meta:
                continue
            source = meta.get("source", "")
            title = meta.get("title", "タイトル不明")
            channel = meta.get("channel", "不明")
            date = meta.get("date", "")
            
            if source and source not in seen_sources:
                seen_sources.add(source)
                categories = categorize_video_title(title)
                learned_videos.append({
                    "title": title,
                    "channel": channel,
                    "date": date,
                    "source": source,
                    "categories": categories
                })
        
        return learned_videos
    except Exception as e:
        print(f"Error reading learned videos: {e}")
        return []

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest YouTube videos for Uma Musume AI")
    parser.add_argument("--base-query", type=str, default="ウマ娘", help="Base search query for YouTube")
    parser.add_argument("--max", type=int, default=3, help="Max videos to fetch per keyword")
    args = parser.parse_args()
    
    ingest_videos(args.base_query, args.max)

