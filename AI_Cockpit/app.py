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
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    return {}

def save_config(c):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f: json.dump(c, f, indent=4)
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
        # Windowsのエンコードエラー対策のため utf-8 指定
        try:
            with open(LOG_FILE, encoding='utf-8') as f: st.code(f.read())
        except:
            st.warning("Log file encoding error. functionality limited.")