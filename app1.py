import streamlit as st
import tensorflow as tf
import numpy as np
from PIL import Image
from tensorflow.keras.preprocessing.image import img_to_array
import os
from datetime import datetime
import plotly.express as px
from gtts import gTTS
import mysql.connector

tf.keras.backend.clear_session()
st.set_page_config(page_title="Plant Detector", layout="wide")

# ---------------- MYSQL CONNECTION ----------------
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="plant_ai"
)
cursor = db.cursor()

# ---------------- BACKGROUND ----------------
st.markdown("""
<style>
.stApp {
    background-image: url("https://images.unsplash.com/photo-1500382017468-9049fed747ef");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}
.big-text {
    font-size: 20px;
    font-weight: bold;
    color: white;
    background: rgba(0,0,0,0.7);
    padding: 10px;
    border-radius: 10px;
    margin-top: 10px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- MODEL ----------------
model = tf.keras.models.load_model("plant_disease_model.keras", compile=False)
class_names = ["Early_Blight", "Healthy", "Late_Blight"]

# ---------------- MULTI LANGUAGE ----------------
languages = {
    "English": "en",
    "Hindi": "hi",
    "Marathi": "mr"
}

treatment_text = {
    "English": {
        "Early_Blight": "Remove infected leaves. Use Mancozeb.",
        "Late_Blight": "Use copper fungicide.",
        "Healthy": "No disease detected."
    },
    "Hindi": {
        "Early_Blight": "संक्रमित पत्तियां हटाएं। मैनकोजेब का उपयोग करें।",
        "Late_Blight": "कॉपर फंगीसाइड का उपयोग करें।",
        "Healthy": "कोई रोग नहीं मिला।"
    },
    "Marathi": {
        "Early_Blight": "संक्रमित पाने काढा. मॅनकोझेब वापरा.",
        "Late_Blight": "कॉपर फंगीसाइड वापरा.",
        "Healthy": "रोग आढळला नाही."
    }
}

# ---------------- ADVANCED PLANT CARE ----------------
plant_care = {
    "Early_Blight": {
        "description": "Fungal disease causing dark brown spots.",
        "symptoms": ["Brown spots", "Yellow leaves"],
        "prevention": ["Avoid overhead watering", "Maintain spacing"],
        "organic": ["Neem oil spray"]
    },
    "Late_Blight": {
        "description": "Serious fungal infection in wet climate.",
        "symptoms": ["Water soaked lesions"],
        "prevention": ["Good air circulation"],
        "organic": ["Garlic spray"]
    },
    "Healthy": {
        "description": "Plant is healthy.",
        "symptoms": ["Green leaves"],
        "prevention": ["Regular watering"],
        "organic": ["Natural compost"]
    }
}

# ---------------- SESSION ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "last_probs" not in st.session_state:
    st.session_state.last_probs = []

# ---------------- LOGIN FUNCTIONS ----------------
def signup(u, p):
    try:
        cursor.execute("INSERT INTO users (username,password) VALUES (%s,%s)", (u,p))
        db.commit()
        return True
    except:
        return False

def login(u, p):
    cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (u,p))
    return cursor.fetchone()

# ---------------- LOGIN PAGE ----------------
if not st.session_state.logged_in:

    st.title("🔐 Login to Plant Disease Detector")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Login"):
            if login(username,password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Invalid credentials")

    with col2:
        if st.button("Signup"):
            if signup(username,password):
                st.success("Account created! Login now.")
            else:
                st.error("Username already exists")

# ---------------- MAIN APP ----------------
else:

    st.sidebar.write(f"👋 Welcome {st.session_state.username}")

    selected_language = st.sidebar.selectbox("🌎 Select Language", list(languages.keys()))
    lang_code = languages[selected_language]

    menu = st.sidebar.radio("Navigation",
                            ["Dashboard","Detect Disease","Live Camera", "Prediction Chart","History","Logout"])

    # ---------------- DASHBOARD ----------------
    if menu == "Dashboard":
        st.title("🌿 Plant Disease Detection System")
        st.write("Upload image or use live camera to detect disease.")

    # ---------------- DETECT DISEASE ----------------
    elif menu == "Detect Disease":

        uploaded_file = st.file_uploader("Upload Plant Image", type=["jpg","png","jpeg"])

        if uploaded_file:
            img = Image.open(uploaded_file).convert("RGB")
            st.image(img, use_container_width=True)

            img_resized = img.resize((224,224))
            img_array = img_to_array(img_resized)/255.0
            img_array = np.expand_dims(img_array, axis=0)

            prediction = model.predict(img_array)
            class_idx = np.argmax(prediction)
            disease = class_names[class_idx]
            confidence = float(np.max(prediction)*100)

            st.session_state.last_probs = prediction[0].tolist()

            st.markdown(f"<div class='big-text'>Disease: {disease}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='big-text'>Confidence: {confidence:.2f}%</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='big-text'>Treatment: {treatment_text[selected_language][disease]}</div>", unsafe_allow_html=True)

            # 🔊 Voice Output
            voice_text = f"Disease {disease}. Confidence {confidence:.2f} percent. Treatment {treatment_text[selected_language][disease]}"
            tts = gTTS(voice_text, lang=lang_code)
            tts.save("voice.mp3")
            audio_file = open("voice.mp3", "rb")
            st.audio(audio_file.read(), format="audio/mp3")

            # SAVE HISTORY
            cursor.execute(
                "INSERT INTO history (username,disease,confidence,date) VALUES (%s,%s,%s,%s)",
                (st.session_state.username,disease,confidence,str(datetime.now()))
            )
            db.commit()

            # PLANT CARE
            if disease in plant_care:
                st.markdown("## 🌱 Plant Care Recommendation")
                st.write("### Description:", plant_care[disease]["description"])
                st.write("### Symptoms:")
                for s in plant_care[disease]["symptoms"]:
                    st.write("•", s)
                st.write("### Prevention:")
                for p in plant_care[disease]["prevention"]:
                    st.write("•", p)
                st.write("### Organic Solution:")
                for o in plant_care[disease]["organic"]:
                    st.write("•", o)

    # ---------------- LIVE CAMERA ----------------
    elif menu == "Live Camera":

        camera_image = st.camera_input("Take plant photo")

        if camera_image:
            img = Image.open(camera_image).convert("RGB")
            st.image(img, use_container_width=True)

    # ---------------- PREDICTION CHART ----------------
    elif menu == "Prediction Chart":

        if not st.session_state.last_probs:
            st.warning("Upload image first.")
        else:
            df = {
                "Disease": class_names,
                "Probability": st.session_state.last_probs
            }
            fig = px.bar(df, x="Disease", y="Probability")
            st.plotly_chart(fig, use_container_width=True)

    # ---------------- HISTORY ----------------
    elif menu == "History":

        cursor.execute("SELECT disease,confidence,date FROM history WHERE username=%s", (st.session_state.username,))
        data = cursor.fetchall()

        if not data:
            st.info("No history found.")
        else:
            st.table(data)

    # ---------------- LOGOUT ----------------
    elif menu == "Logout":
        st.session_state.clear()
        st.rerun()
