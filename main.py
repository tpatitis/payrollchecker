import streamlit as st
import pandas as pd
import os

# --- ΡΥΘΜΙΣΗ ΣΕΛΙΔΑΣ ---
st.set_page_config(
    page_title="Payroll Verifier Pro",
    page_icon="🛡️",
    layout="wide"
)

# --- ΑΡΧΕΙΑ ΔΕΔΟΜΕΝΩΝ ---
PROJECTS_FILE = 'data_projects.csv'
CHECKLIST_FILE = 'checklist_results.csv'

# --- ΣΥΝΑΡΤΗΣΕΙΣ ΔΙΑΧΕΙΡΙΣΗΣ ΔΕΔΟΜΕΝΩΝ ---
def load_data(filename, columns):
    """Φορτώνει δεδομένα και χειρίζεται περιπτώσεις κενού αρχείου"""
    if not os.path.isfile(filename) or os.path.getsize(filename) == 0:
        return pd.DataFrame(columns=columns)
    try:
        return pd.read_csv(filename)
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=columns)

def save_to_csv(df, filename):
    """Αποθηκεύει το DataFrame σε CSV με σωστό encoding"""
    df.to_csv(filename, index=False, encoding='utf-8-sig')

# --- ΠΛΕΥΡΙΚΟ ΜΕΝΟΥ (NAVIGATION) ---
st.sidebar.title("📑 Μενού Διαχείρισης")
st.sidebar.divider()
page = st.sidebar.radio(
    "Μετάβαση σε:",
    ["1. Διαχείριση Έργων", 
     "2. Checklist ανά Έργο", 
     "3. Μισθοδοσία Υπαλλήλων"]
)

# --- ΣΤΑΔΙΟ 1: ΔΙΑΧΕΙΡΙΣΗ ΕΡΓΩΝ (CRUD) ---
if page == "1. Διαχείριση Έργων":
    st.header("🏢 Διαχείριση Επιχειρήσεων")
    
    # Φόρμα Καταχώρησης / Επεξεργασίας
    with st.expander("➕ Προσθήκη / Επεξεργασία Έργου", expanded=True):
        with st.form("project_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Επωνυμία Επιχείρησης")
                afm = st.text_input("ΑΦΜ (9 ψηφία)", max_chars=9)
            with col2:
                mis = st.text_input("Κωδικός Έργου (MIS)")
                budget = st.number_input("Συνολικός Προϋπολογισμός (€)", min_value=0.0, step=100.0)
            
            if st.form_submit_button("💾 Αποθήκευση Στοιχείων"):
                if name and afm:
                    df = load_data(PROJECTS_FILE, ["Επωνυμία", "ΑΦΜ", "MIS", "Προϋπολογισμός"])
                    # Αν το ΑΦΜ υπάρχει, ενημέρωσε. Αν όχι, πρόσθεσε.
                    if afm in df['ΑΦΜ'].astype(str).values:
                        df.loc[df['ΑΦΜ'].astype(str) == afm, ["Επωνυμία", "MIS", "Προϋπολογισμός"]] = [name, mis, budget]
                        st.info(f"Ενημερώθηκαν τα στοιχεία του ΑΦΜ: {afm}")
                    else:
                        new_row = pd.DataFrame([{"Επωνυμία": name, "ΑΦΜ": afm, "MIS": mis, "Προϋπολογισμός": budget}])
                        df = pd.concat([df, new_row], ignore_index=True)
                        st.success(f"Το έργο '{name}' προστέθηκε!")
                    
                    save_to_csv(df, PROJECTS_FILE)
                    st.rerun()
                else:
                    st.warning("Συμπληρώστε Επωνυμία και ΑΦΜ.")

    # Προβολή και Διαγραφή
    df_list = load_data(PROJECTS_FILE, ["Επωνυμία", "ΑΦΜ", "MIS", "Προϋπολογισμός"])
    if not df_list.empty:
        st.divider()
        st.subheader("📋 Λίστα Καταχωρημένων Έργων")
        for i, row in df_list.iterrows():
            with st.container():
                c1, c2, c3, c4 = st.columns([3, 2, 1, 0.5])
                c1.write(f"**{row['Επωνυμία']}**")
                c2.write(f"ΑΦΜ: {row['ΑΦΜ']} | MIS: {row['MIS']}")
                c3.write(f"{row['Προϋπολογισμός']} €")
                if c4.button("🗑️", key=f"del_{row['ΑΦΜ']}"):
                    df_list = df_list.drop(i)
                    save_to_csv(df_list, PROJECTS_FILE)
                    st.rerun()
                st.divider()

