import streamlit as st
import pandas as pd
import os
import google.generativeai as genai
from PIL import Image
import json

# --- 1. ΡΥΘΜΙΣΗ AI (GEMINI) ---
# Αντικατάστησε το κλειδί παρακάτω με το δικό σου
GOOGLE_API_KEY = "ΤΟ_API_KEY_ΣΟΥ_ΕΔΩ" 
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
    if not os.path.isfile(f) or os.path.getsize(f) == 0: return pd.DataFrame(columns=cols)
    return pd.read_csv(f)

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
elif page == "2. Checklist ανά Έργο":
    st.header("📂 Γενικά Παραδοτέα")
    # [Ο κώδικας του σταδίου 2 παραμένει ίδιος]

# --- ΣΤΑΔΙΟ 3: ΜΙΣΘΟΔΟΣΙΑ ΜΕ AI ---
elif page == "3. Μισθοδοσία Υπαλλήλων":
    st.header("👤 Έλεγχος & AI Ανάγνωση")
    projects_df = load_data(PROJECTS_FILE, ["Επωνυμία", "ΑΦΜ"])
    
    if projects_df.empty:
        st.warning("⚠️ Καταχωρήστε επιχείρηση στο Στάδιο 1.")
    else:
        # Επιλογή Επιχείρησης & Περιόδου
        c1, c2, c3 = st.columns([1.5, 1, 1])
        sel_proj = c1.selectbox("Επιχείρηση:", projects_df['Επωνυμία'])
        sel_afm = str(projects_df[projects_df['Επωνυμία'] == sel_proj]['ΑΦΜ'].iloc[0])
        sel_month = c2.selectbox("Μήνας:", ["Ιανουάριος", "Φεβρουάριος", "Μάρτιος", "Απρίλιος", "Μάιος", "Ιούνιος", "Ιούλιος", "Αύγουστος", "Σεπτέμβριος", "Οκτώβριος", "Νοέμβριος", "Δεκέμβριος"])
        sel_year = c3.selectbox("Έτος:", ["2024", "2025", "2026"], index=1)
        period = f"{sel_month} {sel_year}"

        # Επιλογή Υπαλλήλου
        all_emps = load_data(EMPLOYEES_FILE, ["ΑΦΜ_Εργου", "Ονοματεπώνυμο", "ΑΦΜ_Υπαλλήλου", "ΑΜΚΑ_Υπαλλήλου"])
        curr_emps = all_emps[all_emps['ΑΦΜ_Εργου'].astype(str) == sel_afm]
        emp_list = curr_emps.apply(lambda x: f"{x['Ονοματεπώνυμο']} (ΑΦΜ: {x['ΑΦΜ_Υπαλλήλου']})", axis=1).tolist()

        if emp_list:
            sel_emp = st.selectbox("🔍 Επιλογή Υπαλλήλου:", ["--- Επιλογή ---"] + emp_list)
            if sel_emp != "--- Επιλογή ---":
                emp_afm = sel_emp.split("(ΑΦΜ: ")[1].replace(")", "")
                fin_key = f"FIN_{sel_afm}_{emp_afm}_{period}"

                st.subheader("💰 Οικονομικά Στοιχεία")
                uploaded_file = st.file_uploader("📂 Ανεβάστε τη Μισθοδοτική (Image/PDF)", type=['png', 'jpg', 'jpeg', 'pdf'])
                
                # Αρχικοποίηση τιμών
                ocr_vals = {}
                if uploaded_file:
                    with st.spinner("🤖 Το AI αναλύει τη μισθοδοτική..."):
                        ocr_vals = extract_payroll_with_ai(uploaded_file)
                        if ocr_vals: st.success("✅ Ανάλυση επιτυχής!")

                # Φόρτωση από CSV για manual override
                fin_df = load_data(FINANCIALS_FILE, ["ID_Κλειδί", "ΙΚΑ_Εργ", "ΙΚΑ_Εργοδ", "ΤΕΚΑ_Εργ", "ΤΕΚΑ_Εργοδ", "Σύνολο_Εισφ", "ΦΜΥ", "Καθαρές", "Σύνολο_Αποδ", "ΟΠΣΚΕ"])
                ext_fin = fin_df[fin_df['ID_Κλειδί'] == fin_key]

                def gv(k):
                    if not ext_fin.empty: return float(ext_fin[k].iloc[0])
                    return ocr_vals.get(k, 0.0)

                # Φόρμα με τα πεδία
                f1, f2 = st.columns(2)
                v_ika_erg = f1.number_input("Εργαζ. ΙΚΑ", value=gv("ΙΚΑ_Εργ"), format="%.2f")
                v_ika_ergo = f2.number_input("Εργοδ. ΙΚΑ", value=gv("ΙΚΑ_Εργοδ"), format="%.2f")
                
                f3, f4 = st.columns(2)
                v_teka_erg = f3.number_input("Εργαζ. ΤΕΚΑ", value=gv("ΤΕΚΑ_Εργ"), format="%.2f")
                v_teka_ergo = f4.number_input("Εργοδ. ΤΕΚΑ", value=gv("ΤΕΚΑ_Εργοδ"), format="%.2f")

                f5, f6, f7 = st.columns(3)
                v_sum_eisf = f5.number_input("Σύνολο Εισφορών", value=gv("Σύνολο_Εισφ"), format="%.2f")
                v_fmy = f6.number_input("ΦΜΥ", value=gv("ΦΜΥ"), format="%.2f")
                v_net = f7.number_input("Καθαρές Αποδοχές", value=gv("Καθαρές"), format="%.2f")

                f8, f9, f10 = st.columns(3)
                v_total_ap = f8.number_input("Σύνολο Αποδοχών", value=gv("Σύνολο_Αποδ"), format="%.2f")
                v_opske = f9.number_input("Αιτούμενο ΟΠΣΚΕ", value=gv("ΟΠΣΚΕ"), format="%.2f")
                
                calc = v_net + v_sum_eisf + v_fmy
                f10.metric("Έλεγχος Αθροίσματος", f"{calc:,.2f} €")

                if st.button("💾 Αποθήκευση", use_container_width=True):
                    new_data = {"ID_Κλειδί": fin_key, "ΙΚΑ_Εργ": v_ika_erg, "ΙΚΑ_Εργοδ": v_ika_ergo, "ΤΕΚΑ_Εργ": v_teka_erg, "ΤΕΚΑ_Εργοδ": v_teka_ergo, "Σύνολο_Εισφ": v_sum_eisf, "ΦΜΥ": v_fmy, "Καθαρές": v_net, "Σύνολο_Αποδ": v_total_ap, "ΟΠΣΚΕ": v_opske}
                    fin_df = pd.concat([fin_df[fin_df['ID_Κλειδί'] != fin_key], pd.DataFrame([new_data])], ignore_index=True)
                    save_to_csv(fin_df, FINANCIALS_FILE)
                    st.toast("✅ Αποθηκεύτηκε επιτυχώς!")
