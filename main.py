import streamlit as st
import pandas as pd
import os
import google.generativeai as genai
from PIL import Image
import json

# --- 1. ΡΥΘΜΙΣΗ AI (GEMINI) ---
GOOGLE_API_KEY = "AIzaSyB_NjdNwQrRHeFzfphVPz8qIfTzgEQ-zSg" 
genai.configure(api_key=GOOGLE_API_KEY)

# --- 2. ΣΥΝΑΡΤΗΣΕΙΣ ΔΕΔΟΜΕΝΩΝ ---
PROJECTS_FILE = 'data_projects.csv'
EMPLOYEES_FILE = 'data_employees.csv'
FINANCIALS_FILE = 'payroll_financials.csv'
CHECKLIST_FILE = 'checklist_results.csv'

def load_data(f, cols):
    if not os.path.isfile(f) or os.path.getsize(f) == 0:
        return pd.DataFrame(columns=cols)
    try:
        return pd.read_csv(f)
    except:
        return pd.DataFrame(columns=cols)

def save_to_csv(df, f):
    df.to_csv(f, index=False, encoding='utf-8-sig')

def extract_payroll_with_ai(uploaded_file):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        img = Image.open(uploaded_file)
        prompt = """
        Ανέλυσε αυτή την εικόνα μισθοδοσίας. Εξήγαγε τα ποσά για τα παρακάτω πεδία σε JSON:
        "ΙΚΑ_Εργ", "ΙΚΑ_Εργοδ", "ΤΕΚΑ_Εργ", "ΤΕΚΑ_Εργοδ", "Σύνολο_Εισφ", "ΦΜΥ", "Καθαρές", "Σύνολο_Αποδ".
        Μην γράψεις τίποτα άλλο εκτός από το JSON. Αν λείπει κάτι, βάλε 0.0.
        """
        response = model.generate_content([prompt, img])
        json_text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(json_text)
    except Exception as e:
        st.error(f"Σφάλμα AI: {e}")
        return None

# --- 3. ΡΥΘΜΙΣΗ ΣΕΛΙΔΑΣ ---
st.set_page_config(page_title="Payroll AI Verifier", layout="wide")
page = st.sidebar.radio("Μενού:", ["1. Διαχείριση Έργων", "2. Checklist ανά Έργο", "3. Μισθοδοσία Υπαλλήλων"])

