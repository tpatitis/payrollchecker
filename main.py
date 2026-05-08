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
        # --- ΠΑΝΩ ΜΕΡΟΣ: 2 ΚΥΡΙΕΣ ΣΤΗΛΕΣ ---
        top_left, top_right = st.columns([1, 1.2], gap="large")

        with top_left:
            st.subheader("🏢 Επιλογή Στοιχείων")
            selected_project = st.selectbox("Επιχείρηση:", projects_df['Επωνυμία'], key="p_select")
            selected_afm = str(projects_df[projects_df['Επωνυμία'] == selected_project]['ΑΦΜ'].iloc[0])
            
            c_m, c_y = st.columns(2)
            selected_month = c_m.selectbox("Μήνας:", ["Ιανουάριος", "Φεβρουάριος", "Μάρτιος", "Απρίλιος", "Μάιος", "Ιούνιος", "Ιούλιος", "Αύγουστος", "Σεπτέμβριος", "Οκτώβριος", "Νοέμβριος", "Δεκέμβριος"])
            selected_year = c_y.selectbox("Έτος:", ["2023", "2024", "2025", "2026", "2027"], index=1)
            period = f"{selected_month} {selected_year}"

        with top_right:
            st.subheader("➕ Νέος Υπάλληλος")
            # Πιο μαζεμένη καταχώρηση σε 2 γραμμές
            r1_c1, r1_c2 = st.columns([2, 1])
            new_emp_name = r1_c1.text_input("Ονοματεπώνυμο", placeholder="ΕΠΩΝΥΜΟ ΟΝΟΜΑ", key="new_emp_name_in")
            new_emp_afm = r1_c2.text_input("ΑΦΜ", key="new_emp_afm_in", max_chars=9)
            
            r2_c1, r2_c2 = st.columns([2, 1])
            new_emp_amka = r2_c1.text_input("ΑΜΚΑ", key="new_emp_amka_in", max_chars=11)
            if r2_c2.button("📥 Αποθήκευση", use_container_width=True):
                if new_emp_name and new_emp_afm:
                    emp_df = load_data(EMPLOYEES_FILE, ["ΑΦΜ_Εργου", "Ονοματεπώνυμο", "ΑΦΜ_Υπαλλήλου", "ΑΜΚΑ_Υπαλλήλου"])
                    mask = (emp_df['ΑΦΜ_Εργου'].astype(str) == selected_afm) & (emp_df['ΑΦΜ_Υπαλλήλου'].astype(str) == new_emp_afm)
                    if not emp_df[mask].empty:
                        emp_df.loc[mask, ["Ονοματεπώνυμο", "ΑΜΚΑ_Υπαλλήλου"]] = [new_emp_name, new_emp_amka]
                    else:
                        new_row = pd.DataFrame([{"ΑΦΜ_Εργου": selected_afm, "Ονοματεπώνυμο": new_emp_name, "ΑΦΜ_Υπαλλήλου": new_emp_afm, "ΑΜΚΑ_Υπαλλήλου": new_emp_amka}])
                        emp_df = pd.concat([emp_df, new_row], ignore_index=True)
                    save_to_csv(emp_df, EMPLOYEES_FILE)
                    st.rerun()

        st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)

        # --- ΚΑΤΩ ΜΕΡΟΣ: ΕΠΙΛΟΓΗ ΚΑΙ ΕΛΕΓΧΟΣ ---
        all_emps_df = load_data(EMPLOYEES_FILE, ["ΑΦΜ_Εργου", "Ονοματεπώνυμο", "ΑΦΜ_Υπαλλήλου", "ΑΜΚΑ_Υπαλλήλου"])
        current_emps = all_emps_df[all_emps_df['ΑΦΜ_Εργου'].astype(str) == selected_afm]
        emp_options = current_emps.apply(lambda x: f"{x['Ονοματεπώνυμο']} (ΑΦΜ: {x['ΑΦΜ_Υπαλλήλου']})", axis=1).tolist()

        if not emp_options:
            st.info("💡 Η λίστα υπαλλήλων είναι κενή.")
        else:
            sel_col1, sel_col2 = st.columns([2, 1])
            selected_option = sel_col1.selectbox("🔍 Επιλογή Υπαλλήλου για Έλεγχο:", ["--- Επιλογή ---"] + emp_options, label_visibility="collapsed")
            
            if selected_option != "--- Επιλογή ---":
                sel_emp_afm = selected_option.split("(ΑΦΜ: ")[1].replace(")", "")
                emp_data = current_emps[current_emps['ΑΦΜ_Υπαλλήλου'].astype(str) == sel_emp_afm].iloc[0]
                
                st.markdown(f"<div style='background-color:#f0f2f6; padding:10px; border-radius:5px; margin-bottom:15px;'>"
                            f"👤 <b>{emp_data['Ονοματεπώνυμο']}</b> | ΑΜΚΑ: {emp_data['ΑΜΚΑ_Υπαλλήλου']} | Περίοδος: {period}</div>", unsafe_allow_html=True)
                
                audit_df = load_data(PAYROLL_CHECKS_FILE, ["ID_Κλειδί", "Έγγραφο", "Κατάσταση", "Σχόλιο"])

                # ΣΥΝΑΡΤΗΣΗ ΓΙΑ ΜΙΚΡΟΤΕΡΑ ΚΕΝΑ ΣΤΙΣ ΓΡΑΜΜΕΣ
                def render_check_row(label, key_id, current_df):
                    existing = current_df[current_df['ID_Κλειδί'] == key_id]
                    val = existing['Κατάσταση'].iloc[0] if not existing.empty else "Έλλειψη ❌"
                    note = existing['Σχόλιο'].iloc[0] if not existing.empty and pd.notna(existing['Σχόλιο'].iloc[0]) else ""
                    
                    c1, c2, c3 = st.columns([1.5, 1, 2], gap="small")
                    c1.markdown(f"<div style='font-size:0.85rem; padding-top:5px;'>{label}</div>", unsafe_allow_html=True)
                    res_stat = c2.selectbox("", ["Έλλειψη ❌", "Υπάρχει ✅", "Δεν απαιτείται"], index=["Έλλειψη ❌", "Υπάρχει ✅", "Δεν απαιτείται"].index(val), key=f"s_{key_id}", label_visibility="collapsed")
                    res_note = c3.text_input("", value=note, key=f"n_{key_id}", label_visibility="collapsed", placeholder="Σχόλιο...")
                    return {"ID_Κλειδί": key_id, "Έγγραφο": label, "Κατάσταση": res_stat, "Σχόλιο": res_note}

                # Εμφάνιση ελέγχων
                all_results = []
                st.caption("📌 ΚΕΝΤΡΙΚΑ ΔΙΚΑΙΟΛΟΓΗΤΙΚΑ")
                all_results.append(render_check_row("Αναγγελία Πρόσληψης (Ε3)", f"PERM_{selected_afm}_{sel_emp_afm}_E3", audit_df))
                all_results.append(render_check_row("Ταυτότητα Εργαζομένου", f"PERM_{selected_afm}_{sel_emp_afm}_ID", audit_df))
                
                st.markdown("<div style='margin:10px 0;'></div>", unsafe_allow_html=True)
                st.caption(f"📅 ΜΗΝΙΑΙΑ ΠΑΡΑΔΟΤΕΑ ({period})")
                m_docs = ["Extrait", "Έμβασμα Πληρωμής", "Λογιστικό άρθρο καταχώρησης", "Λογιστικό άρθρο πληρωμής", "Βιβλίο εσόδων-εξόδων"]
                for md in m_docs:
                    all_results.append(render_check_row(md, f"MONTH_{selected_afm}_{sel_emp_afm}_{period}_{md}", audit_df))

                # Κουμπιά στο τέλος
                st.write("")
                b1, b2, _ = st.columns([1, 1, 2])
                if b1.button("💾 Αποθήκευση Ελέγχου", use_container_width=True):
                    new_keys = [r['ID_Κλειδί'] for r in all_results]
                    audit_df = audit_df[~audit_df['ID_Κλειδί'].isin(new_keys)]
                    save_to_csv(pd.concat([audit_df, pd.DataFrame(all_results)], ignore_index=True), PAYROLL_CHECKS_FILE)
                    st.toast("Αποθηκεύτηκε!")
                
                if b2.button("🗑️ Διαγραφή Υπαλλήλου", use_container_width=True):
                    all_emps_df = all_emps_df[~((all_emps_df['ΑΦΜ_Εργου'].astype(str) == selected_afm) & (all_emps_df['ΑΦΜ_Υπαλλήλου'].astype(str) == sel_emp_afm))]
                    save_to_csv(all_emps_df, EMPLOYEES_FILE)
                    st.rerun()
