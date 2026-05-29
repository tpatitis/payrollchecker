import streamlit as st
import pandas as pd
import os
import google.generativeai as genai
from PIL import Image
import json

# --- 1. ΡΥΘΜΙΣΗ AI (GEMINI) ---
GOOGLE_API_KEY = "AIzaSyB_NjdNwQrRHeFzfphVPz8qIfTzgEQ-zSg" 
genai.configure(api_key=GOOGLE_API_KEY)

# --- 2. ΣΥΝΑΡΤΗΣΕΙΣ ΔΕΔΟΜΕΝΩΝ ---
PROJECTS_FILE = 'data_projects.csv'
EMPLOYEES_FILE = 'data_employees.csv'
FINANCIALS_FILE = 'payroll_financials.csv'
CHECKLIST_FILE = 'checklist_results.csv'

def load_data(f, cols):
    if not os.path.isfile(f) or os.path.getsize(f) == 0:
        return pd.DataFrame(columns=cols)
    try:
        return pd.read_csv(f)
    except:
        return pd.DataFrame(columns=cols)

def save_to_csv(df, f):
    df.to_csv(f, index=False, encoding='utf-8-sig')

def extract_payroll_with_ai(uploaded_file):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        img = Image.open(uploaded_file)
        prompt = """
        Ανέλυσε αυτή την εικόνα μισθοδοσίας. Εξήγαγε τα ποσά για τα παρακάτω πεδία σε JSON:
        "ΙΚΑ_Εργ", "ΙΚΑ_Εργοδ", "ΤΕΚΑ_Εργ", "ΤΕΚΑ_Εργοδ", "Σύνολο_Εισφ", "ΦΜΥ", "Καθαρές", "Σύνολο_Αποδ".
        Μην γράψεις τίποτα άλλο εκτός από το JSON. Αν λείπει κάτι, βάλε 0.0.
        """
        response = model.generate_content([prompt, img])
        json_text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(json_text)
    except Exception as e:
        st.error(f"Σφάλμα AI: {e}")
        return None

# --- 3. ΡΥΘΜΙΣΗ ΣΕΛΙΔΑΣ ---
st.set_page_config(page_title="Payroll AI Verifier", layout="wide")
page = st.sidebar.radio("Μενού:", ["1. Διαχείριση Έργων", "2. Checklist ανά Έργο", "3. Μισθοδοσία Υπαλλήλων"])

