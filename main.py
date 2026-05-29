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
        
        # Καθαρίζουμε το ΑΦΜ από κενά για σωστή ταυτοποίηση
        selected_afm = str(projects_df[projects_df['Επωνυμία'] == selected_name]['ΑΦΜ'].iloc[0]).strip()
        
        check_df = load_data(CHECKLIST_FILE, ["ΑΦΜ", "Εγγραφο", "Κατάσταση", "Σχόλιο"])
        
        # Εξασφαλίζουμε ότι η στήλη ΑΦΜ στο αρχείο διαβάζεται σωστά ως κείμενο
        if not check_df.empty:
            check_df['ΑΦΜ'] = check_df['ΑΦΜ'].astype(str).str.strip()
            
        required_docs = [
            "Πίνακας Προσωπικού Ε4", "Μισθολογικές καταστάσεις", "ΑΠΔ ΕΦΚΑ", 
            "Αποδεικτικό Υποβολής ΑΠΔ", "ΑΠΔ ΤΕΚΑ", "Αποδεικτικό Υποβολής ΑΠΔ ΤΕΚΑ", 
            "Υπεύθυνη δήλωση συγγενών", "Επιστολή γνωστοποίησης", "Ασφαλιστική ενημερότητα", 
            "Οικονομική καρτέλα ΕΦΚΑ", "Ηλεκτρονική καρτέλα οφειλετών", "Πίνακας χρεών οφειλέτη", 
            "Ανάλυση κίνησης Ηλ. Καρτέλας", "Φορολογική ενημερότητα", "Στοιχεία ρυθμίσεων & Πληρωμή", 
            "Προσωρινές δηλώσεις ΦΜΥ"
        ]
        
        results = []
        for doc in required_docs:
            # Φιλτράρισμα βάσει του συγκεκριμένου ΑΦΜ
            existing = check_df[(check_df['ΑΦΜ'] == selected_afm) & (check_df['Εγγραφο'] == doc)]
            
            c1, c2, c3 = st.columns([1.5, 1.0, 2.5], gap="small")
            c1.markdown(f"<div style='font-size:0.85rem; padding-top:5px;'><b>{doc}</b></div>", unsafe_allow_html=True)
            
            # ΔΙΟΡΘΩΣΗ: Προσθήκη του selected_afm στο key για να είναι μοναδικό ανά επιχείρηση
            status = c2.selectbox(
                "", 
                ["Έλλειψη ❌", "Υπάρχει ✅", "Δεν απαιτείται"], 
                index=["Έλλειψη ❌", "Υπάρχει ✅", "Δεν απαιτείται"].index(existing['Κατάσταση'].iloc[0]) if not existing.empty else 0, 
                key=f"gen_{selected_afm}_{doc}", 
                label_visibility="collapsed"
            )
            
            # ΔΙΟΡΘΩΣΗ: Προσθήκη του selected_afm στο key του text_input
            note = c3.text_input(
                "", 
                value=existing['Σχόλιο'].iloc[0] if not existing.empty else "", 
                key=f"gen_n_{selected_afm}_{doc}", 
                label_visibility="collapsed",
                placeholder="Σχόλιο..."
            )
            
            results.append({"ΑΦΜ": selected_afm, "Εγγραφο": doc, "Κατάσταση": status, "Σχόλιο": note})
            
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾 Αποθήκευση Checklist", use_container_width=True):
            # Κρατάμε τις υπόλοιπες επιχειρήσεις και αντικαθιστούμε μόνο την τρέχουσα
            check_df = check_df[check_df['ΑΦΜ'] != selected_afm]
            save_to_csv(pd.concat([check_df, pd.DataFrame(results)], ignore_index=True), CHECKLIST_FILE)
            st.success(f"✅ Το checklist για την επιχείρηση '{selected_name}' αποθηκεύτηκε επιτυχώς!")
            st.rerun()

