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

# --- 4. ΣΤΑΔΙΟ 3: ΜΙΣΘΟΔΟΣΙΑ ΥΠΑΛΛΗΛΩΝ (ΑΝΑΝΕΩΜΕΝΟ SCHEMA) ---
class PayrollFinancials(BaseModel):
    ΙΚΑ_Εργ: float = Field(description="Οι κρατήσεις ή εισφορές του ασφαλισμένου/εργαζομένου για το κύριο ταμείο (ΙΚΑ/ΕΦΚΑ).")
    ΙΚΑ_Εργοδ: float = Field(description="Οι εισφορές του εργοδότη για το κύριο ταμείο (ΙΚΑ/ΕΦΚΑ).")
    ΤΕΚΑ_Εργ: float = Field(description="Οι κρατήσεις του εργαζομένου για το ΤΕΚΑ. Αν δεν υπάρχει, βάλε 0.0.")
    ΤΕΚΑ_Εργοδ: float = Field(description="Οι εισφορές του εργοδότη για το ΤΕΚΑ. Αν δεν υπάρχει, βάλε 0.0.")
    Σύνολο_Εισφ: float = Field(description="Το άθροισμα όλων των ασφαλιστικών κρατήσεων/εισφορών.")
    ΦΜΥ: float = Field(description="Ο Φόρος Μισθωτών Υπηρεσιών (Φ.Μ.Υ.). Αν δεν υπάρχει, βάλε 0.0.")
    Καθαρές: float = Field(description="Το τελικό πληρωτέο ποσό στον εργαζόμενο (Καθαρές Αποδοχές).")
    Τακτικές_Αποδ: float = Field(description="Οι βασικές/τακτικές μικρές αποδοχές του υπαλλήλου.")
    Υπερωρίες: float = Field(description="Αμοιβή για υπερωρίες ή υπερεργασία. Αν δεν υπάρχει, βάλε 0.0.")
    Λοιπά_Αποδ: float = Field(description="Λοιπά επιδόματα, bonus ή αναδρομικά. Αν δεν υπάρχει, βάλε 0.0.")
    Σύνολο_Αποδ: float = Field(description="Το συνολικό μικτό ποσό (Άθροισμα Τακτικών, Υπερωριών και Λοιπών).")
    ΟΠΣΚΕ: float = Field(description="Αιτούμενο ποσό ΟΠΣΚΕ. Αν δεν προκύπτει αυτόματα, βάλε 0.0.")

def extract_financials_with_ai_stage3(uploaded_file, emp_name):
    """Συνάρτηση AI OCR που αναλύει το έγγραφο μέσω του Gemini API και επιστρέφει δομημένο JSON"""
    API_KEY = st.secrets.get("GEMINI_API_KEY")
    if not API_KEY:
        st.error("🔑 Παρακαλώ ορίστε το Google Gemini API Key στα Secrets.")
        return {}

    try:
        client = genai.Client(api_key=API_KEY)
        file_bytes = uploaded_file.read()
        mime_type = uploaded_file.type
        
        file_part = types.Part.from_bytes(
            data=file_bytes,
            mime_type=mime_type,
        )

        prompt = f"""
        Είσαι ένας σχολαστικός Έλληνας λογιστής και ορκωτός ελεγκτής μισθοδοσίας. 
        Σου δίνεται ένα έγγραφο μισθοδοσίας. 
        
        Ο Στόχος σου είναι να εντοπίσεις και να εξάγεις τα οικονομικά στοιχεία ΑΠΟΚΛΕΙΣΤΙΚΑ ΚΑΙ ΜΟΝΟ για τον εξής υπάλληλο:
        👉 ΥΠΑΛΛΗΛΟΣ ΠΡΟΣ ΕΛΕΓΧΟ: "{emp_name}"
        
        ΑΥΣΤΗΡΟΙ ΚΑΝΟΝΕΣ:
        1. ΠΡΟΥΠΟΘΕΣΗ ΟΝΟΜΑΤΟΣ: Αν το όνομα "{emp_name}" ΔΕΝ αναγράφεται πουθενά μέσα στο έγγραφο, τότε ΜΗΝ ΕΞΑΓΕΙΣ ΚΑΝΕΝΑ ΠΟΣΟ. Βάλε παντού 0.0.
        2. ΜΟΝΟ ΑΤΟΜΙΚΑ ΣΤΟΙΧΕΙΑ: Βρες τη γραμμή ή το τμήμα που αντιστοιχεί στον "{emp_name}" και πάρε ΜΟΝΟ τα δικά του ποσά. 
        3. ΔΙΑΧΩΡΙΣΜΟΣ ΑΠΟΔΟΧΩΝ: Ξεχώρισε τις Τακτικές Αποδοχές, τις Υπερωρίες και τα Λοιπά επιδόματα αν υπάρχουν διακριτά στο έγγραφο.
        4. Το 'Καθαρές' είναι ΠΑΝΤΑ το πληρωτέο ποσό στον εργαζόμενο.
        """

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[file_part, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=PayrollFinancials,
                temperature=0.0
            ),
        )
        return json.loads(response.text)
    except Exception as e:
        st.error(f"❌ Σφάλμα κατά την επεξεργασία AI OCR: {e}")
        return {}

