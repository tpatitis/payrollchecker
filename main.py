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

# --- 3. ΣΥΝΑΡΤΗΣΕΙΣ ΔΙΑΧΕΙΡΙΣΗΣ ΔΕΔΟΜΕΝΩΝ ---
def load_data(filename, columns):
    """Φορτώνει δεδομένα ή επιστρέφει κενό DataFrame αν το αρχείο δεν υπάρχει"""
    if not os.path.isfile(filename) or os.path.getsize(filename) == 0:
        return pd.DataFrame(columns=columns)
    try:
        return pd.read_csv(filename)
    except Exception:
        return pd.DataFrame(columns=columns)

def save_to_csv(df, filename):
    """Αποθηκεύει δεδομένα σε CSV με UTF-8 encoding"""
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
                else:
                    st.error("⚠️ Συμπληρώστε Επωνυμία και ΑΦΜ.")

    df_list = load_data(PROJECTS_FILE, ["Επωνυμία", "ΑΦΜ", "MIS", "Προϋπολογισμός"])
    if not df_list.empty:
        st.divider()
        st.subheader("📋 Καταχωρημένες Επιχειρήσεις")
        for i, row in df_list.iterrows():
            c1, c2, c3, c4 = st.columns([3, 2, 1, 0.5])
            c1.write(f"**{row['Επωνυμία']}**")
            c2.write(f"ΑΦΜ: {row['ΑΦΜ']}")
            c3.write(f"{row['Προϋπολογισμός']} €")
            if c4.button("🗑️", key=f"del_{row['ΑΦΜ']}"):
                df_list = df_list.drop(i)
                save_to_csv(df_list, PROJECTS_FILE)
                st.rerun()

# --- ΣΤΑΔΙΟ 2: CHECKLIST ΑΝΑ ΕΡΓΟ ---
elif page == "2. Checklist ανά Έργο":
    st.header("📂 Γενικά Παραδοτέα Μισθοδοσίας")
    projects_df = load_data(PROJECTS_FILE, ["Επωνυμία", "ΑΦΜ"])
    
    if projects_df.empty:
        st.warning("⚠️ Καταχωρήστε μια επιχείρηση στο Στάδιο 1.")
    else:
        selected_name = st.selectbox("Επιλέξτε Επιχείρηση:", projects_df['Επωνυμία'])
        selected_afm = str(projects_df[projects_df['Επωνυμία'] == selected_name]['ΑΦΜ'].iloc[0])
        check_df = load_data(CHECKLIST_FILE, ["ΑΦΜ", "Εγγραφο", "Κατάσταση", "Σχόλιο"])
        
        required_docs = [
            "Πίνακας Προσωπικού Ε4", "Μισθολογικές καταστάσεις", "ΑΠΔ ΕΦΚΑ", "Αποδεικτικό Υποβολής ΑΠΔ",
            "ΑΠΔ ΤΕΚΑ", "Αποδεικτικό Υποβολής ΑΠΔ ΤΕΚΑ", "Υπεύθυνη δήλωση συγγενών", "Επιστολή γνωστοποίησης", 
            "Ασφαλιστική ενημερότητα", "Οικονομική καρτέλα ΕΦΚΑ", "Ηλεκτρονική καρτέλα οφειλετών", 
            "Πίνακας χρεών οφειλέτη", "Ανάλυση κίνησης Ηλ. Καρτέλας", "Φορολογική ενημερότητα", 
            "Στοιχεία ρυθμίσεων & Πληρωμή", "Προσωρινές δηλώσεις ΦΜΥ"
        ]
        
        h1, h2, h3 = st.columns([1.2, 0.8, 3.0], gap="small")
        h1.caption("📄 Έγγραφο")
        h2.caption("📊 Κατάσταση")
        h3.caption("📝 Παρατήρηση")
        st.divider()

        options = ["Έλλειψη ❌", "Υπάρχει ✅", "Δεν απαιτείται"]
        results = []

        for doc in required_docs:
            existing = check_df[(check_df['ΑΦΜ'].astype(str) == selected_afm) & (check_df['Εγγραφο'] == doc)]
            curr_val = existing['Κατάσταση'].iloc[0] if not existing.empty else "Έλλειψη ❌"
            curr_note = existing['Σχόλιο'].iloc[0] if not existing.empty and pd.notna(existing['Σχόλιο'].iloc[0]) else ""

            c1, c2, c3 = st.columns([1.2, 0.8, 3.0], gap="small")
            c1.markdown(f"<div style='margin-top:5px; font-size:0.85rem; line-height:1;'><b>{doc}</b></div>", unsafe_allow_html=True)
            status = c2.selectbox("", options, index=options.index(curr_val) if curr_val in options else 0, key=f"st_{selected_afm}_{doc}", label_visibility="collapsed")
            note = c3.text_input("Σχόλιο...", value=curr_note, key=f"nt_{selected_afm}_{doc}", label_visibility="collapsed")
            results.append({"ΑΦΜ": selected_afm, "Εγγραφο": doc, "Κατάσταση": status, "Σχόλιο": note})

        if st.button(f"💾 Αποθήκευση Checklist για {selected_name}"):
            check_df = check_df[check_df['ΑΦΜ'].astype(str) != selected_afm]
            new_data = pd.DataFrame(results)
            save_to_csv(pd.concat([check_df, new_data], ignore_index=True), CHECKLIST_FILE)
            st.success("✅ Το Checklist αποθηκεύτηκε!")
            st.rerun()

