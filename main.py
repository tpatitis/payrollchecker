import streamlit as st

import pandas as pd

import os

import json

from google import genai

from google.genai import types

from pydantic import BaseModel, Field


# --- 1. ΡΥΘΜΙΣΗ ΣΕΛΙΔΑΣ ---

st.set_page_config(

    page_title="Payroll Verifier Pro",

    page_icon="🛡️",

    layout="wide"

)


# --- 2. ΟΡΙΣΜΟΣ ΑΡΧΕΙΩΝ ΔΕΔΟΜΕΝΩΝ ---

PROJECTS_FILE = 'data_projects.csv'

CHECKLIST_FILE = 'checklist_results.csv'

EMPLOYEES_FILE = 'data_employees.csv'


# Ορίστε τα αρχεία που θα χρησιμοποιείτε

FINANCIALS_FILE = 'payroll_financials.csv'

PAYROLL_CHECKS_FILE = 'payroll_checks.csv'


# --- 3. ΣΥΝΑΡΤΗΣΕΙΣ ΔΙΑΧΕΙΡΙΣΗΣ ΔΕΔΟΜΕΝΩΝ ---

def load_data(filename, columns):

    try:

        df = pd.read_csv(filename)

    except FileNotFoundError:

        df = pd.DataFrame(columns=columns)

    return df


def save_to_csv(df, filename):

    df.to_csv(filename, index=False)


# --- 4. ΣΤΑΔΙΟ 3: ΜΙΣΘΟΔΟΣΙΑ ΥΠΑΛΛΗΛΩΝ (STRUCTURED OUTPUT SCHEMA) ---

class FinancialGroup(BaseModel):

    ΙΚΑ_Εργαζομένου: float = 0.0

    ΙΚΑ_Εργοδότη: float = 0.0

    ΤΕΚΑ_Εργαζομένου: float = 0.0

    ΤΕΚΑ_Εργοδότη: float = 0.0

    Σύνολο_Εισφορών: float = 0.0

    ΦΜΥ: float = 0.0

    Καθαρές_αποδοχές: float = 0.0

    Σύνολο_Κόστος: float = 0.0


class PayrollFinancials(BaseModel):

    Τακτικές: FinancialGroup

    Δώρο_Πάσχα: FinancialGroup

    Δώρο_Χριστουγέννων: FinancialGroup

    Επίδομα_Άδειας: FinancialGroup

    Λοιπά: FinancialGroup


def extract_financials_with_ai_stage3(uploaded_file, emp_name):

    """Συνάρτηση AI OCR που αναλύει το έγγραφο μέσω του Gemini API και επιστρέφει δομημένο JSON"""

    API_KEY = st.secrets.get("GEMINI_API_KEY")

    if not API_KEY:

        st.error("🔑 Παρακαλώ ορίστε το Google Gemini API Key στα Secrets.")

        return {}


    try:

        client = genai.Client(api_key=API_KEY)

        file_bytes = uploaded_file.read()

        mime_type = uploaded_file.type

        file_part = types.Part.from_bytes(

            data=file_bytes,

            mime_type=mime_type,

        )


        prompt = f"""

        Είσαι έμπειρος Έλληνας λογιστής. Σου δίνεται ένα έγγραφο μισθοδοσίας.

        Στόχος σου είναι να εξάγεις τα οικονομικά στοιχεία ΑΠΟΚΛΕΙΣΤΙΚΑ για τον υπάλληλο: "{emp_name}".


        ΑΥΣΤΗΡΟΙ ΚΑΝΟΝΕΣ:

        1. ΠΡΟΥΠΟΘΕΣΗ ΟΝΟΜΑΤΟΣ: Αν το όνομα "{emp_name}" ΔΕΝ αναγράφεται στο έγγραφο, επέστρεψε 0.0 σε όλα τα πεδία.

        2. ΔΟΜΗ ΔΕΔΟΜΕΝΩΝ: Πρέπει να ομαδοποιήσεις τα ποσά ανά τύπο αποδοχών (Τακτικές, Δώρο_Πάσχα, Δώρο_Χριστουγέννων, Επίδομα_Άδειας, Λοιπά).

        3. ΑΤΟΜΙΚΑ ΣΤΟΙΧΕΙΑ: Κάθε ομάδα (π.χ. Δώρο Πάσχα) πρέπει να περιέχει τα δικά της ΙΚΑ, ΦΜΥ και Καθαρές αποδοχές όπως αναγράφονται στο έγγραφο. 

           Αν για κάποια ομάδα δεν υπάρχουν κρατήσεις, βάλε 0.0.

        4. ΑΓΝΟΗΣΕ ΓΕΝΙΚΑ ΣΥΝΟΛΑ: Μην παίρνεις τα συνολικά αθροίσματα της επιχείρησης, μόνο τη γραμμή του "{emp_name}".

        5. ΑΚΡΙΒΕΙΑ: Το 'Καθαρές' είναι το πληρωτέο ποσό. Αν ένα ποσό δεν υπάρχει, βάλε 0.0.

        """


        response = client.models.generate_content(

            model='gemini-2.5-flash',

            contents=[file_part, prompt],

            config=types.GenerateContentConfig(

                response_mime_type="application/json",

                response_schema=PayrollFinancials,

                temperature=0.0

            ),

        )

        return json.loads(response.text)

    except Exception as e:

        st.error(f"❌ Σφάλμα κατά την επεξεργασία AI OCR: {e}")

        return {}

