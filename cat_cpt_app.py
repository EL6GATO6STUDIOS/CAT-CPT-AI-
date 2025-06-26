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

# Dil çeviri fonksiyonları
def translate_to_en(text):
    try:
        detected = detect(text)
    except:
        detected = "tr"
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

# Hugging Face API üzerinden yanıt al
def query_huggingface(payload, api_key):
    headers