# --- ΣΤΑΔΙΟ 3: ΜΙΣΘΟΔΟΣΙΑ ΥΠΑΛΛΗΛΩΝ ---
elif page == "3. Μισθοδοσία Υπαλλήλων":
    st.header("👤 Διαχείριση & Έλεγχος Υπαλλήλων")
    projects_df = load_data(PROJECTS_FILE, ["Επωνυμία", "ΑΦΜ"])
    
    if projects_df.empty:
        st.warning("⚠️ Καταχωρήστε μια επιχείρηση στο Στάδιο 1.")
    else:
        top_l, top_r = st.columns([1, 1.2], gap="large")
        with top_l:
            st.subheader("🏢 Επιλογή Στοιχείων")
            selected_project = st.selectbox("Επιχείρηση:", projects_df['Επωνυμία'])
            selected_afm = str(projects_df[projects_df['Επωνυμία'] == selected_project]['ΑΦΜ'].iloc[0])
            c_m, c_y = st.columns(2)
            selected_month = c_m.selectbox("Μήνας:", ["Ιανουάριος", "Φεβρουάριος", "Μάρτιος", "Απρίλιος", "Μάιος", "Ιούνιος", "Ιούλιος", "Αύγουστος", "Σεπτέμβριος", "Οκτώβριος", "Νοέμβριος", "Δεκέμβριος"])
            selected_year = c_y.selectbox("Έτος:", ["2023", "2024", "2025", "2026", "2027"], index=1)
            period = f"{selected_month} {selected_year}"

        with top_r:
            st.subheader("➕ Καταχώρηση / Ενημέρωση")
            r1c1, r1c2 = st.columns([2, 1])
            new_emp_name = r1c1.text_input("Ονοματεπώνυμο", key="n_name")
            new_emp_afm = r1c2.text_input("ΑΦΜ", max_chars=9, key="n_afm")
            r2c1, r2c2 = st.columns([2, 1])
            new_emp_amka = r2c1.text_input("ΑΜΚΑ", max_chars=11, key="n_amka")
            if r2c2.button("📥 Αποθήκευση", use_container_width=True):
                if new_emp_name and new_emp_afm:
                    emp_df = load_data(EMPLOYEES_FILE, ["ΑΦΜ_Εργου", "Ονοματεπώνυμο", "ΑΦΜ_Υπαλλήλου", "ΑΜΚΑ_Υπαλλήλου"])
                    mask = (emp_df['ΑΦΜ_Εργου'].astype(str) == selected_afm) & (emp_df['ΑΦΜ_Υπαλλήλου'].astype(str) == new_emp_afm)
                    if not emp_df[mask].empty:
                        emp_df.loc[mask, ["Ονοματεπώνυμο", "ΑΜΚΑ_Υπαλλήλου"]] = [new_emp_name, new_emp_amka]
                    else:
                        emp_df = pd.concat([emp_df, pd.DataFrame([{"ΑΦΜ_Εργου": selected_afm, "Ονοματεπώνυμο": new_emp_name, "ΑΦΜ_Υπαλλήλου": new_emp_afm, "ΑΜΚΑ_Υπαλλήλου": new_emp_amka}])], ignore_index=True)
                    save_to_csv(emp_df, EMPLOYEES_FILE)
                    st.rerun()

        st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)

        all_emps_df = load_data(EMPLOYEES_FILE, ["ΑΦΜ_Εργου", "Ονοματεπώνυμο", "ΑΦΜ_Υπαλλήλου", "ΑΜΚΑ_Υπαλλήλου"])
        current_emps = all_emps_df[all_emps_df['ΑΦΜ_Εργου'].astype(str) == selected_afm]
        emp_opts = current_emps.apply(lambda x: f"{x['Ονοματεπώνυμο']} (ΑΦΜ: {x['ΑΦΜ_Υπαλλήλου']})", axis=1).tolist()

        if not emp_opts:
            st.info("💡 Η λίστα υπαλλήλων είναι κενή.")
        else:
            selected_option = st.selectbox("🔍 Επιλογή Υπαλλήλου:", ["--- Επιλογή ---"] + emp_opts)
            if selected_option != "--- Επιλογή ---":
                sel_emp_afm = selected_option.split("(ΑΦΜ: ")[1].replace(")", "")
                emp_data = current_emps[current_emps['ΑΦΜ_Υπαλλήλου'].astype(str) == sel_emp_afm].iloc[0]
                fin_key = f"FIN_{selected_afm}_{sel_emp_afm}_{period}"
                
                st.markdown(f"<div style='background-color:#f0f2f6; padding:10px; border-radius:5px; margin-bottom:15px; font-size:0.9rem;'>"
                            f"👤 <b>{emp_data['Ονοματεπώνυμο']}</b> | ΑΜΚΑ: {emp_data['ΑΜΚΑ_Υπαλλήλου']} | Περίοδος: {period}</div>", unsafe_allow_html=True)
                
                # --- ΕΛΕΓΧΟΣ ΔΙΚΑΙΟΛΟΓΗΤΙΚΩΝ ---
                audit_df = load_data(PAYROLL_CHECKS_FILE, ["ID_Κλειδί", "Έγγραφο", "Κατάσταση", "Σχόλιο"])
                all_results = []
                def draw_row(label, key_id):
                    existing = audit_df[audit_df['ID_Κλειδί'] == key_id]
                    c1, c2, c3 = st.columns([1.5, 1, 2], gap="small")
                    c1.markdown(f"<div style='font-size:0.85rem; padding-top:5px;'>{label}</div>", unsafe_allow_html=True)
                    stat = c2.selectbox("", ["Έλλειψη ❌", "Υπάρχει ✅", "Δεν απαιτείται"], index=["Έλλειψη ❌", "Υπάρχει ✅", "Δεν απαιτείται"].index(existing['Κατάσταση'].iloc[0]) if not existing.empty else 0, key=f"s_{key_id}", label_visibility="collapsed")
                    note = c3.text_input("", value=existing['Σχόλιο'].iloc[0] if not existing.empty else "", key=f"n_{key_id}", label_visibility="collapsed", placeholder="Σχόλιο...")
                    return {"ID_Κλειδί": key_id, "Έγγραφο": label, "Κατάσταση": stat, "Σχόλιο": note}

                st.caption("📌 ΚΕΝΤΡΙΚΑ ΔΙΚΑΙΟΛΟΓΗΤΙΚΑ")
                all_results.append(draw_row("Αναγγελία Πρόσληψης (Ε3)", f"PERM_{selected_afm}_{sel_emp_afm}_E3"))
                all_results.append(draw_row("Ταυτότητα Εργαζομένου", f"PERM_{selected_afm}_{sel_emp_afm}_ID"))
                st.caption(f"📅 ΜΗΝΙΑΙΑ ΠΑΡΑΔΟΤΕΑ ({period})")
                for md in ["Extrait", "Έμβασμα Πληρωμής", "Λογιστικό άρθρο καταχώρησης", "Λογιστικό άρθρο πληρωμής", "Βιβλίο εσόδων-εξόδων"]:
                    all_results.append(draw_row(md, f"MONTH_{selected_afm}_{sel_emp_afm}_{period}_{md}"))

                # --- ΟΙΚΟΝΟΜΙΚΑ ΣΤΟΙΧΕΙΑ (ΒΑΣΕΙ ΕΙΚΟΝΑΣ) ---
                st.markdown("<hr style='margin:15px 0;'>", unsafe_allow_html=True)
                st.subheader("💰 Οικονομικά Στοιχεία")
                uploaded_file = st.file_uploader("📂 Μεταφορτώστε τη Μισθοδοτική (OCR)", type=['png', 'jpg', 'jpeg', 'pdf'], key=f"up_{fin_key}")

                fin_df = load_data(FINANCIALS_FILE, ["ID_Κλειδί", "ΙΚΑ_Εργ", "ΙΚΑ_Εργοδ", "ΤΕΚΑ_Εργ", "ΤΕΚΑ_Εργοδ", "Σύνολο_Εισφ", "ΦΜΥ", "Καθαρές", "Σύνολο_Αποδ", "ΟΠΣΚΕ"])
                ext_fin = fin_df[fin_df['ID_Κλειδί'] == fin_key]
                def gv(k): return float(ext_fin[k].iloc[0]) if not ext_fin.empty and k in ext_fin.columns else 0.0

                c1, c2 = st.columns(2); v_ika_erg = c1.number_input("Εισφορές Εργαζομένου ΙΚΑ", value=gv("ΙΚΑ_Εργ"), format="%.2f"); v_ika_ergo = c2.number_input("Εισφορές Εργοδότη ΙΚΑ", value=gv("ΙΚΑ_Εργοδ"), format="%.2f")
                c3, c4 = st.columns(2); v_teka_erg = c3.number_input("Εισφορές Εργαζομένου ΤΕΚΑ", value=gv("ΤΕΚΑ_Εργ"), format="%.2f"); v_teka_ergo = c4.number_input("Εισφορές Εργοδότη ΤΕΚΑ", value=gv("ΤΕΚΑ_Εργοδ"), format="%.2f")
                c5, c6, c7 = st.columns(3); v_sum_eisf = c5.number_input("Σύνολο Εισφορών", value=gv("Σύνολο_Εισφ"), format="%.2f"); v_fmy = c6.number_input("ΦΜΥ Εργαζομένου", value=gv("ΦΜΥ"), format="%.2f"); v_net = c7.number_input("Καθαρές Αποδοχές", value=gv("Καθαρές"), format="%.2f")
                c8, c9, c10 = st.columns(3); v_total_ap = c8.number_input("Σύνολο Αποδοχών", value=gv("Σύνολο_Αποδ"), format="%.2f"); v_opske = c9.number_input("Αιτούμενο ΟΠΣΚΕ", value=gv("ΟΠΣΚΕ"), format="%.2f")
                
                calc_total = v_net + v_sum_eisf + v_fmy
                c10.markdown(f"<div style='background-color:#e8f5e9; padding:10px; border-radius:5px; border:1px solid #4caf50; text-align:center; margin-top:15px;'><small>Έλεγχος Αθροίσματος</small><br><b>{calc_total:,.2f} €</b></div>", unsafe_allow_html=True)

                if st.button("💾 Αποθήκευση Όλων", use_container_width=True):
                    # Save Checks
                    new_ks = [r['ID_Κλειδί'] for r in all_results]
                    audit_df = pd.concat([audit_df[~audit_df['ID_Κλειδί'].isin(new_ks)], pd.DataFrame(all_results)], ignore_index=True)
                    save_to_csv(audit_df, PAYROLL_CHECKS_FILE)
                    # Save Financials
                    fin_row = {"ID_Κλειδί": fin_key, "ΙΚΑ_Εργ": v_ika_erg, "ΙΚΑ_Εργοδ": v_ika_ergo, "ΤΕΚΑ_Εργ": v_teka_erg, "ΤΕΚΑ_Εργοδ": v_teka_ergo, "Σύνολο_Εισφ": v_sum_eisf, "ΦΜΥ": v_fmy, "Καθαρές": v_net, "Σύνολο_Αποδ": v_total_ap, "ΟΠΣΚΕ": v_opske}
                    fin_df = pd.concat([fin_df[fin_df['ID_Κλειδί'] != fin_key], pd.DataFrame([fin_row])], ignore_index=True)
                    save_to_csv(fin_df, FINANCIALS_FILE)
                    st.toast("✅ Επιτυχής αποθήκευση!")
