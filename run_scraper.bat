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
start python image_scraper.py

REM ブラウザでGradioのURLを開く
timeout /t 5 /nobreak
start http://127.0.0.1:7860/

echo Gradioのインターフェースがブラウザで開かれました。
echo スクリプトを終了するには、このウィンドウを閉じてください。
pause