def render_stage_3(fin_key, emp_data, selected_month, selected_year, period, selected_afm):
    """Συνάρτηση σχεδίασης του UI για το Στάδιο 3"""
    
    # --- ΕΛΕΓΧΟΣ ΔΙΚΑΙΟΛΟΓΗΤΙΚΩΝ ---
    audit_df = load_data(PAYROLL_CHECKS_FILE, ["ID_Κλειδί", "Έγγραφο", "Κατάσταση", "Σχόλιο"])
    if not audit_df.empty:
        audit_df['Σχόλιο'] = audit_df['Σχόλιο'].fillna('').astype(str).str.replace('nan', '', case=False)
    
    all_results = []
    def draw_row(label, key_id):
        existing = audit_df[audit_df['ID_Κλειδί'] == key_id]
        c1, c2, c3 = st.columns([1.5, 1, 2], gap="small")
        c1.markdown(f"<div style='font-size:0.85rem; padding-top:5px;'>{label}</div>", unsafe_allow_html=True)
        stat = c2.selectbox("", ["Έλλειψη ❌", "Υπάρχει ✅", "Δεν απαιτείται"], index=["Έλλειψη ❌", "Υπάρχει ✅", "Δεν απαιτείται"].index(existing['Κατάσταση'].iloc[0]) if not existing.empty else 0, key=f"s_{key_id}", label_visibility="collapsed")
        
        val_note = existing['Σχόλιο'].iloc[0] if not existing.empty else ""
        if val_note.lower() == 'nan':
            val_note = ""
            
        note = c3.text_input("", value=val_note, key=f"n_{key_id}", label_visibility="collapsed", placeholder="Σχόλιο...")
        return {"ID_Κλειδί": key_id, "Έγγραφο": label, "Κατάσταση": stat, "Σχόλιο": note}

    st.caption("📌 ΚΕΝΤΡΙΚΑ ΔΙΚΑΙΟΛΟΓΗΤΙΚΑ")
    all_results.append(draw_row("Αναγγελία Πρόσληψης (Ε3)", f"PERM_{selected_afm}_{emp_data['ΑΦΜ']}_E3"))
    all_results.append(draw_row("Ταυτότητα Εργαζομένου", f"PERM_{selected_afm}_{emp_data['ΑΦΜ']}_ID"))
    st.caption(f"📅 ΜΗΝΙΑΙΑ ΠΑΡΑΔΟΤΕΑ ({period})")
    for md in ["Extrait", "Έμβασμα Πληρωμής", "Λογιστικό άρθρο καταχώρησης", "Λογιστικό άρθρο πληρωμής", "Βιβλίο εσόδων-εξόδων"]:
        all_results.append(draw_row(md, f"MONTH_{selected_afm}_{emp_data['ΑΦΜ']}_{period}_{md}"))

    # --- ΟΙΚΟΝΟΜΙΚΑ ΣΤΟΙΧΕΙΑ & AI OCR ---
    st.markdown("<hr style='margin:15px 0;'>", unsafe_allow_html=True)
    st.subheader("💰 Οικονομικά Στοιχεία")
    
    uploaded_file = st.file_uploader("📂 Μεταφορτώστε τη Μισθοδοτική", type=['png', 'jpg', 'jpeg', 'pdf'], key=f"up_{fin_key}")
    
    # Προσθήκη των νέων στηλών στη λίστα φορτώματος
    fin_cols = ["ID_Κλειδί", "ΙΚΑ_Εργ", "ΙΚΑ_Εργοδ", "ΤΕΚΑ_Εργ", "ΤΕΚΑ_Εργοδ", "Σύνολο_Εισφ", "ΦΜΥ", "Καθαρές", "Τακτικές_Αποδ", "Υπερωρίες", "Λοιπά_Αποδ", "Σύνολο_Αποδ", "ΟΠΣΚΕ"]
    fin_df = load_data(FINANCIALS_FILE, fin_cols)
    ext_fin = fin_df[fin_df['ID_Κλειδί'] == fin_key]
    
    default_values = {k: (float(ext_fin[k].iloc[0]) if not ext_fin.empty and k in ext_fin.columns else 0.0) for k in fin_cols if k != "ID_Κλειδί"}
    
    if uploaded_file is not None:
        file_fingerprint = f"{uploaded_file.name}_{uploaded_file.size}"
        trigger_key = f"ocr_data_{fin_key}_{file_fingerprint}"
        
        if st.button("🤖 Έναρξη Ανάλυσης AI", type="primary", use_container_width=True):
            with st.spinner("⏳ Το AI μελετά το έγγραφο μισθοδοσίας..."):
                ocr_data = extract_financials_with_ai_stage3(uploaded_file, emp_data['Ονοματεπώνυμο'])
                if ocr_data:
                    st.session_state[trigger_key] = ocr_data
                    st.success("🎯 Η ανάλυση ολοκληρώθηκε!")
        
        if trigger_key in st.session_state:
            for k, v in st.session_state[trigger_key].items():
                if k in default_values:
                    default_values[k] = v

    c1, c2 = st.columns(2)
    v_ika_erg = c1.number_input("Εισφορές Εργαζομένου ΙΚΑ", value=default_values["ΙΚΑ_Εργ"], format="%.2f")
    v_ika_ergo = c2.number_input("Εισφορές Εργοδότη ΙΚΑ", value=default_values["ΙΚΑ_Εργοδ"], format="%.2f")
    
    c3, c4 = st.columns(2)
    v_teka_erg = c3.number_input("Εισφορές Εργαζομένου ΤΕΚΑ", value=default_values["ΤΕΚΑ_Εργ"], format="%.2f")
    v_teka_ergo = c4.number_input("Εισφορές Εργοδότη ΤΕΚΑ", value=default_values["ΤΕΚΑ_Εργοδ"], format="%.2f")
    
    c5, c6, c7 = st.columns(3)
    v_sum_eisf = c5.number_input("Σύνολο Εισφορών", value=default_values["Σύνολο_Εισφ"], format="%.2f")
    v_fmy = c6.number_input("ΦΜΥ Εργαζομένου", value=default_values["ΦΜΥ"], format="%.2f")
    v_net = c7.number_input("Καθαρές Αποδοχές", value=default_values["Καθαρές"], format="%.2f")
    
    # --- ΝΕΟ: ΔΙΑΧΩΡΙΣΜΟΣ ΑΠΟΔΟΧΩΝ ΣΤΟ UI ---
    st.markdown("<p style='font-size:0.9rem; color:#666; margin-bottom:2px;'>Ανάλυση Αποδοχών</p>", unsafe_allow_html=True)
    col_ap1, col_ap2, col_ap3 = st.columns(3)
    v_tak_ap = col_ap1.number_input("Τακτικές Αποδοχές", value=default_values["Τακτικές_Αποδ"], format="%.2f")
    v_yp_ap = col_ap2.number_input("Υπερωρίες / Υπερεργασία", value=default_values["Υπερωρίες"], format="%.2f")
    v_loip_ap = col_ap3.number_input("Λοιπά Επιδόματα / Bonus", value=default_values["Λοιπά_Αποδ"], format="%.2f")
    
    # Το Σύνολο Αποδοχών υπολογίζεται αυτόματα από το άθροισμα των 3 παραπάνω
    v_total_ap = v_tak_ap + v_yp_ap + v_loip_ap
    
    c8, c9, c10 = st.columns(3)
    c8.number_input("Σύνολο Αποδοχών (Μικτά)", value=v_total_ap, format="%.2f", disabled=True, help="Υπολογίζεται αυτόματα ως άθροισμα των Τακτικών, Υπερωριών και Λοιπών.")
    v_opske = c9.number_input("Αιτούμενο ΟΠΣΚΕ", value=default_values["ΟΠΣΚΕ"], format="%.2f")
    
    calc_total = v_net + v_sum_eisf + v_fmy
    c10.markdown(f"<div style='background-color:#e8f5e9; padding:10px; border-radius:5px; border:1px solid #4caf50; text-align:center; margin-top:15px;'><small>Έλεγχος Αθροίσματος</small><br><b>{calc_total:,.2f} €</b></div>", unsafe_allow_html=True)

    if st.button("💾 Αποθήκευση Όλων", use_container_width=True):
        new_ks = [r['ID_Κλειδί'] for r in all_results]
        audit_df = pd.concat([audit_df[~audit_df['ID_Κλειδί'].isin(new_ks)], pd.DataFrame(all_results)], ignore_index=True)
        save_to_csv(audit_df, PAYROLL_CHECKS_FILE)
        
        # Αποθήκευση μαζί με τις νέες στήλες αναλογίας
        fin_row = {
            "ID_Κλειδί": fin_key, "ΙΚΑ_Εργ": v_ika_erg, "ΙΚΑ_Εργοδ": v_ika_ergo, 
            "ΤΕΚΑ_Εργ": v_teka_erg, "ΤΕΚΑ_Εργοδ": v_teka_ergo, "Σύνολο_Εισφ": v_sum_eisf, 
            "ΦΜΥ": v_fmy, "Καθαρές": v_net, "Τακτικές_Αποδ": v_tak_ap, "Υπερωρίες": v_yp_ap, 
            "Λοιπά_Αποδ": v_loip_ap, "Σύνολο_Αποδ": v_total_ap, "ΟΠΣΚΕ": v_opske
        }
        fin_df = pd.concat([fin_df[fin_df['ID_Κλειδί'] != fin_key], pd.DataFrame([fin_row])], ignore_index=True)
        save_to_csv(fin_df, FINANCIALS_FILE)
        
        if 'trigger_key' in locals() and trigger_key in st.session_state:
            del st.session_state[trigger_key]
            
        st.success("✅ Τα στοιχεία αποθηκεύτηκαν!")
        st.rerun()

