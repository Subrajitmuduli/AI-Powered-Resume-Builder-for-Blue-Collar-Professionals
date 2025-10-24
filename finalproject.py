
"""
AI-Powered Resume Builder for Blue-Collar Professionals
✅ Optional profile photo in PDF
✅ Voice input for all credential fields
"""

import os
import io
import json
import unicodedata
import tempfile
import streamlit as st
from fpdf import FPDF
from PIL import Image
import speech_recognition as sr

st.markdown("""
    <style>
        /* ===== ANIMATED BACKGROUND ===== */
        @keyframes gradientMove {
            0% {background-position: 0% 50%;}
            50% {background-position: 100% 50%;}
            100% {background-position: 0% 50%;}
        }

        [data-testid="stAppViewContainer"] {
            background: linear-gradient(135deg, #a2d2ff, #b9fbc0, #ffe6a7, #ffd6e0);
            background-size: 400% 400%;
            animation: gradientMove 18s ease infinite;
            color: #222;
        }

        /* ===== SIDEBAR DESIGN ===== */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #001f3f, #004080, #0074D9);
            background-size: 400% 400%;
            animation: gradientMove 15s ease infinite;
            color: white !important;
        }
        [data-testid="stSidebar"] * {
            color: white !important;
        }

        /* ===== BUTTONS ===== */
        div.stButton > button {
            background: linear-gradient(90deg, #0074D9, #00BCD4);
            color: white;
            border: none;
            border-radius: 10px;
            padding: 0.6em 1.2em;
            font-weight: bold;
            transition: 0.3s ease;
        }
        div.stButton > button:hover {
            background: linear-gradient(90deg, #00BCD4, #0074D9);
            transform: scale(1.05);
        }

        /* ===== INPUTS ===== */
        input, textarea, select {
            border-radius: 8px !important;
            border: 1px solid #90caf9 !important;
        }

        /* ===== TITLES ===== */
        h1, h2, h3, h4, h5 {
            font-family: 'Poppins', sans-serif;
            color: #0d47a1;
        }

        /* ===== METRIC CARDS ===== */
        div[data-testid="stMetricValue"] {
            color: #1565c0;
            font-size: 22px;
            font-weight: 700;
        }

        /* ===== LOGIN CARD ===== */
        .login-bg {
            background: linear-gradient(-45deg, #4facfe, #00f2fe, #00c6ff, #0072ff);
            background-size: 400% 400%;
            animation: gradientMove 10s ease infinite;
            padding: 45px;
            border-radius: 20px;
            color: white;
            text-align: center;
            box-shadow: 0px 4px 10px rgba(0,0,0,0.3);
        }

        /* ===== CARD CONTAINERS ===== */
        .card {
            background: rgba(255,255,255,0.9);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0px 2px 6px rgba(0,0,0,0.15);
            margin-bottom: 20px;
        }

        /* ===== SCROLLBAR ===== */
        ::-webkit-scrollbar {
            width: 10px;
        }
        ::-webkit-scrollbar-thumb {
            background: #4a90e2;
            border-radius: 10px;
        }
    </style>
""", unsafe_allow_html=True)
# ---------------------- Voice Input Helper ----------------------

def voice_input(prompt: str) -> str:
    """Capture voice input and convert it to text using Google Speech Recognition."""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info(f"🎙️ Listening... please speak your {prompt}")
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=10)
            text = r.recognize_google(audio)
            st.success(f"✅ Recognized {prompt}: {text}")
            return text
        except sr.UnknownValueError:
            st.warning("❌ Sorry, could not understand your voice.")
        except sr.RequestError:
            st.error("⚠️ Voice service unavailable. Check your internet connection.")
        except sr.WaitTimeoutError:
            st.warning("⌛ Listening timed out, please try again.")
    return ""

# ---------------------- Resume Generation ----------------------

try:
    import openai
    OPENAI_AVAILABLE = True
except Exception:
    OPENAI_AVAILABLE = False

def generate_resume_text(data: dict) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if OPENAI_AVAILABLE and api_key:
        openai.api_key = api_key
        prompt = build_prompt_for_openai(data)
        try:
            resp = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=700,
            )
            return resp["choices"][0]["message"]["content"].strip()
        except Exception as e:
            st.warning(f"OpenAI call failed: {e}. Using fallback template.")
    return build_fallback_resume_text(data)

