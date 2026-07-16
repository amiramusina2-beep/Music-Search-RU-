import streamlit as st
import json
import os
import yt_dlp

# Настройка страницы
st.set_page_config(page_title="Музыкальный плеер", layout="centered", page_icon="🎵")

# CSS для крупных шрифтов и стилизации кнопок под пальцы
st.markdown("""
<style>
    /* Увеличенный шрифт для удобства родителей */
    html, body, [class*="css"] {
        font-size: 16px !important;
    }
    
    /* Стилизация кнопок под пальцы (высота не менее 45px) */
    div.stButton > button {
        border-radius: 12px !important;
        font-size: 15px !important;
        font-weight: bold !important;
        min-height: 45px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        margin-top: 5px !important;
        margin-bottom: 5px !important;
    }
    
    /* Шрифт для вкладок */
    button[data-baseweb="tab"] {
        font-size: 17px !important;
        font-weight: bold !important;
    }
    
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }
</style>
""", unsafe_allow_html=True)

FAVORITES_FILE = "favorites.json"

# Загрузка избранного
def load_favorites():
    if os.path.exists(FAVORITES_FILE):
        try:
            with open(FAVORITES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

# Сохранение избранного
def save_favorites(favs):
    with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
        json.dump(favs, f, ensure_ascii=False, indent=4)

# Инициализация состояния
if "favorites" not in st.session_state:
    st.session_state.favorites = load_favorites()

if "current_track" not in st.session_state:
    st.session_state.current_track = None

if "current_audio_url" not in st.session_state:
    st.session_state.current_audio_url = None

# Функция поиска на YouTube
@st.cache_data(ttl=600)
def search_youtube(query, limit=10):
    ydl_opts = {
        'default_search': 'ytsearch',
        'max_results': limit,
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
            tracks = []
            if 'entries' in info:
                for entry in info['entries']:
                    video_id = entry.get('id')
                    if video_id:
                        title = entry.get('title', 'Без названия')
                        artist = entry.get('uploader', 'Исполнитель')
                        url = f"https://www.youtube.com/watch?v={video_id}"
                        image_url = f"https://img.youtube.com/vi/{video_id}/0.jpg"
                        tracks.append({
                            "id": video_id,
                            "title": title,
                            "artist": artist,
                            "url": url,
                            "image": image_url
                        })
            return tracks
    except Exception as e:
        st.error(f"Ошибка поиска: {e}")
        return []

# Получение аудиопотока
def get_audio_stream_url(video_id):
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
    }
    url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('url')
    except Exception:
        return None

# Генерация поискового запроса для рекомендаций 2026 года
def get_recommendation_query(lang, category):
    lang_term = {
        "Русский": "русские хиты 2026 новые песни новинки чарт",
        "Английский": "english billboard hits 2026 new songs",
        "Испанский": "top canciones españolas exitos 2026",
        "Французский": "top chansons françaises nouveautés 2026"
    }.get(lang, "songs 2026")
    
    cat_term = {
        "Популярные": "свежий чарт топ музыка" if lang == "Русский" else "top trends music",
        "Новые": "самые новые премьеры релизы этого месяца" if lang == "Русский" else "brand new releases latest",
        "Старые": "ретро ностальгия старые золотые хиты" if lang == "Русский" else "old school classics retro gold"
    }.get(category, "trends")
    
    return f"{cat_term} {lang_term}"

# --- ИНТЕРФЕЙС ПРИЛОЖЕНИЯ ---

st.title("🎵 Мобильный MP3 Плеер")

# 1. ПОИСК НАВЕРХУ
st.write("### 🔍 Поиск песни")
search_input = st.text_input(
    "Введите название песни или исполнителя и нажмите Enter", 
    placeholder="Например: MACAN, Любэ, Кино...", 
    key="search_bar",
    label_visibility="collapsed"
)

# 2. АУДИОПЛЕЕР (Отображается сверху при воспроизведении)
if st.session_state.current_track and st.session_state.current_audio_url:
    st.write("---")
    track = st.session_state.current_track
    audio_url = st.session_state.current_audio_url
    
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 15px; background-color: #1e1e1e; padding: 15px; border-radius: 15px; border-left: 5px solid #1DB954; box-shadow: 0 4px 10px rgba(0,0,0,0.3);">
        <img src="{track["image"]}" style="width: 70px; height: 70px; border-radius: 10px; object-fit: cover;">
        <div>
            <div style="font-size: 13px; font-weight: bold; color: #1DB954; text-transform: uppercase;">Сейчас играет:</div>
            <div style="font-size: 17px; font-weight: bold; color: white; margin-top: 2px;">{track['title']}</div>
            <div style="font-size: 14px; color: #b3b3b3;">{track['artist']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.audio(audio_url, format="audio/mp3", autoplay=True)
    st.write("---")

# 3. НАСТРОЙКИ РЕКОМЕНДАЦИЙ
st.write("### ⚙️ Настройки музыки")
col_lang, col_cat = st.columns(2)
with col_lang:
    selected_lang = st.selectbox("Язык песен:", ["Русский", "Английский", "Испанский", "Французский"], index=0)
with col_cat:
    selected_cat = st.selectbox("Категория:", ["Популярные", "Новые", "Старые"], index=0)

recs_query = get_recommendation_query(selected_lang, selected_cat)

# Вкладки плеера
tab_main, tab_favs = st.tabs(["✨ Главная (Рекомендации)", "⭐ Моё Избранное"])

# Функция вывода списка треков
def render_song_list(songs, unique_suffix):
    for song in songs:
        # Карточка трека с фиксированным темным фоном для идеальной видимости текста в любой теме
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 15px; margin-top: 15px; margin-bottom: 8px; background-color: #1c1c1e; padding: 12px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.25);">
            <img src="{song["image"]}" style="width: 60px; height: 60px; border-radius: 8px; object-fit: cover;">
            <div>
                <div style="font-weight: bold; font-size: 15px; color: #FFFFFF; line-height: 1.3;">{song['title']}</div>
                <div style="font-size: 13px; color: #A4A4A4; margin-top: 4px;">{song['artist']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Кнопки действия строкой ниже
        col_btn_play, col_btn_fav = st.columns(2)
        
        with col_btn_play:
            if st.button("▶ Воспроизвести", key=f"play_{unique_suffix}_{song['id']}", use_container_width=True):
                with st.spinner("Загрузка..."):
                    stream_url = get_audio_stream_url(song['id'])
                    if stream_url:
                        st.session_state.current_track = song
                        st.session_state.current_audio_url = stream_url
                        st.rerun()
                    else:
                        st.error("Ошибка!")
                        
        with col_btn_fav:
            is_fav = any(f["id"] == song["id"] for f in st.session_state.favorites)
            btn_label = "❤️ Убрать" if is_fav else "🖤 В избранное"
            if st.button(btn_label, key=f"fav_{unique_suffix}_{song['id']}", use_container_width=True):
                if is_fav:
                    st.session_state.favorites = [f for f in st.session_state.favorites if f["id"] != song["id"]]
                else:
                    st.session_state.favorites.append(song)
                save_favorites(st.session_state.favorites)
                st.rerun()
        st.write(" ") # Небольшой отступ между треками

with tab_main:
    # Результаты ручного поиска
    if search_input:
        st.subheader(f"🔍 Найдено по запросу «{search_input}»")
        with st.spinner("Поиск треков..."):
            search_results = search_youtube(search_input, limit=6)
        
        if not search_results:
            st.warning("Ничего не найдено.")
        else:
            render_song_list(search_results, "search")
            st.write("---")

    # Секция рекомендаций
    st.subheader(f"🔥 Рекомендации")
    with st.spinner("Загрузка рекомендаций..."):
        recs_results = search_youtube(recs_query, limit=10)
        
    if not recs_results:
        st.info("Не удалось загрузить рекомендации.")
    else:
        render_song_list(recs_results, "rec")

with tab_favs:
    st.subheader("⭐ Избранное")
    if not st.session_state.favorites:
        st.info("Вы еще не добавили ни одного трека в избранное.")
    else:
        render_song_list(st.session_state.favorites, "fav_tab")