# --- ΣΤΑΔΙΟ 2: CHECKLIST ΑΝΑ ΕΡΓΟ ---
elif page == "2. Checklist ανά Έργο":
    st.header("📂 Γενικά παραδοτέα μισθοδοσίας (checklist)")
    projects_df = load_data(PROJECTS_FILE, ["Επωνυμία", "ΑΦΜ", "MIS"])
    
    if projects_df.empty:
        st.warning("⚠️ Παρακαλώ καταχωρήστε πρώτα μια επιχείρηση στο Στάδιο 1.")
    else:
        # Επιλογή Έργου
        selected_name = st.selectbox("Επιλέξτε Επιχείρηση για έλεγχο:", projects_df['Επωνυμία'])
        selected_afm = str(projects_df[projects_df['Επωνυμία'] == selected_name]['ΑΦΜ'].iloc[0])

        # Φόρτωση παλιών απαντήσεων
        check_df = load_data(CHECKLIST_FILE, ["ΑΦΜ", "Εγγραφο", "Κατάσταση", "Σχόλιο"])
        
        required_docs = [
            "Πίνακας Προσωπικού Ε4", "Μισθολογικές καταστάσεις", "ΑΠΔ ΕΦΚΑ", "Αποδεικτικό Υποβολής ΑΠΔ",
            "ΑΠΔ ΤΕΚΑ", "Αποδεικτικό Υποβολής ΑΠΔ ΤΕΚΑ", "Υπεύθυνη δήλωση συγγενών", "Επιστολή γνωστοποίησης", 
            "Ασφαλιστική ενημερότητα", "Οικονομική καρτέλα ΕΦΚΑ",
            "Ηλεκτρονική καρτέλα οφειλετών", "Πίνακας χρεών οφειλέτη",
            "Ανάλυση κίνησης Ηλ. Καρτέλας", "Φορολογική ενημερότητα",
            "Στοιχεία ρυθμίσεων & Πληρωμή", "Προσωρινές δηλώσεις ΦΜΥ"
        ]
        
        st.subheader(f"📋 Έλεγχος Φακέλου: {selected_name}")
        
        # Επικεφαλίδες Πίνακα
        h1, h2, h3 = st.columns([1.2, 0.8, 3.0], gap="small")
        h1.caption("📄 Έγγραφο")
        h2.caption("📊 Κατάσταση")
        h3.caption("📝 Παρατήρηση")
        st.divider()

        options = ["Έλλειψη ❌", "Υπάρχει ✅", "Δεν απαιτείται"]
        results = []

        for doc in required_docs:
            existing = check_df[(check_df['ΑΦΜ'].astype(str) == selected_afm) & (check_df['Εγγραφο'] == doc)]
            
            if not existing.empty:
                current_val = existing['Κατάσταση'].iloc[0]
                current_note = existing['Σχόλιο'].iloc[0] if pd.notna(existing['Σχόλιο'].iloc[0]) else ""
            else:
                current_val = "Έλλειψη ❌"
                current_note = ""

            # Διάταξη με extra_small gap και ελάχιστο padding
            c1, c2, c3 = st.columns([1.2, 0.8, 3.0], gap="small")
            c1.markdown(f"<div style='padding-top:2px; font-size:0.85rem; line-height:1.2;'><b>{doc}</b></div>", unsafe_allow_html=True)
            
            status = c2.selectbox("", options, index=options.index(current_val) if current_val in options else 0, key=f"st_{selected_afm}_{doc}", label_visibility="collapsed")
            note = c3.text_input("Σχόλιο...", value=current_note, key=f"nt_{selected_afm}_{doc}", label_visibility="collapsed")
            
            results.append({"ΑΦΜ": selected_afm, "Εγγραφο": doc, "Κατάσταση": status, "Σχόλιο": note})

        st.divider()
        # Γενικές Σημειώσεις ανά Έργο
        gen_existing = check_df[(check_df['ΑΦΜ'].astype(str) == selected_afm) & (check_df['Εγγραφο'] == "ΓΕΝΙΚΕΣ ΣΗΜΕΙΩΣΕΙΣ")]
        prev_gen_note = gen_existing['Σχόλιο'].iloc[0] if not gen_existing.empty else ""
        
        st.subheader("📝 Γενικές Σημειώσεις Ελέγχου")
        general_notes = st.text_area("Συνολικές παρατηρήσεις...", value=prev_gen_note, key=f"gen_note_{selected_afm}", label_visibility="collapsed")

        if st.button(f"💾 Αποθήκευση Checklist για {selected_name}"):
            check_df = check_df[check_df['ΑΦΜ'].astype(str) != selected_afm]
            new_data = pd.DataFrame(results)
            gen_note_row = pd.DataFrame([{"ΑΦΜ": selected_afm, "Εγγραφο": "ΓΕΝΙΚΕΣ ΣΗΜΕΙΩΣΕΙΣ", "Κατάσταση": "-", "Σχόλιο": general_notes}])
            final_df = pd.concat([check_df, new_data, gen_note_row], ignore_index=True)
            save_to_csv(final_df, CHECKLIST_FILE)
            st.success(f"✅ Αποθηκεύτηκε!")
            st.rerun()

