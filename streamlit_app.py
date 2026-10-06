import json
import re
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Minhas Músicas", page_icon="🎵", layout="centered")

BASE = Path(__file__).parent


# ---------- Configuração (vem do st.secrets, nunca fica no código) ----------
def get_secret(key, default=""):
    try:
        return st.secrets[key]
    except Exception:
        return default


INSTAGRAM_USER = get_secret("INSTAGRAM_USER", "seu_usuario")
DOWNLOAD_URL = get_secret("DROPBOX_DOWNLOAD_URL", "")  # link da pasta/zip no Dropbox
TRACKS = get_secret("TRACKS", [])  # lista de {"title": "...", "url": "..."}


def to_stream_url(url: str) -> str:
    """Converte link compartilhado do Dropbox em link direto para tocar."""
    url = url.replace("www.dropbox.com", "dl.dropboxusercontent.com")
    url = re.sub(r"[?&]dl=\d", "", url)
    return url + ("&" if "?" in url else "?") + "raw=1"


def normalize(name: str) -> str:
    return name.strip().lstrip("@").lower()


@st.cache_data(show_spinner=False)
def load_followers() -> set:
    """Lê followers.txt (um usuário por linha) e/ou followers_*.json exportado do Instagram."""
    users = set()
    txt = BASE / "followers.txt"
    if txt.exists():
        for line in txt.read_text(encoding="utf-8").splitlines():
            if line.strip() and not line.startswith("#"):
                users.add(normalize(line))
    for f in BASE.glob("followers_*.json"):
        data = json.loads(f.read_text(encoding="utf-8"))
        if isinstance(data, dict):  # alguns exports vêm dentro de uma chave
            data = next(iter(data.values()))
        for item in data:
            for entry in item.get("string_list_data", []):
                if entry.get("value"):
                    users.add(normalize(entry["value"]))
    return users


# ---------- Página ----------
st.title("🎵 Minhas Músicas")
st.write("Ouça à vontade. Para **baixar**, é só me seguir no Instagram.")

st.subheader("▶️ Ouvir")
if not TRACKS:
    st.info("Adicione suas faixas em `TRACKS` no secrets.toml.")
for t in TRACKS:
    st.markdown(f"**{t['title']}**")
    st.audio(to_stream_url(t["url"]))

st.divider()
st.subheader("⬇️ Baixar")

if "verified" not in st.session_state:
    st.session_state.verified = False

if not st.session_state.verified:
    st.markdown(
        f"1. Siga [@{INSTAGRAM_USER}](https://instagram.com/{INSTAGRAM_USER}) no Instagram\n"
        "2. Digite seu usuário abaixo e clique em verificar"
    )
    with st.form("verificacao"):
        user = st.text_input("Seu usuário do Instagram", placeholder="@seuusuario")
        ok = st.form_submit_button("Verificar")
    if ok:
        if normalize(user) and normalize(user) in load_followers():
            st.session_state.verified = True
            st.rerun()
        else:
            st.error(
                "Não encontrei esse usuário entre os seguidores. "
                "Confira se digitou certo e se já me segue. "
                "A lista é atualizada periodicamente, então pode levar um tempo."
            )

if st.session_state.verified:
    st.success("Verificado! Obrigado por seguir 💛")
    st.link_button("Baixar músicas (Dropbox)", DOWNLOAD_URL, type="primary")
