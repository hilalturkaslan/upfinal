import streamlit as st
import ffmpeg
import tempfile
import os
import requests
import speech_recognition as sr

LIBRETRANSLATE_URL = 'https://libretranslate.de/translate'


st.set_page_config(
    page_title="EchoTranslate: From Video Echoes to Global Voices",
    page_icon=":movie_camera:",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
        .main {
            background: radial-gradient(circle at center, #004080, #0056a0, #007acc);
            color: white; 
        }
        .sidebar .sidebar-content {
            background-color: #0d1a3d; 
        }
        .css-18e3f0h {
            background-color: #1e3a6e; 
        }
        h1 {
            font-size: 3em;
            text-align: center;
            margin-top: 50px;
            color: #ffffff; 
            text-shadow: 0 0 15px rgba(255, 255, 255, 0.8); 
        }
    </style>
""", unsafe_allow_html=True)

st.title("EchoTranslate: From Video Echoes to Global Voices")
st.write("""
Bu uygulama, video dosyanızı ses dosyasına dönüştürür, metne çevirir ve seçtiğiniz dillere tercüme eder. Tüm sonuçlar indirilebilir dosyalar olarak sunulur.
""")

uploaded_file = st.file_uploader("Bir video dosyası yükleyin", type=["mp4", "mov", "avi"])

languages = st.multiselect(
    "Metni çevirmek istediğiniz dilleri seçin",
    ["en", "fr", "de", "es", "it", "pt"],
    ["en"]
)

if st.button("İşlemi Başlat"):
    if uploaded_file is not None and languages:
        with st.spinner('İşlem yapılıyor...'):
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
                    audio_path = temp_audio_file.name
                    convert_video_to_audio(uploaded_file, audio_path)

                transcription = transcribe_audio(audio_path)
                st.write("Transkript:")
                st.write(transcription)

                translations = translate_text(transcription, languages)

                st.write("Çeviriler:")
                for lang, text in translations.items():
                    st.write(f"{lang}: {text}")

                    srt_file = generate_srt_file(text, lang)
                    st.download_button(f"{lang} Çevirisini İndir (.srt)", data=open(srt_file, "r").read(), file_name=f"translation_{lang}.srt")

                os.remove(audio_path)
                for lang in translations.keys():
                    os.remove(f"translation_{lang}.srt")
            except Exception as e:
                st.error(f"Bir hata oluştu: {e}")
    else:
        st.error("Lütfen bir video dosyası yükleyin ve en az bir dil seçin.")

    st.write("Geri bildirim bırakın:")
    feedback = st.text_area("Geri bildiriminiz:")
    if st.button("Geri Bildirimi Gönder"):
        if feedback:
            st.write("Geri bildiriminiz alındı, teşekkür ederiz!")
        else:
            st.warning("Lütfen geri bildirim girin.")

def convert_video_to_audio(video_file, audio_path):
    ffmpeg.input(video_file).output(audio_path).run()

def transcribe_audio(audio_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio_data = recognizer.record(source)
    try:
        text = recognizer.recognize_google(audio_data)
    except sr.UnknownValueError:
        text = "Ses tanınamadı"
    except sr.RequestError as e:
        text = f"Bir hata oluştu: {e}"
    return text

def translate_text(text, target_languages):
    translations = {}
    for lang in target_languages:
        response = requests.post(LIBRETRANSLATE_URL, data={
            'q': text,
            'source': 'en',
            'target': lang
        })
        if response.status_code == 200:
            result = response.json()
            translations[lang] = result['translatedText']
        else:
            translations[lang] = "Çeviri hatası"
    return translations

def generate_srt_file(text, lang):
    srt_path = f"translation_{lang}.srt"
    with open(srt_path, "w") as srt_file:
        lines = text.split('\n')
        for i, line in enumerate(lines):
            srt_file.write(f"{i+1}\n")
            srt_file.write(f"00:00:00,000 --> 00:00:10,000\n")  
            srt_file.write(f"{line}\n\n")
    return srt_path