def render_stage_3(fin_key, emp_data, selected_month, selected_year, period, selected_afm):
    """Συνάρτηση σχεδίασης του UI για το Στάδιο 3"""
    
    # --- ΕΛΕΓΧΟΣ ΔΙΚΑΙΟΛΟΓΗΤΙΚΩΝ ---
    audit_df = load_data(PAYROLL_CHECKS_FILE, ["ID_Κλειδί", "Έγγραφο", "Κατάσταση", "Σχόλιο"])
    if not audit_df.empty:
        audit_df['Σχόλιο'] = audit_df['Σχόλιο'].fillna('').astype(str).str.replace('nan', '', case=False)
    
    all_results = []
    def draw_row(label, key_id):
        existing = audit_df[audit_df['ID_Κλειδί'] == key_id]
        c1, c2, c3 = st.columns([1.5, 1, 2], gap="small")
        c1.markdown(f"<div style='font-size:0.85rem; padding-top:5px;'>{label}</div>", unsafe_allow_html=True)
        stat = c2.selectbox("", ["Έλλειψη ❌", "Υπάρχει ✅", "Δεν απαιτείται"], index=["Έλλειψη ❌", "Υπάρχει ✅", "Δεν απαιτείται"].index(existing['Κατάσταση'].iloc[0]) if not existing.empty else 0, key=f"s_{key_id}", label_visibility="collapsed")
        
        val_note = existing['Σχόλιο'].iloc[0] if not existing.empty else ""
        if val_note.lower() == 'nan':
            val_note = ""
            
        note = c3.text_input("", value=val_note, key=f"n_{key_id}", label_visibility="collapsed", placeholder="Σχόλιο...")
        return {"ID_Κλειδί": key_id, "Έγγραφο": label, "Κατάσταση": stat, "Σχόλιο": note}

    st.caption("📌 ΚΕΝΤΡΙΚΑ ΔΙΚΑΙΟΛΟΓΗΤΙΚΑ")
    all_results.append(draw_row("Αναγγελία Πρόσληψης (Ε3)", f"PERM_{selected_afm}_{emp_data['ΑΦΜ']}_E3"))
    all_results.append(draw_row("Ταυτότητα Εργαζομένου", f"PERM_{selected_afm}_{emp_data['ΑΦΜ']}_ID"))
    st.caption(f"📅 ΜΗΝΙΑΙΑ ΠΑΡΑΔΟΤΕΑ ({period})")
    for md in ["Extrait", "Έμβασμα Πληρωμής", "Λογιστικό άρθρο καταχώρησης", "Λογιστικό άρθρο πληρωμής", "Βιβλίο εσόδων-εξόδων"]:
        all_results.append(draw_row(md, f"MONTH_{selected_afm}_{emp_data['ΑΦΜ']}_{period}_{md}"))

    # --- ΟΙΚΟΝΟΜΙΚΑ ΣΤΟΙΧΕΙΑ & AI OCR ---
    st.markdown("<hr style='margin:15px 0;'>", unsafe_allow_html=True)
    st.subheader("💰 Οικονομικά Στοιχεία")
    
    uploaded_file = st.file_uploader("📂 Μεταφορτώστε τη Μισθοδοτική", type=['png', 'jpg', 'jpeg', 'pdf'], key=f"up_{fin_key}")
    
    fin_df = load_data(FINANCIALS_FILE, ["ID_Κλειδί", "ΙΚΑ_Εργ", "ΙΚΑ_Εργοδ", "ΤΕΚΑ_Εργ", "ΤΕΚΑ_Εργοδ", "Σύνολο_Εισφ", "ΦΜΥ", "Καθαρές", "Σύνολο_Αποδ", "ΟΠΣΚΕ"])
    ext_fin = fin_df[fin_df['ID_Κλειδί'] == fin_key]
    
    default_values = {k: (float(ext_fin[k].iloc[0]) if not ext_fin.empty and k in ext_fin.columns else 0.0) for k in fin_df.columns if k != "ID_Κλειδί"}
    
    if uploaded_file is not None:
        file_fingerprint = f"{uploaded_file.name}_{uploaded_file.size}"
        trigger_key = f"ocr_data_{fin_key}_{file_fingerprint}"
        
        if st.button("🤖 Έναρξη Ανάλυσης AI", type="primary", use_container_width=True):
            with st.spinner("⏳ Το AI μελετά το έγγραφο μισθοδοσίας..."):
                ocr_data = extract_financials_with_ai_stage3(uploaded_file, emp_data['Ονοματεπώνυμο'])
                if ocr_data:
                    st.session_state[trigger_key] = ocr_data
                    st.success("🎯 Η ανάλυση ολοκληρώθηκε!")
        
        if trigger_key in st.session_state:
            for k, v in st.session_state[trigger_key].items():
                if k in default_values:
                    default_values[k] = v

    c1, c2 = st.columns(2)
    v_ika_erg = c1.number_input("Εισφορές Εργαζομένου ΙΚΑ", value=default_values["ΙΚΑ_Εργ"], format="%.2f")
    v_ika_ergo = c2.number_input("Εισφορές Εργοδότη ΙΚΑ", value=default_values["ΙΚΑ_Εργοδ"], format="%.2f")
    
    c3, c4 = st.columns(2)
    v_teka_erg = c3.number_input("Εισφορές Εργαζομένου ΤΕΚΑ", value=default_values["ΤΕΚΑ_Εργ"], format="%.2f")
    v_teka_ergo = c4.number_input("Εισφορές Εργοδότη ΤΕΚΑ", value=default_values["ΤΕΚΑ_Εργοδ"], format="%.2f")
    
    c5, c6, c7 = st.columns(3)
    v_sum_eisf = c5.number_input("Σύνολο Εισφορών", value=default_values["Σύνολο_Εισφ"], format="%.2f")
    v_fmy = c6.number_input("ΦΜΥ Εργαζομένου", value=default_values["ΦΜΥ"], format="%.2f")
    v_net = c7.number_input("Καθαρές Αποδοχές", value=default_values["Καθαρές"], format="%.2f")
    
    c8, c9, c10 = st.columns(3)
    v_total_ap = c8.number_input("Σύνολο Αποδοχών", value=default_values["Σύνολο_Αποδ"], format="%.2f")
    v_opske = c9.number_input("Αιτούμενο ΟΠΣΚΕ", value=default_values["ΟΠΣΚΕ"], format="%.2f")
    
    calc_total = v_net + v_sum_eisf + v_fmy
    c10.markdown(f"<div style='background-color:#e8f5e9; padding:10px; border-radius:5px; border:1px solid #4caf50; text-align:center; margin-top:15px;'><small>Έλεγχος Αθροίσματος</small><br><b>{calc_total:,.2f} €</b></div>", unsafe_allow_html=True)

    if st.button("💾 Αποθήκευση Όλων", use_container_width=True):
        new_ks = [r['ID_Κλειδί'] for r in all_results]
        audit_df = pd.concat([audit_df[~audit_df['ID_Κλειδί'].isin(new_ks)], pd.DataFrame(all_results)], ignore_index=True)
        save_to_csv(audit_df, PAYROLL_CHECKS_FILE)
        
        fin_row = {"ID_Κλειδί": fin_key, "ΙΚΑ_Εργ": v_ika_erg, "ΙΚΑ_Εργοδ": v_ika_ergo, "ΤΕΚΑ_Εργ": v_teka_erg, "ΤΕΚΑ_Εργοδ": v_teka_ergo, "Σύνολο_Εισφ": v_sum_eisf, "ΦΜΥ": v_fmy, "Καθαρές": v_net, "Σύνολο_Αποδ": v_total_ap, "ΟΠΣΚΕ": v_opske}
        fin_df = pd.concat([fin_df[fin_df['ID_Κλειδί'] != fin_key], pd.DataFrame([fin_row])], ignore_index=True)
        save_to_csv(fin_df, FINANCIALS_FILE)
        
        if 'trigger_key' in locals() and trigger_key in st.session_state:
            del st.session_state[trigger_key]
            
        st.success("✅ Τα στοιχεία αποθηκεύτηκαν!")
        st.rerun()

