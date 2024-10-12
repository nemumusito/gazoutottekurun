@echo off
echo プロジェクトを起動します...

REM 仮想環境の作成（存在しない場合）
if not exist venv (
    echo 仮想環境を作成しています...
    python -m venv venv
)

REM 仮想環境のアクティベーション
call venv\Scripts\activate

REM requirements.txtのインストール（ファイルが存在する場合）
if exist requirements.txt (
    echo 必要なパッケージをインストールしています...
    pip install -r requirements.txt
)

REM image_scraper.pyの実行
echo スクレイピングを開始します...
python image_scraper.py

echo スクレイピングが完了しました。
pause