# --- ΣΤΑΔΙΟ 3: ΜΙΣΘΟΔΟΣΙΑ ΥΠΑΛΛΗΛΩΝ ---
elif page == "3. Μισθοδοσία Υπαλλήλων":
    st.header("👤 Διαχείριση & Έλεγχος Υπαλλήλων")
    
    projects_df = load_data(PROJECTS_FILE, ["Επωνυμία", "ΑΦΜ"])
    
    if projects_df.empty:
        st.warning("⚠️ Καταχωρήστε μια επιχείρηση στο Στάδιο 1.")
    else:
        # 1. Επιλογή Επιχείρησης, Μήνα & Έτους
        col_sel1, col_sel2, col_sel3 = st.columns([2, 1, 1])
        with col_sel1:
            selected_project = st.selectbox("Επιλέξτε Επιχείρηση:", projects_df['Επωνυμία'], key="p_select")
            selected_afm = str(projects_df[projects_df['Επωνυμία'] == selected_project]['ΑΦΜ'].iloc[0])
        with col_sel2:
            selected_month = st.selectbox("Μήνας:", ["Ιανουάριος", "Φεβρουάριος", "Μάρτιος", "Απρίλιος", "Μάιος", "Ιούνιος", "Ιούλιος", "Αύγουστος", "Σεπτέμβριος", "Οκτώβριος", "Νοέμβριος", "Δεκέμβριος"])
        with col_sel3:
            selected_year = st.selectbox("Έτος:", ["2023", "2024", "2025", "2026", "2027"], index=1)

        period = f"{selected_month} {selected_year}"
        st.divider()

        # 2. ΠΕΔΙΟ ΣΥΜΠΛΗΡΩΣΗΣ ΣΤΟΙΧΕΙΩΝ ΥΠΑΛΛΗΛΟΥ
        st.subheader(f"➕ Καταχώρηση / Επεξεργασία Υπαλλήλου ({selected_project})")
        with st.container():
            c1, c2, c3, c4 = st.columns([1.5, 1, 1, 0.8])
            new_emp_name = c1.text_input("Ονοματεπώνυμο", placeholder="ΕΠΩΝΥΜΟ ΟΝΟΜΑ", key="new_emp_name_in")
            new_emp_afm = c2.text_input("ΑΦΜ Υπαλλήλου", key="new_emp_afm_in", max_chars=9)
            new_emp_amka = c3.text_input("ΑΜΚΑ Υπαλλήλου", key="new_emp_amka_in", max_chars=11)
            
            if c4.button("📥 Αποθήκευση", use_container_width=True):
                if new_emp_name and new_emp_afm:
                    emp_df = load_data(EMPLOYEES_FILE, ["ΑΦΜ_Εργου", "Ονοματεπώνυμο", "ΑΦΜ_Υπαλλήλου", "ΑΜΚΑ_Υπαλλήλου"])
                    mask = (emp_df['ΑΦΜ_Εργου'].astype(str) == selected_afm) & (emp_df['ΑΦΜ_Υπαλλήλου'].astype(str) == new_emp_afm)
                    
                    if not emp_df[mask].empty:
                        emp_df.loc[mask, ["Ονοματεπώνυμο", "ΑΜΚΑ_Υπαλλήλου"]] = [new_emp_name, new_emp_amka]
                        st.info("🔄 Τα στοιχεία του υπαλλήλου ενημερώθηκαν.")
                    else:
                        new_row = pd.DataFrame([{"ΑΦΜ_Εργου": selected_afm, "Ονοματεπώνυμο": new_emp_name, "ΑΦΜ_Υπαλλήλου": new_emp_afm, "ΑΜΚΑ_Υπαλλήλου": new_emp_amka}])
                        emp_df = pd.concat([emp_df, new_row], ignore_index=True)
                        st.success(f"✅ Ο υπάλληλος {new_emp_name} προστέθηκε!")
                    
                    save_to_csv(emp_df, EMPLOYEES_FILE)
                    st.rerun()
                else:
                    st.error("⚠️ Το Ονοματεπώνυμο και το ΑΦΜ είναι υποχρεωτικά.")

        st.divider()

        # 3. DROPDOWN MENU ΕΠΙΛΟΓΗΣ ΥΠΑΛΛΗΛΟΥ
        st.subheader("🔍 Επιλογή Υπαλλήλου για Έλεγχο")
        all_emps_df = load_data(EMPLOYEES_FILE, ["ΑΦΜ_Εργου", "Ονοματεπώνυμο", "ΑΦΜ_Υπαλλήλου", "ΑΜΚΑ_Υπαλλήλου"])
        current_emps = all_emps_df[all_emps_df['ΑΦΜ_Εργου'].astype(str) == selected_afm]
        emp_options = current_emps.apply(lambda x: f"{x['Ονοματεπώνυμο']} (ΑΦΜ: {x['ΑΦΜ_Υπαλλήλου']})", axis=1).tolist()

        if not emp_options:
            st.info("💡 Η λίστα υπαλλήλων είναι κενή. Προσθέστε υπαλλήλους παραπάνω.")
        else:
            selected_option = st.selectbox("Επιλέξτε Υπάλληλο:", ["--- Επιλογή ---"] + emp_options)

            if selected_option != "--- Επιλογή ---":
                sel_emp_afm = selected_option.split("(ΑΦΜ: ")[1].replace(")", "")
                emp_data = current_emps[current_emps['ΑΦΜ_Υπαλλήλου'].astype(str) == sel_emp_afm].iloc[0]
                
                st.info(f"👤 **Υπάλληλος:** {emp_data['Ονοματεπώνυμο']} | **ΑΜΚΑ:** {emp_data['ΑΜΚΑ_Υπαλλήλου']}")
                
                # Φόρτωση ελέγχων
                audit_df = load_data(PAYROLL_CHECKS_FILE, ["ID_Κλειδί", "Έγγραφο", "Κατάσταση", "Σχόλιο"])

                # --- Α. ΚΕΝΤΡΙΚΑ ΔΙΚΑΙΟΛΟΓΗΤΙΚΑ ---
                st.subheader("📌 Κεντρικά Δικαιολογητικά (Άπαξ)")
                perm_docs = ["Αναγγελία Πρόσληψης (Ε3)", "Ταυτότητα Εργαζομένου"]
                perm_results = []
                for p_doc in perm_docs:
                    p_key = f"PERM_{selected_afm}_{sel_emp_afm}_{p_doc}"
                    existing_p = audit_df[audit_df['ID_Κλειδί'] == p_key]
                    p_val = existing_p['Κατάσταση'].iloc[0] if not existing_p.empty else "Έλλειψη ❌"
                    p_note = existing_p['Σχόλιο'].iloc[0] if not existing_p.empty and pd.notna(existing_p['Σχόλιο'].iloc[0]) else ""
                    
                    pc1, pc2, pc3 = st.columns([1.5, 1, 2], gap="small")
                    pc1.markdown(f"<div style='margin-top:5px; font-size:0.85rem;'><b>{p_doc}</b></div>", unsafe_allow_html=True)
                    p_status = pc2.selectbox("Status", ["Έλλειψη ❌", "Υπάρχει ✅", "Δεν απαιτείται"], index=["Έλλειψη ❌", "Υπάρχει ✅", "Δεν απαιτείται"].index(p_val), key=f"p_st_{p_key}", label_visibility="collapsed")
                    p_comment = pc3.text_input("Παρατήρηση", value=p_note, key=f"p_nt_{p_key}", label_visibility="collapsed")
                    perm_results.append({"ID_Κλειδί": p_key, "Έγγραφο": p_doc, "Κατάσταση": p_status, "Σχόλιο": p_comment})

                st.divider()

                # --- Β. ΜΗΝΙΑΙΑ ΠΑΡΑΔΟΤΕΑ ---
                st.subheader(f"📅 Παραδοτέα Περιόδου: {period}")
                monthly_docs = ["Extrait", "Έμβασμα Πληρωμής", "Λογιστικό άρθρο καταχώρησης μισθοδοσίας", "Λογιστικό άρθρο πληρωμής μισθοδοσίας", "Βιβλίο εσόδων-εξόδων (Μισθοδοσία)"]
                month_results = []
                for m_doc in monthly_docs:
                    m_key = f"MONTH_{selected_afm}_{sel_emp_afm}_{period}_{m_doc}"
                    existing_m = audit_df[audit_df['ID_Κλειδί'] == m_key]
                    m_val = existing_m['Κατάσταση'].iloc[0] if not existing_m.empty else "Έλλειψη ❌"
                    m_note = existing_m['Σχόλιο'].iloc[0] if not existing_m.empty and pd.notna(existing_m['Σχόλιο'].iloc[0]) else ""

                    mc1, mc2, mc3 = st.columns([1.5, 1, 2], gap="small")
                    mc1.markdown(f"<div style='margin-top:5px; font-size:0.85rem;'>{m_doc}</div>", unsafe_allow_html=True)
                    m_status = mc2.selectbox("Status", ["Έλλειψη ❌", "Υπάρχει ✅", "Δεν απαιτείται"], index=["Έλλειψη ❌", "Υπάρχει ✅", "Δεν απαιτείται"].index(m_val), key=f"m_st_{m_key}", label_visibility="collapsed")
                    m_comment = mc3.text_input("Παρατήρηση", value=m_note, key=f"m_nt_{m_key}", label_visibility="collapsed")
                    month_results.append({"ID_Κλειδί": m_key, "Έγγραφο": m_doc, "Κατάσταση": m_status, "Σχόλιο": m_comment})

                if st.button(f"💾 Αποθήκευση Ελέγχου για {emp_data['Ονοματεπώνυμο']}"):
                    all_new_keys = [r['ID_Κλειδί'] for r in perm_results + month_results]
                    audit_df = audit_df[~audit_df['ID_Κλειδί'].isin(all_new_keys)]
                    final_audit_df = pd.concat([audit_df, pd.DataFrame(perm_results), pd.DataFrame(month_results)], ignore_index=True)
                    save_to_csv(final_audit_df, PAYROLL_CHECKS_FILE)
                    st.success("✅ Ο έλεγχος αποθηκεύτηκε!")
                    st.rerun()

                with st.expander("⚙️ Επιλογές Διαγραφής"):
                    if st.button(f"🗑️ Οριστική Διαγραφή Υπαλλήλου"):
                        all_emps_df = all_emps_df[~((all_emps_df['ΑΦΜ_Εργου'].astype(str) == selected_afm) & (all_emps_df['ΑΦΜ_Υπαλλήλου'].astype(str) == sel_emp_afm))]
                        save_to_csv(all_emps_df, EMPLOYEES_FILE)
                        st.rerun()