def render_financial_fields(tab_prefix, group_data, fields_to_show=None):

    """

    Εμφανίζει τα πεδία εισαγωγής.

    - tab_prefix: String για το μοναδικό key

    - group_data: Dictionary ή Pydantic model με τις τιμές

    - fields_to_show: Λίστα με τα πεδία που θέλουμε να εμφανίσουμε (προαιρετικό)

    """

    # 1. Μετατροπή σε dict αν είναι Pydantic model (όπως το FinancialGroup)

    if hasattr(group_data, 'model_dump'):

        data = group_data.model_dump()

    else:

        data = group_data if isinstance(group_data, dict) else {}


    # 2. Αν δεν ορίσουμε πεδία, εμφάνισε όλα όσα περιέχει το group_data

    if fields_to_show is None:

        fields_to_show = list(data.keys())

    

    financials = {}

    cols = st.columns(2)

    

    # 3. Εμφάνιση των πεδίων

    for i, field in enumerate(fields_to_show):

        with cols[i % 2]:

            val = data.get(field, 0.0)

            financials[field] = st.number_input(

                field.replace("_", " "), 

                value=float(val), 

                format="%.2f", 

                key=f"{tab_prefix}_{field}"

            )

    return financials

    

    # Χρησιμοποιούμε το current_values που ήρθε από το OCR ή το CSV

    with cols[0]:

        ika_erg = st.number_input("ΙΚΑ Εργαζόμενου", value=float(current_values.get("ΙΚΑ_Εργαζομένου", 0.0)), format="%.2f", key=f"{tab_prefix}_ika_erg")

        ika_ergod = st.number_input("ΙΚΑ Εργοδότη", value=float(current_values.get("ΙΚΑ_Εργοδότη", 0.0)), format="%.2f", key=f"{tab_prefix}_ika_ergod")

        teka_erg = st.number_input("ΤΕΚΑ Εργαζόμενου", value=float(current_values.get("ΤΕΚΑ_Εργαζομένου", 0.0)), format="%.2f", key=f"{tab_prefix}_teka_erg")

        teka_ergod = st.number_input("ΤΕΚΑ Εργοδότη", value=float(current_values.get("ΤΕΚΑ_Εργοδότη", 0.0)), format="%.2f", key=f"{tab_prefix}_teka_ergod")

    with cols[1]:

        fmy = st.number_input("ΦΜΥ", value=float(current_values.get("ΦΜΥ", 0.0)), format="%.2f", key=f"{tab_prefix}_fmy")

        kathares = st.number_input("Καθαρές Αποδοχές", value=float(current_values.get("Καθαρές_αποδοχές", 0.0)), format="%.2f", key=f"{tab_prefix}_kathares")

        opsk = st.number_input("ΟΠΣΚΕ", value=float(current_values.get("Επιδοτούμενο_ΟΠΣΚΕ", 0.0)), format="%.2f", key=f"{tab_prefix}_opsk")


    return {

        "ΙΚΑ_Εργαζομένου": ika_erg,

        "ΙΚΑ_Εργοδότη": ika_ergod,

        "ΤΕΚΑ_Εργαζομένου": teka_erg,

        "ΤΕΚΑ_Εργοδότη": teka_ergod,

        "ΦΜΥ": fmy,

        "Καθαρέ_αποδοχέςς": kathares,

        "Επιδοτούμενο_ΟΠΣΚΕ": opsk

    }

