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
import re

# Anahtar kelime çıkarımı için
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
nltk.download('punkt')
nltk.download('stopwords')

stop_words = set(stopwords.words('turkish'))

def extract_keywords(text):
    words = word_tokenize(text.lower())
    keywords = [word for word in words if word.isalpha() and word not in stop_words]
    return ' '.join(keywords)

API_URL = "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"

def translate_to_en(text):
    text = text.strip()
    if len(text.split()) <= 2:
        return text
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
    text = text.strip()
    if len(text.split()) <= 2 or target_lang == "en":
        return text
    try:
        return GoogleTranslator(source='en', target=target_lang).translate(text)
    except:
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

st.set_page_config(page_title="Cat CPT - Kedi Yapay Zekası", layout="wide")
st.title("😺 Cat CPT - Kedi Yapay Zekası")

st.sidebar.title("🔐 Hugging Face API Key Girişi")
api_key = st.sidebar.text_input("Hugging Face API Anahtarınızı girin:", type="password")
if not api_key:
    st.sidebar.warning("Devam etmek için API anahtarınızı girin.")
    st.stop()

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
        user_input_en = translate_to_en(extract_keywords(user_input)) if user_input else ""
        file_text_en = translate_to_en(extract_keywords(file_text)) if file_text else ""

        prompt = ""
        if len(user_input_en.strip()) > 10:
            prompt += "Verdiğin bilgilerin sonunda mümkünse hangi kaynağa dayandığını da belirt. Güvenilir, gerçek bilgilere dayandır."
        if user_input_en:
            prompt += f"\n\nKullanıcının sorusu (anahtar kelimeler): {user_input_en}\n"
        if file_text_en:
            prompt += f"Yüklü dosya içeriği (anahtar kelimeler): {file_text_en}"

        response_en = query_huggingface({"inputs": prompt}, api_key)

        try:
            final_lang = detect(user_input) if user_input else "tr"
        except:
            final_lang = "tr"

        response = translate_from_en(response_en, final_lang)
        st.markdown(f"**😺 Cat CPT Cevabı:**\n\n{response}")

        if st.button("🔊 Sesli Oku"):
            try:
                tts = gTTS(text=response, lang=final_lang)
                audio_path = "catcpt_response.mp3"
                tts.save(audio_path)
                audio_file = open(audio_path, "rb")
                audio_bytes = audio_file.read()
                st.audio(audio_bytes, format='audio/mp3')
            except Exception as e:
                st.error(f"Ses oluşturulamadı: {e}")
