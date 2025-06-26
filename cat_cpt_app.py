import streamlit as st
import requests
from PIL import Image
from langdetect import detect
from deep_translator import GoogleTranslator
import tempfile
import os
import fitz  # PyMuPDF
import docx2txt
from gtts import gTTS

# Hugging Face API ayarları
API_URL = "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"

def translate_to_en(text):
    try:
        detected = detect(text)
    except:
        detected = "en"
    if detected != "en":
        try:
            return GoogleTranslator(source='auto', target='en').translate(text)
        except:
            return text
    return text

def translate_from_en(text, target_lang):
    if target_lang != "en":
        try:
            return GoogleTranslator(source='en', target=target_lang).translate(text)
        except:
            return text
    return text

def query_huggingface(payload, api_key):
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.post(API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()[0]["generated_text"]
    else:
        return f"❗ API Hatası: {response.status_code} - {response.text}"

def process_file(file):
    ext = file.name.split('.')[-1].lower()
    text = ""
    if ext in ["txt"]:
        text = file.getvalue().decode("utf-8")
    elif ext in ["pdf"]:
        try:
            doc = fitz.open(stream=file.read(), filetype="pdf")
            for page in doc:
                text += page.get_text()
        except:
            text = "[PDF dosyası okunamadı]"
    elif ext in ["doc", "docx"]:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
                tmp.write(file.read())
                tmp.flush()
                text = docx2txt.process(tmp.name)
                os.unlink(tmp.name)
        except:
            text = "[DOCX dosyası okunamadı]"
    else:
        text = "[Desteklenmeyen dosya türü]"
    return text

st.set_page_config(page_title="Cat CPT", layout="wide")
st.title("😺 Cat CPT - Kedi Yapay Zekası")

st.sidebar.title("🔐 Hugging Face API Key Girişi")
api_key = st.sidebar.text_input("Hugging Face API Anahtarınızı girin:", type="password")
if not api_key:
    st.sidebar.warning("Devam etmek için API anahtarınızı girin.")
    st.stop()

st.sidebar.title("🐾 Kedi Irkı Seçimi")
breeds = ["British Shorthair", "Van Kedisi", "Sfenks", "Scottish Fold", "Maine Coon", "Sokak Kedisi"]
selected_breed = st.sidebar.selectbox("Hangi kedi ırkını temsil ediyorsun?", breeds)

roleplay_mode = st.sidebar.checkbox("🎮 Rol yapma modu (hikaye anlatımı)")

user_input = st.text_area("Sorunuzu yazın:", height=100)

uploaded_file = st.file_uploader("📎 Dosya yükleyin (PDF, DOCX, TXT)", type=['pdf', 'docx', 'txt'])
file_text = ""
if uploaded_file:
    file_text = process_file(uploaded_file)
    if file_text and "Desteklenmeyen" not in file_text:
        st.info(f"Dosya içeriği başarıyla okundu. Uzunluk: {len(file_text)} karakter.")
    else:
        st.warning(file_text)

if st.button("Gönder"):
    if not user_input and not file_text:
        st.warning("Lütfen bir soru yazın veya dosya yükleyin.")
    else:
        user_input_en = translate_to_en(user_input) if user_input else ""
        file_text_en = translate_to_en(file_text) if file_text else ""

        personality_texts = {
            "British Shorthair": "Sen British Shorthair cinsi bir kedisin. Soğukkanlı, akıllı ve biraz mesafeli şekilde konuşursun.",
            "Van Kedisi": "Sen Van Kedisi cinsi bir kedisin. Meraklı, enerjik ve neşeli bir tavırla konuşursun.",
            "Sfenks": "Sen Sfenks cinsi bir kedisin. Zarif, entelektüel ve sofistike bir konuşma tarzın vardır.",
            "Scottish Fold": "Sen Scottish Fold cinsi bir kedisin. Sessiz, sevimli ve düşünceli şekilde konuşursun.",
            "Maine Coon": "Sen Maine Coon cinsi bir kedisin. Bilge, koruyucu ve arkadaş canlısı bir tavrın vardır.",
            "Sokak Kedisi": "Sen sokak kedisisin. Alaycı ama içten, samimi ve zeki konuşursun."
        }

        breed_prompt = personality_texts.get(selected_breed, "Sen bir kedi gibi konuşmalısın.")
        source_instruction = " Verdiğin bilgilerin sonunda mümkünse hangi kaynağa dayandığını da belirt. Güvenilir, gerçek bilgilere dayandır."
        roleplay_instruction = " Kullanıcının verdiği hikayeyi bir kedi karakteri olarak maceralı ve yaratıcı şekilde anlatmaya devam et."

        prompt = f"{breed_prompt}{source_instruction}"
        if roleplay_mode:
            prompt += roleplay_instruction
        if user_input_en:
            prompt += f"\nKullanıcının sorusu: {user_input_en}"
        if file_text_en:
            prompt += f"\nYüklü dosya içeriği: {file_text_en}"

        response_en = query_huggingface({"inputs": prompt}, api_key)
        final_lang = detect(user_input) if user_input else "tr"
        response = translate_from_en(response_en, final_lang)
        st.markdown(f"**😺 Cat CPT Cevabı ({selected_breed}):**\n\n{response}")

        if st.button("🔊 Sesli Yanıtla"):
            try:
                tts = gTTS(text=response, lang=final_lang)
                tts.save("catcpt_audio.mp3")
                audio_file = open("catcpt_audio.mp3", "rb")
                audio_bytes = audio_file.read()
                st.audio(audio_bytes, format='audio/mp3')
            except Exception as e:
                st.error(f"Sesli yanıt oluşturulamadı: {e}")