# --- 5. ΠΛΕΥΡΙΚΟ ΜΕΝΟΥ ---
st.sidebar.title("📑 Μενού Διαχείρισης")
page = st.sidebar.radio(
    "Μετάβαση σε:",
    ["1. Διαχείριση Έργων", 
     "2. Checklist ανά Έργο", 
     "3. Μισθοδοσία Υπαλλήλων"]
)

# --- ΣΤΑΔΙΟ 1: ΔΙΑΧΕΙΡΙΣΗ ΕΡΓΩΝ ---
if page == "1. Διαχείριση Έργων":
    st.header("🏢 Διαχείριση Επιχειρήσεων")
    with st.expander("➕ Προσθήκη / Επεξεργασία Έργου", expanded=True):
        with st.form("project_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Επωνυμία Επιχείρησης")
                afm = st.text_input("ΑΦΜ (9 ψηφία)", max_chars=9)
            with col2:
                mis = st.text_input("Κωδικός Έργου (MIS)")
                budget = st.number_input("Συνολικός Προϋπολογισμός (€)", min_value=0.0)
            if st.form_submit_button("💾 Αποθήκευση Στοιχείων"):
                if name and afm:
                    df = load_data(PROJECTS_FILE, ["Επωνυμία", "ΑΦΜ", "MIS", "Προϋπολογισμός"])
                    if afm in df['ΑΦΜ'].astype(str).values:
                        df.loc[df['ΑΦΜ'].astype(str) == afm, ["Επωνυμία", "MIS", "Προϋπολογισμός"]] = [name, mis, budget]
                    else:
                        new_row = pd.DataFrame([{"Επωνυμία": name, "ΑΦΜ": afm, "MIS": mis, "Προϋπολογισμός": budget}])
                        df = pd.concat([df, new_row], ignore_index=True)
                    save_to_csv(df, PROJECTS_FILE)
                    st.success("✅ Το έργο αποθηκεύτηκε!")
                    st.rerun()

    st.markdown("### 📋 Λίστα Εγγεγραμμένων Επιχειρήσεων")
    df_display = load_data(PROJECTS_FILE, ["Επωνυμία", "ΑΦΜ", "MIS", "Προϋπολογισμός"])
    if not df_display.empty:
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        with st.expander("🗑️ Διαγραφή Επιχείρησης"):
            delete_afm = st.selectbox("Επιλέξτε ΑΦΜ για διαγραφή:", df_display['ΑΦΜ'].unique())
            if st.button("Οριστική Διαγραφή", type="primary"):
                df_display = df_display[df_display['ΑΦΜ'].astype(str) != str(delete_afm)]
                save_to_csv(df_display, PROJECTS_FILE)
                st.rerun()

