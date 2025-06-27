import streamlit as st import requests from PIL import Image from langdetect import detect from deep_translator import GoogleTranslator import tempfile import os import fitz  # PyMuPDF import docx2txt from gtts import gTTS

🔽 Gerekli NLTK verisi indir

import nltk nltk.download("punkt")

from nltk.tokenize import word_tokenize

Hugging Face API ayarları

API_URL = "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"

Dil çeviri fonksiyonları

def translate_to_en(text): try: detected = detect(text) except: detected = "en" if detected != "en": try: return GoogleTranslator(source='auto', target='en').translate(text) except: return text return text

def translate_from_en(text, target_lang): if target_lang != "en": try: return GoogleTranslator(source='en', target=target_lang).translate(text) except: return text return text

Anahtar kelime çıkarımı (otomatik kaynaklandırma için)

def extract_keywords(text): words = word_tokenize(text.lower()) keywords = [w for w in words if w.isalnum() and len(w) > 3] return " ".join(keywords[:5])

Hugging Face API üzerinden yanıt al

def query_huggingface(payload, api_key): headers = {"Authorization": f"Bearer {api_key}"} response = requests.post(API_URL, headers=headers, json=payload) if response.status_code == 200: return response.json()[0]["generated_text"] else: return f"❗ API Hatası: {response.status_code} - {response.text}"

Dosya içeriği okuma

def process_file(file): ext = file.name.split('.')[-1].lower() text = "" if ext in ["txt"]: text = file.getvalue().decode("utf-8") elif ext in ["pdf"]: try: doc = fitz.open(stream=file.read(), filetype="pdf") for page in doc: text += page.get_text() except: text = "[PDF dosyası okunamadı]" elif ext in ["doc", "docx"]: try: with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp: tmp.write(file.read()) tmp.flush() text = docx2txt.process(tmp.name) os.unlink(tmp.name) except: text = "[DOCX dosyası okunamadı]" else: text = "[Desteklenmeyen dosya türü]" return text

Uygulama başlığı

st.set_page_config(page_title="Cat CPT", layout="wide") st.title("😺 Cat CPT - Kedi Yapay Zekası")

API key girişi

st.sidebar.title("🔐 Hugging Face API Key Girişi") api_key = st.sidebar.text_input("Hugging Face API Anahtarınızı girin:", type="password") if not api_key: st.sidebar.warning("Devam etmek için API anahtarınızı girin.") st.stop()

Rol yapma modu

roleplay_mode = st.sidebar.checkbox("🎮 Rol yapma modu (hikaye anlatımı)")

Kullanıcı girişi

user_input = st.text_area("Sorunuzu yazın:", height=100)

Dosya yükleme

uploaded_file = st.file_uploader("📎 Dosya yükleyin (PDF, DOCX, TXT)", type=['pdf', 'docx', 'txt']) file_text = "" if uploaded_file: file_text = process_file(uploaded_file) if file_text and "Desteklenmeyen" not in file_text: st.info(f"Dosya içeriği başarıyla okundu. Uzunluk: {len(file_text)} karakter.") else: st.warning(file_text)

if st.button("Gönder"): if not user_input and not file_text: st.warning("Lütfen bir soru yazın veya dosya yükleyin.") else: user_input_en = translate_to_en(extract_keywords(user_input)) if user_input else "" file_text_en = translate_to_en(file_text) if file_text else ""

prompt = ""
    if roleplay_mode:
        prompt += "Kullanıcının verdiği hikayeyi yaratıcı şekilde geliştir."
    else:
        prompt += "Kısa, açık ve güvenilir kaynaklara dayalı cevap ver. Gereksiz detaylardan kaçın."

    prompt += "\n\n"
    if user_input_en:
        prompt += f"Soru: {user_input_en}\n"
    if file_text_en:
        prompt += f"Belge: {file_text_en}"

    response_en = query_huggingface({"inputs": prompt}, api_key)
    final_lang = detect(user_input) if user_input else "tr"
    response = translate_from_en(response_en, final_lang)
    st.markdown(f"**😺 Cat CPT Cevabı:**\n\n{response}")

    # Sesli yanıt
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

