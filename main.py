import streamlit as st
import pandas as pd
import os
import json
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# --- 1. ΡΥΘΜΙΣΗ ΣΕΛΙΔΑΣ ---
st.set_page_config(
    page_title="Payroll Verifier Pro",
    page_icon="🛡️",
    layout="wide"
)

# --- 2. ΟΡΙΣΜΟΣ ΑΡΧΕΙΩΝ ΔΕΔΟΜΕΝΩΝ ---
PROJECTS_FILE = 'data_projects.csv'
CHECKLIST_FILE = 'checklist_results.csv'
EMPLOYEES_FILE = 'data_employees.csv'
FINANCIALS_FILE = 'payroll_financials.csv'
PAYROLL_CHECKS_FILE = 'payroll_checks.csv'

# --- 3. ΣΥΝΑΡΤΗΣΕΙΣ ΔΙΑΧΕΙΡΙΣΗΣ ΔΕΔΟΜΕΝΩΝ ---
def load_data(filename, columns):
    if not os.path.isfile(filename) or os.path.getsize(filename) == 0:
        return pd.DataFrame(columns=columns)
    try:
        return pd.read_csv(filename)
    except Exception:
        return pd.DataFrame(columns=columns)

def save_to_csv(df, filename):
    df.to_csv(filename, index=False, encoding='utf-8-sig')

# --- 4. ΣΤΑΔΙΟ 3: ΜΙΣΘΟΔΟΣΙΑ ΥΠΑΛΛΗΛΩΝ ---
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

def render_stage_3(fin_key, emp_data, selected_month, selected_year, period, selected_afm):
    fin_cols = ["ID_Κλειδί", "ΙΚΑ_Εργ", "ΙΚΑ_Εργοδ", "ΤΕΚΑ_Εργ", "ΤΕΚΑ_Εργοδ", "Σύνολο_Εισφ", "ΦΜΥ", "Καθαρές", 
                "Τακτικές_Αποδ", "Υπερωρίες", "Δώρο_Πάσχα", "Δώρο_Χριστουγέννων", "Επίδομα_Άδειας", "Λοιπά_Αποδ", "Σύνολο_Αποδ", "ΟΠΣΚΕ"]
    fin_df = load_data(FINANCIALS_FILE, fin_cols)
    ext_fin = fin_df[fin_df['ID_Κλειδί'] == fin_key]
    
    d = {k: (float(ext_fin[k].iloc[0]) if not ext_fin.empty and k in ext_fin.columns else 0.0) for k in fin_cols}

    st.subheader("📊 Κατηγορίες Αποδοχών")
    t1, t2, t3, t4 = st.tabs(["Τακτικές", "Επίδομα Αδείας", "Δώρο Πάσχα", "Δώρο Χριστουγέννων"])
    
    with t1: v_tak_ap = st.number_input("Ποσό Τακτικών (€)", value=d["Τακτικές_Αποδ"], format="%.2f", key=f"tak_{fin_key}")
    with t2: v_epidoma_ad = st.number_input("Ποσό Επιδόματος Αδείας (€)", value=d["Επίδομα_Άδειας"], format="%.2f", key=f"ad_{fin_key}")
    with t3: v_doro_pasxa = st.number_input("Ποσό Δώρου Πάσχα (€)", value=d["Δώρο_Πάσχα"], format="%.2f", key=f"pas_{fin_key}")
    with t4: v_doro_xrist = st.number_input("Ποσό Δώρου Χριστουγέννων (€)", value=d["Δώρο_Χριστουγέννων"], format="%.2f", key=f"xri_{fin_key}")
    
    st.divider()
    st.subheader("📉 Στοιχεία Εισφορών & Φόρων")
    c1, c2, c3, c4 = st.columns(4)
    v_ika_erg = c1.number_input("ΙΚΑ Εργαζ.", value=d["ΙΚΑ_Εργ"], format="%.2f", key=f"ikae_{fin_key}")
    v_ika_ergo = c2.number_input("ΙΚΑ Εργοδ.", value=d["ΙΚΑ_Εργοδ"], format="%.2f", key=f"ikao_{fin_key}")
    v_teka_erg = c3.number_input("ΤΕΚΑ Εργαζ.", value=d["ΤΕΚΑ_Εργ"], format="%.2f", key=f"tekae_{fin_key}")
    v_teka_ergo = c4.number_input("ΤΕΚΑ Εργοδ.", value=d["ΤΕΚΑ_Εργοδ"], format="%.2f", key=f"tekao_{fin_key}")
    
    v_sum_eisf = st.number_input("Σύνολο Εισφορών", value=d["Σύνολο_Εισφ"], format="%.2f", key=f"seisf_{fin_key}")
    v_fmy = st.number_input("ΦΜΥ", value=d["ΦΜΥ"], format="%.2f", key=f"fmy_{fin_key}")
    v_net = st.number_input("Καθαρές Αποδοχές", value=d["Καθαρές"], format="%.2f", key=f"net_{fin_key}")
    v_opske = st.number_input("Αιτούμενο ΟΠΣΚΕ", value=d["ΟΠΣΚΕ"], format="%.2f", key=f"opske_{fin_key}")

    if st.button("💾 Αποθήκευση Όλων", key=f"save_{fin_key}"):
        fin_row = {"ID_Κλειδί": fin_key, "ΙΚΑ_Εργ": v_ika_erg, "ΙΚΑ_Εργοδ": v_ika_ergo, "ΤΕΚΑ_Εργ": v_teka_erg, 
                   "ΤΕΚΑ_Εργοδ": v_teka_ergo, "Σύνολο_Εισφ": v_sum_eisf, "ΦΜΥ": v_fmy, "Καθαρές": v_net, 
                   "Τακτικές_Αποδ": v_tak_ap, "Υπερωρίες": 0.0, "Δώρο_Πάσχα": v_doro_pasxa, 
                   "Δώρο_Χριστουγέννων": v_doro_xrist, "Επίδομα_Άδειας": v_epidoma_ad, "Λοιπά_Αποδ": 0.0, 
                   "Σύνολο_Αποδ": v_tak_ap + v_epidoma_ad + v_doro_pasxa + v_doro_xrist, "ΟΠΣΚΕ": v_opske}
        fin_df = pd.concat([fin_df[fin_df['ID_Κλειδί'] != fin_key], pd.DataFrame([fin_row])], ignore_index=True)
        save_to_csv(fin_df, FINANCIALS_FILE)
        st.success("✅ Αποθηκεύτηκε!")
        st.rerun()

