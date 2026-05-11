import streamlit as st
import random
import json
import io
from gtts import gTTS
from groq import Groq

# GROQ
api_key=("Enter your GROQ API key here")
client = Groq(api_key=api_key)

st.set_page_config(page_title="AI Spelling Tutor", page_icon="📝")
st.title("📝 AI Adaptive Spelling Tutor")

# --- SESSION STATE INITIALIZATION ---
if "words" not in st.session_state:
    st.session_state.words = []
if "score" not in st.session_state:
    st.session_state.score = 0
if "wrong_words" not in st.session_state:
    st.session_state.wrong_words = []
if "current_word" not in st.session_state:
    st.session_state.current_word = None
if "game_active" not in st.session_state:
    st.session_state.game_active = False

# --- SIDEBAR: SETTINGS ---
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Enter Groq API Key", type="password")
    difficulty = st.selectbox("Select Difficulty", ["easy", "normal", "hard"])
    
    if st.button("Start / Reset Game"):
        if not api_key:
            st.error("Please enter an API key first!")
        else:
            st.session_state.game_active = True
            st.session_state.score = 0
            st.session_state.wrong_words = []
            st.session_state.words = []
            st.session_state.current_word = None
            st.info("Loading words from AI...")

# AI WORDS
def get_words_from_ai(api_key, difficulty):
    client = Groq(api_key=api_key)
    prompt = f"Generate 10 spelling words for {difficulty} difficulty. Return ONLY JSON array of objects with 'word' and 'type' keys."
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are an adaptive spelling tutor. Return JSON format: [{'word':'apple', 'type':'new'}]"},
                {"role": "user", "content": prompt}
            ]
        )
        data = json.loads(response.choices[0].message.content)
        return [item["word"].lower() for item in data]
    except Exception as e:
        st.warning(f"AI failed: {e}. Using backup words.")
        backups = {
            "easy": ["cat", "sun", "book"],
            "normal": ["banana", "elephant", "bicycle"],
            "hard": ["necessary", "rhythm", "accommodation"]
        }
        return backups[difficulty]
    
    # --- SPEECH FUNCTION ---
def speak_word(word):
    tts = gTTS(text=f"Spell the word: {word}", lang='en')
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    return fp

# --- MAIN GAME LOGIC ---
if st.session_state.game_active:
    # 1. Load words if list is empty
    if not st.session_state.words and not st.session_state.current_word:
        st.session_state.words = get_words_from_ai(api_key, difficulty)
    # 2. Select a new word if needed
    if not st.session_state.current_word and st.session_state.words:
        st.session_state.current_word = random.choice(st.session_state.words)

    # 3. Game UI
    if st.session_state.current_word:
        st.subheader(f"Score: {st.session_state.score}")
        
        # Audio Player
        audio_fp = speak_word(st.session_state.current_word)
        st.audio(audio_fp, format="audio/mp3", autoplay=True)
        
        # User Input
        with st.form(key="spelling_form", clear_on_submit=True):
            user_input = st.text_input("Type your spelling here:").lower().strip()
            submit = st.form_submit_button("Check Spelling")

        if submit:
            if user_input == st.session_state.current_word:
                st.success(f"Correct! '{st.session_state.current_word}'")
                st.session_state.score += 1
                st.session_state.words.remove(st.session_state.current_word)
                st.session_state.current_word = None # Reset to pick new word next rerun
                st.rerun()
            else:
                st.error(f"Wrong! This word will come back later.")
                if st.session_state.current_word not in st.session_state.wrong_words:
                    st.session_state.wrong_words.append(st.session_state.current_word)
                # We don't remove it from words so it repeats
                st.session_state.current_word = None
                st.rerun()

                # 4. Game Over State
    if not st.session_state.words and not st.session_state.current_word:
        st.balloons()
        st.success(f"Game Over! Final Score: {st.session_state.score}")
        if st.session_state.wrong_words:
            st.write("Words to review:", st.session_state.wrong_words)
        st.session_state.game_active = False

else:
    st.info("Select a difficulty and click 'Start Game' in the sidebar to begin.")