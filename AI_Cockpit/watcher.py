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
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

def write_log(msg):
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    content = f"[{ts}] {msg}\n"
    print(content.strip())
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
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
        
        # ローカルとリモートのコミットハッシュを比較
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
            # Windowsでは shell=True が必要
            proc = subprocess.Popen(run_cmd, cwd=path, shell=True, 
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # 4. Screenshot
            time.sleep(5)
            pyautogui.screenshot(SCREENSHOT_FILE)
            write_log("✅ Cycle Completed.")
            
            # Check for immediate errors
            if proc.poll() is not None:
                out, err = proc.communicate()
                write_log(f"❌ Error:\n{err.decode('cp932', errors='ignore')}\n{out.decode('cp932', errors='ignore')}")

    except Exception as e:
        write_log(f"⚠️ Error: {e}")

if __name__ == "__main__":
    print("🛡️ Watcher Started.")
    while True:
        run_pipeline()
        time.sleep(30)