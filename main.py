import streamlit as st
import pandas as pd
import os

# --- ΡΥΘΜΙΣΗ ΣΕΛΙΔΑΣ ---
st.set_page_config(page_title="Payroll Verifier Pro", layout="wide")

# --- ΑΡΧΕΙΑ ΔΕΔΟΜΕΝΩΝ ---
PROJECTS_FILE = 'data_projects.csv'
CHECKLIST_FILE = 'checklist_results.csv'

# --- ΣΥΝΑΡΤΗΣΕΙΣ ---
def load_data(filename, columns):
    if not os.path.isfile(filename) or os.path.getsize(filename) == 0:
        return pd.DataFrame(columns=columns)
    try:
        return pd.read_csv(filename)
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=columns)

def save_to_csv(df, filename):
    df.to_csv(filename, index=False, encoding='utf-8-sig')

# --- ΠΛΕΥΡΙΚΟ ΜΕΝΟΥ ---
page = st.sidebar.radio("Μενού:", ["1. Διαχείριση Έργων", "2. Checklist ανά Έργο", "3. Μισθοδοσία"])

# --- ΣΤΑΔΙΟ 1: ΔΙΑΧΕΙΡΙΣΗ ΕΡΓΩΝ (CRUD) ---
if page == "1. Διαχείριση Έργων":
    st.header("🏢 Διαχείριση Επιχειρήσεων")
    
    # Φόρμα Καταχώρησης
    with st.expander("➕ Προσθήκη / Επεξεργασία Έργου"):
        with st.form("project_form"):
            name = st.text_input("Επωνυμία")
            afm = st.text_input("ΑΦΜ", max_chars=9)
            mis = st.text_input("MIS")
            if st.form_submit_button("Αποθήκευση"):
                df = load_data(PROJECTS_FILE, ["Επωνυμία", "ΑΦΜ", "MIS"])
                if afm in df['ΑΦΜ'].astype(str).values:
                    df.loc[df['ΑΦΜ'].astype(str) == afm, ["Επωνυμία", "MIS"]] = [name, mis]
                else:
                    new_row = pd.DataFrame([{"Επωνυμία": name, "ΑΦΜ": afm, "MIS": mis}])
                    df = pd.concat([df, new_row], ignore_index=True)
                save_to_csv(df, PROJECTS_FILE)
                st.success("Ενημερώθηκε!")
                st.rerun()

    # Πίνακας με κουμπί Διαγραφής
    df = load_data(PROJECTS_FILE, ["Επωνυμία", "ΑΦΜ", "MIS"])
    if not df.empty:
        st.subheader("Καταχωρημένα Έργα")
        for i, row in df.iterrows():
            cols = st.columns([3, 2, 1, 1])
            cols[0].write(row['Επωνυμία'])
            cols[1].write(f"ΑΦΜ: {row['ΑΦΜ']}")
            if cols[3].button("🗑️", key=f"del_{row['ΑΦΜ']}"):
                df = df.drop(i)
                save_to_csv(df, PROJECTS_FILE)
                st.rerun()

# --- ΣΤΑΔΙΟ 2: CHECKLIST ΑΝΑ ΕΡΓΟ ---
elif page == "2. Checklist ανά Έργο":
    st.header("📂 Checklist Παραδοτέων")
    projects_df = load_data(PROJECTS_FILE, ["Επωνυμία", "ΑΦΜ", "MIS"])
    
    if projects_df.empty:
        st.warning("Πρώτα καταχωρήστε έργο στο Στάδιο 1.")
    else:
        # Επιλογή Έργου
        selected_name = st.selectbox("Επιλέξτε Επιχείρηση:", projects_df['Επωνυμία'])
        selected_afm = projects_df[projects_df['Επωνυμία'] == selected_name]['ΑΦΜ'].iloc[0]

        # Φόρτωση παλιών απαντήσεων για το συγκεκριμένο ΑΦΜ
        check_df = load_data(CHECKLIST_FILE, ["ΑΦΜ", "Εγγραφο", "Κατάσταση", "Σχόλιο"])
        
        required_docs = ["Πίνακας Ε4", "ΑΠΔ ΕΦΚΑ", "Φορολογική Ενημερότητα", "Ασφαλιστική Ενημερότητα"]
        
        st.subheader(f"Έλεγχος για: {selected_name}")
        
        results = []
        for doc in required_docs:
            # Εύρεση προηγούμενης τιμής
            existing = check_df[(check_df['ΑΦΜ'] == selected_afm) & (check_df['Εγγραφο'] == doc)]
            prev_status = existing['Κατάσταση'].iloc[0] if not existing.empty else "Έλλειψη ❌"
            prev_note = existing['Σχόλιο'].iloc[0] if not existing.empty else ""

            c1, c2, c3 = st.columns([1.2, 0.8, 2.5], gap="small")
            c1.write(f"**{doc}**")
            status = c2.selectbox("", ["Έλλειψη ❌", "Υπάρχει ✅", "Δεν απαιτείται"], index=["Έλλειψη ❌", "Υπάρχει ✅", "Δεν απαιτείται"].index(prev_status), key=f"st_{selected_afm}_{doc}")
            note = c3.text_input("Παρατήρηση", value=prev_note, key=f"nt_{selected_afm}_{doc}")
            results.append({"ΑΦΜ": selected_afm, "Εγγραφο": doc, "Κατάσταση": status, "Σχόλιο": note})

        if st.button("💾 Οριστική Αποθήκευση Checklist"):
            # Αφαιρούμε τα παλιά δεδομένα του συγκεκριμένου ΑΦΜ και προσθέτουμε τα νέα
            check_df = check_df[check_df['ΑΦΜ'] != selected_afm]
            new_data = pd.DataFrame(results)
            check_df = pd.concat([check_df, new_data], ignore_index=True)
            save_to_csv(check_df, CHECKLIST_FILE)
            st.success(f"Το checklist για την επιχείρηση {selected_name} αποθηκεύτηκε!")
