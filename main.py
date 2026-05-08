import streamlit as st
import pandas as pd
import os
import google.generativeai as genai
from PIL import Image
import json

# --- 1. ΡΥΘΜΙΣΗ AI (GEMINI) ---
# Αντικατάστησε το κλειδί παρακάτω με το δικό σου
GOOGLE_API_KEY = "AIzaSyB_NjdNwQrRHeFzfphVPz8qIfTzgEQ-zSg" 
genai.configure(api_key=GOOGLE_API_KEY)

def extract_payroll_with_ai(uploaded_file):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        img = Image.open(uploaded_file)
        
        prompt = """
        Ανέλυσε αυτή την εικόνα μισθοδοσίας. Εξήγαγε τα ποσά για τα παρακάτω πεδία σε JSON μορφή:
        "ΙΚΑ_Εργ", "ΙΚΑ_Εργοδ", "ΤΕΚΑ_Εργ", "ΤΕΚΑ_Εργοδ", "Σύνολο_Εισφ", "ΦΜΥ", "Καθαρές", "Σύνολο_Αποδ".
        Μην γράψεις τίποτα άλλο εκτός από το JSON. Αν λείπει κάτι, βάλε 0.0.
        """
        
        response = model.generate_content([prompt, img])
        # Καθαρισμός του κειμένου από markdown tags
        json_text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(json_text)
    except Exception as e:
        st.error(f"Σφάλμα AI: {e}")
        return None

# --- 2. ΡΥΘΜΙΣΗ ΣΕΛΙΔΑΣ & ΑΡΧΕΙΩΝ ---
st.set_page_config(page_title="Payroll AI Verifier", layout="wide")

PROJECTS_FILE = 'data_projects.csv'
EMPLOYEES_FILE = 'data_employees.csv'
FINANCIALS_FILE = 'payroll_financials.csv'
CHECKLIST_FILE = 'checklist_results.csv'
PAYROLL_CHECKS_FILE = 'payroll_checks.csv'

def load_data(f, cols):
    # 1. Έλεγχος αν το αρχείο υπάρχει
    if not os.path.isfile(f):
        return pd.DataFrame(columns=cols)
    
    # 2. Έλεγχος αν το αρχείο είναι άδειο (0 bytes)
    if os.path.getsize(f) == 0:
        return pd.DataFrame(columns=cols)
        
    try:
        df = pd.read_csv(f)
        # 3. Έλεγχος αν το αρχείο είχε δεδομένα αλλά ήταν κατεστραμμένο ή κενό μετά το διάβασμα
        if df.empty and len(df.columns) == 0:
            return pd.DataFrame(columns=cols)
        return df
    except (pd.errors.EmptyDataError, pd.errors.ParserError):
        # Αν συμβεί το σφάλμα, επέστρεψε άδειο DataFrame με τις στήλες
        return pd.DataFrame(columns=cols)

def save_to_csv(df, f):
    df.to_csv(f, index=False, encoding='utf-8-sig')

# --- 3. ΜΕΝΟΥ ---
page = st.sidebar.radio("Μενού:", ["1. Διαχείριση Έργων", "2. Checklist ανά Έργο", "3. Μισθοδοσία Υπαλλήλων"])

