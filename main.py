import streamlit as st
import pandas as pd
import os
import json
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# --- 1. ΡΥΘΜΙΣΗ ΣΕΛΙΔΑΣ ---
st.set_page_config(page_title="Payroll Verifier Pro", page_icon="🛡️", layout="wide")

# --- 2. ΟΡΙΣΜΟΣ ΑΡΧΕΙΩΝ & ΥΠΟΔΟΜΗΣ ---
PROJECTS_FILE = 'data_projects.csv'
CHECKLIST_FILE = 'checklist_results.csv'
EMPLOYEES_FILE = 'data_employees.csv'
FINANCIALS_FILE = 'payroll_financials.csv'
PAYROLL_CHECKS_FILE = 'payroll_checks.csv'

def load_data(filename, columns):
    if not os.path.isfile(filename) or os.path.getsize(filename) == 0:
        return pd.DataFrame(columns=columns)
    try:
        return pd.read_csv(filename)
    except Exception:
        return pd.DataFrame(columns=columns)

def save_to_csv(df, filename):
    df.to_csv(filename, index=False, encoding='utf-8-sig')

# --- 3. SCHEMA AI ---
class PayrollFinancials(BaseModel):
    ΙΚΑ_Εργ: float
    ΙΚΑ_Εργοδ: float
    ΤΕΚΑ_Εργ: float
    ΤΕΚΑ_Εργοδ: float
    Σύνολο_Εισφ: float
    ΦΜΥ: float
    Καθαρές: float
    Τακτικές_Αποδ: float
    Υπερωρίες: float
    Δώρο_Πάσχα: float
    Δώρο_Χριστουγέννων: float
    Επίδομα_Άδειας: float
    Λοιπά_Αποδ: float
    Σύνολο_Αποδ: float
    ΟΠΣΚΕ: float

# --- 4. ΣΥΝΑΡΤΗΣΕΙΣ ΛΟΓΙΚΗΣ ---
def extract_financials_with_ai_stage3(uploaded_file, emp_name):
    API_KEY = st.secrets.get("GEMINI_API_KEY")
    if not API_KEY: return {}
    try:
        client = genai.Client(api_key=API_KEY)
        file_part = types.Part.from_bytes(data=uploaded_file.read(), mime_type=uploaded_file.type)
        prompt = f"Εξήγαγε τα οικονομικά στοιχεία για τον υπάλληλο: {emp_name}. Αν δεν βρεις το όνομα, βάλε παντού 0."
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[file_part, prompt],
            config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=PayrollFinancials)
        )
        return json.loads(response.text)
    except Exception as e:
        st.error(f"Σφάλμα AI: {e}")
        return {}

