import streamlit as st
import json
import os
import yt_dlp

# Настройка страницы
st.set_page_config(page_title="MP3 Плеер", layout="centered", page_icon="🎵")

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

# Функция для быстрого поиска метаданных
@st.cache_data(ttl=600)
def search_youtube(query, limit=10):
    ydl_opts = {
        'default_search': 'ytsearch',
        'max_results': limit,
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,  # Быстрый сбор данных без загрузки тяжелых потоков
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

# Функция для извлечения прямой ссылки на аудиопоток (MP3/M4A)
def get_audio_stream_url(video_id):
    ydl_opts = {
        'format': 'bestaudio/best',  # Извлекаем только аудио самого лучшего качества
        'quiet': True,
        'no_warnings': True,
    }
    url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('url')  # Это прямая ссылка на аудиофайл на сервере
    except Exception:
        return None

# Генерация поискового запроса для рекомендаций (фокус на свежих чартах 2026 года)
def get_recommendation_query(lang, category):
    lang_term = {
        "Русский": "русские хиты 2026 новые песни новинки",
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

st.title("🎵 MP3 Музыкальный плеер")

# 1. ПОИСК НАВЕРХУ
st.write("### 🔍 Поиск музыки")
search_input = st.text_input(
    "Введите название песни или исполнителя и нажмите Enter", 
    placeholder="Например: Асфальт 8, MACAN, Coldplay...", 
    key="search_bar"
)

# 2. АУДИОПЛЕЕР (Отображается, когда трек запущен)
if st.session_state.current_track and st.session_state.current_audio_url:
    st.write("---")
    track = st.session_state.current_track
    audio_url = st.session_state.current_audio_url
    
    col_img, col_text = st.columns([1, 4])
    with col_img:
        st.image(track["image"], width=80)
    with col_text:
        st.markdown(f"#### **{track['title']}**")
        st.text(f"Исполнитель: {track['artist']}")
    
    # Чистый аудиоплеер без видеоплеера YouTube
    st.audio(audio_url, format="audio/mp3", autoplay=True)
    st.write("---")

# 3. НАСТРОЙКИ РЕКОМЕНДАЦИЙ
st.write("### ⚙️ Настройки рекомендаций")
col_lang, col_cat = st.columns(2)
with col_lang:
    selected_lang = st.selectbox("Выбрать язык", ["Русский", "Английский", "Испанский", "Французский"], index=0)
with col_cat:
    selected_cat = st.selectbox("Выбрать категорию", ["Популярные", "Новые", "Старые"], index=0)

# Автоматический запрос на основе настроек
recs_query = get_recommendation_query(selected_lang, selected_cat)

# Вкладки
tab_main, tab_favs = st.tabs(["✨ Главная", "⭐ Моё Избранное"])

with tab_main:
    # Вывод результатов поиска
    if search_input:
        st.subheader(f"🔍 Результаты поиска для: «{search_input}»")
        with st.spinner("Ищем треки..."):
            search_results = search_youtube(search_input, limit=6)
        
        if not search_results:
            st.warning("Ничего не найдено.")
        else:
            for song in search_results:
                col_img, col_info, col_play, col_fav = st.columns([1, 4, 1.5, 1.5])
                with col_img:
                    st.image(song["image"], width=60)
                with col_info:
                    st.markdown(f"**{song['title']}**  \n*{song['artist']}*")
                with col_play:
                    if st.button("▶ Слушать", key=f"search_play_{song['id']}", use_container_width=True):
                        with st.spinner("Получение аудиопотока..."):
                            stream_url = get_audio_stream_url(song['id'])
                            if stream_url:
                                st.session_state.current_track = song
                                st.session_state.current_audio_url = stream_url
                                st.rerun()
                            else:
                                st.error("Не удалось запустить этот трек.")
                with col_fav:
                    is_fav = any(f["id"] == song["id"] for f in st.session_state.favorites)
                    btn_label = "❤️ Убрать" if is_fav else "🖤 В избранное"
                    if st.button(btn_label, key=f"search_fav_{song['id']}", use_container_width=True):
                        if is_fav:
                            st.session_state.favorites = [f for f in st.session_state.favorites if f["id"] != song["id"]]
                        else:
                            st.session_state.favorites.append(song)
                        save_favorites(st.session_state.favorites)
                        st.rerun()
            st.write("---")

    # Секция рекомендаций
    st.subheader(f"🔥 Рекомендации ({selected_lang} / {selected_cat})")
    with st.spinner("Загрузка свежих рекомендаций..."):
        recs_results = search_youtube(recs_query, limit=10)
        
    if not recs_results:
        st.info("Не удалось загрузить рекомендации.")
    else:
        for song in recs_results:
            col_img, col_info, col_play, col_fav = st.columns([1, 4, 1.5, 1.5])
            with col_img:
                st.image(song["image"], width=60)
            with col_info:
                st.markdown(f"**{song['title']}**  \n*{song['artist']}*")
            with col_play:
                if st.button("▶ Слушать", key=f"rec_play_{song['id']}", use_container_width=True):
                    with st.spinner("Получение аудиопотока..."):
                        stream_url = get_audio_stream_url(song['id'])
                        if stream_url:
                            st.session_state.current_track = song
                            st.session_state.current_audio_url = stream_url
                            st.rerun()
                        else:
                            st.error("Не удалось запустить этот трек.")
            with col_fav:
                is_fav = any(f["id"] == song["id"] for f in st.session_state.favorites)
                btn_label = "❤️ Убрать" if is_fav else "🖤 В избранное"
                if st.button(btn_label, key=f"rec_fav_{song['id']}", use_container_width=True):
                    if is_fav:
                        st.session_state.favorites = [f for f in st.session_state.favorites if f["id"] != song["id"]]
                    else:
                        st.session_state.favorites.append(song)
                    save_favorites(st.session_state.favorites)
                    st.rerun()

with tab_favs:
    st.subheader("⭐ Избранное")
    if not st.session_state.favorites:
        st.info("Вы еще не добавили ни одного трека в избранное.")
    else:
        for song in st.session_state.favorites:
            col_img, col_info, col_play, col_fav = st.columns([1, 4, 1.5, 1.5])
            with col_img:
                st.image(song["image"], width=60)
            with col_info:
                st.markdown(f"**{song['title']}**  \n*{song['artist']}*")
            with col_play:
                if st.button("▶ Слушать", key=f"fav_play_{song['id']}", use_container_width=True):
                    with st.spinner("Получение аудиопотока..."):
                        stream_url = get_audio_stream_url(song['id'])
                        if stream_url:
                            st.session_state.current_track = song
                            st.session_state.current_audio_url = stream_url
                            st.rerun()
                        else:
                            st.error("Не удалось запустить этот трек.")
            with col_fav:
                if st.button("❌ Удалить", key=f"fav_del_{song['id']}", use_container_width=True):
                    st.session_state.favorites = [f for f in st.session_state.favorites if f["id"] != song["id"]]
                    save_favorites(st.session_state.favorites)
                    st.rerun()