import streamlit as st
import pandas as pd
import os

# --- ΡΥΘΜΙΣΗ ΣΕΛΙΔΑΣ ---
st.set_page_config(
    page_title="Payroll Verifier Pro",
    page_icon="🛡️",
    layout="wide"
)

# --- ΣΥΝΑΡΤΗΣΕΙΣ ΔΙΑΧΕΙΡΙΣΗΣ ΔΕΔΟΜΕΝΩΝ ---
def save_data(data_dict, filename):
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
    st.header("📂 Έλεγχος Φακέλου Επιχείρησης")
    st.info("Επιλέξτε την κατάσταση για κάθε γενικό έγγραφο.")

    required_docs = [
        "Πίνακας Προσωπικού Ε4", "ΑΠΔ ΕΦΚΑ", "Αποδεικτικό ΑΠΔ",
        "ΑΠΔ ΤΕΚΑ", "Αποδεικτικό ΤΕΚΑ", "Μισθολογικές καταστάσεις",
        "Ασφαλιστική ενημερότητα", "Οικονομική καρτέλα ΕΦΚΑ",
        "Ηλεκτρονική καρτέλα οφειλετών", "Πίνακας χρεών οφειλέτη",
        "Ανάλυση κίνησης Ηλ. Καρτέλας", "Φορολογική ενημερότητα",
        "Στοιχεία ρυθμίσεων & Πληρωμή", "Προσωρινές δηλώσεις ΦΜΥ",
        "Υπεύθυνη δήλωση συγγενών", "Επιστολή γνωστοποίησης"
    ]

    col_left, col_right = st.columns(2)
    half = len(required_docs) // 2
    
    with col_left:
        for doc in required_docs[:half]:
            c1, c2 = st.columns([2, 1])
            c1.markdown(f"<div style='font-size:0.9rem;'>{doc}</div>", unsafe_allow_html=True)
            c2.selectbox("", ["❌", "✅", "⚠️"], key=f"ch_{doc}", label_visibility="collapsed")

    with col_right:
        for doc in required_docs[half:]:
            c1, c2 = st.columns([2, 1])
            c1.markdown(f"<div style='font-size:0.9rem;'>{doc}</div>", unsafe_allow_html=True)
            c2.selectbox("", ["❌", "✅", "⚠️"], key=f"ch_{doc}", label_visibility="collapsed")

    st.divider()
    with st.expander("📝 Προσθήκη Σημειώσεων"):
        st.text_area("Γράψτε παρατηρήσεις...", label_visibility="collapsed")

# --- ΣΤΑΔΙΟ 3: ΜΙΣΘΟΔΟΣΙΑ ΥΠΑΛΛΗΛΩΝ ---
elif page == "3. Μισθοδοσία Υπαλλήλων":
    st.header("👤 Διαχείριση Υπαλλήλων & Παραδοτέων")

    if not os.path.isfile('data_projects.csv'):
        st.error("⚠️ Παρακαλώ καταχωρήστε πρώτα ένα έργο στο Στάδιο 1.")
    else:
        projects_df = pd.read_csv('data_projects.csv')
        selected_p = st.selectbox("Επιλέξτε Επιχείρηση:", projects_df['Επωνυμία'].unique())
        
        target_month = st.selectbox("Μήνας Ελέγχου:", 
            ["Ιανουάριος", "Φεβρουάριος", "Μάρτιος", "Απρίλιος", "Μάιος", "Ιούνιος", 
             "Ιούλιος", "Αύγουστος", "Σεπτέμβριος", "Οκτώβριος", "Νοέμβριος", "Δεκέμβριος"])

        tab1, tab2 = st.tabs(["📋 Μόνιμα Έγγραφα", "💰 Μηνιαία Παραδοτέα"])

        with tab1:
            st.subheader("Γενικά Έγγραφα Εργαζομένου")
            col_a, col_b = st.columns(2)
            with col_a:
                st.file_uploader("Αναγγελία Πρόσληψης (Ε3)", type=['pdf', 'jpg', 'png'], key="e3")
            with col_b:
                st.file_uploader("Ταυτότητα", type=['pdf', 'jpg', 'png'], key="id")

        with tab2:
            st.subheader(f"Παραδοτέα Μηνός: {target_month}")
            monthly_docs = [
                "Extrait Τραπέζης", "Παραστατικό Πληρωμής", 
                "Λογιστικό Άρθρο Καταχώρησης", "Λογιστικό Άρθρο Πληρωμής", 
                "Βιβλίο Εσόδων-Εξόδων"
            ]
            for m_doc in monthly_docs:
                mc1, mc2, mc3 = st.columns([2, 1, 1])
                mc1.write(f"📄 {m_doc}")
                mc2.file_uploader("Upload", type=['pdf', 'jpg', 'png'], key=f"up_{m_doc}", label_visibility="collapsed")
                mc3.selectbox("Status", ["❌", "✅", "⚠️"], key=f"st_{m_doc}")