# --- 5. UI RENDER STAGE 3 ---
def render_stage_3(fin_key, emp_data, selected_month, selected_year, period, selected_afm):
    # Φόρτωση δεδομένων
    fin_cols = ["ID_Κλειδί", "ΙΚΑ_Εργ", "ΙΚΑ_Εργοδ", "ΤΕΚΑ_Εργ", "ΤΕΚΑ_Εργοδ", "Σύνολο_Εισφ", "ΦΜΥ", "Καθαρές", 
                "Τακτικές_Αποδ", "Υπερωρίες", "Δώρο_Πάσχα", "Δώρο_Χριστουγέννων", "Επίδομα_Άδειας", "Λοιπά_Αποδ", "Σύνολο_Αποδ", "ΟΠΣΚΕ"]
    fin_df = load_data(FINANCIALS_FILE, fin_cols)
    for col in fin_cols:
        if col not in fin_df.columns: fin_df[col] = 0.0
    ext_fin = fin_df[fin_df['ID_Κλειδί'] == fin_key]
    d = {k: (float(ext_fin[k].iloc[0]) if not ext_fin.empty and k in ext_fin.columns else 0.0) for k in fin_cols}

    st.subheader("📊 Κατηγορίες Αποδοχών")
    t1, t2, t3, t4, t5 = st.tabs(["Τακτικές", "Επίδομα Αδείας", "Δώρο Πάσχα", "Δώρο Χριστουγέννων", "Υπερωρίες/Λοιπά"])
    
    with t1: v_tak = st.number_input("Τακτικές (€)", value=d["Τακτικές_Αποδ"], format="%.2f")
    with t2: v_ad  = st.number_input("Επίδομα Αδείας (€)", value=d["Επίδομα_Άδειας"], format="%.2f")
    with t3: v_pas = st.number_input("Δώρο Πάσχα (€)", value=d["Δώρο_Πάσχα"], format="%.2f")
    with t4: v_xri = st.number_input("Δώρο Χριστουγέννων (€)", value=d["Δώρο_Χριστουγέννων"], format="%.2f")
    with t5: 
        v_ype = st.number_input("Υπερωρίες (€)", value=d["Υπερωρίες"], format="%.2f")
        v_loi = st.number_input("Λοιπά/Bonus (€)", value=d["Λοιπά_Αποδ"], format="%.2f")

    st.divider()
    st.subheader("📉 Στοιχεία Εισφορών & Φόρων")
    c1, c2, c3, c4 = st.columns(4)
    v_ika_e = c1.number_input("ΙΚΑ Εργαζ.", value=d["ΙΚΑ_Εργ"], format="%.2f")
    v_ika_o = c2.number_input("ΙΚΑ Εργοδ.", value=d["ΙΚΑ_Εργοδ"], format="%.2f")
    v_tek_e = c3.number_input("ΤΕΚΑ Εργαζ.", value=d["ΤΕΚΑ_Εργ"], format="%.2f")
    v_tek_o = c4.number_input("ΤΕΚΑ Εργοδ.", value=d["ΤΕΚΑ_Εργοδ"], format="%.2f")
    
    c5, c6, c7, c8 = st.columns(4)
    v_sum_e = c5.number_input("Σύνολο Εισφορών", value=d["Σύνολο_Εισφ"], format="%.2f")
    v_fmy   = c6.number_input("ΦΜΥ", value=d["ΦΜΥ"], format="%.2f")
    v_net   = c7.number_input("Καθαρές", value=d["Καθαρές"], format="%.2f")
    
    total_mix = v_tak + v_ad + v_pas + v_xri + v_ype + v_loi
    c8.metric("Σύνολο Μικτών", f"{total_mix:,.2f} €")
    
    v_ops = st.number_input("Αιτούμενο ΟΠΣΚΕ", value=d["ΟΠΣΚΕ"], format="%.2f")

    if st.button("💾 Αποθήκευση"):
        row = {"ID_Κλειδί": fin_key, "ΙΚΑ_Εργ": v_ika_e, "ΙΚΑ_Εργοδ": v_ika_o, "ΤΕΚΑ_Εργ": v_tek_e, "ΤΕΚΑ_Εργοδ": v_tek_o, 
               "Σύνολο_Εισφ": v_sum_e, "ΦΜΥ": v_fmy, "Καθαρές": v_net, "Τακτικές_Αποδ": v_tak, "Υπερωρίες": v_ype, 
               "Δώρο_Πάσχα": v_pas, "Δώρο_Χριστουγέννων": v_xri, "Επίδομα_Άδειας": v_ad, "Λοιπά_Αποδ": v_loi, 
               "Σύνολο_Αποδ": total_mix, "ΟΠΣΚΕ": v_ops}
        fin_df = pd.concat([fin_df[fin_df['ID_Κλειδί'] != fin_key], pd.DataFrame([row])], ignore_index=True)
        save_to_csv(fin_df, FINANCIALS_FILE)
        st.success("Αποθηκεύτηκε!")

# --- 6. ΚΥΡΙΟ ΠΡΟΓΡΑΜΜΑ ---
# (Εδώ παραμένει η λογική του sidebar και η επιλογή σελίδας όπως την είχαμε)
# ... [Το υπόλοιπο κομμάτι του κώδικα για το sidebar και την πλοήγηση παραμένει ίδιο] ...
