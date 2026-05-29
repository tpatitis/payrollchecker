import streamlit as st
import pandas as pd
import os

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
PAYROLL_CHECKS_FILE = 'payroll_checks.csv'
FINANCIALS_FILE = 'payroll_financials.csv'

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

# --- ΣΤΑΔΙΟ 3: ΟΙΚΟΝΟΜΙΚΑ ΣΤΟΙΧΕΙΑ & AI ΑΝΑΛΥΣΗ ---
def render_stage_3(fin_key, emp_data, selected_month, selected_year, period, all_results, audit_df):
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
    
    # 3. Σιγουρευόμαστε ότι υπάρχουν οι μεταβλητές στο session_state για να μην χάνονται στην αλλαγή καρτέλας
    for k, v in base_values.items():
        state_name = f"val_{fin_key}_{k}"
        if state_name not in st.session_state:
            st.session_state[state_name] = v

    # 4. Upload Αρχείου & AI Ανάλυση
    uploaded_file = st.file_uploader("📂 Ανεβάστε το αποδεικτικό μισθοδοσίας (PDF / Εικόνα)", type=["pdf", "png", "jpg", "jpeg"], key=f"file_{fin_key}")

    if uploaded_file is not None:
        file_fingerprint = f"{uploaded_file.name}_{uploaded_file.size}"
        trigger_key = f"ocr_data_{fin_key}_{file_fingerprint}"
        
        if st.button("🤖 Έναρξη Ανάλυσης AI", type="primary", use_container_width=True):
            with st.spinner("⏳ Το AI μελετά το έγγραφο και ελέγχει την περίοδο..."):
                # Εδώ καλείται η δική σου συνάρτηση AI (extract_financials_with_ai)
                ocr_data = extract_financials_with_ai(uploaded_file, emp_data['Ονοματεπώνυμο'])
                if ocr_data:
                    st.session_state[trigger_key] = ocr_data
                    # Μόλις έρθουν τα νέα δεδομένα από το AI, τα περνάμε αμέσως στα μόνιμα state των αποδοχών
                    for k, v in ocr_data.items():
                        st.session_state[f"val_{fin_key}_{k}"] = v
                    st.rerun()
    
    # 5. Έλεγχος Μήνα (Validation)
    current_doc_period = st.session_state[f"val_{fin_key}_Περίοδος_Εγγράφου"]
    if current_doc_period:
        ai_period = str(current_doc_period).lower()
        user_month = selected_month.lower()
        user_year = str(selected_year)
        
        if (user_month[:4] not in ai_period) or (user_year not in ai_period):
            st.warning(
                f"⚠️ **ΠΡΟΣΟΧΗ: ΠΙΘΑΝΟ ΛΑΘΟΣ ΑΡΧΕΙΟ Ή ΠΟΛΛΑΠΛΟΙ ΜΗΝΕΣ!**\n\n"
                f"Έχετε επιλέξει περίοδο **{period}**, αλλά το AI εντόπισε στο έγγραφο την ένδειξη: "
                f"« **{current_doc_period}** ». Παρακαλώ επαληθεύστε τα στοιχεία."
            )
        else:
            st.success(f"✅ Η περίοδος του εγγράφου επαληθεύτηκε επιτυχώς: **{current_doc_period}**")

    # Εμφάνιση περιόδου (συνδεδεμένη με το session_state)
    st.text_input(
        "📅 Περίοδος που αναγράφεται στο έγγραφο (AI Εύρημα)", 
        value=st.session_state[f"val_{fin_key}_Περίοδος_Εγγράφου"], 
        key=f"input_period_doc_{fin_key}"
    )
    st.session_state[f"val_{fin_key}_Περίοδος_Εγγράφου"] = st.session_state[f"input_period_doc_{fin_key}"]
    
    st.markdown("<hr style='margin:15px 0;'>", unsafe_allow_html=True)
    
    # 6. 🔄 ΜΕΝΟΥ ΕΠΙΛΟΓΗΣ ΕΙΔΟΥΣ ΑΠΟΔΟΧΩΝ (Η αλλαγή εδώ εμφανίζει αυτόματα τα σωστά ποσά)
    type_of_payroll = st.selectbox(
        "📊 Επιλέξτε Είδος Αποδοχών για προβολή/καταχώρηση:",
        ["Τακτικές Αποδοχές", "Δώρο Πάσχα", "Δώρο Χριστουγέννων", "Επίδομα Άδειας"],
        key=f"select_type_{fin_key}"
    )

    # Δυναμική εμφάνιση καρτέλας με βάση την επιλογή
    if type_of_payroll == "Τακτικές Αποδοχές":
        st.markdown("### 🛠️ Τακτικές Αποδοχές Μήνα")
        st.number_input(
            "Μικτές Τακτικές Αποδοχές", 
            value=float(st.session_state[f"val_{fin_key}_Τακτικές_Αποδοχές"]), 
            format="%.2f",
            key=f"num_tak_{fin_key}"
        )
        st.session_state[f"val_{fin_key}_Τακτικές_Αποδοχές"] = st.session_state[f"num_tak_{fin_key}"]
        
    elif type_of_payroll == "Δώρο Πάσχα":
        st.markdown("### 🌸 Δώρο Πάσχα")
        st.number_input(
            "Ποσό Δώρου Πάσχα (Μικτά)", 
            value=float(st.session_state[f"val_{fin_key}_Δώρο_Πάσχα"]), 
            format="%.2f",
            key=f"num_pas_{fin_key}"
        )
        st.session_state[f"val_{fin_key}_Δώρο_Πάσχα"] = st.session_state[f"num_pas_{fin_key}"]
        
    elif type_of_payroll == "Δώρο Χριστουγέννων":
        st.markdown("### 🎄 Δώρο Χριστουγέννων")
        st.number_input(
            "Ποσό Δώρου Χριστουγέννων (Μικτά)", 
            value=float(st.session_state[f"val_{fin_key}_Δώρο_Χριστουγέννων"]), 
            format="%.2f",
            key=f"num_xris_{fin_key}"
        )
        st.session_state[f"val_{fin_key}_Δώρο_Χριστουγέννων"] = st.session_state[f"num_xris_{fin_key}"]
        
    elif type_of_payroll == "Επίδομα Άδειας":
        st.markdown("### 🏖️ Επίδομα Άδειας")
        st.number_input(
            "Ποσό Επιδόματος Άδειας (Μικτά)", 
            value=float(st.session_state[f"val_{fin_key}_Επίδομα_Άδειας"]), 
            format="%.2f",
            key=f"num_ade_{fin_key}"
        )
        st.session_state[f"val_{fin_key}_Επίδομα_Άδειας"] = st.session_state[f"num_ade_{fin_key}"]

    st.markdown("<br>", unsafe_allow_html=True)

    # 7. --- ΚΟΙΝΑ ΣΤΟΙΧΕΙΑ ΚΡΑΤΗΣΕΩΝ & ΦΟΡΩΝ (Πάντα ορατά στο κάτω μέρος) ---
    st.markdown("##### **Κρατήσεις & Ασφαλιστικά (Συνολικά Έντυπου)**")
    c1, c2 = st.columns(2)
    v_ika_erg = c1.number_input("Εισφορές Εργαζομένου ΙΚΑ", value=float(st.session_state[f"val_{fin_key}_ΙΚΑ_Εργ"]), format="%.2f", key=f"inp_ika_erg_{fin_key}")
    st.session_state[f"val_{fin_key}_ΙΚΑ_Εργ"] = v_ika_erg

    v_ika_ergo = c2.number_input("Εισφορές Εργοδότη ΙΚΑ", value=float(st.session_state[f"val_{fin_key}_ΙΚΑ_Εργοδ"]), format="%.2f", key=f"inp_ika_ergod_{fin_key}")
    st.session_state[f"val_{fin_key}_ΙΚΑ_Εργοδ"] = v_ika_ergo
    
    c3, c4 = st.columns(2)
    v_teka_erg = c3.number_input("Εισφορές Εργαζομένου ΤΕΚΑ", value=float(st.session_state[f"val_{fin_key}_ΤΕΚΑ_Εργ"]), format="%.2f", key=f"inp_teka_erg_{fin_key}")
    st.session_state[f"val_{fin_key}_ΤΕΚΑ_Εργ"] = v_teka_erg

    v_teka_ergo = c4.number_input("Εισφορές Εργοδότη ΤΕΚΑ", value=float(st.session_state[f"val_{fin_key}_ΤΕΚΑ_Εργοδ"]), format="%.2f", key=f"inp_teka_ergod_{fin_key}")
    st.session_state[f"val_{fin_key}_ΤΕΚΑ_Εργοδ"] = v_teka_ergo
    
    st.markdown("##### **Σύνολα & Φόροι**")
    c5, c6, c7 = st.columns(3)
    v_sum_eisf = c5.number_input("Σύνολο Εισφορών", value=float(st.session_state[f"val_{fin_key}_Σύνολο_Εισφ"]), format="%.2f", key=f"inp_sum_eisf_{fin_key}")
    st.session_state[f"val_{fin_key}_Σύνολο_Εισφ"] = v_sum_eisf

    v_fmy = c6.number_input("ΦΜΥ Εργαζομένου", value=float(st.session_state[f"val_{fin_key}_ΦΜΥ"]), format="%.2f", key=f"inp_fmy_{fin_key}")
    st.session_state[f"val_{fin_key}_ΦΜΥ"] = v_fmy

    v_net = c7.number_input("Καθαρές Αποδοχές (Πληρωτέο)", value=float(st.session_state[f"val_{fin_key}_Καθαρές"]), format="%.2f", key=f"inp_net_{fin_key}")
    st.session_state[f"val_{fin_key}_Καθαρές"] = v_net
    
    c8, c9 = st.columns(2)
    v_total_ap = c8.number_input("Σύνολο Μικτών Αποδοχών (Όπως αναγράφεται)", value=float(st.session_state[f"val_{fin_key}_Σύνολο_Αποδ"]), format="%.2f", key=f"inp_tot_ap_{fin_key}")
    st.session_state[f"val_{fin_key}_Σύνολο_Αποδ"] = v_total_ap

    v_opske = c9.number_input("Αιτούμενο Ποσό ΟΠΣΚΕ", value=float(st.session_state[f"val_{fin_key}_ΟΠΣΚΕ"]), format="%.2f", key=f"inp_opske_{fin_key}")
    st.session_state[f"val_{fin_key}_ΟΠΣΚΕ"] = v_opske
    
    st.markdown("<br>", unsafe_allow_html=True)

    # 8. --- ΑΠΟΘΗΚΕΥΣΗ ΔΕΔΟΜΕΝΩΝ ---
    if st.button("💾 Αποθήκευση Όλων", use_container_width=True, key=f"save_btn_{fin_key}"):
        # Αποθήκευση Checklists
        new_ks = [r['ID_Κλειδί'] for r in all_results]
        audit_df = pd.concat([audit_df[~audit_df['ID_Κλειδί'].isin(new_ks)], pd.DataFrame(all_results)], ignore_index=True)
        save_to_csv(audit_df, PAYROLL_CHECKS_FILE)
        
        # Συλλογή όλων των δεδομένων απευθείας από το session_state
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
        
        # Ένωση και αποθήκευση στο CSV
        fin_df = pd.concat([fin_df[fin_df['ID_Κλειδί'] != fin_key], pd.DataFrame([fin_row])], ignore_index=True)
        save_to_csv(fin_df, FINANCIALS_FILE)
        
        # Καθαρισμός προσωρινών AI keys
        if 'trigger_key' in locals() and trigger_key in st.session_state:
            del st.session_state[trigger_key]
            
        st.session_state[f"success_emp_{fin_key}"] = True
        st.success("✅ Τα στοιχεία αποθηκεύτηκαν επιτυχώς!")
        st.rerun()