# --- ΣΤΑΔΙΟ 3: ΜΙΣΘΟΔΟΣΙΑ ---
elif page == "3. Μισθοδοσία":
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

        # 2. ΠΕΔΙΟ ΣΥΜΠΛΗΡΩΣΗΣ ΣΤΟΙΧΕΙΩΝ (Καταχώρηση)
        st.subheader(f"➕ Προσθήκη Υπαλλήλου στην επιχείρηση {selected_project}")
        with st.container():
            c1, c2, c3 = st.columns([2, 1, 1])
            new_emp_name = c1.text_input("Ονοματεπώνυμο Υπαλλήλου", placeholder="π.χ. ΠΑΠΑΔΟΠΟΥΛΟΣ ΙΩΑΝΝΗΣ")
            new_emp_id = c2.text_input("ΑΦΜ Υπαλλήλου (Προαιρετικό)")
            
            if c3.button("📥 Καταχώρηση Υπαλλήλου", use_container_width=True):
                if new_emp_name:
                    emp_df = load_data('data_employees.csv', ["ΑΦΜ_Εργου", "Ονοματεπώνυμο", "ΑΦΜ_Υπαλλήλου"])
                    # Έλεγχος αν υπάρχει ήδη ο υπάλληλος στην ίδια επιχείρηση
                    exists = emp_df[(emp_df['ΑΦΜ_Εργου'].astype(str) == selected_afm) & 
                                    (emp_df['Ονοματεπώνυμο'] == new_emp_name)]
                    
                    if exists.empty:
                        new_row = pd.DataFrame([{"ΑΦΜ_Εργου": selected_afm, "Ονοματεπώνυμο": new_emp_name, "ΑΦΜ_Υπαλλήλου": new_emp_id}])
                        emp_df = pd.concat([emp_df, new_row], ignore_index=True)
                        save_to_csv(emp_df, 'data_employees.csv')
                        st.success(f"Ο υπάλληλος {new_emp_name} αποθηκεύτηκε!")
                        st.rerun()
                    else:
                        st.warning("Ο υπάλληλος υπάρχει ήδη σε αυτή την επιχείρηση.")
                else:
                    st.error("Συμπληρώστε το όνομα του υπαλλήλου.")

        st.divider()

        # 3. DROPDOWN MENU ΕΠΙΛΟΓΗΣ (Από τους αποθηκευμένους)
        st.subheader("🔍 Επιλογή Υπαλλήλου για Έλεγχο")
        all_emps_df = load_data('data_employees.csv', ["ΑΦΜ_Εργου", "Ονοματεπώνυμο", "ΑΦΜ_Υπαλλήλου"])
        # Φιλτράρισμα υπαλλήλων μόνο για την επιλεγμένη επιχείρηση
        current_project_emps = all_emps_df[all_emps_df['ΑΦΜ_Εργου'].astype(str) == selected_afm]['Ονοματεπώνυμο'].tolist()

        if not current_project_emps:
            st.info("Δεν υπάρχουν αποθηκευμένοι υπάλληλοι για αυτή την επιχείρηση. Καταχωρήστε έναν παραπάνω.")
        else:
            selected_emp = st.selectbox("Επιλέξτε Υπάλληλο από τη λίστα:", ["--- Επιλέξτε ---"] + current_project_emps)

            if selected_emp != "--- Επιλέξτε ---":
                st.info(f"📍 Έλεγχος Παραδοτέων: **{selected_emp}** | Μήνας: **{selected_month}**")
                
                # Εδώ θα έρθουν τα πεδία των παραδοτέων που θα ορίσουμε στη συνέχεια
                st.write("*(Εδώ θα προστεθούν τα checkbox/upload για τα έγγραφα του υπαλλήλου)*")
                
                if st.button("🗑️ Διαγραφή Υπαλλήλου από το αρχείο"):
                    all_emps_df = all_emps_df[~((all_emps_df['ΑΦΜ_Εργου'].astype(str) == selected_afm) & 
                                               (all_emps_df['Ονοματεπώνυμο'] == selected_emp))]
                    save_to_csv(all_emps_df, 'data_employees.csv')
                    st.rerun()