def render_stage_3(fin_key, emp_data, selected_month, selected_year, period, selected_afm):

    # --- ΠΡΟΣΘΗΚΗ OCR UPLOADER ---

    st.subheader("📄 Αυτόματη Ανάγνωση Μισθοδοσίας")

    uploaded_file = st.file_uploader("Ανέβασε αρχείο μισθοδοσίας (PDF/Image)", type=['pdf', 'png', 'jpg'], key=f"upload_{fin_key}")

    

    if uploaded_file is not None:

        if st.button("🚀 Ανάλυση με AI"):

            with st.spinner("Αναλύω το έγγραφο..."):

                ocr_results = extract_financials_with_ai_stage3(uploaded_file, emp_data["Ονοματεπώνυμο"])

                if ocr_results:

                    st.session_state[f"ocr_data_{fin_key}"] = ocr_results

                    st.success("✅ Τα δεδομένα εξήχθησαν επιτυχώς!")

                    st.rerun() # Επανεκκίνηση για να εμφανιστούν οι τιμές στα πεδία

    

    # Φόρτωση δεδομένων

    fin_cols = ["ID_Κλειδί", "ΙΚΑ_Εργαζομένου", "ΙΚΑ_Εργοδότη", "ΤΕΚΑ_Εργαζομένου", "ΤΕΚΑ_Εργοδότη", "Σύνολο_Εισφορών", "ΦΜΥ", "Καθαρές_αποδοχές", "Τακτικές_Αποδ", "Υπερωρίες", "Δώρο_Πάσχα", "Δώρο_Χριστουγέννων", "Επίδομα_Άδειας", "Λοιπά_Αποδ", "Σύνολο_Αποδ", "ΟΠΣΚΕ"]

    

    # Χρήση της global FINANCIALS_FILE που ορίστηκε στην αρχή του αρχείου

    fin_df = load_data(FINANCIALS_FILE, fin_cols)


    # Διασφάλιση ότι όλες οι στήλες υπάρχουν

    for col in fin_cols:

        if col not in fin_df.columns:

            fin_df[col] = 0.0


    # Εύρεση τρέχοντων δεδομένων

    ext_fin = fin_df[fin_df['ID_Κλειδί'] == fin_key]

    default_values = {k: (float(ext_fin[k].iloc[0]) if not ext_fin.empty and k in ext_fin.columns else 0.0) for k in fin_cols if k != "ID_Κλειδί"}

        

    # Αν υπάρχει OCR data, το περνάμε ως default

    trigger_key = f"ocr_data_{fin_key}"

    if trigger_key in st.session_state:

        ocr_data = st.session_state[trigger_key]

        for k in default_values:

            if k in ocr_data:

                default_values[k] = ocr_data[k]


    # Εμφάνιση default values για debugging

    st.write("Default Values loaded:", default_values)


    

    # Αρχικοποίηση του dictionary αν δεν υπάρχει

    st.session_state["financial_data"] = {

        "ΙΚΑ_Εργ": 0.0, "ΙΚΑ_Εργοδ": 0.0, "ΤΕΚΑ_Εργ": 0.0, "ΤΕΚΑ_Εργοδ": 0.0,

        "Σύνολο_Εισφ": 0.0, "ΦΜΥ": 0.0, "Καθαρές": 0.0, "ΟΠΣΚΕ": 0.0,

        "Τακτικές_Αποδ": default_values.get("Τακτικές_Αποδ", 0.0),

        "Δώρο_Πάσχα": default_values.get("Δώρο_Πάσχα", 0.0),

        "Δώρο_Χριστουγέννων": default_values.get("Δώρο_Χριστουγέννων", 0.0),

        "Επίδομα_Άδειας": default_values.get("Επίδομα_Άδειας", 0.0)

    }


    # 1. Πάρε τα δεδομένα από το OCR αν υπάρχουν...

    ocr_data = st.session_state.get(f"ocr_data_{fin_key}", {})

    

    def get_val(key_name):

        if key_name in ocr_data: return ocr_data[key_name]

        return default_values.get(key_name, 0.0)


    # 2. Tabs με σωστή ανάθεση τιμών

    tabs = st.tabs(["Τακτικές αποδοχές", "Δώρο Πάσχα", "Δώρο Χριστουγέννων", "Επίδομα αδείας"])


    # --- TAB 0: Τακτικές αποδοχές ---

    with tabs[0]:

               

        group_data = st.session_state.get("ocr_results", {}).get("Τακτικές_Αποδοχές", FinancialGroup())

        # Εμφάνιση πεδίων και λήψη αποτελεσμάτων

        tak_data = render_financial_fields(f"{fin_key}_tak", group_data)

        # Αποθήκευση στο state ως ξεχωριστό αντικείμενο

        st.session_state["financial_data"]["Τακτικές"] = tak_data

    # --- TAB 1: Δώρο Πάσχα ---

    

    with tabs[1]:

        group_data = st.session_state.get("ocr_results", {}).get("Δώρο_Πάσχα", FinancialGroup())

        # Εμφάνιση πεδίων και λήψη αποτελεσμάτων

        doro_pasxa_data = render_financial_fields(f"{fin_key}_pasxa", group_data)

        # Αποθήκευση στο state ως ξεχωριστό αντικείμενο

        st.session_state["financial_data"]["Δώρο_Πάσχα"] = doro_pasxa_data

   

    # --- TAB 2: Δώρο Χριστουγέννων ---

    with tabs[2]:

        group_data = st.session_state.get("ocr_results", {}).get("Δώρο_Χριστουγέννων", FinancialGroup())

        # Εμφάνιση πεδίων και λήψη αποτελεσμάτων

        doro_xrist_data = render_financial_fields(f"{fin_key}_xrist", group_data)

        # Αποθήκευση στο state ως ξεχωριστό αντικείμενο

        st.session_state["financial_data"]["Δώρο_Χριστουγέννων"] = doro_xrist_data

       

    # --- TAB 3: Επίδομα αδείας ---

    with tabs[3]:

        group_data = st.session_state.get("ocr_results", {}).get("Επίδομα_Άδειας", FinancialGroup())

        # Εμφάνιση πεδίων και λήψη αποτελεσμάτων

        epidom_data = render_financial_fields(f"{fin_key}_epidom", group_data)

        # Αποθήκευση στο state ως ξεχωριστό αντικείμενο

        st.session_state["financial_data"]["Επίδομα_Άδειας"] = epidom_data

    

        

    if st.button("💾 Αποθήκευση Όλων"):

        # Δημιουργία flat dictionary για το CSV

        flat_data = {"ID_Κλειδί": fin_key}

    

        # Προσθήκη όλων των επιμέρους στοιχείων (π.χ. Δώρο_Πάσχα_ΙΚΑ_Εργ)

        for group_name, group_dict in st.session_state["financial_data"].items():

            if isinstance(group_dict, dict):

                for field, val in group_dict.items():

                    flat_data[f"{group_name}_{field}"] = val

            else:

                flat_data[group_name] = group_dict

            

        # 3. Φόρτωση, ενημέρωση και αποθήκευση στο CSV

        fin_df = load_data(FINANCIALS_FILE, list(flat_row.keys()))

        

        # Αφαιρούμε παλιά εγγραφή για το ίδιο ID αν υπάρχει

        fin_df = fin_df[fin_df['ID_Κλειδί'] != fin_key]

        

        # Προσθήκη νέας γραμμής

        new_row = pd.DataFrame([flat_row])

        fin_df = pd.concat([fin_df, new_row], ignore_index=True)

        

        save_to_csv(fin_df, FINANCIALS_FILE)

        st.success("✅ Τα στοιχεία αποθηκεύτηκαν επιτυχώς στο CSV!")

    