# --- ΣΤΑΔΙΟ 2: CHECKLIST ΑΝΑ ΕΡΓΟ ---
elif page == "2. Checklist ανά Έργο":
    st.header("📂 Γενικά Παραδοτέα Μισθοδοσίας")
    projects_df = load_data(PROJECTS_FILE, ["Επωνυμία", "ΑΦΜ"])
    if projects_df.empty:
        st.warning("⚠️ Καταχωρήστε μια επιχείρηση στο Στάδιο 1.")
    else:
        selected_name = st.selectbox("Επιλέξτε Επιχείρηση:", projects_df['Επωνυμία'])
        selected_afm = str(projects_df[projects_df['Επωνυμία'] == selected_name]['ΑΦΜ'].iloc[0]).strip()
        check_df = load_data(CHECKLIST_FILE, ["ΑΦΜ", "Εγγραφο", "Κατάσταση", "Σχόλιο"])
        
        if not check_df.empty:
            check_df['ΑΦΜ'] = check_df['ΑΦΜ'].astype(str).str.strip()
            check_df['Σχόλιο'] = check_df['Σχόλιο'].fillna('').astype(str).str.replace('nan', '', case=False)
            
        required_docs = [
            "Πίνακας Προσωπικού Ε4", "Μισθολογικές καταστάσεις", "ΑΠΔ ΕΦΚΑ", 
            "Αποδεικτικό Υποβολής ΑΠΔ", "ΑΠΔ ΤΕΚΑ", "Αποδεικτικό Υποβολής ΑΠΔ ΤΕΚΑ", 
            "Υπεύθυνη δήλωση συγγενών", "Επιστολή γνωστοποίησης", "Ασφαλιστική ενημερότητα", 
            "Οικονομική καρτέλα ΕΦΚΑ", "Ηλεκτρονική καρτέλα οφειλετών", "Πίνακας χρεών οφειλέτη", 
            "Ανάλυση κίνησης Ηλ. Καρτέλας", "Φορολογική ενημερότητα", "Στοιχεία ρυθμίσεων & Πληρωμή", 
            "Προσωρινές δηλώσεις ΦΜΥ"
        ]
        
        if f"success_{selected_afm}" in st.session_state:
            st.success(f"✅ Το checklist για την επιχείρηση '{selected_name}' αποθηκεύτηκε επιτυχώς!")
            del st.session_state[f"success_{selected_afm}"]
        
        results = []
        for doc in required_docs:
            existing = check_df[(check_df['ΑΦΜ'] == selected_afm) & (check_df['Εγγραφο'] == doc)]
            
            c1, c2, c3 = st.columns([1.5, 1.0, 2.5], gap="small")
            c1.markdown(f"<div style='font-size:0.85rem; padding-top:5px;'><b>{doc}</b></div>", unsafe_allow_html=True)
            
            status = c2.selectbox(
                "", 
                ["Έλλειψη ❌", "Υπάρχει ✅", "Δεν απαιτείται"], 
                index=["Έλλειψη ❌", "Υπάρχει ✅", "Δεν απαιτείται"].index(existing['Κατάσταση'].iloc[0]) if not existing.empty else 0, 
                key=f"gen_{selected_afm}_{doc}", 
                label_visibility="collapsed"
            )
            
            val_note = existing['Σχόλιο'].iloc[0] if not existing.empty else ""
            if val_note.lower() == 'nan':
                val_note = ""
                
            note = c3.text_input(
                "", 
                value=val_note, 
                key=f"gen_n_{selected_afm}_{doc}", 
                label_visibility="collapsed",
                placeholder="Σημειώσεις..."
            )
            
            results.append({"ΑΦΜ": selected_afm, "Εγγραφο": doc, "Κατάσταση": status, "Σχόλιο": note})
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("💾 Αποθήκευση Checklist", use_container_width=True):
            check_df = check_df[check_df['ΑΦΜ'] != selected_afm]
            save_to_csv(pd.concat([check_df, pd.DataFrame(results)], ignore_index=True), CHECKLIST_FILE)
            st.session_state[f"success_{selected_afm}"] = True
            st.rerun()