def build_prompt_for_openai(data: dict) -> str:
    prompt = (
        "You are a helpful assistant that writes concise, professional resume content "
        "for blue-collar professionals. Produce:\n"
        "1) Professional Summary\n"
        "2) Experience\n"
        "3) Skills and Certifications\n"
        "4) Education\n\n"
        "User data (JSON):\n" + json.dumps(data, indent=2)
    )
    return prompt

def build_fallback_resume_text(data: dict) -> str:
    name = data.get("name", "")
    trade = data.get("trade", "")
    years = data.get("years_experience", "")
    summary = f"Reliable {trade} with {years} years of experience in {trade.lower()} work. "
    if data.get("special_notes"):
        summary += data.get("special_notes") + " "
    summary += "Known for strong work ethic, safety-first approach, and consistent on-time completion of projects."

    exp_lines = [l.strip() for l in data.get("experience_text", "").splitlines() if l.strip()]
    if not exp_lines:
        exp_lines = [
            f"Performed {trade.lower()} tasks including installation, maintenance, and repairs.",
            "Followed safety protocols and maintained jobsite cleanliness.",
            "Collaborated with teams to complete projects on schedule."
        ]

    skills = data.get("skills_list") or [s.strip() for s in (data.get("skills_text") or "").split(',') if s.strip()]
    if not skills:
        skills = [f"{trade} installation", "Equipment maintenance", "Safety compliance"]

    certs = data.get("certifications") or []
    certs_text = ", ".join(certs) if certs else "N/A"

    parts = []
    parts.append(f"PROFESSIONAL SUMMARY\n{summary}\n")
    parts.append("EXPERIENCE\n" + "\n".join(f"- {e}" for e in exp_lines))
    parts.append("\nSKILLS\n" + "\n".join(f"- {s}" for s in skills))
    parts.append("\nCERTIFICATIONS\n" + certs_text)
    if data.get("education"):
        parts.append("\nEDUCATION\n" + data.get("education"))
    return "\n".join(parts)

# ---------------------- PDF Creation ---------------------- 

def create_pdf_bytes(resume_text: str, name: str, contact_info: dict = None,
                     template: str = "Modern Blue", photo_bytes: bytes = None) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Optional photo  
    
    photo_width, photo_height = 35, 35
    if photo_bytes:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                tmp.write(photo_bytes)
                tmp.flush()
                tmp_path = tmp.name
            img = Image.open(tmp_path).convert("RGB")
            img.save(tmp_path, "PNG")
            pdf.image(tmp_path, x=15, y=20, w=photo_width, h=photo_height)
        except Exception as e:
            print(f"⚠️ Could not embed photo: {e}")
        finally:
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                os.remove(tmp_path)

    # Fonts & colors
    heading_font = ("Helvetica", 'B', 20)
    body_font = ("Helvetica", '', 12)
    primary_color = (0, 102, 204) if template == "Modern Blue" else (0, 0, 0)

    pdf.set_xy(60, 25)
    pdf.set_text_color(*primary_color)
    pdf.set_font(*heading_font)
    pdf.cell(0, 10, (name or "").upper(), ln=True)

    if contact_info:
        pdf.set_font(*body_font)
        pdf.set_text_color(0, 0, 0)
        contact_line = " | ".join([v for v in [contact_info.get('city'),
                                               contact_info.get('phone'),
                                               contact_info.get('email')] if v])
        pdf.set_x(60)
        pdf.cell(0, 8, contact_line, ln=True)

    pdf.set_y(pdf.get_y() + 10)
    pdf.set_font(*body_font)
    pdf.multi_cell(0, 7, resume_text)

    out = pdf.output(dest='S')
    return out.encode('latin-1', 'ignore') if isinstance(out, str) else out

# ---------------------- Streamlit UI ----------------------

st.set_page_config(page_title="AI Resume Builder — Blue-Collar", layout="wide")
st.title("🎯 AI-Powered Resume Builder for Blue-Collar Professionals")
st.write("Create professional, trade-focused resumes in minutes. Now with **voice input**!")

# Initialize session_state for voice inputs

for field in ["name", "city", "phone", "email", "education", "skills_text", "certifications", "experience_text", "special_notes"]:
    if field not in st.session_state:
        st.session_state[field] = ""

# ---------- Voice Input Section ----------