# --- 5. ΠΛΕΥΡΙΚΟ ΜΕΝΟΥ ---

st.sidebar.title("📑 Μενού Διαχείρισης")

page = st.sidebar.radio(

    "Μετάβαση σε:",

    ["1. Διαχείριση Έργων", "2. Checklist ανά Έργο", "3. Μισθοδοσία Υπαλλήλων"]

)


# --- ΣΤΑΔΙΟ 1: ΔΙΑΧΕΙΡΙΣΗ ΕΡΓΩΝ ---

if page == "1. Διαχείριση Έργων":

    st.header("🏢 Διαχείριση Επιχειρήσεων")

    with st.expander("➕ Προσθήκη / Επεξεργασία Έργου", expanded=True):

        with st.form("project_form"):

            col1, col2 = st.columns(2)

            with col1:

                name = st.text_input("Επωνυμία Επιχείρησης")

                afm = st.text_input("ΑΦΜ (9 ψηφία)", max_chars=9)

            with col2:

                mis = st.text_input("Κωδικός Έργου (MIS)")

                budget = st.number_input("Συνολικός Προϋπολογισμός (€)", min_value=0.0)

            if st.form_submit_button("💾 Αποθήκευση Στοιχείων"):

                if name and afm:

                    df = load_data(PROJECTS_FILE, ["Επωνυμία", "ΑΦΜ", "MIS", "Προϋπολογισμός"])

                    if afm in df['ΑΦΜ'].astype(str).values:

                        df.loc[df['ΑΦΜ'].astype(str) == afm, ["Επωνυμία", "MIS", "Προϋπολογισμός"]] = [name, mis, budget]

                    else:

                        new_row = pd.DataFrame([{"Επωνυμία": name, "ΑΦΜ": afm, "MIS": mis, "Προϋπολογισμός": budget}])

                        df = pd.concat([df, new_row], ignore_index=True)

                    save_to_csv(df, PROJECTS_FILE)

                    st.success("✅ Το έργο αποθηκεύτηκε!")

                    st.rerun()


    st.markdown("### 📋 Λίστα Εγγεγραμμένων Επιχειρήσεων")

    df_display = load_data(PROJECTS_FILE, ["Επωνυμία", "ΑΦΜ", "MIS", "Προϋπολογισμός"])

    if not df_display.empty:

        st.dataframe(df_display, use_container_width=True, hide_index=True)

        with st.expander("🗑️ Διαγραφή Επιχείρησης"):

            delete_afm = st.selectbox("Επιλέξτε ΑΦΜ για διαγραφή:", df_display['ΑΦΜ'].astype(str).unique())

            if st.button("Οριστική Διαγραφή", type="primary"):

                df_display = df_display[df_display['ΑΦΜ'].astype(str) != str(delete_afm)]

                save_to_csv(df_display, PROJECTS_FILE)

                st.rerun()


