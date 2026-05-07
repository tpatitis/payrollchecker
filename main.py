import streamlit as st
import pandas as pd
import os

# --- ΣΥΝΑΡΤΗΣΕΙΣ ΔΙΑΧΕΙΡΙΣΗΣ ΔΕΔΟΜΕΝΩΝ ---
def save_project_data(data_dict):
    df = pd.DataFrame([data_dict])
    # Αν το αρχείο δεν υπάρχει, το δημιουργεί με headers. Αν υπάρχει, προσθέτει τη γραμμή.
    if not os.path.isfile('project_info.csv'):
        df.to_csv('project_info.csv', index=False, encoding='utf-8-sig')
    else:
        df.to_csv('project_info.csv', mode='a', index=False, header=False, encoding='utf-8-sig')

# --- UI ΕΦΑΡΜΟΓΗΣ ---
st.set_page_config(page_title="Payroll Verifier", layout="wide")

st.sidebar.title("Μενού Ελέγχου")
page = st.sidebar.radio("Επιλέξτε Στάδιο:", 
    ["Αρχική - Στοιχεία Έργου", "Γενικά Παραδοτέα", "Μισθοδοσία Υπαλλήλων"])

if page == "Αρχική - Στοιχεία Έργου":
    st.header("🏢 Γενικά Στοιχεία Έργου & Επιχείρησης")
    
    with st.form("project_form"):
        company = st.text_input("Επωνυμία Επιχείρησης")
        afm = st.text_input("ΑΦΜ", max_chars=9)
        mis = st.text_input("Κωδικός Έργου")
        budget = st.number_input("Προϋπολογισμός (€)", min_value=0.0)
        
        submitted = st.form_submit_button("Αποθήκευση Στοιχείων")
        
        if submitted:
            if company and afm and mis:  # Βασικός έλεγχος αν είναι κενά
                project_data = {
                    "Επωνυμία": company,
                    "ΑΦΜ": afm,
                    "MIS": mis,
                    "Προϋπολογισμός": budget
                }
                save_project_data(project_data)
                st.success(f"Το έργο '{company}' αποθηκεύτηκε στο αρχείο project_info.csv!")
            else:
                st.error("Παρακαλώ συμπληρώστε όλα τα βασικά πεδία.")

    # Προβολή αποθηκευμένων έργων (για επιβεβαίωση)
    if os.path.isfile('project_info.csv'):
        st.subheader("📋 Καταχωρημένα Έργα")
        view_df = pd.read_csv('project_info.csv')
        st.dataframe(view_df)