# --- ΣΤΑΔΙΟ 1 ---
if page == "1. Διαχείριση Έργων":
    st.header("🏢 Διαχείριση Επιχειρήσεων")
    with st.form("project_form"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Επωνυμία")
        afm = c1.text_input("ΑΦΜ", max_chars=9)
        mis = c2.text_input("MIS")
        budget = c2.number_input("Προϋπολογισμός", min_value=0.0)
        if st.form_submit_button("Αποθήκευση"):
            df = load_data(PROJECTS_FILE, ["Επωνυμία", "ΑΦΜ", "MIS", "Προϋπολογισμός"])
            new_row = pd.DataFrame([{"Επωνυμία": name, "ΑΦΜ": afm, "MIS": mis, "Προϋπολογισμός": budget}])
            save_to_csv(pd.concat([df, new_row], ignore_index=True), PROJECTS_FILE)
            st.success("✅ Αποθηκεύτηκε!")
            st.rerun()
    st.dataframe(load_data(PROJECTS_FILE, ["Επωνυμία", "ΑΦΜ", "MIS", "Προϋπολογισμός"]), use_container_width=True)

# --- ΣΤΑΔΙΟ 2 ---
# --- ΣΤΑΔΙΟ 2: CHECKLIST ΑΝΑ ΕΡΓΟ ---
elif page == "2. Checklist ανά Έργο":
    st.header("📂 Γενικά Παραδοτέα Μισθοδοσίας")
    projects_df = load_data(PROJECTS_FILE, ["Επωνυμία", "ΑΦΜ"])
    
    if projects_df.empty:
        st.warning("⚠️ Καταχωρήστε μια επιχείρηση στο Στάδιο 1.")
    else:
        # Επιλογή Επιχείρησης
        selected_name = st.selectbox("Επιλέξτε Επιχείρηση:", projects_df['Επωνυμία'])
        selected_afm = str(projects_df[projects_df['Επωνυμία'] == selected_name]['ΑΦΜ'].iloc[0])
        
        # Φόρτωση υπαρχόντων αποτελεσμάτων
        check_df = load_data(CHECKLIST_FILE, ["ΑΦΜ", "Εγγραφο", "Κατάσταση", "Σχόλιο"])
        
        # Η λίστα με τα έγγραφα που θέλουμε να ελέγχουμε
        required_docs = [
            "Πίνακας Προσωπικού Ε4", "Μισθολογικές καταστάσεις", "ΑΠΔ ΕΦΚΑ", 
            "Αποδεικτικό Υποβολής ΑΠΔ", "ΑΠΔ ΤΕΚΑ", "Αποδεικτικό Υποβολής ΑΠΔ ΤΕΚΑ", 
            "Υπεύθυνη δήλωση συγγενών", "Επιστολή γνωστοποίησης", "Ασφαλιστική ενημερότητα", 
            "Οικονομική καρτέλα ΕΦΚΑ", "Ηλεκτρονική καρτέλα οφειλετών", "Πίνακας χρεών οφειλέτη", 
            "Ανάλυση κίνησης Ηλ. Καρτέλας", "Φορολογική ενημερότητα", "Στοιχεία ρυθμίσεων & Πληρωμή", 
            "Προσωρινές δηλώσεις ΦΜΥ"
        ]
        
        results = []
        st.markdown("---")
        
        # Δημιουργία γραμμών για κάθε έγγραφο
        for doc in required_docs:
            # Αναζήτηση αν υπάρχει ήδη αποθηκευμένη τιμή για αυτό το ΑΦΜ και αυτό το έγγραφο
            existing = check_df[(check_df['ΑΦΜ'].astype(str) == selected_afm) & (check_df['Εγγραφο'] == doc)]
            
            c1, c2, c3 = st.columns([1.5, 1, 2], gap="small")
            
            with c1:
                st.markdown(f"<div style='padding-top:10px;'><b>{doc}</b></div>", unsafe_allow_html=True)
            
            with c2:
                # Καθορισμός default επιλογής αν υπάρχει στη βάση
                current_status = existing['Κατάσταση'].iloc[0] if not existing.empty else "Έλλειψη ❌"
                status_options = ["Έλλειψη ❌", "Υπάρχει ✅", "Δεν απαιτείται"]
                status = st.selectbox(
                    "Κατάσταση", 
                    status_options, 
                    index=status_options.index(current_status),
                    key=f"status_{selected_afm}_{doc}",
                    label_visibility="collapsed"
                )
            
            with c3:
                current_comment = existing['Σχόλιο'].iloc[0] if not existing.empty else ""
                note = st.text_input(
                    "Σχόλιο", 
                    value=current_comment, 
                    key=f"note_{selected_afm}_{doc}", 
                    label_visibility="collapsed",
                    placeholder="Προσθέστε σχόλιο..."
                )
            
            results.append({"ΑΦΜ": selected_afm, "Εγγραφο": doc, "Κατάσταση": status, "Σχόλιο": note})

        st.markdown("---")
        if st.button("💾 Αποθήκευση Checklist Επιχείρησης", use_container_width=True):
            # Αφαιρούμε τις παλιές εγγραφές για τη συγκεκριμένη επιχείρηση και προσθέτουμε τις νέες
            other_projects = check_df[check_df['ΑΦΜ'].astype(str) != selected_afm]
            final_df = pd.concat([other_projects, pd.DataFrame(results)], ignore_index=True)
            save_to_csv(final_df, CHECKLIST_FILE)
            st.success(f"✅ Το checklist για την επιχείρηση {selected_name} ενημερώθηκε!")

# --- ΣΤΑΔΙΟ 3: ΜΙΣΘΟΔΟΣΙΑ ΥΠΑΛΛΗΛΩΝ ---
elif page == "3. Μισθοδοσία Υπαλλήλων":
    st.header("👤 Διαχείριση & Έλεγχος Υπαλλήλων")
    projects_df = load_data(PROJECTS_FILE, ["Επωνυμία", "ΑΦΜ"])
    
    if projects_df.empty:
        st.warning("⚠️ Καταχωρήστε μια επιχείρηση στο Στάδιο 1.")
    else:
        # --- ΠΑΝΩ ΜΕΡΟΣ: ΕΠΙΛΟΓΗ & ΠΡΟΣΘΗΚΗ ---
        top_l, top_r = st.columns([1, 1.2], gap="large")
        
        with top_l:
            st.subheader("🏢 Επιλογή Στοιχείων")
            selected_project = st.selectbox("Επιχείρηση:", projects_df['Επωνυμία'])
            selected_afm = str(projects_df[projects_df['Επωνυμία'] == selected_project]['ΑΦΜ'].iloc[0])
            
            c_m, c_y = st.columns(2)
            selected_month = c_m.selectbox("Μήνας:", ["Ιανουάριος", "Φεβρουάριος", "Μάρτιος", "Απρίλιος", "Μάιος", "Ιούνιος", "Ιούλιος", "Αύγουστος", "Σεπτέμβριος", "Οκτώβριος", "Νοέμβριος", "Δεκέμβριος"])
            selected_year = c_y.selectbox("Έτος:", ["2024", "2025", "2026"], index=1)
            period = f"{selected_month} {selected_year}"

        with top_r:
            st.subheader("➕ Προσθήκη Υπαλλήλου")
            with st.container(border=True):
                new_emp_name = st.text_input("Ονοματεπώνυμο", key="n_name")
                c_afm, c_amka = st.columns(2)
                new_emp_afm = c_afm.text_input("ΑΦΜ Υπαλλήλου", max_chars=9, key="n_afm")
                new_emp_amka = c_amka.text_input("ΑΜΚΑ Υπαλλήλου", max_chars=11, key="n_amka")
                
                if st.button("📥 Καταχώρηση Υπαλλήλου", use_container_width=True):
                    if new_emp_name and new_emp_afm:
                        emp_df = load_data(EMPLOYEES_FILE, ["ΑΦΜ_Εργου", "Ονοματεπώνυμο", "ΑΦΜ_Υπαλλήλου", "ΑΜΚΑ_Υπαλλήλου"])
                        # Έλεγχος αν υπάρχει ήδη
                        mask = (emp_df['ΑΦΜ_Εργου'].astype(str) == selected_afm) & (emp_df['ΑΦΜ_Υπαλλήλου'].astype(str) == new_emp_afm)
                        if not emp_df[mask].empty:
                            emp_df.loc[mask, ["Ονοματεπώνυμο", "ΑΜΚΑ_Υπαλλήλου"]] = [new_emp_name, new_emp_amka]
                        else:
                            new_row = pd.DataFrame([{"ΑΦΜ_Εργου": selected_afm, "Ονοματεπώνυμο": new_emp_name, "ΑΦΜ_Υπαλλήλου": new_emp_afm, "ΑΜΚΑ_Υπαλλήλου": new_emp_amka}])
                            emp_df = pd.concat([emp_df, new_row], ignore_index=True)
                        save_to_csv(emp_df, EMPLOYEES_FILE)
                        st.success(f"Ο υπάλληλος {new_emp_name} προστέθηκε!")
                        st.rerun()

        st.markdown("---")

        # --- ΕΠΙΛΟΓΗ ΥΠΑΛΛΗΛΟΥ ΑΠΟ ΤΗ ΛΙΣΤΑ ---
        all_emps_df = load_data(EMPLOYEES_FILE, ["ΑΦΜ_Εργου", "Ονοματεπώνυμο", "ΑΦΜ_Υπαλλήλου", "ΑΜΚΑ_Υπαλλήλου"])
        current_emps = all_emps_df[all_emps_df['ΑΦΜ_Εργου'].astype(str) == selected_afm]
        emp_options = current_emps.apply(lambda x: f"{x['Ονοματεπώνυμο']} (ΑΦΜ: {x['ΑΦΜ_Υπαλλήλου']})", axis=1).tolist()

        if not emp_options:
            st.info("💡 Η λίστα υπαλλήλων είναι κενή. Προσθέστε έναν υπάλληλο παραπάνω.")
        else:
            selected_option = st.selectbox("🔍 Επιλογή Υπαλλήλου για Έλεγχο:", ["--- Επιλογή ---"] + emp_options)
            
            if selected_option != "--- Επιλογή ---":
                sel_emp_afm = selected_option.split("(ΑΦΜ: ")[1].replace(")", "")
                emp_data = current_emps[current_emps['ΑΦΜ_Υπαλλήλου'].astype(str) == sel_emp_afm].iloc[0]
                fin_key = f"FIN_{selected_afm}_{sel_emp_afm}_{period}"
                
                st.info(f"📋 **Έλεγχος:** {emp_data['Ονοματεπώνυμο']} | **Περίοδος:** {period}")

                # --- ΑΙ ΑΝΑΛΥΣΗ ΜΙΣΘΟ
