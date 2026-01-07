承知しました。
帰宅後、このままテキストファイル（spec_v2.1.mdなど）として保存すればそのまま設計図として使える形式でまとめました。
これまで議論した「GitOps（強制同期）」「JSON動的設定」「プロセスKill」の機能を全て盛り込んだ、Remote PM System Ver 2.1 の正式仕様書です。
📋 Remote PM System 仕様書 (Ver 2.1)
1. システム概要
本システムは、モバイル端末（Gemini + GitHub）でのコード生成・編集を正（Master）とし、Mac miniをビルド＆実行専用の従（Slave）として稼働させるリモート開発環境である。
コンセプト: "GitOps & Cockpit"
 * GitOps: コードの反映は全てGit経由で行う。コンフリクト防止のため、ローカル変更は破棄し強制同期する。
 * Cockpit: 実行コマンドや対象プロジェクトの切り替えは、Streamlit上のGUI（コックピット）から動的に行う。
2. システム構成
構成図
Smartphone (Gemini/GitHub) ➡️ Push ➡️ GitHub Cloud ➡️ Pull ➡️ Mac mini (Watcher) ➡️ Build/Run ➡️ Streamlit (Dashboard)
主要コンポーネント
| コンポーネント | ファイル名 | 役割 |
|---|---|---|
| Configuration | config.json | 監視対象パス、実行コマンド、Killコマンドを定義する動的設定ファイル。 |
| Watcher | watcher.py | GitHubを監視し、変更検知時に「Kill → Pull → Run → Screenshot」を行う常駐スクリプト。 |
| Dashboard | app.py | スマホ用UI。設定ファイルの書き換え、実行結果（画像/ログ）の閲覧を行う。 |
3. ディレクトリ構造
Macのデスクトップに以下の構成で配置する。
~/Desktop/Gemini_Cockpit/
├── config.json        # [可変] 設定ファイル（スマホから編集可能）
├── watcher.py         # [常駐] 監視・実行プログラム
├── app.py             # [常駐] Streamlitサーバー
├── report.png         # [自動] 最新のスクリーンショット
└── build.log          # [自動] 最新の実行/ビルドログ

4. 機能要件
A. 自動同期・実行機能 (watcher.py)
 * ポーリング: 30秒間隔で設定ファイル (config.json) を読み込み、指定されたGitリポジトリの更新を確認する。
 * 強制同期: 更新がある場合、ローカルの変更を破棄し (git reset --hard)、リモートの最新状態に強制一致させる。
 * プロセス管理: ビルド実行前に、設定された kill_cmd を実行して古いプロセスを終了させる。
 * 非同期実行: run_cmd はバックグラウンドで実行し、標準出力/エラーを build.log に書き出す。
 * 結果保存: アプリ起動待機時間（5秒）の後、画面全体のスクリーンショットを report.png に保存する。
B. コックピット機能 (app.py)
 * Mission Control (サイドバー):
   * Project Path, Run Command, Kill Command, Branch の4項目をGUIで編集し、config.json を更新できる。
 * モニタリング (メイン画面):
   * Tab 1 (Screen): report.png を表示。
   * Tab 2 (Logs): build.log の中身をテキスト表示。
5. 実装コード
① 設定ファイル: config.json (初期値)
{
    "project_path": "/Users/あなたのユーザー名/Projects/TToDo",
    "branch": "main",
    "run_cmd": "dotnet run",
    "kill_cmd": "pkill -f TToDo"
}

② 監視・実行スクリプト: watcher.py
import time
import json
import os
import subprocess
import pyautogui
from git import Repo

# === 設定エリア ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, 'config.json')
SCREENSHOT_FILE = os.path.join(BASE_DIR, 'report.png')
LOG_FILE = os.path.join(BASE_DIR, 'build.log')

def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except:
        return None

def write_log(msg):
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    content = f"[{ts}] {msg}\n"
    print(content.strip())
    with open(LOG_FILE, 'w') as f:
        f.write(content)

def run_pipeline():
    conf = load_config()
    if not conf: return

    path = conf.get("project_path")
    branch = conf.get("branch", "main")
    run_cmd = conf.get("run_cmd")
    kill_cmd = conf.get("kill_cmd")

    if not os.path.exists(path):
        write_log(f"Path not found: {path}")
        return

    try:
        repo = Repo(path)
        origin = repo.remotes.origin
        origin.fetch()
        
        if repo.head.commit != origin.refs[branch].commit:
            write_log(f"🚀 Update detected in {path}")
            
            # 1. Kill Old Process
            if kill_cmd:
                subprocess.run(kill_cmd, shell=True)
                time.sleep(1)
            
            # 2. Force Sync
            repo.git.reset('--hard', f'origin/{branch}')
            
            # 3. Run New Command
            write_log(f"⚙️ Running: {run_cmd}")
            proc = subprocess.Popen(run_cmd, cwd=path, shell=True, 
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # 4. Screenshot
            time.sleep(5)
            pyautogui.screenshot(SCREENSHOT_FILE)
            write_log("✅ Cycle Completed.")
            
            # Check for immediate errors
            if proc.poll() is not None:
                out, err = proc.communicate()
                write_log(f"❌ Error:\n{err.decode()}\n{out.decode()}")

    except Exception as e:
        write_log(f"⚠️ Error: {e}")

if __name__ == "__main__":
    print("🛡️ Watcher Started.")
    while True:
        run_pipeline()
        time.sleep(30)

③ コックピットアプリ: app.py
import streamlit as st
import json
import os
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, 'config.json')
SCREENSHOT_FILE = os.path.join(BASE_DIR, 'report.png')
LOG_FILE = os.path.join(BASE_DIR, 'build.log')

st.set_page_config(page_title="Dev Cockpit", layout="centered")

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f: return json.load(f)
    return {}

def save_config(c):
    with open(CONFIG_FILE, 'w') as f: json.dump(c, f, indent=4)
    st.toast("Settings Updated!")

conf = load_config()

with st.sidebar:
    st.header("⚙️ Mission Control")
    with st.form("settings"):
        p = st.text_input("Path", value=conf.get("project_path",""))
        r = st.text_input("Run Cmd", value=conf.get("run_cmd",""))
        k = st.text_input("Kill Cmd", value=conf.get("kill_cmd",""))
        b = st.text_input("Branch", value=conf.get("branch","main"))
        if st.form_submit_button("Update"):
            save_config({"project_path":p, "run_cmd":r, "kill_cmd":k, "branch":b})
    
    if st.button("Reload"): st.rerun()

st.title("📡 Gemini Cockpit")
t1, t2 = st.tabs(["🖥️ Screen", "📝 Logs"])

with t1:
    if os.path.exists(SCREENSHOT_FILE):
        st.image(SCREENSHOT_FILE, caption=f"Last update: {time.ctime(os.path.getmtime(SCREENSHOT_FILE))}")
    else: st.info("No Image")

with t2:
    if st.button("Refresh Log"): st.rerun()
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE) as f: st.code(f.read())

6. 運用・環境要件
 * Git認証: SSH接続を設定し、パスワード入力なしで git pull が通る状態にすること。
 * スリープ設定: アプリ「Amphetamine」等を使用し、ディスプレイのスリープを無効化すること（スクショ黒画面回避のため）。
 * 起動コマンド:
   * Terminal A: streamlit run app.py
   * Terminal B: python watcher.py
