import streamlit as st
import requests
import re
from pydantic import BaseModel

# ——— Perplexica endpoints
PERPLEXICA_BASE = "http://localhost:3000/api"
ENDPOINTS = {
    "web":    f"{PERPLEXICA_BASE}/search",
    "images": f"{PERPLEXICA_BASE}/images",
    "videos": f"{PERPLEXICA_BASE}/videos",
}

# ——— Pydantic-style request model
class SearchRequest(BaseModel):
    query: str
    mode: str

# ——— Helper to call Perplexica
@st.cache_data(ttl=300)
def search_perplexica(query: str, mode: str):
    url = ENDPOINTS.get(mode)
    if not url:
        raise ValueError(f"Unknown mode: {mode}")

    payload = {"query": query}
    if mode == "web":
        payload.update({"focusMode": "webSearch", "optimizationMode": "speed"})
    else:
        # adjust if necessary for images/videos
        payload.update({
            "chatModel": {"provider": "gemini", "model": "gemini-2.5-flash-preview-05-20"},
            "chatHistory": []
        })

    resp = requests.post(url, json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()

# ——— Streamlit UI
st.set_page_config(page_title="🔍 Perplexica All‑in‑One", layout="wide")
st.title("🔍 Perplexica Search")

query = st.text_input("Enter your query…")
search_button = st.button("Search")

tab_web, tab_images, tab_videos = st.tabs(["🌐 Web", "🖼️ Images", "▶️ Videos"])

def extract_youtube_id(url: str) -> str | None:
    for p in (r"youtu\.be/([^?&]+)", r"youtube\.com/watch\?v=([^?&]+)"):
        m = re.search(p, url)
        if m: return m.group(1)
    return None

if search_button and query:
    with st.spinner("Searching Web…"):
        try:
            web_result = search_perplexica(query, "web")
        except Exception as e:
            st.error(f"Web search failed: {e}")
            web_result = None
    with st.spinner("Searching Images…"):
        try:
            imgs = search_perplexica(query, "images").get("images", [])
        except:
            imgs = []
    with st.spinner("Searching Videos…"):
        try:
            vids = search_perplexica(query, "videos").get("videos", [])
        except:
            vids = []

    # — Web Tab
    with tab_web:
        if web_result:
            st.markdown("### Web Search Result")
            for p in web_result.get("message", "").split("\n\n"):
                st.markdown(f"> {p}")

            st.markdown("---### Sources")
            for i, src in enumerate(web_result.get("sources", []), start=1):
                meta = src.get("metadata", {})
                title, url = meta.get("title"), meta.get("url")
                snippet = src.get("pageContent", "")
                with st.expander(f"{i}. {title}"):
                    cols = st.columns([1, 4])
                    with cols[0]:
                        yt = extract_youtube_id(url)
                        if yt:
                            st.image(f"https://img.youtube.com/vi/{yt}/hqdefault.jpg", use_container_width=True)
                    with cols[1]:
                        st.markdown(f"[🔗 Source]({url})")
                        st.markdown(f"> {snippet}")
        else:
            st.info("No web results.")

    # — Images Tab
    with tab_images:
        st.markdown("### Image Search Results")
        if imgs:
            cols = st.columns(4)
            for idx, img in enumerate(imgs):
                with cols[idx % 4]:
                    st.image(img["img_src"], caption=img["title"], use_container_width=True)
                    st.markdown(f"[🔗 Source]({img['url']})")
        else:
            st.info("No images found.")

    # — Videos Tab
    with tab_videos:
        st.markdown("### Video Search Results")
        if vids:
            cols = st.columns(3)
            for idx, vid in enumerate(vids):
                with cols[idx % 3]:
                    st.image(vid["img_src"], use_container_width=True)
                    st.markdown(f"**[{vid['title']}]({vid['url']})**")
                    with st.expander("▶️ Play"):
                        iframe = vid.get("iframe_src")
                        if iframe:
                            st.components.v1.html(
                                f'<iframe width="100%" height="200" src="{iframe}" '
                                'frameborder="0" allow="accelerometer; autoplay; '
                                'clipboard-write; encrypted-media; gyroscope; picture-in-picture" '
                                'allowfullscreen></iframe>',
                                height=220)
                        else:
                            st.video(vid["url"])
        else:
            st.info("No videos found.")
else:
    for tab in (tab_web, tab_images, tab_videos):
        with tab:
            st.info("Enter a query above and click **Search**.")
