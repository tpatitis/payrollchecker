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

# --- 3. PYDANTIC SCHEMA ΓΙΑ STRUCTURED OUTPUT ΑΠΟ ΤΟ AI ---
class PayrollData(BaseModel):
    Περίοδος_Εγγράφου: str = Field(description="Ο μήνας και το έτος της απόδειξης μισθοδοσίας, π.χ. ΜΑΪΟΣ 2026")
    Τακτικές_Αποδοχές: float = Field(description="Μικτές τακτικές αποδοχές / βασικός μισθός")
    Δώρο_Πάσχα: float = Field(description="Ποσό για Δώρο Πάσχα, αν δεν υπάρχει βάλε 0")
    Δώρο_Χριστουγέννων: float = Field(description="Ποσό για Δώρο Χριστουγέννων, αν δεν υπάρχει βάλε 0")
    Επίδομα_Άδειας: float = Field(description="Ποσό για Επίδομα Άδειας, αν δεν υπάρχει βάλε 0")
    Σύνολο_Αποδ: float = Field(description="Συνολικές μικτές αποδοχές (άθροισμα όλων των αποδοχών)")
    ΙΚΑ_Εργ: float = Field(description="Ασφαλιστικές εισφορές εργαζομένου (κράτηση υπαλλήλου)")
    ΙΚΑ_Εργοδ: float = Field(description="Ασφαλιστικές εισφορές εργοδότη")
    ΤΕΚΑ_Εργ: float = Field(description="Εισφορές εργαζομένου ΤΕΚΑ, αν δεν υπάρχει βάλε 0")
    ΤΕΚΑ_Εργοδ: float = Field(description="Εισφορές εργοδότη ΤΕΚΑ, αν δεν υπάρχει βάλε 0")
    Σύνολο_Εισφ: float = Field(description="Συνολικό ποσό εισφορών (κρατήσεων)")
    ΦΜΥ: float = Field(description="Φόρος Μισθωτών Υπηρεσιών (Φ.Μ.Υ.), αν δεν υπάρχει βάλε 0")
    Καθαρές: float = Field(description="Καθαρό πληρωτέο ποσό στον εργαζόμενο")
    ΟΠΣΚΕ: float = Field(description="Το αιτούμενο ποσό για το ΟΠΣΚΕ (συνήθως ταυτίζεται με το Σύνολο Μικτών)")

# --- 4. ΣΥΝΑΡΤΗΣΕΙΣ ΔΙΑΧΕΙΡΙΣΗΣ ΔΕΔΟΜΕΝΩΝ ---
def load_data(filename, columns):
    if not os.path.isfile(filename) or os.path.getsize(filename) == 0:
        return pd.DataFrame(columns=columns)
    try:
        return pd.read_csv(filename)
    except Exception:
        return pd.DataFrame(columns=columns)

def save_to_csv(df, filename):
    df.to_csv(filename, index=False, encoding='utf-8-sig')

def extract_financials_with_ai(uploaded_file, employee_name):
    # Έλεγχος αν υπάρχει το API Key στα secrets
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("❌ Δεν βρέθηκε το 'GEMINI_API_KEY' στα Streamlit Secrets! Παρακαλώ ρυθμίστε το στο αρχείο .streamlit/secrets.toml")
        return None
    
    try:
        # Αρχικοποίηση του νέου GenAI Client
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        
        # Διάβασμα των bytes του αρχείου
        file_bytes = uploaded_file.read()
        mime_type = uploaded_file.type
        
        # Προετοιμασία του αρχείου ως inline data για το API
        document_part = types.Part.from_bytes(
            data=file_bytes,
            mime_type=mime_type
        )
        
        prompt = f"""
        Είσαι ένας έμπειρος Έλληνας λογιστής και ελεγκτής μισθοδοσίας. 
        Μελέτησε προσεκτικά την επισυναπτόμενη απόδειξη μισθοδοσίας/έντυπο για τον υπάλληλο με όνομα "{employee_name}".
        Εξήγαγε όλα τα οικονομικά μεγέθη και τις κρατήσεις που ζητούνται στο σχήμα. 
        Σιγουρέψου ότι μετατρέπεις όλα τα ποσά σε αριθμούς (float) και αν κάποιο πεδίο λείπει, βάλε 0.0.
        """
        
        # Κλήση του μοντέλου gemini-2.5-flash με απαίτηση για δομημένο JSON βάσει του Pydantic Schema
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[document_part, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=PayrollData,
                temperature=0.1,  # Χαμηλό temperature για μέγιστη ακρίβεια στα νούμερα
            ),
        )
        
        # Μετατροπή του string JSON σε python dictionary
        return json.loads(response.text)
        
    except Exception as e:
        st.error(f"❌ Σφάλμα κατά την ανάλυση του εγγράφου από το AI: {str(e)}")
        return None

