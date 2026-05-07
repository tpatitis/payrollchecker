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
def save_project_data(data_dict):
    """Αποθηκεύει τα στοιχεία της επιχείρησης σε CSV"""
    df = pd.DataFrame([data_dict])
    file_exists = os.path.isfile('data_projects.csv')
    
    # Χρήση utf-8-sig για να ανοίγει σωστά το Excel με Ελληνικά
    df.to_csv('data_projects.csv', mode='a', index=False, 
              header=not file_exists, encoding='utf-8-sig')

# --- ΠΛΕΥΡΙΚΟ ΜΕΝΟΥ (NAVIGATION) ---
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
    st.info("Συμπληρώστε τα βασικά στοιχεία της επιχείρησης για την έναρξη του ελέγχου.")

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
                project_info = {
                    "Επωνυμία": company,
                    "ΑΦΜ": afm,
                    "MIS": mis,
                    "Προϋπολογισμός": budget
                }
                save_project_data(project_info)
                st.success("Τα στοιχεία αποθηκεύτηκαν με επιτυχία στο 'data_projects.csv'!")
            else:
                st.warning("Παρακαλώ συμπληρώστε όλα τα υποχρεωτικά πεδία (Επωνυμία, ΑΦΜ, MIS).")

    # Προβολή Ιστορικού
    if os.path.isfile('data_projects.csv'):
        st.divider()
        st.subheader("📋 Καταχωρημένα Έργα")
        history_df = pd.read_csv('data_projects.csv')
        st.dataframe(history_df, use_container_width=True)

# --- ΣΤΑΔΙΟ 2: ΓΕΝΙΚΑ ΠΑΡΑΔΟΤΕΑ ---
elif page == "2. Γενικά Παραδοτέα (Checklist)":
    st.header("📂 Λίστα Γενικών Παραδοτέων")
    st.write("Ελέγξτε την πληρότητα των εγγράφων που αφορούν το σύνολο της επιχείρησης.")

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
        "Υπεύθυνη δήλωση περι συγγενών"
        "Επιστολή γνωστοποίησης"
    ]

    # Δημιουργία πίνακα Checklist
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
    st.header("👤 Στοιχεία Μισθοδοσίας ανά Υπάλληλο")
    st.warning("Αυτή η ενότητα θα παραμετροποιηθεί στο επόμενο βήμα για τη σύνδεση με το OCR.")
    
    st.info("Εδώ θα γίνεται η καταχώρηση των υπαλλήλων και ο έλεγχος των ατομικών τους δικαιολογητικών (Αποδείξεις πληρωμής, Συμβάσεις κλπ).")