st.subheader("🎤 Voice Input (optional)")
if st.button("🎙️ Speak Name"): st.session_state.name = voice_input("name")
if st.button("🎙️ Speak City"): st.session_state.city = voice_input("city or location")
if st.button("🎙️ Speak Phone"): st.session_state.phone = voice_input("phone number")
if st.button("🎙️ Speak Email"): st.session_state.email = voice_input("email address")
if st.button("🎙️ Speak Education"): st.session_state.education = voice_input("education or training")
if st.button("🎙️ Speak Skills"): st.session_state.skills_text = voice_input("skills (say them separated by commas)")
if st.button("🎙️ Speak Certifications"): st.session_state.certifications = voice_input("certifications")
if st.button("🎙️ Speak Experience"): st.session_state.experience_text = voice_input("work experience")
if st.button("🎙️ Speak Special Notes"): st.session_state.special_notes = voice_input("special notes")

# ---------- Form ----------

with st.form("resume_form"):
    col1, col2 = st.columns([2, 1])
    with col1:
        name = st.text_input("Full name", value=st.session_state.name)
        city = st.text_input("City / Location", value=st.session_state.city)
        phone = st.text_input("Phone (optional)", value=st.session_state.phone)
        email = st.text_input("Email (optional)", value=st.session_state.email)
        trade = st.selectbox("Trade / Profession", [
            "Electrician", "Plumber", "Welder", "HVAC Technician", "Carpenter",
            "Heavy Equipment Operator", "Mechanic", "Construction Laborer", "Painter", "Other"
        ])
        if trade == "Other":
            trade = st.text_input("Please specify trade", value="")
        years_experience = st.selectbox("Years of experience", ["0-1", "1-3", "3-5", "5-10", "10+"])
        education = st.text_input("Education / Training", value=st.session_state.education)
        template = st.selectbox("Choose Resume Template",
                                ["Modern Blue", "Classic Gray", "Minimalist Black & White"])
        photo = st.file_uploader("Upload a profile photo (optional)", type=["jpg", "jpeg", "png"])
    with col2:
        skills_text = st.text_area("Core skills (comma-separated)", value=st.session_state.skills_text)
        certifications = st.text_area("Certifications (one per line)", value=st.session_state.certifications)

    st.subheader("Work history / Experience (brief lines)")
    experience_text = st.text_area("Describe your experience (one per line)", value=st.session_state.experience_text)

    st.subheader("Optional — Special notes")
    special_notes = st.text_input("Add any key highlights", value=st.session_state.special_notes)

    uploaded_files = st.file_uploader("Upload certificates — optional", accept_multiple_files=True)
    submitted = st.form_submit_button("Generate Resume")

# ---------- After Submit ----------

if submitted:
    data = {
        "name": name.strip(),
        "city": city.strip(),
        "phone": phone.strip(),
        "email": email.strip(),
        "trade": trade.strip(),
        "years_experience": years_experience,
        "education": education.strip(),
        "skills_text": skills_text.strip(),
        "skills_list": [s.strip() for s in skills_text.split(',') if s.strip()],
        "certifications": [c.strip() for c in certifications.splitlines() if c.strip()],
        "experience_text": experience_text.strip(),
        "special_notes": special_notes.strip(),
    }

    with st.spinner("Generating resume..."):
        resume_text = generate_resume_text(data)

    st.success("✅ Resume generated successfully!")
    st.subheader("Resume Preview")
    st.code(resume_text, language='')

    contact_info = {"city": city, "phone": phone, "email": email}
    photo_bytes = photo.read() if photo else None
    pdf_bytes = create_pdf_bytes(resume_text, name or 'Resume', contact_info, template, photo_bytes)

    st.download_button(
        label="📄 Download Resume (PDF)",
        data=pdf_bytes,
        file_name=f"{name.replace(' ', '_') or 'resume'}.pdf",
        mime="application/pdf",
    )

    if uploaded_files:
        save_dir = os.path.join("certificates", name.replace(' ', '_') or 'user')
        os.makedirs(save_dir, exist_ok=True)
        for up in uploaded_files:
            with open(os.path.join(save_dir, up.name), 'wb') as f:
                f.write(up.read())
        st.info(f"📁 Saved uploaded certificates to `{save_dir}`")
else:
    st.info("🎤 Fill the form (or use voice input) and click **Generate Resume** to create your resume.")

st.markdown("---")
st.markdown("====================================================================     **THANK YOU**    ====================================================================")