# --- 5. ΠΛΕΥΡΙΚΟ ΜΕΝΟΥ ---
st.sidebar.title("📑 Μενού Διαχείρισης")
page = st.sidebar.radio("Μετάβαση σε:", ["1. Διαχείριση Έργων", "2. Checklist ανά Έργο", "3. Μισθοδοσία Υπαλλήλων"])

if page == "3. Μισθοδοσία Υπαλλήλων":
    st.header("👤 Έλεγχος Μισθοδοσίας Υπαλλήλων")
    projects_df = load_data(PROJECTS_FILE, ["Επωνυμία", "ΑΦΜ"])
    if projects_df.empty:
        st.error("⚠️ Καταχωρήστε επιχείρηση στο 'Στάδιο 1'.")
    else:
        selected_project_name = st.selectbox("Επιλέξτε Επιχείρηση:", projects_df['Επωνυμία'])
        
        # Sidebar Υπαλλήλων
        st.sidebar.markdown("---")
        emp_df = load_data(EMPLOYEES_FILE, ["ID", "Ονοματεπώνυμο", "ΑΦΜ", "ΑΜΚΑ"])
        
        with st.sidebar.expander("➕ Προσθήκη Υπαλλήλου"):
            with st.form("add_emp"):
                n_name = st.text_input("Ονοματεπώνυμο")
                n_afm = st.text_input("ΑΦΜ")
                n_amka = st.text_input("ΑΜΚΑ")
                if st.form_submit_button("Προσθήκη"):
                    new_row = pd.DataFrame([{"ID": f"EMP_{n_amka}", "Ονοματεπώνυμο": n_name, "ΑΦΜ": n_afm, "ΑΜΚΑ": n_amka}])
                    save_to_csv(pd.concat([emp_df, new_row]), EMPLOYEES_FILE)
                    st.rerun()
        
        if not emp_df.empty:
            emp_options = {f"{r['Ονοματεπώνυμο']} (ΑΜΚΑ: {r['ΑΜΚΑ']})": r for _, r in emp_df.iterrows()}
            s_emp_label = st.sidebar.selectbox("Επιλέξτε Υπάλληλο:", list(emp_options.keys()))
            emp_data = emp_options[s_emp_label]
            
            s_month = st.sidebar.selectbox("Μήνας:", ["Ιανουάριος", "Φεβρουάριος", "Μάρτιος", "Απρίλιος", "Μάιος", "Ιούνιος", "Ιούλιος", "Αύγουστος", "Σεπτέμβριος", "Οκτώβριος", "Νοέμβριος", "Δεκέμβριος"], index=4)
            s_year = st.sidebar.number_input("Έτος:", value=2026)
            
            render_stage_3(f"{emp_data['ID']}_{s_month}_{s_year}", emp_data, s_month, s_year, f"{s_month} {s_year}", "000000000")
        else:
            st.warning("⚠️ Δεν υπάρχουν υπάλληλοι.")
