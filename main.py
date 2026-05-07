import streamlit as st
import pandas as pd

# Ρύθμιση σελίδας
st.set_page_config(page_title="Payroll Verifier", layout="wide")

# Πλευρικό Μενού (Navigation)
st.sidebar.title("Μενού Ελέγχου")
page = st.sidebar.radio("Επιλέξτε Στάδιο:", 
    ["Αρχική - Στοιχεία Έργου", 
     "Γενικά Παραδοτέα", 
     "Μισθοδοσία Υπαλλήλων"])

# --- ΣΤΑΔΙΟ 1: ΣΤΟΙΧΕΙΑ ΕΡΓΟΥ ---
if page == "Αρχική - Στοιχεία Έργου":
    st.header("🏢 Γενικά Στοιχεία Έργου & Επιχείρησης")
    with st.form("project_form"):
        company = st.text_input("Επωνυμία Επιχείρησης")
        mis = st.text_input("Κωδικός Έργου")
        budget = st.number_input("Προϋπολογισμός (€)", min_value=0.0)
        submitted = st.form_submit_button("Αποθήκευση")
        if submitted:
            st.success(f"Το έργο {mis} καταχωρήθηκε τοπικά!")

# --- ΣΤΑΔΙΟ 2: ΓΕΝΙΚΑ ΠΑΡΑΔΟΤΕΑ ---
elif page == "Γενικά Παραδοτέα":
    st.header("📂 Γενικά Παραδοτέα Μισθοδοσίας")
    st.info("Εδώ θα ανεβαίνουν τα έγγραφα που αφορούν όλη την επιχείρηση (ΑΠΔ, ΦΜΥ κλπ)")
    # Θα προσθέσουμε το upload logic αργότερα

# --- ΣΤΑΔΙΟ 3: ΜΙΣΘΟΔΟΣΙΑ ΥΠΑΛΛΗΛΩΝ ---
elif page == "Μισθοδοσία Υπαλλήλων":
    st.header("👤 Στοιχεία Μισθοδοσίας ανά Υπάλληλο")
    st.write("Συγκεντρωτική κατάσταση και έλεγχος δικαιολογητικών.")
    # Εδώ θα μπει ο πίνακας και το OCR αργότερα
