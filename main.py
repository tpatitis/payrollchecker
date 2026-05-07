import streamlit as st
import pandas as pd
import os

# --- 1. ΡΥΘΜΙΣΗ ΣΕΛΙΔΑΣ ---
st.set_page_config(
    page_title="Payroll Verifier Pro",
    page_icon="🛡️",
    layout="wide"
)

# --- 2. ΑΡΧΕΙΑ ΔΕΔΟΜΕΝΩΝ ---
PROJECTS_FILE = 'data_projects.csv'
CHECKLIST_FILE = 'checklist_results.csv'
EMPLOYEES_FILE = 'data_employees.csv'

# --- 3. ΣΥΝΑΡΤΗΣΕΙΣ ΔΙΑΧΕΙΡΙΣΗΣ ΔΕΔΟΜΕΝΩΝ ---
def load_data(filename, columns):
    """Φορτώνει δεδομένα και αν το αρχείο λείπει ή είναι κενό, επιστρέφει κενό DataFrame με στήλες"""
    if not os.path.isfile(filename) or os.path.getsize(filename) == 0:
        return pd.DataFrame(columns=columns)
    try:
        return pd.read_csv(filename)
    except Exception:
        return pd.DataFrame(columns=columns)

def save_to_csv(df, filename):
    """Αποθηκεύει δεδομένα σε CSV"""
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
                    st.success("Αποθηκεύτηκε!")
                    st.rerun()

    df_list = load_data(PROJECTS_FILE, ["Επωνυμία", "ΑΦΜ", "MIS", "Προϋπολογισμός"])
    if not df_list.empty:
        st.divider()
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
    st.header("📂 Γενικά παραδοτέα μισθοδοσίας")
    projects_df = load_data(PROJECTS_FILE, ["Επωνυμία", "ΑΦΜ"])
    
    if projects_df.empty:
        st.warning("⚠️ Καταχωρήστε μια επιχείρηση στο Στάδιο 1.")
    else:
        selected_name = st.selectbox("Επιλέξτε Επιχείρηση:", projects_df['Επωνυμία'])
        selected_afm = str(projects_df[projects_df['Επωνυμία'] == selected_name]['ΑΦΜ'].iloc[0])
        check_df = load_data(CHECKLIST_FILE, ["ΑΦΜ", "Εγγραφο", "Κατάσταση", "Σχόλιο"])
        
        required_docs = ["Πίνακας Προσωπικού Ε4", "Μισθολογικές καταστάσεις", "ΑΠΔ ΕΦΚΑ", "Αποδεικτικό Υποβολής ΑΠΔ", "ΑΠΔ ΤΕΚΑ", "Αποδεικτικό Υποβολής ΑΠΔ ΤΕΚΑ", "Υπεύθυνη δήλωση συγγενών", "Επιστολή γνωστοποίησης", "Ασφαλιστική ενημερότητα", "Οικονομική καρτέλα ΕΦΚΑ", "Ηλεκτρονική καρτέλα οφειλετών", "Πίνακας χρεών οφειλέτη", "Ανάλυση κίνησης Ηλ. Καρτέλας", "Φορολογική ενημερότητα", "Στοιχεία ρυθμίσεων & Πληρωμή", "Προσωρινές δηλώσεις ΦΜΥ"]
        
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

        if st.button(f"💾 Αποθήκευση για {selected_name}"):
            check_df = check_df[check_df['ΑΦΜ'].astype(str) != selected_afm]
            new_data = pd.DataFrame(results)
            save_to_csv(pd.concat([check_df, new_data], ignore_index=True), CHECKLIST_FILE)
            st.success("Αποθηκεύτηκε!")
            st.rerun()

