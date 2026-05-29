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
PAYROLL_CHECKS_FILE = 'payroll_checks.csv'

def load_data(filename, columns):
    if not os.path.isfile(filename) or os.path.getsize(filename) == 0:
        return pd.DataFrame(columns=columns)
    return pd.read_csv(filename)

def save_to_csv(df, filename):
    df.to_csv(filename, index=False, encoding='utf-8-sig')

# --- 3. ΣΤΑΔΙΟ 3: ΜΙΣΘΟΔΟΣΙΑ (RENDER) ---
def render_stage_3(fin_key, emp_data, selected_month, selected_year, period, selected_afm):
    # Φόρτωση
    fin_cols = ["ID_Κλειδί", "ΙΚΑ_Εργ", "ΙΚΑ_Εργοδ", "ΤΕΚΑ_Εργ", "ΤΕΚΑ_Εργοδ", "Σύνολο_Εισφ", "ΦΜΥ", "Καθαρές", 
                "Τακτικές_Αποδ", "Υπερωρίες", "Δώρο_Πάσχα", "Δώρο_Χριστουγέννων", "Επίδομα_Άδειας", "Λοιπά_Αποδ", "Σύνολο_Αποδ", "ΟΠΣΚΕ"]
    fin_df = load_data(FINANCIALS_FILE, fin_cols)
    ext_fin = fin_df[fin_df['ID_Κλειδί'] == fin_key]
    d = {k: (float(ext_fin[k].iloc[0]) if not ext_fin.empty and k in ext_fin.columns else 0.0) for k in fin_cols}

    # Tabs Αποδοχών
    st.subheader("📊 Κατηγορίες Αποδοχών")
    t1, t2, t3, t4 = st.tabs(["Τακτικές Αποδοχές", "Επίδομα Αδείας", "Δώρο Πάσχα", "Δώρο Χριστουγέννων"])
    
    with t1: v_tak = st.number_input("Ποσό (€)", value=d["Τακτικές_Αποδ"], format="%.2f", key=f"tak_{fin_key}")
    with t2: v_ad  = st.number_input("Ποσό (€)", value=d["Επίδομα_Άδειας"], format="%.2f", key=f"ad_{fin_key}")
    with t3: v_pas = st.number_input("Ποσό (€)", value=d["Δώρο_Πάσχα"], format="%.2f", key=f"pas_{fin_key}")
    with t4: v_xri = st.number_input("Ποσό (€)", value=d["Δώρο_Χριστουγέννων"], format="%.2f", key=f"xri_{fin_key}")

    # Σταθερά Πεδία
    st.markdown("<hr>", unsafe_allow_html=True)
    st.subheader("📉 Στοιχεία Εισφορών & Φόρων")
    c1, c2, c3, c4 = st.columns(4)
    v_ika_e = c1.number_input("ΙΚΑ Εργαζ.", value=d["ΙΚΑ_Εργ"], format="%.2f", key=f"ie_{fin_key}")
    v_ika_o = c2.number_input("ΙΚΑ Εργοδ.", value=d["ΙΚΑ_Εργοδ"], format="%.2f", key=f"io_{fin_key}")
    v_tek_e = c3.number_input("ΤΕΚΑ Εργαζ.", value=d["ΤΕΚΑ_Εργ"], format="%.2f", key=f"te_{fin_key}")
    v_tek_o = c4.number_input("ΤΕΚΑ Εργοδ.", value=d["ΤΕΚΑ_Εργοδ"], format="%.2f", key=f"to_{fin_key}")
    
    c5, c6, c7, c8 = st.columns(4)
    v_sum_e = c5.number_input("Σύνολο Εισφορών", value=d["Σύνολο_Εισφ"], format="%.2f", key=f"se_{fin_key}")
    v_fmy   = c6.number_input("ΦΜΥ", value=d["ΦΜΥ"], format="%.2f", key=f"fmy_{fin_key}")
    v_net   = c7.number_input("Καθαρές", value=d["Καθαρές"], format="%.2f", key=f"net_{fin_key}")
    
    total_mix = v_tak + v_ad + v_pas + v_xri
    c8.metric("Σύνολο Μικτών", f"{total_mix:,.2f} €")
    
    v_ops = st.number_input("Αιτούμενο ΟΠΣΚΕ", value=d["ΟΠΣΚΕ"], format="%.2f", key=f"ops_{fin_key}")

    if st.button("💾 Αποθήκευση Όλων", key=f"save_{fin_key}"):
        row = {"ID_Κλειδί": fin_key, "ΙΚΑ_Εργ": v_ika_e, "ΙΚΑ_Εργοδ": v_ika_o, "ΤΕΚΑ_Εργ": v_tek_e, "ΤΕΚΑ_Εργοδ": v_tek_o, 
               "Σύνολο_Εισφ": v_sum_e, "ΦΜΥ": v_fmy, "Καθαρές": v_net, "Τακτικές_Αποδ": v_tak, "Επίδομα_Άδειας": v_ad, 
               "Δώρο_Πάσχα": v_pas, "Δώρο_Χριστουγέννων": v_xri, "Σύνολο_Αποδ": total_mix, "ΟΠΣΚΕ": v_ops}
        fin_df = pd.concat([fin_df[fin_df['ID_Κλειδί'] != fin_key], pd.DataFrame([row])], ignore_index=True)
        save_to_csv(fin_df, FINANCIALS_FILE)
        st.success("✅ Αποθηκεύτηκε!")
        st.rerun()

# --- 4. MAIN NAVIGATION ---
st.sidebar.title("📑 Μενού")
page = st.sidebar.radio("Μετάβαση σε:", ["1. Διαχείριση Έργων", "2. Checklist", "3. Μισθοδοσία Υπαλλήλων"])

if page == "3. Μισθοδοσία Υπαλλήλων":
    # (Εδώ τοποθετείς τον κώδικα για την επιλογή υπαλλήλου/μήνα που είχες)
    # Και στο τέλος της if-else δομής καλείς:
    # render_stage_3(...)
    pass
