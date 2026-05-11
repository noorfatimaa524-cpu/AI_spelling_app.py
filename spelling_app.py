import streamlit as st
import random
import json
import io
from gtts import gTTS
from groq import Groq

# GROQ
api_key=("Enter your GROQ API key here")
client = Groq(api_key=api_key)
st.set_page_config(page_title="Pro AI Spelling Tutor", page_icon="🎓", layout="wide")

# --- SESSION STATE INITIALIZATION ---
if "word_data" not in st.session_state:
    st.session_state.word_data = []  # List of dicts: {"word": "", "definition": "", "example": ""}
if "score" not in st.session_state:
    st.session_state.score = 0
if "total_attempts" not in st.session_state:
    st.session_state.total_attempts = 0
if "wrong_words" not in st.session_state:
    st.session_state.wrong_words = []
if "game_active" not in st.session_state:
    st.session_state.game_active = False

# --- SIDEBAR: SETTINGS ---
with st.sidebar:
    st.title("⚙️ Controls")
    api_key = st.text_input("Groq API Key", type="password")
    diff = st.select_slider("Difficulty", options=["easy", "normal", "hard"])
    
    if st.button("🚀 Start New Session"):
        if api_key:
            with st.spinner("AI is crafting your lesson..."):
                st.session_state.word_data = get_advanced_content(api_key, diff)
                st.session_state.score = 0
                st.session_state.total_attempts = 0
                st.session_state.wrong_words = []
                st.session_state.game_active = True
                st.rerun()
        else:
            st.error("Enter API Key first!")

# AI WORDS
def get_advanced_content(api_key, difficulty):
    client = Groq(api_key=api_key)
    prompt = f"""
    Generate 8 spelling words for {difficulty} level.
    For each word, provide a brief definition and one example sentence.
    Return ONLY a JSON array like this:
    [
      {{"word": "necessary", "definition": "needed to be done", "example": "Sleep is necessary for health."}}
    ]
    """
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"} # Ensures valid JSON
        )
        raw_data = json.loads(response.choices[0].message.content)
        # Handle cases where AI wraps list in a key
        return raw_data if isinstance(raw_data, list) else list(raw_data.values())[0]
    except Exception as e:
        st.error(f"AI Error: {e}")
        return [{"word": "example", "definition": "a representative form", "example": "This is an example."}]

def play_audio(text):
    tts = gTTS(text=text, lang='en')
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    return f

# --- MAIN GAME LOGIC ---
if st.session_state.game_active and st.session_state.word_data:
    current_item = st.session_state.word_data[0] # Always grab the first word in queue
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write(f"### Word {st.session_state.score + 1}")
        progress = st.progress(0) # Logic for progress bar below
        
        # Audio Section
        st.write("🔈 **Listen to the word:**")
        audio_fp = play_audio(f"The word is {current_item['word']}. {current_item['example']}")
        st.audio(audio_fp, format="audio/mp3")
        
        # Clues (Expandable)
        with st.expander("💡 Need a hint? (Definition & Example)"):
            st.write(f"**Definition:** {current_item['definition']}")
            st.write(f"**Example:** *{current_item['example']}*")

        # Input
        with st.form(key="input_form", clear_on_submit=True):
            user_input = st.text_input("Type your spelling:").strip().lower()
            if st.form_submit_button("Submit Answer"):
                st.session_state.total_attempts += 1
                
                if user_input == current_item['word'].lower():
                    st.toast("Correct! ✨", icon="✅")
                    st.session_state.score += 1
                    st.session_state.word_data.pop(0) # Remove if correct
                else:
                    st.error(f"Not quite! The correct spelling was: **{current_item['word']}**")
                    st.session_state.wrong_words.append(current_item['word'])
                    # Spaced Repetition: Move the missed word to the back of the list
                    failed_word = st.session_state.word_data.pop(0)
                    st.session_state.word_data.append(failed_word) 
                
                st.rerun()

    with col2:
        st.metric("Score", f"{st.session_state.score}")
        st.metric("Accuracy", f"{int((st.session_state.score/st.session_state.total_attempts)*100 if st.session_state.total_attempts > 0 else 0)}%")
        
        if st.session_state.wrong_words:
            st.write("📝 **Review List:**")
            for w in set(st.session_state.wrong_words):
                st.caption(f"- {w}")

elif not st.session_state.game_active:
    st.header("Welcome to the Advanced Spelling Tutor")
    st.write("This app uses AI to generate custom spelling lists with definitions and context.")
    st.info("👈 Set your API key and difficulty in the sidebar to start!")
else:
    st.balloons()
    st.success("🎉 Session Complete!")
    st.metric("Final Score", st.session_state.score)
    if st.button("Finish"):
        st.session_state.game_active = False
        st.rerun()

else:
    st.info("Select a difficulty and click 'Start Game' in the sidebar to begin.")