# --- ΣΤΑΔΙΟ 1: ΔΙΑΧΕΙΡΙΣΗ ΕΡΓΩΝ ---
if page == "1. Διαχείριση Έργων":
    st.header("🏢 Διαχείριση Επιχειρήσεων")
    with st.form("project_form"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Επωνυμία Επιχείρησης")
        afm = c1.text_input("ΑΦΜ", max_chars=9)
        mis = c2.text_input("Κωδικός MIS")
        budget = c2.number_input("Συνολικός Προϋπολογισμός (€)", min_value=0.0)
        if st.form_submit_button("💾 Αποθήκευση"):
            df = load_data(PROJECTS_FILE, ["Επωνυμία", "ΑΦΜ", "MIS", "Προϋπολογισμός"])
            new_row = pd.DataFrame([{"Επωνυμία": name, "ΑΦΜ": afm, "MIS": mis, "Προϋπολογισμός": budget}])
            save_to_csv(pd.concat([df, new_row], ignore_index=True), PROJECTS_FILE)
            st.success("Το έργο αποθηκεύτηκε!")
            st.rerun()
    st.dataframe(load_data(PROJECTS_FILE, ["Επωνυμία", "ΑΦΜ", "MIS", "Προϋπολογισμός"]), use_container_width=True, hide_index=True)

# --- ΣΤΑΔΙΟ 2: CHECKLIST ΑΝΑ ΕΡΓΟ ---
elif page == "2. Checklist ανά Έργο":
    st.header("📂 Γενικά Παραδοτέα Επιχείρησης")
    projects_df = load_data(PROJECTS_FILE, ["Επωνυμία", "ΑΦΜ"])
    if projects_df.empty:
        st.warning("⚠️ Προσθέστε επιχείρηση στο Στάδιο 1.")
    else:
        sel_name = st.selectbox("Επιλέξτε Επιχείρηση:", projects_df['Επωνυμία'])
        sel_afm = str(projects_df[projects_df['Επωνυμία'] == sel_name]['ΑΦΜ'].iloc[0])
        check_df = load_data(CHECKLIST_FILE, ["ΑΦΜ", "Εγγραφο", "Κατάσταση", "Σχόλιο"])
        
        docs = ["Πίνακας Ε4", "Μισθολογικές καταστάσεις", "ΑΠΔ ΕΦΚΑ", "Αποδεικτικό ΑΠΔ", "ΑΠΔ ΤΕΚΑ", "Ασφαλιστική ενημερότητα", "Φορολογική ενημερότητα", "Προσωρινές ΦΜΥ"]
        results = []
        
        for d in docs:
            existing = check_df[(check_df['ΑΦΜ'].astype(str) == sel_afm) & (check_df['Εγγραφο'] == d)]
            c1, c2, c3 = st.columns([1.5, 1, 2])
            c1.markdown(f"**{d}**")
            curr_st = existing['Κατάσταση'].iloc[0] if not existing.empty else "Έλλειψη ❌"
            status = c2.selectbox("Κατάσταση", ["Έλλειψη ❌", "Υπάρχει ✅", "Δεν απαιτείται"], index=["Έλλειψη ❌", "Υπάρχει ✅", "Δεν απαιτείται"].index(curr_st), key=f"s_{sel_afm}_{d}", label_visibility="collapsed")
            note = c3.text_input("Σχόλιο", value=existing['Σχόλιο'].iloc[0] if not existing.empty else "", key=f"n_{sel_afm}_{d}", label_visibility="collapsed", placeholder="Σχόλιο...")
            results.append({"ΑΦΜ": sel_afm, "Εγγραφο": d, "Κατάσταση": status, "Σχόλιο": note})
        
        if st.button("💾 Αποθήκευση Checklist", use_container_width=True):
            others = check_df[check_df['ΑΦΜ'].astype(str) != sel_afm]
            save_to_csv(pd.concat([others, pd.DataFrame(results)], ignore_index=True), CHECKLIST_FILE)
            st.success("Ενημερώθηκε!")

# --- ΣΤΑΔΙΟ 3: ΜΙΣΘΟΔΟΣΙΑ ---
elif page == "3. Μισθοδοσία Υπαλλήλων":
    st.header("👤 Έλεγχος Υπαλλήλων")
    projects_df = load_data(PROJECTS_FILE, ["Επωνυμία", "ΑΦΜ"])
    if projects_df.empty:
        st.warning("⚠️ Προσθέστε επιχείρηση στο Στάδιο 1.")
    else:
        col_l, col_r = st.columns([1, 1.2])
        with col_l:
            sel_p = st.selectbox("Επιχείρηση:", projects_df['Επωνυμία'])
            s_afm = str(projects_df[projects_df['Επωνυμία'] == sel_p]['ΑΦΜ'].iloc[0])
            m_c, y_c = st.columns(2)
            month = m_c.selectbox("Μήνας:", ["Ιανουάριος", "Φεβρουάριος", "Μάρτιος", "Απρίλιος", "Μάιος", "Ιούνιος", "Ιούλιος", "Αύγουστος", "Σεπτέμβριος", "Οκτώβριος", "Νοέμβριος", "Δεκέμβριος"])
            year = y_c.selectbox("Έτος:", ["2024", "2025", "2026"], index=1)
            period = f"{month} {year}"
        
        with col_r:
            st.subheader("➕ Προσθήκη Υπαλλήλου")
            e_name = st.text_input("Ονοματεπώνυμο")
            c_a, c_m = st.columns(2)
            e_afm = c_a.text_input("ΑΦΜ", max_chars=9)
            e_amka = c_m.text_input("ΑΜΚΑ", max_chars=11)
            if st.button("Καταχώρηση Υπαλλήλου"):
                edf = load_data(EMPLOYEES_FILE, ["ΑΦΜ_Εργου", "Ονοματεπώνυμο", "ΑΦΜ_Υπαλλήλου", "ΑΜΚΑ_Υπαλλήλου"])
                save_to_csv(pd.concat([edf, pd.DataFrame([{"ΑΦΜ_Εργου": s_afm, "Ονοματεπώνυμο": e_name, "ΑΦΜ_Υπαλλήλου": e_afm, "ΑΜΚΑ_Υπαλλήλου": e_amka}])], ignore_index=True), EMPLOYEES_FILE)
                st.rerun()

        st.divider()
        all_e = load_data(EMPLOYEES_FILE, ["ΑΦΜ_Εργου", "Ονοματεπώνυμο", "ΑΦΜ_Υπαλλήλου", "ΑΜΚΑ_Υπαλλήλου"])
        c_emps = all_e[all_e['
