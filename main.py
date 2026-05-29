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

# --- 4. ΣΤΑΔΙΟ 3: ΜΙΣΘΟΔΟΣΙΑ ΥΠΑΛΛΗΛΩΝ (STRUCTURED OUTPUT SCHEMA) ---
class PayrollFinancials(BaseModel):
    ΙΚΑ_Εργ: float = Field(description="Οι κρατήσεις ή εισφορές του ασφαλισμένου/εργαζομένου για το κύριο ταμείο (ΙΚΑ/ΕΦΚΑ). Μην το μπερδεύεις με τις εργοδοτικές.")
    ΙΚΑ_Εργοδ: float = Field(description="Οι εισφορές του εργοδότη για το κύριο ταμείο (ΙΚΑ/ΕΦΚΑ).")
    ΤΕΚΑ_Εργ: float = Field(description="Οι κρατήσεις του εργαζομένου για το ΤΕΚΑ (επικουρικό). Αν δεν υπάρχει, βάλε 0.0.")
    ΤΕΚΑ_Εργοδ: float = Field(description="Οι εισφορές του εργοδότη για το ΤΕΚΑ. Αν δεν υπάρχει, βάλε 0.0.")
    Σύνολο_Εισφ: float = Field(description="Το άθροισμα όλων των ασφαλιστικών κρατήσεων/εισφορών εργαζομένου και εργοδότη.")
    ΦΜΥ: float = Field(description="Ο Φόρος Μισθωτών Υπηρεσιών (Φ.Μ.Υ.). Αν δεν υπάρχει, βάλε 0.0.")
    Καθαρές: float = Field(description="Το τελικό πληρωτέο ποσό στον εργαζόμενο (Καθαρές Αποδοχές).")
    Τακτικές_Αποδ: float = Field(description="Οι μικτές τακτικές αποδοχές / βασικός μισθός.")
    Υπερωρίες: float = Field(description="Ποσό για υπερωρίες ή υπερεργασία, αν δεν υπάρχει βάλε 0.0.")
    Δώρο_Πάσχα: float = Field(description="Ποσό για Δώρο Πάσχα, αν δεν υπάρχει βάλε 0.0.")
    Δώρο_Χριστουγέννων: float = Field(description="Ποσό για Δώρο Χριστουγέννων, αν δεν υπάρχει βάλε 0.0.")
    Επίδομα_Άδειας: float = Field(description="Ποσό για Επίδομα Άδειας, αν δεν υπάρχει βάλε 0.0.")
    Λοιπά_Αποδ: float = Field(description="Λοιπά επιδόματα, bonus ή αναδρομικά, αν δεν υπάρχει βάλε 0.0.")
    Σύνολο_Αποδ: float = Field(description="Οι συνολικές μικτές αποδοχές (άθροισμα όλων των επιμέρους αποδοχών).")
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
        3. ΑΓΝΟΗΣΕ ΓΕΝΙΚΑ ΣΥΝΟΛΑ: Μην πάρεις ποτέ τα συνολικά αθροίσματα της επιχείρησης.
        4. ΔΙΑΧΩΡΙΣΜΟΣ ΑΠΟΔΟΧΩΝ: Ξεχώρισε προσεκτικά τον Βασικό Μισθό (Τακτικές), τις Υπερωρίες, τα Δώρα (Πάσχα/Χριστουγέννων), το Επίδομα Άδειας και τα Λοιπά Bonus.
        5. Το 'Καθαρές' είναι ΠΑΝΤΑ το πληρωτέο ποσό στον εργαζόμενο.
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
    # 1. Φόρτωση δεδομένων
    fin_cols = ["ID_Κλειδί", "ΙΚΑ_Εργ", "ΙΚΑ_Εργοδ", "ΤΕΚΑ_Εργ", "ΤΕΚΑ_Εργοδ", "Σύνολο_Εισφ", "ΦΜΥ", "Καθαρές", 
                "Τακτικές_Αποδ", "Υπερωρίες", "Δώρο_Πάσχα", "Δώρο_Χριστουγέννων", "Επίδομα_Άδειας", "Λοιπά_Αποδ", "Σύνολο_Αποδ", "ΟΠΣΚΕ"]
    fin_df = load_data(FINANCIALS_FILE, fin_cols)
    ext_fin = fin_df[fin_df['ID_Κλειδί'] == fin_key]
    
    # Δημιουργία dictionary με default τιμές
    d = {k: (float(ext_fin[k].iloc[0]) if not ext_fin.empty and k in ext_fin.columns else 0.0) for k in fin_cols}

    # 2. Tabs Αποδοχών
    st.subheader("📊 Κατηγορίες Αποδοχών")
    t1, t2, t3, t4 = st.tabs(["Τακτικές Αποδοχές", "Επίδομα Αδείας", "Δώρο Πάσχα", "Δώρο Χριστουγέννων"])
    
    with t1: v_tak_ap = st.number_input("Ποσό Τακτικών (€)", value=d["Τακτικές_Αποδ"], format="%.2f", key=f"tak_{fin_key}")
    with t2: v_epidoma_ad = st.number_input("Ποσό Επιδόματος Αδείας (€)", value=d["Επίδομα_Άδειας"], format="%.2f", key=f"ad_{fin_key}")
    with t3: v_doro_pasxa = st.number_input("Ποσό Δώρου Πάσχα (€)", value=d["Δώρο_Πάσχα"], format="%.2f", key=f"pas_{fin_key}")
    with t4: v_doro_xrist = st.number_input("Ποσό Δώρου Χριστουγέννων (€)", value=d["Δώρο_Χριστουγέννων"], format="%.2f", key=f"xri_{fin_key}")
    
    v_yp_ap = 0.0 # Αν χρειάζεται
    v_loip_ap = 0.0

    # 3. Σταθερά Πεδία Εισφορών
    st.divider()
    st.subheader("📉 Στοιχεία Εισφορών & Φόρων")
    c1, c2, c3, c4 = st.columns(4)
    v_ika_erg = c1.number_input("ΙΚΑ Εργαζ.", value=d["ΙΚΑ_Εργ"], format="%.2f", key=f"ikae_{fin_key}")
    v_ika_ergo = c2.number_input("ΙΚΑ Εργοδ.", value=d["ΙΚΑ_Εργοδ"], format="%.2f", key=f"ikao_{fin_key}")
    v_teka_erg = c3.number_input("ΤΕΚΑ Εργαζ.", value=d["ΤΕΚΑ_Εργ"], format="%.2f", key=f"tekae_{fin_key}")
    v_teka_ergo = c4.number_input("ΤΕΚΑ Εργοδ.", value=d["ΤΕΚΑ_Εργοδ"], format="%.2f", key=f"tekao_{fin_key}")
    
    c5, c6, c7, c8 = st.columns(4)
    v_sum_eisf = c5.number_input("Σύνολο Εισφορών", value=d["Σύνολο_Εισφ"], format="%.2f", key=f"seisf_{fin_key}")
    v_fmy = c6.number_input("ΦΜΥ", value=d["ΦΜΥ"], format="%.2f", key=f"fmy_{fin_key}")
    v_net = c7.number_input("Καθαρές Αποδοχές", value=d["Καθαρές"], format="%.2f", key=f"net_{fin_key}")
    
    v_total_ap = v_tak_ap + v_epidoma_ad + v_doro_pasxa + v_doro_xrist + v_loip_ap
    c8.metric("Σύνολο Μικτών", f"{v_total_ap:,.2f} €")
    
    v_opske = st.number_input("Αιτούμενο ΟΠΣΚΕ", value=d["ΟΠΣΚΕ"], format="%.2f", key=f"opske_{fin_key}")

    # 4. Αποθήκευση
    if st.button("💾 Αποθήκευση Όλων", key=f"save_{fin_key}"):
        fin_row = {
            "ID_Κλειδί": fin_key, "ΙΚΑ_Εργ": v_ika_erg, "ΙΚΑ_Εργοδ": v_ika_ergo, 
            "ΤΕΚΑ_Εργ": v_teka_erg, "ΤΕΚΑ_Εργοδ": v_teka_ergo, "Σύνολο_Εισφ": v_sum_eisf, 
            "ΦΜΥ": v_fmy, "Καθαρές": v_net, "Τακτικές_Αποδ": v_tak_ap, "Υπερωρίες": v_yp_ap, 
            "Δώρο_Πάσχα": v_doro_pasxa, "Δώρο_Χριστουγέννων": v_doro_xrist, "Επίδομα_Άδειας": v_epidoma_ad,
            "Λοιπά_Αποδ": v_loip_ap, "Σύνολο_Αποδ": v_total_ap, "ΟΠΣΚΕ": v_opske
        }
        # Ενημέρωση DataFrame
        fin_df = pd.concat([fin_df[fin_df['ID_Κλειδί'] != fin_key], pd.DataFrame([fin_row])], ignore_index=True)
        save_to_csv(fin_df, FINANCIALS_FILE)
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

