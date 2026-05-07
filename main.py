import streamlit as st
import pandas as pd
import os

# --- ΡΥΘΜΙΣΗ ΣΕΛΙΔΑΣ ---
st.set_page_config(
    page_title="Payroll Verifier Pro",
    page_icon="🛡️",
    layout="wide"
)

# --- ΣΥΝΑΡΤΗΣΕΙΣ ΔΙΑΧΕΙΡΙΣΗΣ ΔΕΔΟΜΕΝΩΝ (BACKEND) ---
def save_data(data_dict, filename):
    """Γενική συνάρτηση αποθήκευσης σε CSV"""
    df = pd.DataFrame([data_dict])
    file_exists = os.path.isfile(filename)
    df.to_csv(filename, mode='a', index=False, 
              header=not file_exists, encoding='utf-8-sig')

# --- ΠΛΕΥΡΙΚΟ ΜΕΝΟΥ ---
st.sidebar.title("📑 Μενού Διαχείρισης")
st.sidebar.divider()
page = st.sidebar.radio(
    "Μετάβαση σε:",
    ["1. Στοιχεία Έργου & Επιχείρησης", 
     "2. Γενικά Παραδοτέα (Checklist)", 
     "3. Μισθοδοσία Υπαλλήλων"]
)

# --- ΣΤΑΔΙΟ 1: ΣΤΟΙΧΕΙΑ ΕΡΓΟΥ ---
if page == "1. Στοιχεία Έργου & Επιχείρησης":
    st.header("🏢 Γενικά Στοιχεία Έργου & Επιχείρησης")
    
    with st.form("main_project_form"):
        col1, col2 = st.columns(2)
        with col1:
            company = st.text_input("Επωνυμία Επιχείρησης")
            afm = st.text_input("ΑΦΜ (9 ψηφία)", max_chars=9)
        with col2:
            mis = st.text_input("Κωδικός Έργου")
            budget = st.number_input("Συνολικός Προϋπολογισμός (€)", min_value=0.0, step=100.0)
        
        submitted = st.form_submit_button("💾 Αποθήκευση Στοιχείων")
        if submitted:
            if company and afm and mis:
                project_info = {"Επωνυμία": company, "ΑΦΜ": afm, "MIS": mis, "Προϋπολογισμός": budget}
                save_data(project_info, 'data_projects.csv')
                st.success("Το έργο αποθηκεύτηκε!")
            else:
                st.warning("Συμπληρώστε τα υποχρεωτικά πεδία.")

    if os.path.isfile('data_projects.csv'):
        st.divider()
        st.subheader("📋 Καταχωρημένα Έργα")
        st.dataframe(pd.read_csv('data_projects.csv'), use_container_width=True)

# --- ΣΤΑΔΙΟ 2: ΓΕΝΙΚΑ ΠΑΡΑΔΟΤΕΑ ---
elif page == "2. Γενικά Παραδοτέα (Checklist)":
    st.header("📂 Λίστα Γενικών Παραδοτέων")
    st.write("Ελέγξτε την πληρότητα των εγγράφων που αφορούν το σύνολο της επιχείρησης.")

    # Η δική σου λίστα εγγράφων
    required_docs = [
        "Πίνακας Προσωπικού Ε4 (Ετήσιος/Συμπληρωματικός)",
        "ΑΠΔ (Αναλυτική Περιοδική Δήλωση)",
        "Αποδεικτικό Υποβολής ΑΠΔ (Taxisnet)",
        "ΑΠΔ ΤΕΚΑ (Αναλυτική Περιοδική Δήλωση)",
        "Αποδεικτικό Υποβολής ΑΠΔ ΤΕΚΑ (Taxisnet)",
        "Μηνιαίες μισθολογικές καταστάσεις",
        "Ασφαλιστική ενημερότητα",
        "Οικονομική καρτέλα εργοδότη απο ΕΦΚΑ",
        "Ηλεκτρονική καρτέλα οφειλετών",
        "Πίνακας χρεών οφειλέτη",
        "Ανάλυση κίνησης απο Ηλεκτρονική καρτέλα οφειλέτη",
        "Φορολογική ενημερότητα",
        "Στοιχεία ρυθμίσεων και Πληρωμή",
        "Προσωρινές δηλώσεις ΦΜΥ",
        "Υπεύθυνη δήλωση περι συγγενών",
        "Επιστολή γνωστοποίησης"
    ]

    for doc in required_docs:
        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown(f"**{doc}**")
        with c2:
            st.selectbox("Κατάσταση", ["❌ Λείπει", "✅ Πλήρες", "⚠️ Εκκρεμεί"], key=doc)
    
    st.divider()
    notes = st.text_area("📝 Σημειώσεις Ελεγκτή")
    if st.button("Προσωρινή Αποθήκευση Checklist"):
        st.toast("Η κατάσταση αποθηκεύτηκε!")

# --- ΣΤΑΔΙΟ 3: ΜΙΣΘΟΔΟΣΙΑ ΥΠΑΛΛΗΛΩΝ ---
elif page == "3. Μισθοδοσία Υπαλλήλων":
    st.header("👤 Διαχείριση Υπαλλήλων")

    if not os.path.isfile('data_projects.csv'):
        st.error("⚠️ Πρέπει πρώτα να καταχωρήσετε ένα έργο στο Στάδιο 1.")
    else:
        projects_df = pd.read_csv('data_projects.csv')
        project_list = projects_df['Επωνυμία'].tolist()
        selected_p = st.selectbox("Επιλέξτε Επιχείρηση/Έργο:", project_list)

        # Φόρμα Προσθήκης Υπαλλήλου
        with st.expander("➕ Προσθήκη Νέου Υπαλλήλου"):
            with st.form("add_emp"):
                e_col1, e_col2 = st.columns(2)
                with e_col1:
                    name = st.text_input("Ονοματεπώνυμο")
                    amka = st.text_input("ΑΜΚΑ", max_chars=11)
                with e_col2:
                    pos = st.text_input("Θέση/Ειδικότητα")
                    sal = st.number_input("Μηνιαίος Μισθός (€)", min_value=0.0)
                
                if st.form_submit_button("Αποθήκευση Υπαλλήλου"):
                    if name and amka:
                        emp_info = {"Έργο": selected_p, "Όνομα": name, "ΑΜΚΑ": amka, "Ειδικότητα": pos, "Μισθός": sal}
                        save_data(emp_info, 'data_employees.csv')
                        st.success(f"Ο υπάλληλος {name} προστέθηκε!")
                    else:
                        st.error("Το όνομα και το ΑΜΚΑ είναι υποχρεωτικά.")

        # Προβολή Υπαλλήλων
        if os.path.isfile('data_employees.csv'):
            st.divider()
            st.subheader(f"👥 Προσωπικό Έργου: {selected_p}")
            all_emps = pd.read_csv('data_employees.csv')
            filtered_emps = all_emps[all_emps['Έργο'] == selected_p]
            
            if not filtered_emps.empty:
                st.dataframe(filtered_emps[['Όνομα', 'ΑΜΚΑ', 'Ειδικότητα', 'Μισθός']], use_container_width=True)
            else:
                st.write("Δεν έχουν καταχωρηθεί υπάλληλοι για αυτό το έργο.")