# --- ΣΤΑΔΙΟ 1: ΔΙΑΧΕΙΡΙΣΗ ΕΡΓΩΝ ---
if page == "1. Διαχείριση Έργων":
    st.header("🏢 Διαχείριση Επιχειρήσεων")
    with st.form("project_form"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Επωνυμία Επιχείρησης")
        afm = c1.text_input("ΑΦΜ", max_chars=9)
        mis = c2.text_input("Κωδικός MIS")
        budget = c2.number_input("Συνολικός Προϋπολογισμός (€)", min_value=0.0)
        if st.form_submit_button("💾 Αποθήκευση"):
            df = load_data(PROJECTS_FILE, ["Επωνυμία", "ΑΦΜ", "MIS", "Προϋπολογισμός"])
            new_row = pd.DataFrame([{"Επωνυμία": name, "ΑΦΜ": afm, "MIS": mis, "Προϋπολογισμός": budget}])
            save_to_csv(pd.concat([df, new_row], ignore_index=True), PROJECTS_FILE)
            st.success("Το έργο αποθηκεύτηκε!")
            st.rerun()
    st.dataframe(load_data(PROJECTS_FILE, ["Επωνυμία", "ΑΦΜ", "MIS", "Προϋπολογισμός"]), use_container_width=True, hide_index=True)

# --- ΣΤΑΔΙΟ 2: CHECKLIST ΑΝΑ ΕΡΓΟ ---
elif page == "2. Checklist ανά Έργο":
    st.header("📂 Γενικά Παραδοτέα Επιχείρησης")
    projects_df = load_data(PROJECTS_FILE, ["Επωνυμία", "ΑΦΜ"])
    if projects_df.empty:
        st.warning("⚠️ Προσθέστε επιχείρηση στο Στάδιο 1.")
    else:
        sel_name = st.selectbox("Επιλέξτε Επιχείρηση:", projects_df['Επωνυμία'])
        sel_afm = str(projects_df[projects_df['Επωνυμία'] == sel_name]['ΑΦΜ'].iloc[0])
        check_df = load_data(CHECKLIST_FILE, ["ΑΦΜ", "Εγγραφο", "Κατάσταση", "Σχόλιο"])
        
        # Η πλήρης λίστα με όλα τα παραδοτέα που ζήτησες
        docs = [
            "Πίνακας Προσωπικού Ε4 (Ετήσιος/Συμπληρωματικός)",
            "Μισθολογικές καταστάσεις (υπογεγραμμένες)",
            "ΑΠΔ ΕΦΚΑ (Κοινή)",
            "Αποδεικτικό Υποβολής ΑΠΔ ΕΦΚΑ",
            "ΑΠΔ ΤΕΚΑ",
            "Αποδεικτικό Υποβολής ΑΠΔ ΤΕΚΑ",
            "Υπεύθυνη δήλωση μη απασχόλησης συγγενών",
            "Επιστολή γνωστοποίησης όρων σύμβασης",
            "Ασφαλιστική ενημερότητα (σε ισχύ)",
            "Οικονομική καρτέλα εργοδότη ΕΦΚΑ",
            "Ηλεκτρονική καρτέλα οφειλετών (ΚΕΑΟ)",
            "Πίνακας χρεών οφειλέτη",
            "Ανάλυση κίνησης Ηλ. Καρτέλας",
            "Φορολογική ενημερότητα (για είσπραξη χρημάτων)",
            "Στοιχεία ρυθμίσεων & Αποδεικτικά Πληρωμής",
            "Προσωρινές δηλώσεις ΦΜΥ & Αποδεικτικά"
        ]
        
        results = []
        
        # Εμφάνιση της λίστας
        for d in docs:
            existing = check_df[(check_df['ΑΦΜ'].astype(str) == sel_afm) & (check_df['Εγγραφο'] == d)]
            c1, c2, c3 = st.columns([2, 1, 1.5])
            
            c1.markdown(f"**{d}**")
            
            curr_st = existing['Κατάσταση'].iloc[0] if not existing.empty else "Έλλειψη ❌"
            status = c2.selectbox(
                "Κατάσταση", 
                ["Έλλειψη ❌", "Υπάρχει ✅", "Δεν απαιτείται"], 
                index=["Έλλειψη ❌", "Υπάρχει ✅", "Δεν απαιτείται"].index(curr_st), 
                key=f"s_{sel_afm}_{d}", 
                label_visibility="collapsed"
            )
            
            note = c3.text_input(
                "Σχόλιο", 
                value=existing['Σχόλιο'].iloc[0] if not existing.empty else "", 
                key=f"n_{sel_afm}_{d}", 
                label_visibility="collapsed", 
                placeholder="Σημειώσεις..."
            )
            
            results.append({"ΑΦΜ": sel_afm, "Εγγραφο": d, "Κατάσταση": status, "Σχόλιο": note})
        
        st.divider()
        if st.button("💾 Αποθήκευση Checklist", use_container_width=True):
            others = check_df[check_df['ΑΦΜ'].astype(str) != sel_afm]
            save_to_csv(pd.concat([others, pd.DataFrame(results)], ignore_index=True), CHECKLIST_FILE)
            st.success(f"✅ Το checklist για την επιχείρηση {sel_name} ενημερώθηκε!")

# --- ΣΤΑΔΙΟ 3: ΜΙΣΘΟΔΟΣΙΑ ---
elif page == "3. Μισθοδοσία Υπαλλήλων":
    st.header("👤 Έλεγχος Υπαλλήλων & Οικονομικά Στοιχεία")
    projects_df = load_data(PROJECTS_FILE, ["Επωνυμία", "ΑΦΜ"])
    
    if projects_df.empty:
        st.warning("⚠️ Προσθέστε επιχείρηση στο Στάδιο 1.")
    else:
        # Διάταξη: Αριστερά οι επιλογές φίλτρων, δεξιά η φόρμα νέου υπαλλήλου
        col_l, col_r = st.columns([1, 1.2], gap="large")
        
        with col_l:
            st.subheader("⚙️ Φίλτρα Αναζήτησης")
            sel_p = st.selectbox("Επιχείρηση:", projects_df['Επωνυμία'])
            s_afm = str(projects_df[projects_df['Επωνυμία'] == sel_p]['ΑΦΜ'].iloc[0])
            
            m_c, y_c = st.columns(2)
            month = m_c.selectbox("Μήνας:", ["Ιανουάριος", "Φεβρουάριος", "Μάρτιος", "Απρίλιος", "Μάιος", "Ιούνιος", "Ιούλιος", "Αύγουστος", "Σεπτέμβριος", "Οκτώβριος", "Νοέμβριος", "Δεκέμβριος"])
            year = y_c.selectbox("Έτος:", ["2024", "2025", "2026"], index=1)
            period = f"{month} {year}"
        
        with col_r:
            st.subheader("➕ Προσθήκη Νέου Υπαλλήλου")
            with st.form("employee_form", clear_on_submit=True):
                e_name = st.text_input("Ονοματεπώνυμο")
                c_a, c_m = st.columns(2)
                e_afm = c_a.text_input("ΑΦΜ Υπαλλήλου", max_chars=9)
                e_amka = c_m.text_input("ΑΜΚΑ Υπαλλήλου", max_chars=11)
                
                submit_emp = st.form_submit_button("📥 Καταχώρηση Υπαλλήλου", use_container_width=True)
                
                if submit_emp:
                    if not e_name or not e_afm:
                        st.error("⚠️ Το Ονοματεπώνυμο και το ΑΦΜ είναι υποχρεωτικά!")
                    else:
                        edf = load_data(EMPLOYEES_FILE, ["ΑΦΜ_Εργου", "Ονοματεπώνυμο", "ΑΦΜ_Υπαλλήλου", "ΑΜΚΑ_Υπαλλήλου"])
                        new_emp = pd.DataFrame([{
                            "ΑΦΜ_Εργου": s_afm, 
                            "Ονοματεπώνυμο": e_name, 
                            "ΑΦΜ_Υπαλλήλου": e_afm, 
                            "ΑΜΚΑ_Υπαλλήλου": e_amka
                        }])
                        save_to_csv(pd.concat([edf, new_emp], ignore_index=True), EMPLOYEES_FILE)
                        st.success(f"✅ Ο υπάλληλος {e_name} καταχωρήθηκε!")
                        st.rerun()

        st.divider()
        
        # Φόρτωση και φιλτράρισμα υπαλλήλων για τη συγκεκριμένη επιχείρηση
        all_e = load_data(EMPLOYEES_FILE, ["ΑΦΜ_Εργου", "Ονοματεπώνυμο", "ΑΦΜ_Υπαλλήλου", "ΑΜΚΑ_Υπαλλήλου"])
        c_emps = all_e[all_e['ΑΦΜ_Εργου'].astype(str) == s_afm]
        e_list = c_emps.apply(lambda x: f"{x['Ονοματεπώνυμο']} (ΑΦΜ: {x['ΑΦΜ_Υπαλλήλου']})", axis=1).tolist()

        if not e_list:
            st.info("💡 Η λίστα υπαλλήλων είναι κενή για αυτή την επιχείρηση. Προσθέστε έναν υπάλληλο παραπάνω.")
        else:
            sel_e = st.selectbox("🔍 Επιλέξτε Υπάλληλο για Έλεγχο:", ["---"] + e_list)
            
            if sel_e != "---":
                e_afm_val = sel_e.split("(ΑΦΜ: ")[1].replace(")", "")
                emp_data = c_emps[c_emps['ΑΦΜ_Υπαλλήλου'].astype(str) == e_afm_val].iloc[0]
                f_key = f"FIN_{s_afm}_{e_afm_val}_{period}"
                
                # Εμφάνιση ΑΜΚΑ υπαλλήλου στην οθόνη
                st.info(f"📋 **Επιλεγμένος Υπάλληλος:** {emp_data['Ονοματεπώνυμο']} | **ΑΜΚΑ:** {emp_data['ΑΜΚΑ_Υπαλλήλου']} | **Περίοδος:** {period}")
                
                # Upload αρχείου και AI επεξεργασία
                up_pay = st.file_uploader("📂 Ανέβασμα Μισθοδοτικής (AI Ανάλυση)", type=['png', 'jpg', 'jpeg', 'pdf'])
                ocr_data = {}
                if up_pay:
                    with st.spinner("🤖 Το AI διαβάζει τη μισθοδοτική..."):
                        ocr_data = extract_payroll_with_ai(up_pay)
                        if ocr_data:
                            st.success("✅ Η ανάλυση από το AI ολοκληρώθηκε!")

                # Φόρτωση οικονομικών στοιχείων από το αρχείο
                f_df = load_data(FINANCIALS_FILE, ["ID_Κλειδί", "ΙΚΑ_Εργ", "ΙΚΑ_Εργοδ", "ΤΕΚΑ_Εργ", "ΤΕΚΑ_Εργοδ", "Σύνολο_Εισφ", "ΦΜΥ", "Καθαρές", "Σύνολο_Αποδ", "ΟΠΣΚΕ"])
                ext = f_df[f_df['ID_Κλειδί'] == f_key]
                
                def get_v(k): 
                    return float(ext[k].iloc[0]) if not ext.empty else ocr_data.get(k, 0.0)

                # Φόρμα εμφάνισης και επεξεργασίας ποσών
                st.subheader("💰 Ανάλυση Ποσών")
                c1, c2 = st.columns(2)
                v1 = c1.number_input("Εισφορές Εργαζομένου ΙΚΑ", value=get_v("ΙΚΑ_Εργ"), format="%.2f")
                v2 = c2.number_input("Εισφορές Εργοδότη ΙΚΑ", value=get_v("ΙΚΑ_Εργοδ"), format="%.2f")
                
                c3, c4 = st.columns(2)
                v3 = c3.number_input("Εισφορές Εργαζομένου ΤΕΚΑ", value=get_v("ΤΕΚΑ_Εργ"), format="%.2f")
                v4 = c4.number_input("Εισφορές Εργοδότη ΤΕΚΑ", value=get_v("ΤΕΚΑ_Εργοδ"), format="%.2f")

                c5, c6, c7 = st.columns(3)
                v5 = c5.number_input("Σύνολο Ασφαλιστικών Εισφορών", value=get_v("Σύνολο_Εισφ"), format="%.2f")
                v6 = c6.number_input("ΦΜΥ (Φόρος)", value=get_v("ΦΜΥ"), format="%.2f")
                v7 = c7.number_input("Καθαρές Αποδοχές (Πληρωτέο)", value=get_v("Καθαρές"), format="%.2f")

                c8, c9, c10 = st.columns(3)
                v8 = c8.number_input("Σύνολο Αποδοχών (Μικτά)", value=get_v("Σύνολο_Αποδ"), format="%.2f")
                v9 = c9.number_input("Αιτούμενο Ποσό ΟΠΣΚΕ", value=get_v("ΟΠΣΚΕ"), format="%.2f")
                
                # Μαθηματικός Έλεγχος (Καθαρές + Εισφορές + ΦΜΥ)
                calc = v7 + v5 + v6
                c10.metric("Έλεγχος Αθροίσματος", f"{calc:,.2f} €")
                
                if st.button("💾 Αποθήκευση Οικονομικών Στοιχείων", use_container_width=True):
                    row = {
                        "ID_Κλειδί": f_key, "ΙΚΑ_Εργ": v1, "ΙΚΑ_Εργοδ": v2, 
                        "ΤΕΚΑ_Εργ": v3, "ΤΕΚΑ_Εργοδ": v4, "Σύνολο_Εισφ": v5, 
                        "ΦΜΥ": v6, "Καθαρές": v7, "Σύνολο_Αποδ": v8, "ΟΠΣΚΕ": v9
                    }
                    # Αντικατάσταση αν προϋπάρχει η εγγραφή, αλλιώς προσθήκη
                    f_df = pd.concat([f_df[f_df['ID_Κλειδί'] != f_key], pd.DataFrame([row])], ignore_index=True)
                    save_to_csv(f_df, FINANCIALS_FILE)
                    st.toast("✅ Τα οικονομικά στοιχεία αποθηκεύτηκαν!")