# --- ΣΤΑΔΙΟ 3: ΜΙΣΘΟΔΟΣΙΑ ΥΠΑΛΛΗΛΩΝ (Πλήρης Κώδικας) ---
elif page == "3. Μισθοδοσία Υπαλλήλων":
    st.header("👤 Έλεγχος Μισθοδοσίας Υπαλλήλων")
    
    # 1. Επιλογή Επιχείρησης
    projects_df = load_data(PROJECTS_FILE, ["Επωνυμία", "ΑΦΜ"])
    if projects_df.empty:
        st.error("⚠️ Παρακαλώ καταχωρήστε τουλάχιστον μία επιχείρηση στο 'Στάδιο 1'.")
    else:
        selected_project_name = st.selectbox("Επιλέξτε Επιχείρηση:", projects_df['Επωνυμία'], key="stage3_proj")
        selected_project_afm = str(projects_df[projects_df['Επωνυμία'] == selected_project_name]['ΑΦΜ'].iloc[0]).strip()

        # 2. Sidebar Διαχείριση Υπαλλήλων
        st.sidebar.markdown("---")
        st.sidebar.subheader("👥 Διαχείριση Υπαλλήλων")
        
        emp_df = load_data(EMPLOYEES_FILE, ["ID", "Ονοματεπώνυμο", "ΑΦΜ", "ΑΜΚΑ"])
        
        # Φόρμα προσθήκης (sidebar)
        with st.sidebar.expander("➕ Προσθήκη Υπάλληλου"):
            with st.form("add_emp"):
                n_name = st.text_input("Ονοματεπώνυμο")
                n_afm = st.text_input("ΑΦΜ")
                n_amka = st.text_input("ΑΜΚΑ")
                if st.form_submit_button("Προσθήκη"):
                    new_row = pd.DataFrame([{"ID": f"EMP_{n_amka}", "Ονοματεπώνυμο": n_name, "ΑΦΜ": n_afm, "ΑΜΚΑ": n_amka}])
                    save_to_csv(pd.concat([emp_df, new_row]), EMPLOYEES_FILE)
                    st.rerun()
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
        # 3. Επιλογή για έλεγχο
        if not emp_df.empty:
            emp_options = {f"{r['Ονοματεπώνυμο']} (ΑΜΚΑ: {r['ΑΜΚΑ']})": r for _, r in emp_df.iterrows()}
            s_emp_label = st.sidebar.selectbox("Επιλέξτε Υπάλληλο:", list(emp_options.keys()))
            emp_data = emp_options[s_emp_label]
            
            s_month = st.sidebar.selectbox("Μήνας:", ["Ιανουάριος", "Φεβρουάριος", "Μάρτιος", "Απρίλιος", "Μάιος", "Ιούνιος", "Ιούλιος", "Αύγουστος", "Σεπτέμβριος", "Οκτώβριος", "Νοέμβριος", "Δεκέμβριος"], index=4)
            s_year = st.sidebar.number_input("Έτος:", value=2026)
            
            # --- ΕΔΩ ΕΙΝΑΙ ΤΟ ΚΛΕΙΔΙ: Εμφάνιση του περιεχομένου ---
            period = f"{s_month} {s_year}"
            fin_key = f"{emp_data['ID']}_{s_month}_{s_year}"
            
            st.info(f"Ελέγχεις: **{emp_data['Ονοματεπώνυμο']}** για την περίοδο **{period}**")
            
            # Κλήση της συνάρτησης που σχεδιάζει το UI
            render_stage_3(fin_key, emp_data, s_month, s_year, period, selected_project_afm)
        else:
            st.warning("⚠️ Δεν υπάρχουν υπάλληλοι. Προσθέστε έναν από το μενού στα αριστερά.")
