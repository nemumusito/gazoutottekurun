import os
import requests
from bs4 import BeautifulSoup
import time
import re
from urllib.parse import unquote, urlparse
import json
import gradio as gr
from PIL import Image
import io
import webview
import threading
import traceback
import logging

# ロギングの設定
logging.basicConfig(filename='scraper.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# 定数の定義
ASPECT_RATIO_CHOICES = [
    "指定なし ⬜",
    "1:1 ⬛",
    "4:3 🔲",
    "16:9 📺",
    "9:16 📱"
]
BASE_FOLDER = "img"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
TIMEOUT = 30  # リクエストのタイムアウト時間（秒）

# キャンセルフラグ
cancel_flag = threading.Event()

def sanitize_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', "", filename)

def create_folder(base_folder, query):
    sanitized_query = sanitize_filename(query)
    folder_path = os.path.join(base_folder, sanitized_query)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    return folder_path

def parse_aspect_ratio(aspect_ratio):
    if aspect_ratio == "指定なし ⬜":
        return None
    match = re.search(r'(\d+):(\d+)', aspect_ratio)
    if match:
        return float(match.group(1)) / float(match.group(2))
    return None

def download_and_convert_image(url, folder, aspect_ratio, aspect_ratio_tolerance):
    if cancel_flag.is_set():
        return None
    try:
        response = requests.get(url, stream=True, timeout=TIMEOUT)
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '').lower()
            if 'image' in content_type:
                image_data = response.content
                image = Image.open(io.BytesIO(image_data))
                
                # アスペクト比のチェック
                if aspect_ratio is not None:
                    width, height = image.size
                    image_ratio = width / height
                    if abs(image_ratio - aspect_ratio) > aspect_ratio_tolerance:
                        logging.info(f"Aspect ratio mismatch: {url}")
                        return None

                # 元のファイル名を取得
                parsed_url = urlparse(url)
                original_filename = os.path.basename(parsed_url.path)
                filename = sanitize_filename(original_filename)
                
                # 拡張子をwebpに変更
                filename_without_ext, _ = os.path.splitext(filename)
                filename = f"{filename_without_ext}.webp"
                
                filepath = os.path.join(folder, filename)
                
                # 同名ファイルが存在する場合はスキップ
                if os.path.exists(filepath):
                    logging.info(f"File already exists, skipping: {filepath}")
                    return None
                
                # Convert and save as WebP
                image.save(filepath, 'WEBP')
                logging.info(f"Downloaded and converted: {filepath}")
                return filepath
            else:
                logging.warning(f"Not an image: {url}")
        else:
            logging.warning(f"Failed to download: {url}. Status code: {response.status_code}")
    except requests.Timeout:
        logging.error(f"Timeout occurred while downloading: {url}")
    except Exception as e:
        logging.error(f"Error downloading/converting {url}: {str(e)}")
    return None

def fetch_image_urls(search_url, headers):
    if cancel_flag.is_set():
        return []
    try:
        response = requests.get(search_url, headers=headers, timeout=TIMEOUT)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch search results. Status code: {response.status_code}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        image_urls = []
        
        for img in soup.find_all('a', class_='iusc'):
            if cancel_flag.is_set():
                break
            try:
                m_content = json.loads(img.get('m', '{}'))
                img_url = m_content.get('murl')
                if img_url and img_url.startswith('http'):
                    image_urls.append(img_url)
            except json.JSONDecodeError:
                continue
            except Exception as e:
                logging.error(f"Error processing image URL: {str(e)}")
        
        return image_urls
    except requests.Timeout:
        logging.error("Timeout occurred while fetching image URLs")
        return []
    except Exception as e:
        logging.error(f"Error fetching image URLs: {str(e)}")
        return []

def scrape_images(query, num_images=10, aspect_ratio="指定なし ⬜", aspect_ratio_tolerance=0.2, progress=None):
    cancel_flag.clear()
    search_url = f"https://www.bing.com/images/search?q={query}&form=HDRSC2&first=1"
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    
    if not os.path.exists(BASE_FOLDER):
        os.makedirs(BASE_FOLDER)
    folder = create_folder(BASE_FOLDER, query)
    
    image_urls = fetch_image_urls(search_url, headers)
    if not image_urls:
        logging.error("No image URLs found")
        return []
    
    downloaded_images = []
    
    target_ratio = parse_aspect_ratio(aspect_ratio)
    
    if progress is not None:
        progress(0, desc="Downloading images")
    
    for i, img_url in enumerate(image_urls):
        if cancel_flag.is_set():
            break
        if len(downloaded_images) >= num_images:
            break
        
        logging.info(f"Attempting to download: {img_url}")
        filepath = download_and_convert_image(img_url, folder, target_ratio, aspect_ratio_tolerance)
        if filepath:
            downloaded_images.append(filepath)
            if progress is not None:
                progress((len(downloaded_images)) / num_images, desc=f"Downloaded {len(downloaded_images)} of {num_images}")
        else:
            logging.warning(f"Failed to download image {i+1}")
        
        time.sleep(1)  # 1秒待機してサーバーに負荷をかけないようにする

    logging.info(f"Total images downloaded: {len(downloaded_images)}")
    return downloaded_images

def gradio_scrape_images(query, num_images, aspect_ratio, aspect_ratio_tolerance, progress=gr.Progress()):
    try:
        if not query.strip():
            raise ValueError("検索キーワードを入力してください。")
        if num_images < 1 or num_images > 50:
            raise ValueError("ダウンロードする画像の数は1から50の間で指定してください。")
        
        downloaded_images = scrape_images(query, num_images, aspect_ratio, aspect_ratio_tolerance, progress)
        if not downloaded_images:
            if cancel_flag.is_set():
                raise gr.Error("ダウンロードがキャンセルされました。")
            else:
                raise Exception("画像のダウンロードに失敗しました。")
        return downloaded_images
    except Exception as e:
        logging.error(f"Error in gradio_scrape_images: {str(e)}")
        logging.error(traceback.format_exc())
        raise gr.Error(f"エラーが発生しました: {str(e)}")

def cancel_download():
    cancel_flag.set()
    return "ダウンロードをキャンセルしました。"

iface = gr.Interface(
    fn=gradio_scrape_images,
    inputs=[
        gr.Textbox(label="検索したい画像のキーワードを入力してください"),
        gr.Slider(minimum=1, maximum=50, value=10, step=1, label="ダウンロードする画像の数"),
        gr.Dropdown(
            choices=ASPECT_RATIO_CHOICES,
            value="指定なし ⬜",
            label="アスペクト比"
        ),
        gr.Slider(minimum=0.1, maximum=0.5, value=0.2, step=0.1, label="アスペクト比の許容範囲")
    ],
    outputs=gr.Gallery(label="ダウンロードされた画像"),
    title="画像スクレイピングツール",
    description="キーワードを入力すると、関連する画像を自動的にダウンロードして表示します。画像はWebP形式で保存されます。",
    allow_flagging="never",
)

iface.load(lambda: None, None, gr.Button("Clear"), outputs=iface.inputs)
cancel_button = gr.Button("キャンセル")
cancel_button.click(fn=cancel_download, inputs=None, outputs=gr.Textbox())

def run_gradio():
    iface.launch(share=True)

def run_webview():
    webview.create_window("画像スクレイピングツール", "http://127.0.0.1:7860")
    webview.start()

if __name__ == "__main__":
    gradio_thread = threading.Thread(target=run_gradio)
    gradio_thread.start()
    
    # Gradioサーバーが起動するのを少し待つ
    time.sleep(5)
    
    run_webview()
