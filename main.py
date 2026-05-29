import streamlit as st
import pandas as pd
import os
import json
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# --- 1. ΡΥΘΜΙΣΗ ΣΕΛΙΔΑΣ ---
st.set_page_config(page_title="Payroll Verifier Pro", page_icon="🛡️", layout="wide")

# --- 2. ΑΡΧΕΙΑ ---
PROJECTS_FILE = 'data_projects.csv'
CHECKLIST_FILE = 'checklist_results.csv'
EMPLOYEES_FILE = 'data_employees.csv'
FINANCIALS_FILE = 'payroll_financials.csv'

def load_data(filename, columns):
    # Ελέγχουμε αν το αρχείο υπάρχει ΚΑΙ αν έχει περιεχόμενο (μέγεθος > 0)
    if not os.path.isfile(filename) or os.path.getsize(filename) == 0:
        return pd.DataFrame(columns=columns)
    
    try:
        df = pd.read_csv(filename)
        # Αν το αρχείο έχει περιεχόμενο αλλά είναι κατεστραμμένο, επιστρέφουμε κενό df
        if df.empty:
            return pd.DataFrame(columns=columns)
        return df
    except Exception:
        # Αν υπάρξει οποιοδήποτε άλλο πρόβλημα, επιστρέφουμε κενό df για να συνεχίσει το app
        return pd.DataFrame(columns=columns)

def save_to_csv(df, filename):
    df.to_csv(filename, index=False, encoding='utf-8-sig')

# --- 3. ΣΥΝΑΡΤΗΣΗ ΕΜΦΑΝΙΣΗΣ ΜΙΣΘΟΔΟΣΙΑΣ (STAGE 3 UI) ---
def render_stage_3(fin_key, emp_data, selected_month, selected_year, selected_afm):
    fin_cols = ["ID_Κλειδί", "ΙΚΑ_Εργ", "ΙΚΑ_Εργοδ", "Καθαρές", "Τακτικές_Αποδ", "Σύνολο_Αποδ", "ΟΠΣΚΕ"]
    fin_df = load_data(FINANCIALS_FILE, fin_cols)
    ext_fin = fin_df[fin_df['ID_Κλειδί'] == fin_key]
    d = {k: (float(ext_fin[k].iloc[0]) if not ext_fin.empty and k in ext_fin.columns else 0.0) for k in fin_cols}

    st.subheader(f"📊 Στοιχεία για: {emp_data['Ονοματεπώνυμο']}")
    
    col1, col2 = st.columns(2)
    with col1:
        v_tak = st.number_input("Τακτικές Αποδοχές", value=d["Τακτικές_Αποδ"], key=f"tak_{fin_key}")
        v_net = st.number_input("Καθαρές", value=d["Καθαρές"], key=f"net_{fin_key}")
    with col2:
        v_ika_e = st.number_input("ΙΚΑ Εργ.", value=d["ΙΚΑ_Εργ"], key=f"ie_{fin_key}")
        v_ops = st.number_input("ΟΠΣΚΕ", value=d["ΟΠΣΚΕ"], key=f"ops_{fin_key}")

    if st.button("💾 Αποθήκευση", key=f"save_{fin_key}"):
        row = {"ID_Κλειδί": fin_key, "ΙΚΑ_Εργ": v_ika_e, "Καθαρές": v_net, "Τακτικές_Αποδ": v_tak, "ΟΠΣΚΕ": v_ops}
        fin_df = pd.concat([fin_df[fin_df['ID_Κλειδί'] != fin_key], pd.DataFrame([row])], ignore_index=True)
        save_to_csv(fin_df, FINANCIALS_FILE)
        st.success("✅ Αποθηκεύτηκε!")
        st.rerun()

# --- 4. MAIN NAVIGATION ---
st.sidebar.title("📑 Μενού")
page = st.sidebar.radio("Επιλογή:", ["1. Διαχείριση Έργων", "2. Checklist", "3. Μισθοδοσία"])

# --- ΣΤΑΔΙΟ 1 ---
if page == "1. Διαχείριση Έργων":
    st.header("🏢 Διαχείριση Επιχειρήσεων")
    # (Εδώ ο κώδικας για projects)
    df = load_data(PROJECTS_FILE, ["Επωνυμία", "ΑΦΜ"])
    st.dataframe(df)

# --- ΣΤΑΔΙΟ 2 ---
elif page == "2. Checklist":
    st.header("📂 Checklist ανά Έργο")
    # (Εδώ ο κώδικας για checklist)

# --- ΣΤΑΔΙΟ 3 ---
elif page == "3. Μισθοδοσία":
    st.header("👤 Μισθοδοσία Υπαλλήλων")
    projects = load_data(PROJECTS_FILE, ["Επωνυμία", "ΑΦΜ"])
    if projects.empty:
        st.error("⚠️ Πρώτα πρόσθεσε έργο.")
    else:
        proj = st.selectbox("Επιλογή Έργου:", projects['Επωνυμία'])
        
        # Sidebar επιλογές
        st.sidebar.markdown("---")
        emp_df = load_data(EMPLOYEES_FILE, ["ID", "Ονοματεπώνυμο", "ΑΦΜ", "ΑΜΚΑ"])
        if not emp_df.empty:
            emp_choice = st.sidebar.selectbox("Υπάλληλος:", emp_df['Ονοματεπώνυμο'])
            emp_data = emp_df[emp_df['Ονοματεπώνυμο'] == emp_choice].iloc[0]
            month = st.sidebar.selectbox("Μήνας:", ["Ιανουάριος", "Φεβρουάριος"])
            
            # Κλήση της συνάρτησης UI που θα εμφανιστεί στο ΚΕΝΤΡΟ της οθόνης
            render_stage_3(f"{emp_data['ID']}_{month}", emp_data, month, 2026, "000000000")
        else:
            st.warning("⚠️ Πρόσθεσε υπαλλήλους.")
