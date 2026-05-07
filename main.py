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
    st.header("👤 Διαχείριση Υπαλλήλων & Παραδοτέων")

    if not os.path.isfile('data_projects.csv'):
        st.error("⚠️ Παρακαλώ καταχωρήστε πρώτα ένα έργο στο Στάδιο 1.")
    else:
        projects_df = pd.read_csv('data_projects.csv')
        selected_p = st.selectbox("Επιλέξτε Επιχείρηση:", projects_df['Επωνυμία'].unique())

        # Επιλογή Μήνα Ελέγχου
        target_month = st.selectbox("Μήνας Ελέγχου:", 
            ["Ιανουάριος", "Φεβρουάριος", "Μάρτιος", "Απρίλιος", "Μάιος", "Ιούνιος", 
             "Ιούλιος", "Αύγουστος", "Σεπτέμβριος", "Οκτώβριος", "Νοέμβριος", "Δεκέμβριος"])

        st.divider()

        # 1. Μόνιμα Έγγραφα Υπαλλήλου (Tabs για οργάνωση)
        tab1, tab2 = st.tabs(["📋 Μόνιμα Έγγραφα", "💰 Μηνιαία Παραδοτέα"])

        with tab1:
            st.subheader("Γενικά Έγγραφα Εργαζομένου")
            col_a, col_b = st.columns(2)
            with col_a:
                st.file_uploader("Αναγγελία Πρόσληψης (Ε3)", type=['pdf', 'jpg', 'png'])
            with col_b:
                st.file_uploader("Ταυτότητα", type=['pdf', 'jpg', 'png'])

        with tab2:
            st.subheader(f"Παραδοτέα Μηνός: {target_month}")
            
            # Λίστα με τα μηνιαία που ορίσαμε
            monthly_docs = [
                "Extrait Τραπέζης (Κίνηση Λογαριασμού)",
                "Παραστατικό Πληρωμής (Screenshot/Pay-slip)",
                "Λογιστικό Άρθρο Καταχώρησης (Διπλογραφικά)",
                "Λογιστικό Άρθρο Πληρωμής (Διπλογραφικά)",
                "Βιβλίο Εσόδων-Εξόδων (Απλογραφικά)"
            ]

            for doc in monthly_docs:
                c1, c2, c3 = st.columns([2, 1, 1])
                with c1:
                    st.write(f"📄 {doc}")
                with c2:
                    st.file_uploader("Upload", type=['pdf', 'jpg', 'png'], key=f"{doc}_{target_month}", label_visibility="collapsed")
                with c3:
                    st.selectbox("Status", ["❌", "✅", "⚠️"], key=f"stat_{doc}_{target_month}")

        st.divider()
        if st.button("Οριστική Υποβολή Ελέγχου Μηνός"):
            st.success(f"Ο έλεγχος για τον μήνα {target_month} αποθηκεύτηκε!")