# --- ΣΤΑΔΙΟ 3: ΟΙΚΟΝΟΜΙΚΑ ΣΤΟΙΧΕΙΑ & AI ΑΝΑΛΥΣΗ ---
def render_stage_3(fin_key, emp_data, selected_month, selected_year, period):
    st.markdown("### 💰 Στάδιο 3: Έλεγχος & Καταχώρηση Αποδοχών")
    
    # 1. Φόρτωση υπαρχόντων δεδομένων από το CSV
    fin_columns = [
        "ID_Κλειδί", "Περίοδος_Εγγράφου", "Τακτικές_Αποδοχές", "Δώρο_Πάσχα", 
        "Δώρο_Χριστουγέννων", "Επίδομα_Άδειας", "Σύνολο_Αποδ", "ΙΚΑ_Εργ", 
        "ΙΚΑ_Εργοδ", "ΤΕΚΑ_Εργ", "ΤΕΚΑ_Εργοδ", "Σύνολο_Εισφ", "ΦΜΥ", "Καθαρές", "ΟΠΣΚΕ"
    ]
    fin_df = load_data(FINANCIALS_FILE, fin_columns)
    ext_fin = fin_df[fin_df['ID_Κλειδί'] == fin_key]
    
    # 2. Δημιουργία βασικών default τιμών (είτε από το CSV είτε 0.0)
    base_values = {
        k: (ext_fin[k].iloc[0] if not ext_fin.empty and k in ext_fin.columns else (0.0 if k != "Περίοδος_Εγγράφου" else "")) 
        for k in fin_columns if k != "ID_Κλειδί"
    }
    
    # 3. Αρχικοποίηση μεταβλητών στο session_state
    for k, v in base_values.items():
        state_name = f"val_{fin_key}_{k}"
        if state_name not in st.session_state:
            st.session_state[state_name] = v

    if f"success_emp_{fin_key}" in st.session_state:
        st.success("🎉 Τα οικονομικά στοιχεία αποθηκεύτηκαν με επιτυχία!")
        del st.session_state[f"success_emp_{fin_key}"]

    # 4. Upload Αρχείου & AI Ανάλυση
    uploaded_file = st.file_uploader("📂 Ανεβάστε το αποδεικτικό μισθοδοσίας (PDF / Εικόνα)", type=["pdf", "png", "jpg", "jpeg"], key=f"file_{fin_key}")

    if uploaded_file is not None:
        file_fingerprint = f"{uploaded_file.name}_{uploaded_file.size}"
        trigger_key = f"ocr_data_{fin_key}_{file_fingerprint}"
        
        if st.button("🤖 Έναρξη Ανάλυσης AI", type="primary", use_container_width=True):
            with st.spinner("⏳ Το AI μελετά το έγγραφο..."):
                ocr_data = extract_financials_with_ai(uploaded_file, emp_data['Ονοματεπώνυμο'])
                if ocr_data:
                    st.session_state[trigger_key] = ocr_data
                    for k, v in ocr_data.items():
                        st.session_state[f"val_{fin_key}_{k}"] = v
                    st.success("✅ Η ανάλυση ολοκληρώθηκε! Τα πεδία συμπληρώθηκαν αυτόματα.")
                    st.rerun()
    
    # 5. Έλεγχος Μήνα (Validation)
    current_doc_period = st.session_state[f"val_{fin_key}_Περίοδος_Εγγράφου"]
    if current_doc_period:
        ai_period = str(current_doc_period).lower()
        user_month = selected_month.lower()
        user_year = str(selected_year)
        
        if (user_month[:4] not in ai_period) or (user_year not in ai_period):
            st.warning(
                f"⚠️ **ΠΡΟΣΟΧΗ: ΠΙΘΑΝΟ ΛΑΘΟΣ ΑΡΧΕΙΟ!**\n\n"
                f"Έχετε επιλέξει περίοδο **{period}**, αλλά το AI εντόπισε στο έγγραφο την ένδειξη: "
                f"« {current_doc_period} ». Παρακαλώ επαληθεύστε."
            )
        else:
            st.success(f"✅ Η περίοδος του εγγράφου επαληθεύτηκε: **{current_doc_period}**")

    st.text_input(
        "📅 Περίοδος που αναγράφεται στο έγγραφο (AI Εύρημα)", 
        value=st.session_state[f"val_{fin_key}_Περίοδος_Εγγράφου"], 
        key=f"input_period_doc_{fin_key}"
    )
    st.session_state[f"val_{fin_key}_Περίοδος_Εγγράφου"] = st.session_state[f"input_period_doc_{fin_key}"]
    
    st.markdown("<hr style='margin:15px 0;'>", unsafe_allow_html=True)
    
    # 6. ΜΕΝΟΥ ΕΠΙΛΟΓΗΣ ΕΙΔΟΥΣ ΑΠΟΔΟΧΩΝ
    type_of_payroll = st.selectbox(
        "📊 Επιλέξτε Είδος Αποδοχών για προβολή/καταχώρηση:",
        ["Τακτικές Αποδοχές", "Δώρο Πάσχα", "Δώρο Χριστουγέννων", "Επίδομα Άδειας"],
        key=f"payroll_type_select_{fin_key}"
    )

    if type_of_payroll == "Τακτικές Αποδοχές":
        st.markdown("### 🛠️ Τακτικές Αποδοχές Μήνα")
        st.number_input("Μικτές Τακτικές Αποδοχές", value=float(st.session_state[f"val_{fin_key}_Τακτικές_Αποδοχές"]), format="%.2f", key=f"num_tak_{fin_key}")
        st.session_state[f"val_{fin_key}_Τακτικές_Αποδοχές"] = st.session_state[f"num_tak_{fin_key}"]
        
    elif type_of_payroll == "Δώρο Πάσχα":
        st.markdown("### 🌸 Δώρο Πάσχα")
        st.number_input("Ποσό Δώρου Πάσχα (Μικτά)", value=float(st.session_state[f"val_{fin_key}_Δώρο_Πάσχα"]), format="%.2f", key=f"num_pas_{fin_key}")
        st.session_state[f"val_{fin_key}_Δώρο_Πάσχα"] = st.session_state[f"num_pas_{fin_key}"]
        
    elif type_of_payroll == "Δώρο Χριστουγέννων":
        st.markdown("### 🎄 Δώρο Χριστουγέννων")
        st.number_input("Ποσό Δώρου Χριστουγέννων (Μικτά)", value=float(st.session_state[f"val_{fin_key}_Δώρο_Χριστουγέννων"]), format="%.2f", key=f"num_xris_{fin_key}")
        st.session_state[f"val_{fin_key}_Δώρο_Χριστουγέννων"] = st.session_state[f"num_xris_{fin_key}"]
        
    elif type_of_payroll == "Επίδομα Άδειας":
        st.markdown("### 🏖️ Επίδομα Άδειας")
        st.number_input("Ποσό Επιδόματος Άδειας (Μικτά)", value=float(st.session_state[f"val_{fin_key}_Επίδομα_Άδειας"]), format="%.2f", key=f"num_ade_{fin_key}")
        st.session_state[f"val_{fin_key}_Επίδομα_Άδειας"] = st.session_state[f"num_ade_{fin_key}"]

    st.markdown("<br>", unsafe_allow_html=True)

    # --- 7. ΚΟΙΝΑ ΣΤΟΙΧΕΙΑ ΚΡΑΤΗΣΕΩΝ & ΦΟΡΩΝ ---
    st.markdown("##### **Κρατήσεις & Ασφαλιστικά (Συνολικά Έντυπου)**")
    c1, c2 = st.columns(2)
    st.session_state[f"val_{fin_key}_ΙΚΑ_Εργ"] = c1.number_input("Εισφορές Εργαζομένου ΙΚΑ", value=float(st.session_state[f"val_{fin_key}_ΙΚΑ_Εργ"]), format="%.2f", key=f"inp_ika_erg_{fin_key}")
    st.session_state[f"val_{fin_key}_ΙΚΑ_Εργοδ"] = c2.number_input("Εισφορές Εργοδότη ΙΚΑ", value=float(st.session_state[f"val_{fin_key}_ΙΚΑ_Εργοδ"]), format="%.2f", key=f"inp_ika_ergod_{fin_key}")
    
    c3, c4 = st.columns(2)
    st.session_state[f"val_{fin_key}_ΤΕΚΑ_Εργ"] = c3.number_input("Εισφορές Εργαζομένου ΤΕΚΑ", value=float(st.session_state[f"val_{fin_key}_ΤΕΚΑ_Εργ"]), format="%.2f", key=f"inp_teka_erg_{fin_key}")
    st.session_state[f"val_{fin_key}_ΤΕΚΑ_Εργοδ"] = c4.number_input("Εισφορές Εργοδότη ΤΕΚΑ", value=float(st.session_state[f"val_{fin_key}_ΤΕΚΑ_Εργοδ"]), format="%.2f", key=f"inp_teka_ergod_{fin_key}")
    
    st.markdown("##### **Σύνολα & Φόροι**")
    c5, c6, c7 = st.columns(3)
    st.session_state[f"val_{fin_key}_Σύνολο_Εισφ"] = c5.number_input("Σύνολο Εισφορών", value=float(st.session_state[f"val_{fin_key}_Σύνολο_Εισφ"]), format="%.2f", key=f"inp_sum_eisf_{fin_key}")
    st.session_state[f"val_{fin_key}_ΦΜΥ"] = c6.number_input("ΦΜΥ Εργαζομένου", value=float(st.session_state[f"val_{fin_key}_ΦΜΥ"]), format="%.2f", key=f"inp_fmy_{fin_key}")
    st.session_state[f"val_{fin_key}_Καθαρές"] = c7.number_input("Καθαρές Αποδοχές (Πληρωτέο)", value=float(st.session_state[f"val_{fin_key}_Καθαρές"]), format="%.2f", key=f"inp_net_{fin_key}")
    
    c8, c9 = st.columns(2)
    st.session_state[f"val_{fin_key}_Σύνολο_Αποδ"] = c8.number_input("Σύνολο Μικτών Αποδοχών", value=float(st.session_state[f"val_{fin_key}_Σύνολο_Αποδ"]), format="%.2f", key=f"inp_tot_ap_{fin_key}")
    st.session_state[f"val_{fin_key}_ΟΠΣΚΕ"] = c9.number_input("Αιτούμενο Ποσό ΟΠΣΚΕ", value=float(st.session_state[f"val_{fin_key}_ΟΠΣΚΕ"]), format="%.2f", key=f"inp_opske_{fin_key}")
    
    st.markdown("<br>", unsafe_allow_html=True)

    # 8. --- ΑΠΟΘΗΚΕΥΣΗ ΔΕΔΟΜΕΝΩΝ ---
    if st.button("💾 Αποθήκευση Όλων", use_container_width=True, key=f"save_btn_{fin_key}"):
        fin_row = {
            "ID_Κλειδί": fin_key,
            "Περίοδος_Εγγράφου": st.session_state[f"val_{fin_key}_Περίοδος_Εγγράφου"],
            "Τακτικές_Αποδοχές": st.session_state[f"val_{fin_key}_Τακτικές_Αποδοχές"],
            "Δώρο_Πάσχα": st.session_state[f"val_{fin_key}_Δώρο_Πάσχα"],
            "Δώρο_Χριστουγέννων": st.session_state[f"val_{fin_key}_Δώρο_Χριστουγέννων"],
            "Επίδομα_Άδειας": st.session_state[f"val_{fin_key}_Επίδομα_Άδειας"],
            "Σύνολο_Αποδ": st.session_state[f"val_{fin_key}_Σύνολο_Αποδ"],
            "ΙΚΑ_Εργ": st.session_state[f"val_{fin_key}_ΙΚΑ_Εργ"],
            "ΙΚΑ_Εργοδ": st.session_state[f"val_{fin_key}_ΙΚΑ_Εργοδ"],
            "ΤΕΚΑ_Εργ": st.session_state[f"val_{fin_key}_ΤΕΚΑ_Εργ"],
            "ΤΕΚΑ_Εργοδ": st.session_state[f"val_{fin_key}_ΤΕΚΑ_Εργοδ"],
            "Σύνολο_Εισφ": st.session_state[f"val_{fin_key}_Σύνολο_Εισφ"],
            "ΦΜΥ": st.session_state[f"val_{fin_key}_ΦΜΥ"],
            "Καθαρές": st.session_state[f"val_{fin_key}_Καθαρές"],
            "ΟΠΣΚΕ": st.session_state[f"val_{fin_key}_ΟΠΣΚΕ"]
        }
        
        fin_df = pd.concat([fin_df[fin_df['ID_Κλειδί'] != fin_key], pd.DataFrame([fin_row])], ignore_index=True)
        save_to_csv(fin_df, FINANCIALS_FILE)
            
        st.session_state[f"success_emp_{fin_key}"] = True
        st.rerun()