# --- ΣΤΑΔΙΟ 2: CHECKLIST ΑΝΑ ΕΡΓΟ ---

elif page == "2. Checklist ανά Έργο":

    st.header("📂 Γενικά Παραδοτέα Μισθοδοσίας")

    projects_df = load_data(PROJECTS_FILE, ["Επωνυμία", "ΑΦΜ"])

    if projects_df.empty:

        st.warning("⚠️ Καταχωρήστε μια επιχείρηση στο Στάδιο 1.")

    else:

        selected_name = st.selectbox("Επιλέξτε Επιχείρηση:", projects_df['Επωνυμία'])

        selected_afm = str(projects_df[projects_df['Επωνυμία'] == selected_name]['ΑΦΜ'].iloc[0]).strip()

        check_df = load_data(CHECKLIST_FILE, ["ΑΦΜ", "Εγγραφο", "Κατάσταση", "Σχόλιο"])


        if not check_df.empty:

            check_df['ΑΦΜ'] = check_df['ΑΦΜ'].astype(str).str.strip()

            check_df['Σχόλιο'] = check_df['Σχόλιο'].fillna('').astype(str).str.replace('nan', '', case=False)


        required_docs = [

            "Πίνακας Προσωπικού Ε4", "Μισθολογικές καταστάσεις", "ΑΠΔ ΕΦΚΑ",

            "Αποδεικτικό Υποβολής ΑΠΔ", "ΑΠΔ ΤΕΚΑ", "Αποδεικτικό Υποβολής ΑΠΔ ΤΕΚΑ",

            "Υπεύθυνη δήλωση συγγενών", "Επιστολή γνωστοποίησης", "Ασφαλιστική ενημερότητα",

            "Οικονομική καρτέλα ΕΦΚΑ", "Ηλεκτρονική καρτέλα οφειλετών", "Πίνακας χρεών οφειλέτη",

            "Ανάλυση κίνησης Ηλ. Καρτέλας", "Φορολογική ενημερότητα", "Στοιχεία ρυθμίσεων & Πληρωμή",

            "Προσωρινές δηλώσεις ΦΜΥ"

        ]


        if f"success_{selected_afm}" in st.session_state:

            st.success(f"✅ Το checklist για την επιχείρηση '{selected_name}' αποθηκεύτηκε επιτυχώς!")

            del st.session_state[f"success_{selected_afm}"]


        results = []

        for doc in required_docs:

            existing = check_df[(check_df['ΑΦΜ'] == selected_afm) & (check_df['Εγγραφο'] == doc)]


            c1, c2, c3 = st.columns([1.5, 1.0, 2.5], gap="small")

            c1.markdown(f"<div style='font-size:0.85rem; padding-top:5px;'><b>{doc}</b></div>", unsafe_allow_html=True)


            status = c2.selectbox(

                "",

                ["Έλλειψη ❌", "Υπάρχει ✅", "Δεν απαιτείται"],

                index=["Έλλειψη ❌", "Υπάρχει ✅", "Δεν απαιτείται"].index(existing['Κατάσταση'].iloc[0]) if not existing.empty else 0,

                key=f"gen_{selected_afm}_{doc}",

                label_visibility="collapsed"

            )


            val_note = existing['Σχόλιο'].iloc[0] if not existing.empty else ""

            if val_note.lower() == 'nan':

                val_note = ""


            note = c3.text_input(

                "",

                value=val_note,

                key=f"gen_n_{selected_afm}_{doc}",

                label_visibility="collapsed",

                placeholder="Σημειώσεις..."

            )


            results.append({"ΑΦΜ": selected_afm, "Εγγραφο": doc, "Κατάσταση": status, "Σχόλιο": note})


        st.markdown("<br>", unsafe_allow_html=True)

        # Υπολογισμός συνολικών για την αποθήκευση

        v_total_ap = 0.0

        v_yp_ap = 0.0

        v_loip_ap = 0.0


        if st.button("💾 Αποθήκευση Checklist", use_container_width=True):

            check_df = check_df[check_df['ΑΦΜ'] != selected_afm]

            save_to_csv(pd.concat([check_df, pd.DataFrame(results)], ignore_index=True), CHECKLIST_FILE)

            st.session_state[f"success_{selected_afm}"] = True

            st.rerun()


