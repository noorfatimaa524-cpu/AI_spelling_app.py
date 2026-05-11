import streamlit as st
import random
import json
import io
from gtts import gTTS
from groq import Groq

# --- INITIAL SETUP ---
st.set_page_config(page_title="AI Spelling Tutor Pro", page_icon="🎓")

if "word_list" not in st.session_state:
    st.session_state.word_list = []  # List of dicts: {"word": "", "definition": ""}
if "score" not in st.session_state:
    st.session_state.score = 0
if "current_index" not in st.session_state:
    st.session_state.current_index = 0

# --- SIDEBAR ---
with st.sidebar:
    st.header("Learning Settings")
    api_key = st.text_input("Enter Groq API Key", type="password")
    difficulty = st.selectbox("Level", ["easy", "normal", "hard"])
    
    if st.button("Generate New Lesson"):
        if not api_key:
            st.error("Please enter your API Key!")
        else:
            try:
                client = Groq(api_key=api_key)
                # Specific prompt to get definitions and examples
                prompt = f"""
                Generate random spelling words for {difficulty} level. 
                Return ONLY a JSON array of objects with keys: 'word', 'definition'.
                Example: [{{"word": "apple", "definition": "a round fruit"}}]
                """
                chat_completion = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.3-70b-versatile",
                    response_format={"type": "json_object"} # Forces JSON output
                )
                
                raw_json = chat_completion.choices[0].message.content
                data = json.loads(raw_json)
                
                # Extract the list regardless of the key the AI uses
                if isinstance(data, dict):
                    st.session_state.word_list = list(data.values())[0]
                else:
                    st.session_state.word_list = data
                
                st.session_state.current_index = 0
                st.session_state.score = 0
                st.success("Lesson Ready!")
            except Exception as e:
                st.error(f"AI Error: {e}")

# --- MAIN GAME AREA ---
st.title("🎓 AI Spelling & Vocabulary")

if st.session_state.word_list and st.session_state.current_index < len(st.session_state.word_list):
    current_data = st.session_state.word_list[st.session_state.current_index]
    word = current_data['word']
    
    st.write(f"### Word {st.session_state.current_index + 1} of {len(st.session_state.word_list)}")
    
    # 1. Audio (TTS)
    tts = gTTS(text=f"The word is {word}. {current_data.get('example', '')}", lang='en')
    audio_fp = io.BytesIO()
    tts.write_to_fp(audio_fp)
    st.audio(audio_fp, format="audio/mp3")

    # 2. Hints (Definitions)
    with st.expander("👁️ Show Definition"):
        st.write(f"**Definition:** {current_data.get('definition', 'No definition provided.')}")

    # 3. Input Form
    with st.form(key="spell_form", clear_on_submit=True):
        guess = st.text_input("Type the word:").strip().lower()
        submitted = st.form_submit_button("Submit")
        
        if submitted:
            if guess == word.lower():
                st.success(f"Perfect! '{word}' is correct.")
                st.session_state.score += 1
            else:
                st.error(f"Incorrect. The word was: **{word}**")
            
            st.session_state.current_index += 1
            st.rerun()

elif st.session_state.current_index >= len(st.session_state.word_list) and st.session_state.word_list:
    st.balloons()
    st.header("Lesson Finished! 🎉")
    st.subheader(f"Your Accuracy: {(st.session_state.score / len(st.session_state.word_list)) * 100}%")
    if st.button("Restart"):
        st.session_state.word_list = []
        st.rerun()
else:
    st.info("👈 Enter your API key and click 'Generate New Lesson' to start.")