# --- 4. ΠΛΕΥΡΙΚΟ ΜΕΝΟΥ ---
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

# --- ΣΤΑΔΙΟ 3: ΕΝΟΠΟΙΗΣΗ ΣΕΛΙΔΑΣ ΜΙΣΘΟΔΟΣΙΑΣ ΥΠΑΛΛΗΛΩΝ ---
elif page == "3. Μισθοδοσία Υπαλλήλων":
    st.header("👤 Έλεγχος Μισθοδοσίας Υπαλλήλων")
    
    # ---------------- DYNAMIC SIDEBAR FOR EMPLOYEES ----------------
    st.sidebar.markdown("---")
    st.sidebar.subheader("👥 Διαχείριση & Επιλογή Υπαλλήλων")
    
    # Φόρτωση υπαλλήλων
    emp_cols = ["ID", "Ονοματεπώνυμο", "ΑΦΜ", "ΑΜΚΑ"]
    emp_df = load_data(EMPLOYEES_FILE, emp_cols)
    
    # Επιβολή σωστής δομής αν το αρχείο είναι άδειο ή αλλοιωμένο
    if emp_df.empty or not all(col in emp_df.columns for col in emp_cols):
        emp_df = pd.DataFrame(columns=emp_cols)
    else:
        # Μετατροπή σε string και καθαρισμός κενών για σωστούς ελέγχους
        emp_df['ΑΦΜ'] = emp_df['ΑΦΜ'].astype(str).str.strip()
        emp_df['ΑΜΚΑ'] = emp_df['ΑΜΚΑ'].astype(str).str.strip()
    
    # 1. Φόρμα Προσθήκης Υπαλλήλου στο Sidebar (Με έλεγχο διπλότυπου ΑΦΜ/ΑΜΚΑ)
    with st.sidebar.expander("➕ Προσθήκη Νέου Υπάλληλου"):
        with st.form("add_employee_form"):
            new_name = st.text_input("Ονοματεπώνυμο").strip()
            new_afm = st.text_input("ΑΦΜ Υπαλλήλου (9 ψηφία)", max_chars=9).strip()
            new_amka = st.text_input("ΑΜΚΑ Υπαλλήλου (11 ψηφία)", max_chars=11).strip()
            
            if st.form_submit_button("💾 Προσθήκη"):
                if new_name and new_afm and new_amka:
                    generated_id = f"EMP_{new_amka}"
                    
                    # Έλεγχος αν υπάρχει ήδη το ΑΦΜ ή το ΑΜΚΑ
                    if not emp_df.empty and new_afm in emp_df['ΑΦΜ'].values:
                        st.error(f"⚠️ Το ΑΦΜ **{new_afm}** ανήκει ήδη σε καταχωρημένο υπάλληλο!")
                    elif not emp_df.empty and new_amka in emp_df['ΑΜΚΑ'].values:
                        st.error(f"⚠️ Το ΑΜΚΑ **{new_amka}** υπάρχει ήδη στο σύστημα!")
                    else:
                        new_emp = pd.DataFrame([{
                            "ID": generated_id, 
                            "Ονοματεπώνυμο": new_name, 
                            "ΑΦΜ": new_afm,
                            "ΑΜΚΑ": new_amka
                        }])
                        emp_df = pd.concat([emp_df, new_emp], ignore_index=True)
                        save_to_csv(emp_df, EMPLOYEES_FILE)
                        st.success("🎉 Ο υπάλληλος προστέθηκε επιτυχώς!")
                        st.rerun()
                else:
                    st.error("❌ Παρακαλώ συμπληρώστε όλα τα πεδία!")
                    
    # 2. Φόρμα Διαγραφής Υπαλλήλου στο Sidebar
    if not emp_df.empty:
        with st.sidebar.expander("🗑️ Διαγραφή Υπαλλήλου"):
            # ΔΙΟΡΘΩΘΗΚΕ ΤΟ TYPO: row['ΑΜΚΑ'] αντί για row['AMKA']
            delete_options = {
                f"{row['Ονοματεπώνυμο']} (ΑΜΚΑ: {row['ΑΜΚΑ']})": row['ID']
                for _, row in emp_df.iterrows() if pd.notna(row['ΑΜΚΑ'])
            }
            
            if delete_options:
                selected_del_label = st.selectbox("Επιλέξτε υπάλληλο για διαγραφή:", list(delete_options.keys()), key="del_emp_select")
                target_del_id = delete_options[selected_del_label]
                
                if st.button("Οριστική Διαγραφή", type="primary", key="del_emp_btn"):
                    emp_df = emp_df[emp_df['ID'].astype(str) != str(target_del_id)]
                    save_to_csv(emp_df, EMPLOYEES_FILE)
                    st.success("Ο υπάλληλος διαγράφηκε!")
                    st.rerun()
                
    st.sidebar.markdown("---")
    
    # 3. Επιλογή Υπαλλήλου & Περιόδου για το Στάδιο 3
    if emp_df.empty:
        st.warning("⚠️ Δεν υπάρχουν καταχωρημένοι υπάλληλοι. Ανοίξτε το «Προσθήκη Νέου Υπάλληλου» στην αριστερή μπάρα για να βάλετε τον πρώτο!")
    else:
        emp_options = {}
        for _, row in emp_df.iterrows():
            if pd.notna(row["Ονοματεπώνυμο"]) and pd.notna(row["ID"]):
                display_label = f"{row['Ονοματεπώνυμο']} (ΑΜΚΑ: {row['ΑΜΚΑ']})"
                emp_options[display_label] = {
                    "ID": str(row["ID"]), 
                    "Ονοματεπώνυμο": str(row["Ονοματεπώνυμο"]), 
                    "ΑΦΜ": str(row["ΑΦΜ"]),
                    "ΑΜΚΑ": str(row["ΑΜΚΑ"])
                }
        
        if emp_options:
            selected_emp_label = st.sidebar.selectbox("Επιλέξτε Υπάλληλο για Έλεγχο:", list(emp_options.keys()))
            emp_data = emp_options[selected_emp_label]
            
            months = ["Ιανουάριος", "Φεβρουάριος", "Μάρτιος", "Απρίλιος", "Μάιος", "Ιούνιος", 
                      "Ιούλιος", "Αύγουστος", "Σεπτέμβριος", "Οκτώβριος", "Νοέμβριος", "Δεκέμβριος"]
            selected_month = st.sidebar.selectbox("Μήνας:", months, index=4)
            selected_year = st.sidebar.number_input("Έτος:", min_value=2020, max_value=2030, value=2026)
            
            period = f"{selected_month} {selected_year}"
            fin_key = f"{emp_data['ID']}_{selected_month}_{selected_year}"
            
            st.sidebar.info(f"📋 **Στοιχεία Τρέχοντος Ελέγχου**")
            st.sidebar.text(f"👤 ΑΦΜ: {emp_data['ΑΦΜ']}")
            st.sidebar.text(f"🆔 ΑΜΚΑ: {emp_data['ΑΜΚΑ']}")
            st.sidebar.text(f"📅 Περίοδος: {period}")
            
            render_stage_3(fin_key, emp_data, selected_month, selected_year, period)
        else:
            st.warning("⚠️ Τα δεδομένα των υπαλλήλων δεν είναι έγκυρα. Δοκιμάστε να προσθέσετε έναν νέο.")