# --- ΣΤΑΔΙΟ 3: ΜΙΣΘΟΔΟΣΙΑ ΥΠΑΛΛΗΛΩΝ ---
elif page == "3. Μισθοδοσία Υπαλλήλων":
    st.header("👤 Διαχείριση & Έλεγχος Υπαλλήλων")
    
    projects_df = load_data(PROJECTS_FILE, ["Επωνυμία", "ΑΦΜ"])
    
    if projects_df.empty:
        st.warning("⚠️ Παρακαλώ καταχωρήστε πρώτα μια επιχείρηση στο Στάδιο 1.")
    else:
        # 1. Επιλογή Επιχείρησης & Μήνα
        col_sel1, col_sel2 = st.columns(2)
        with col_sel1:
            selected_project = st.selectbox("Επιλέξτε Επιχείρηση:", projects_df['Επωνυμία'], key="p_select")
            selected_afm = str(projects_df[projects_df['Επωνυμία'] == selected_project]['ΑΦΜ'].iloc[0])
        with col_sel2:
            selected_month = st.selectbox("Μήνας Ελέγχου:", ["Ιανουάριος", "Φεβρουάριος", "Μάρτιος", "Απρίλιος", "Μάιος", "Ιούνιος", "Ιούλιος", "Αύγουστος", "Σεπτέμβριος", "Οκτώβριος", "Νοέμβριος", "Δεκέμβριος"])

        st.divider()

        # 2. ΠΕΔΙΟ ΣΥΜΠΛΗΡΩΣΗΣ ΣΤΟΙΧΕΙΩΝ
        st.subheader(f"➕ Καταχώρηση Νέου Υπαλλήλου ({selected_project})")
        with st.container():
            c1, c2, c3 = st.columns([2, 1, 1])
            new_emp_name = c1.text_input("Ονοματεπώνυμο", placeholder="ΕΠΩΝΥΜΟ ΟΝΟΜΑ", key="new_emp_name_in")
            new_emp_id = c2.text_input("ΑΦΜ (Προαιρετικό)", key="new_emp_afm_in")
            
            if c3.button("📥 Αποθήκευση στη Λίστα", use_container_width=True):
                if new_emp_name:
                    emp_df = load_data(EMPLOYEES_FILE, ["ΑΦΜ_Εργου", "Ονοματεπώνυμο", "ΑΦΜ_Υπαλλήλου"])
                    exists = emp_df[(emp_df['ΑΦΜ_Εργου'].astype(str) == selected_afm) & (emp_df['Ονοματεπώνυμο'] == new_emp_name)]
                    
                    if exists.empty:
                        new_row = pd.DataFrame([{"ΑΦΜ_Εργου": selected_afm, "Ονοματεπώνυμο": new_emp_name, "ΑΦΜ_Υπαλλήλου": new_emp_id}])
                        emp_df = pd.concat([emp_df, new_row], ignore_index=True)
                        save_to_csv(emp_df, EMPLOYEES_FILE)
                        st.success(f"Ο υπάλληλος {new_emp_name} προστέθηκε!")
                        st.rerun()
                    else:
                        st.warning("Ο υπάλληλος είναι ήδη καταχωρημένος.")

        st.divider()

        # 3. DROPDOWN MENU ΕΠΙΛΟΓΗΣ
        st.subheader("🔍 Επιλογή Υπαλλήλου για Έλεγχο")
        all_emps_df = load_data(EMPLOYEES_FILE, ["ΑΦΜ_Εργου", "Ονοματεπώνυμο", "ΑΦΜ_Υπαλλήλου"])
        current_list = all_emps_df[all_emps_df['ΑΦΜ_Εργου'].astype(str) == selected_afm]['Ονοματεπώνυμο'].tolist()

        if not current_list:
            st.info("Η λίστα υπαλλήλων είναι κενή. Προσθέστε υπαλλήλους παραπάνω.")
        else:
            selected_emp = st.selectbox("Επιλέξτε από τους καταχωρημένους:", ["--- Λίστα Υπαλλήλων ---"] + current_list)

            if selected_emp != "--- Λίστα Υπαλλήλων ---":
                st.success(f"Επιλέχθηκε: {selected_emp} | Μήνας: {selected_month}")
                
                # Εδώ θα μπουν τα έγγραφα υπαλλήλου
                st.write("*(Εδώ θα ορίσουμε τα έγγραφα του υπαλλήλου)*")
                
                if st.button("🗑️ Διαγραφή Υπαλλήλου από τη βάση"):
                    all_emps_df = all_emps_df[~((all_emps_df['ΑΦΜ_Εργου'].astype(str) == selected_afm) & 
                                               (all_emps_df['Ονοματεπώνυμο'] == selected_emp))]
                    save_to_csv(all_emps_df, EMPLOYEES_FILE)
                    st.rerun()