# --- ΣΤΑΔΙΟ 3: ΜΙΣΘΟΔΟΣΙΑ ΥΠΑΛΛΗΛΩΝ ---
elif page == "3. Μισθοδοσία Υπαλλήλων":
    st.header("👤 Έλεγχος Μισθοδοσίας Υπαλλήλων")
    
    # Χρειάζεται να ξέρουμε την επιλεγμένη επιχείρηση για να περάσουμε το ΑΦΜ της στη render_stage_3
    projects_df = load_data(PROJECTS_FILE, ["Επωνυμία", "ΑΦΜ"])
    if projects_df.empty:
        st.error("⚠️ Παρακαλώ καταχωρήστε τουλάχιστον μία επιχείρηση στο 'Στάδιο 1' πριν προχωρήσετε στον έλεγχο υπαλλήλων.")
    else:
        # Επιλογή επιχείρησης στο κύριο panel
        selected_project_name = st.selectbox("Επιλέξτε Επιχείρηση για τον έλεγχο:", projects_df['Επωνυμία'], key="stage3_project_select")
        selected_project_afm = str(projects_df[projects_df['Επωνυμία'] == selected_project_name]['ΑΦΜ'].iloc[0]).strip()

        # ---------------- DYNAMIC SIDEBAR FOR EMPLOYEES ----------------
        st.sidebar.markdown("---")
        st.sidebar.subheader("👥 Διαχείριση & Επιλογή Υπαλλήλων")
        
        emp_cols = ["ID", "Ονοματεπώνυμο", "ΑΦΜ", "ΑΜΚΑ"]
        emp_df = load_data(EMPLOYEES_FILE, emp_cols)
        
        if emp_df.empty or not all(col in emp_df.columns for col in emp_cols):
            emp_df = pd.DataFrame(columns=emp_cols)
        else:
            emp_df['ΑΦΜ'] = emp_df['ΑΦΜ'].astype(str).str.strip()
            emp_df['AMKA'] = emp_df['ΑΜΚΑ'].astype(str).str.strip() # Διασφάλιση συμβατότητας
        
        # 1. Φόρμα Προσθήκης Υπαλλήλου
        with st.sidebar.expander("➕ Προσθήκη Νέου Υπάλληλου"):
            with st.form("add_employee_form"):
                new_name = st.text_input("Ονοματεπώνυμο").strip()
                new_afm = st.text_input("ΑΦΜ Υπαλλήλου (9 ψηφία)", max_chars=9).strip()
                new_amka = st.text_input("ΑΜΚΑ Υπαλλήλου (11 ψηφία)", max_chars=11).strip()
                
                if st.form_submit_button("💾 Προσθήκη"):
                    if new_name and new_afm and new_amka:
                        generated_id = f"EMP_{new_amka}"
                        
                        if not emp_df.empty and new_afm in emp_df['ΑΦΜ'].values:
                            st.error(f"⚠️ Το ΑΦΜ **{new_afm}** ανήκει ήδη σε υπάλληλο!")
                        elif not emp_df.empty and new_amka in emp_df['ΑΜΚΑ'].values:
                            st.error(f"⚠️ Το ΑΜΚΑ **{new_amka}** υπάρχει ήδη!")
                        else:
                            new_emp = pd.DataFrame([{"ID": generated_id, "Ονοματεπώνυμο": new_name, "ΑΦΜ": new_afm, "ΑΜΚΑ": new_amka}])
                            emp_df = pd.concat([emp_df, new_emp], ignore_index=True)
                            save_to_csv(emp_df, EMPLOYEES_FILE)
                            st.success("🎉 Ο υπάλληλος προστέθηκε!")
                            st.rerun()
                    else:
                        st.error("❌ Συμπληρώστε όλα τα πεδία!")
                        
        # 2. Φόρμα Διαγραφής Υπαλλήλου
        if not emp_df.empty:
            with st.sidebar.expander("🗑️ Διαγραφή Υπαλλήλου"):
                delete_options = {f"{row['Ονοματεπώνυμο']} (ΑΜΚΑ: {row['ΑΜΚΑ']})": row['ID'] for _, row in emp_df.iterrows() if pd.notna(row['ΑΜΚΑ'])}
                if delete_options:
                    selected_del_label = st.selectbox("Επιλέξτε υπάλληλο για διαγραφή:", list(delete_options.keys()), key="del_emp_select")
                    target_del_id = delete_options[selected_del_label]
                    
                    if st.button("Οριστική Διαγραφή", type="primary", key="del_emp_btn"):
                        emp_df = emp_df[emp_df['ID'].astype(str) != str(target_del_id)]
                        save_to_csv(emp_df, EMPLOYEES_FILE)
                        st.success("Ο υπάλληλος διαγράφηκε!")
                        st.rerun()
                    
        st.sidebar.markdown("---")
        
        # 3. Επιλογή Υπαλλήλου & Περιόδου
        if emp_df.empty:
            st.warning("⚠️ Δεν υπάρχουν καταχωρημένοι υπάλληλοι στο σύστημα.")
        else:
            emp_options = {}
            for _, row in emp_df.iterrows():
                if pd.notna(row["Ονοματεπώνυμο"]) and pd.notna(row["ID"]):
                    display_label = f"{row['Ονοματεπώνυμο']} (ΑΜΚΑ: {row['ΑΜΚΑ']})"
                    emp_options[display_label] = {"ID": str(row["ID"]), "Ονοματεπώνυμο": str(row["Ονοματεπώνυμο"]), "ΑΦΜ": str(row["ΑΦΜ"]), "ΑΜΚΑ": str(row["ΑΜΚΑ"])}
            
            if emp_options:
                selected_emp_label = st.sidebar.selectbox("Επιλέξτε Υπάλληλο για Έλεγχο:", list(emp_options.keys()))
                emp_data = emp_options[selected_emp_label]
                
                months = ["Ιανουάριος", "Φεβρουάριος", "Μάρτιος", "Απρίλιος", "Μάιος", "Ιούνιος", "Ιούλιος", "Αύγουστος", "Σεπτέμβριος", "Οκτώβριος", "Νοέμβριος", "Δεκέμβριος"]
                selected_month = st.sidebar.selectbox("Μήνας:", months, index=4)
                selected_year = st.sidebar.number_input("Έτος:", min_value=2020, max_value=2030, value=2026)
                
                period = f"{selected_month} {selected_year}"
                fin_key = f"{emp_data['ID']}_{selected_month}_{selected_year}"
                
                st.sidebar.info(f"📋 **Στοιχεία Τρέχοντος Ελέγχου**")
                st.sidebar.text(f"🏢 Εταιρεία: {selected_project_name}")
                st.sidebar.text(f"👤 ΑΦΜ Υπαλλ.: {emp_data['ΑΦΜ']}")
                st.sidebar.text(f"🆔 ΑΜΚΑ Υπαλλ.: {emp_data['ΑΜΚΑ']}")
                st.sidebar.text(f"📅 Περίοδος: {period}")
                
                # ΔΙΟΡΘΩΘΗΚΕ: Προσθήκη του selected_project_afm ως 6ο όρισμα
                render_stage_3(fin_key, emp_data, selected_month, selected_year, period, selected_project_afm)
            else:
                st.warning("⚠️ Τα δεδομένα των υπαλλήλων δεν είναι έγκυρα.")
