import streamlit as st
import requests

st.set_page_config(
    page_title="Matsya Mitra - Coastal Voice Assistant",
    page_icon="🌊",
    layout="centered"
)

st.title("🌊 Matsya Mitra (మత్స్య మిత్ర)")
st.subheader("AI Voice Assistant for Fisherfolk & Coastal Families")
st.markdown("Query marine weather updates, cyclone warnings, and government welfare schemes instantly in **Telugu & Telglish** using **Gnani Prisma (STT), Evon (LLM), and Timbre (TTS)**.")

st.divider()

API_URL = "http://127.0.0.1:8000/api/v1/voice-query"

st.markdown("### 🎙️ Voice Query Input")
uploaded_file = st.file_uploader("Upload an audio file (.wav or .mp3)", type=["wav", "mp3", "m4a"])

if uploaded_file is not None:
    st.audio(uploaded_file, format="audio/wav")
    
    if st.button("🚀 Process Voice Query with Gnani AI Ecosystem", type="primary"):
        with st.spinner("Processing via Prisma STT -> Evon Reasoning -> Timbre TTS..."):
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "audio/wav")}
                response = requests.post(API_URL, files=files)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    st.success("Query processed successfully across Gnani models!")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric(label="Latency", value=f"{data.get('latency_ms')} ms")
                    with col2:
                        st.metric(label="Code-Mixed", value="Yes" if data.get('code_mixed_detected') else "No")
                    with col3:
                        st.metric(label="Timbre TTS", value="Active" if data.get('audio_synthesized') else "Pending")
                    
                    st.markdown("### 📝 Prisma STT Transcription")
                    st.info(data.get('transcription'))
                    
                    st.markdown("### 🤖 Evon Reasoning & Response")
                    st.success(data.get('response_text'))
                    
                else:
                    st.error(f"Server Error: {response.text}")
                    
            except requests.exceptions.ConnectionError:
                st.error("Could not connect to FastAPI backend. Ensure Uvicorn is running on port 8000.")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

st.divider()
st.markdown("*Built for The Great Indian AI Internship Challenge using Gnani AI APIs.*")