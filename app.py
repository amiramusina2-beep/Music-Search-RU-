import streamlit as st
import json
import os
import yt_dlp

# Настройка страницы (используем centered layout, чтобы на ПК приложение выглядело как аккуратный мобильный плеер)
st.set_page_config(page_title="Музыкальный плеер", layout="centered", page_icon="🎵")

# Внедряем CSS стили для адаптивности, крупных шрифтов и удобных кнопок
st.markdown("""
<style>
    /* Увеличенный шрифт для лучшей читаемости */
    html, body, [class*="css"] {
        font-size: 16px !important;
    }
    
    /* Делаем кнопки крупными (не менее 44px в высоту), чтобы по ним было удобно кликать пальцем */
    div.stButton > button {
        border-radius: 12px !important;
        font-size: 15px !important;
        font-weight: bold !important;
        min-height: 45px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        margin-bottom: 5px !important;
    }
    
    /* Крупный и четкий текст для вкладок */
    button[data-baseweb="tab"] {
        font-size: 17px !important;
        font-weight: bold !important;
    }
    
    /* Убираем лишние отступы, чтобы на экранах телефонов помещалось больше информации */
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

# Функция поиска на YouTube через yt-dlp
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
    placeholder="Например: MACAN, Любэ, Coldplay...", 
    key="search_bar",
    label_visibility="collapsed"
)

# 2. АУДИОПЛЕЕР (Отображается, когда запущен трек)
if st.session_state.current_track and st.session_state.current_audio_url:
    st.write("---")
    track = st.session_state.current_track
    audio_url = st.session_state.current_audio_url
    
    # Красивое отображение играющего трека
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 15px; background-color: #1e1e1e; padding: 15px; border-radius: 15px;">
        <img src="{track["image"]}" style="width: 70px; height: 70px; border-radius: 10px; object-fit: cover;">
        <div>
            <div style="font-size: 18px; font-weight: bold; color: #1DB954;">Сейчас играет:</div>
            <div style="font-size: 16px; font-weight: bold; color: white;">{track['title']}</div>
            <div style="font-size: 14px; color: #b3b3b3;">{track['artist']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Чистый аудиоплеер
    st.audio(audio_url, format="audio/mp3", autoplay=True)
    st.write("---")

# 3. НАСТРОЙКИ РЕКОМЕНДАЦИЙ (Выбор языка и категории)
st.write("### ⚙️ Настройки музыки")
col_lang, col_cat = st.columns(2)
with col_lang:
    selected_lang = st.selectbox("Язык песен:", ["Русский", "Английский", "Испанский", "Французский"], index=0)
with col_cat:
    selected_cat = st.selectbox("Категория:", ["Популярные", "Новые", "Старые"], index=0)

recs_query = get_recommendation_query(selected_lang, selected_cat)

# Вкладки плеера
tab_main, tab_favs = st.tabs(["✨ Главная (Рекомендации)", "⭐ Моё Избранное"])

# Функция для вывода списка треков (адаптированная под мобильный и ПК)
def render_song_list(songs, unique_suffix):
    for song in songs:
        # 3 колонки: [Контент (картинка + текст), Кнопка играть, Кнопка избранного]
        # Соотношение 4:1.2:1.2 отлично помещается на экранах любых смартфонов
        col_content, col_play, col_fav = st.columns([4, 1.2, 1.2])
        
        with col_content:
            # HTML-карточка песни: картинка и текст в одной строке
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px; height: 50px;">
                <img src="{song["image"]}" style="width: 50px; height: 50px; border-radius: 8px; object-fit: cover;">
                <div style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                    <div style="font-weight: bold; font-size: 15px; color: #FFFFFF; overflow: hidden; text-overflow: ellipsis; max-width: 250px;">{song['title']}</div>
                    <div style="font-size: 13px; color: #B3B3B3; overflow: hidden; text-overflow: ellipsis; max-width: 250px;">{song['artist']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with col_play:
            if st.button("▶", key=f"play_{unique_suffix}_{song['id']}", use_container_width=True):
                with st.spinner("Загрузка..."):
                    stream_url = get_audio_stream_url(song['id'])
                    if stream_url:
                        st.session_state.current_track = song
                        st.session_state.current_audio_url = stream_url
                        st.rerun()
                    else:
                        st.error("Ошибка!")
                        
        with col_fav:
            is_fav = any(f["id"] == song["id"] for f in st.session_state.favorites)
            btn_label = "❤️" if is_fav else "🤍"
            if st.button(btn_label, key=f"fav_{unique_suffix}_{song['id']}", use_container_width=True):
                if is_fav:
                    st.session_state.favorites = [f for f in st.session_state.favorites if f["id"] != song["id"]]
                else:
                    st.session_state.favorites.append(song)
                save_favorites(st.session_state.favorites)
                st.rerun()

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