# --- ΣΤΑΔΙΟ 3: ΜΙΣΘΟΔΟΣΙΑ ΥΠΑΛΛΗΛΩΝ ---

elif page == "3. Μισθοδοσία Υπαλλήλων":

    st.header("👤 Έλεγχος Μισθοδοσίας Υπαλλήλων")

    projects_df = load_data(PROJECTS_FILE, ["Επωνυμία", "ΑΦΜ"])

    if projects_df.empty:

        st.error("⚠️ Παρακαλώ καταχωρήστε τουλάχιστον μία επιχείρηση στο 'Στάδιο 1' πριν προχωρήσετε.")

    else:

        selected_project_name = st.selectbox("Επιλέξτε Επιχείρηση για τον έλεγχο:", projects_df['Επωνυμία'], key="stage3_project_select")

        selected_project_afm = str(projects_df[projects_df['Επωνυμία'] == selected_project_name]['ΑΦΜ'].iloc[0])


        # ---------------- DYNAMIC SIDEBAR FOR EMPLOYEES ----------------

        st.sidebar.markdown("---")

        st.sidebar.subheader("👥 Διαχείριση & Επιλογή Υπαλλήλων")

        emp_cols = ["ID", "Ονοματεπώνυμο", "ΑΦΜ", "ΑΜΚΑ"]

        emp_df = load_data(EMPLOYEES_FILE, emp_cols)


        if emp_df.empty or not all(col in emp_df.columns for col in emp_cols):

            emp_df = pd.DataFrame(columns=emp_cols)

        else:

            emp_df['ΑΦΜ'] = emp_df['ΑΦΜ'].astype(str).str.strip()

            emp_df['ΑΜΚΑ'] = emp_df['ΑΜΚΑ'].astype(str).str.strip()


        # 1. Φόρμα Προσθήκης Υπαλλήλου

        with st.sidebar.expander("➕ Προσθήκη Νέου Υπάλληλου"):

            with st.form("add_employee_form"):

                new_name = st.text_input("Ονοματεπώνυμο").strip()

                new_afm = st.text_input("ΑΦΜ Υπαλλήλου (9 ψηφία)", max_chars=9).strip()

                new_amka = st.text_input("ΑΜΚΑ Υπαλλήλου (11 ψηφία)", max_chars=11).strip()


                if st.form_submit_button("💾 Προσθήκη"):

                    if new_name and new_afm and new_amka:

                        generated_id = f"EMP_{new_amka}"


                        if not emp_df.empty and new_afm in emp_df['ΑΦΜ'].values:

                            st.error(f"⚠️ Το ΑΦΜ **{new_afm}** ανήκει ήδη σε υπάλληλο!")

                        elif not emp_df.empty and new_amka in emp_df['ΑΜΚΑ'].values:

                            st.error(f"⚠️ Το ΑΜΚΑ **{new_amka}** υπάρχει ήδη!")

                        else:

                            new_emp = pd.DataFrame([{"ID": generated_id, "Ονοματεπώνυμο": new_name, "ΑΦΜ": new_afm, "ΑΜΚΑ": new_amka}])

                            emp_df = pd.concat([emp_df, new_emp], ignore_index=True)

                            save_to_csv(emp_df, EMPLOYEES_FILE)

                            st.success("🎉 Ο υπάλληλος προστέθηκε!")

                            st.rerun()

                    else:

                        st.error("❌ Συμπληρώστε όλα τα πεδία!")


        # 2. Φόρμα Διαγραφής Υπαλλήλου

        if not emp_df.empty:

            with st.sidebar.expander("🗑️ Διαγραφή Υπαλλήλου"):

                delete_options = {f"{row['Ονοματεπώνυμο']} (ΑΜΚΑ: {row['ΑΜΚΑ']})": row['ID'] for _, row in emp_df.iterrows() if pd.notna(row['ΑΜΚΑ'])}

                if delete_options:

                    selected_del_label = st.selectbox("Επιλέξτε υπάλληλο για διαγραφή:", list(delete_options.keys()))

                    target_del_id = delete_options[selected_del_label]


                    if st.button("Οριστική Διαγραφή", type="primary", key="del_emp_btn"):

                        emp_df = emp_df[emp_df['ID'].astype(str) != str(target_del_id)]

                        save_to_csv(emp_df, EMPLOYEES_FILE)

                        st.success("Ο υπάλληλος διαγράφηκε!")

                        st.rerun()


        st.sidebar.markdown("---")

        # 3. Επιλογή Υπαλλήλου & Περιόδου

        if emp_df.empty:

            st.warning("⚠️ Δεν υπάρχουν καταχωρημένοι υπάλληλοι στο σύστημα.")

        else:

            emp_options = {}

            for _, row in emp_df.iterrows():

                if pd.notna(row["Ονοματεπώνυμο"]) and pd.notna(row["ID"]):

                    display_label = f"{row['Ονοματεπώνυμο']} (ΑΜΚΑ: {row['ΑΜΚΑ']})"

                    emp_options[display_label] = {

                        "ID": str(row["ID"]),

                        "Ονοματεπώνυμο": str(row["Ονοματεπώνυμο"]),

                        "ΑΦΜ": str(row["ΑΦΜ"]),

                        "ΑΜΚΑ": str(row["ΑΜΚΑ"])

                    }


            if emp_options:

                selected_emp_label = st.sidebar.selectbox("Επιλέξτε Υπάλληλο για Έλεγχο:", list(emp_options.keys()))

                emp_data = emp_options[selected_emp_label]


                months = ["Ιανουάριος", "Φεβρουάριος", "Μάρτιος", "Απρίλιος", "Μάιος", "Ιούνιος", "Ιούλιος", "Αύγουστος", "Σεπτέμβριος", "Οκτώβριος", "Νοέμβριος", "Δεκέμβριος"]

                selected_month = st.sidebar.selectbox("Μήνας:", months, index=4)

                selected_year = st.sidebar.number_input("Έτος:", min_value=2020, max_value=2030, value=2026)


                period = f"{selected_month} {selected_year}"

                fin_key = f"{emp_data['ID']}_{selected_month}_{selected_year}"


                st.sidebar.info(f"📋 **Στοιχεία Τρέχοντος Ελέγχου**")

                st.sidebar.text(f"🏢 Εταιρεία: {selected_project_name}")

                st.sidebar.text(f"👤 ΑΦΜ Υπαλλ.: {emp_data['ΑΦΜ']}")

                st.sidebar.text(f"🆔 ΑΜΚΑ Υπαλλ.: {emp_data['ΑΜΚΑ']}")

                st.sidebar.text(f"📅 Περίοδος: {period}")


                render_stage_3(fin_key, emp_data, selected_month, selected_year, period, selected_project_afm)

            else:

                st.warning("⚠️ Τα δεδομένα των υπαλλήλων δεν είναι έγκυρα.")
