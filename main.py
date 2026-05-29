```python
# ========================= IMPORTS =========================
import streamlit as st
import pandas as pd
import os
import json

from google import genai
from google.genai import types
from pydantic import BaseModel, Field


# ========================= PAGE CONFIG =========================
st.set_page_config(
    page_title="Payroll Verifier Pro",
    page_icon="🛡️",
    layout="wide"
)


# ========================= FILES =========================
PROJECTS_FILE = 'data_projects.csv'
CHECKLIST_FILE = 'checklist_results.csv'
EMPLOYEES_FILE = 'data_employees.csv'
FINANCIALS_FILE = 'payroll_financials.csv'
PAYROLL_CHECKS_FILE = 'payroll_checks.csv'


# ========================= HELPERS =========================
def load_data(filename, columns):

    if not os.path.isfile(filename) or os.path.getsize(filename) == 0:
        return pd.DataFrame(columns=columns)

    try:
        return pd.read_csv(filename)

    except Exception:
        return pd.DataFrame(columns=columns)


def save_to_csv(df, filename):
    df.to_csv(filename, index=False, encoding='utf-8-sig')


# ========================= AI SCHEMA =========================
class PayrollFinancials(BaseModel):

    ΙΚΑ_Εργ: float = Field(description="Οι κρατήσεις ή εισφορές του ασφαλισμένου/εργαζομένου για το κύριο ταμείο (ΙΚΑ/ΕΦΚΑ). Μην το μπερδεύεις με τις εργοδοτικές.")
    ΙΚΑ_Εργοδ: float = Field(description="Οι εισφορές του εργοδότη για το κύριο ταμείο (ΙΚΑ/ΕΦΚΑ).")
    ΤΕΚΑ_Εργ: float = Field(description="Οι κρατήσεις του εργαζομένου για το ΤΕΚΑ (επικουρικό). Αν δεν υπάρχει, βάλε 0.0.")
    ΤΕΚΑ_Εργοδ: float = Field(description="Οι εισφορές του εργοδότη για το ΤΕΚΑ. Αν δεν υπάρχει, βάλε 0.0.")
    Σύνολο_Εισφ: float = Field(description="Το άθροισμα όλων των ασφαλιστικών κρατήσεων/εισφορών εργαζομένου και εργοδότη.")
    ΦΜΥ: float = Field(description="Ο Φόρος Μισθωτών Υπηρεσιών (Φ.Μ.Υ.). Αν δεν υπάρχει, βάλε 0.0.")
    Καθαρές: float = Field(description="Το τελικό πληρωτέο ποσό στον εργαζόμενο (Καθαρές Αποδοχές).")
    Τακτικές_Αποδ: float = Field(description="Οι μικτές τακτικές αποδοχές / βασικός μισθός.")
    Υπερωρίες: float = Field(description="Ποσό για υπερωρίες ή υπερεργασία, αν δεν υπάρχει βάλε 0.0.")
    Δώρο_Πάσχα: float = Field(description="Ποσό για Δώρο Πάσχα, αν δεν υπάρχει βάλε 0.0.")
    Δώρο_Χριστουγέννων: float = Field(description="Ποσό για Δώρο Χριστουγέννων, αν δεν υπάρχει βάλε 0.0.")
    Επίδομα_Άδειας: float = Field(description="Ποσό για Επίδομα Άδειας, αν δεν υπάρχει βάλε 0.0.")
    Λοιπά_Αποδ: float = Field(description="Λοιπά επιδόματα, bonus ή αναδρομικά, αν δεν υπάρχει βάλε 0.0.")
    Σύνολο_Αποδ: float = Field(description="Οι συνολικές μικτές αποδοχές (άθροισμα όλων των επιμέρους αποδοχών).")
    ΟΠΣΚΕ: float = Field(description="Αιτούμενο ποσό ΟΠΣΚΕ. Αν δεν προκύπτει αυτόματα, βάλε 0.0.")


# ========================= AI OCR =========================
def extract_financials_with_ai_stage3(uploaded_file, emp_name):

    API_KEY = st.secrets.get("GEMINI_API_KEY")

    if not API_KEY:
        st.error("❌ Δεν βρέθηκε GEMINI_API_KEY")
        return {}

    try:

        client = genai.Client(api_key=API_KEY)

        uploaded_file.seek(0)

        file_bytes = uploaded_file.read()

        file_part = types.Part.from_bytes(
            data=file_bytes,
            mime_type=uploaded_file.type
        )

        prompt = f"""
        Είσαι Έλληνας λογιστής μισθοδοσίας.

        Βρες στοιχεία ΜΟΝΟ για τον υπάλληλο:
        "{emp_name}"

        ΚΑΝΟΝΕΣ:
        1. Αν ΔΕΝ βρεις το όνομα, βάλε όλα 0.
        2. Πάρε μόνο ατομικά ποσά.
        3. Αγνόησε συνολικά ποσά εταιρείας.
        4. Βρες καθαρές, ΦΜΥ, ΙΚΑ, ΤΕΚΑ, δώρα κτλ.
        """

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[file_part, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=PayrollFinancials,
                temperature=0.0
            )
        )

        return json.loads(response.text)

    except Exception as e:

        st.error(f"❌ AI Error: {e}")

        return {}


# ========================= FINANCIAL FIELDS =========================
def render_financial_fields(tab_key, default_values, ocr_data):

    def get_val(field):

        return float(
            ocr_data.get(
                field,
                default_values.get(field, 0.0)
            )
        )

    c1, c2 = st.columns(2)

    v_ika_erg = c1.number_input(
        "ΙΚΑ Εργαζομένου",
        value=get_val("ΙΚΑ_Εργ"),
        format="%.2f",
        key=f"ika_erg_{tab_key}"
    )

    v_ika_ergo = c2.number_input(
        "ΙΚΑ Εργοδότη",
        value=get_val("ΙΚΑ_Εργοδ"),
        format="%.2f",
        key=f"ika_ergo_{tab_key}"
    )

    c3, c4 = st.columns(2)

    v_teka_erg = c3.number_input(
        "ΤΕΚΑ Εργαζομένου",
        value=get_val("ΤΕΚΑ_Εργ"),
        format="%.2f",
        key=f"teka_erg_{tab_key}"
    )

    v_teka_ergo = c4.number_input(
        "ΤΕΚΑ Εργοδότη",
        value=get_val("ΤΕΚΑ_Εργοδ"),
        format="%.2f",
        key=f"teka_ergo_{tab_key}"
    )

    c5, c6, c7 = st.columns(3)

    v_sum_eisf = c5.number_input(
        "Σύνολο Εισφορών",
        value=get_val("Σύνολο_Εισφ"),
        format="%.2f",
        key=f"sum_eisf_{tab_key}"
    )

    v_fmy = c6.number_input(
        "ΦΜΥ",
        value=get_val("ΦΜΥ"),
        format="%.2f",
        key=f"fmy_{tab_key}"
    )

    v_net = c7.number_input(
        "Καθαρές Αποδοχές",
        value=get_val("Καθαρές"),
        format="%.2f",
        key=f"net_{tab_key}"
    )

    st.markdown("---")

    v_opske = st.number_input(
        "Αιτούμενο ΟΠΣΚΕ",
        value=get_val("ΟΠΣΚΕ"),
        format="%.2f",
        key=f"opske_{tab_key}"
    )

    return (
        v_ika_erg,
        v_ika_ergo,
        v_teka_erg,
        v_teka_ergo,
        v_sum_eisf,
        v_fmy,
        v_net,
        v_opske
    )


# ========================= STAGE 3 =========================
def render_stage_3(
    fin_key,
    emp_data,
    selected_month,
    selected_year,
    period,
    selected_afm
):

    st.subheader("💰 Οικονομικά Στοιχεία")

    uploaded_file = st.file_uploader(
        "📂 Μεταφόρτωση Μισθοδοτικής",
        type=['pdf', 'png', 'jpg', 'jpeg'],
        key=f"upload_{fin_key}"
    )

    fin_cols = [
        "ID_Κλειδί",
        "ΙΚΑ_Εργ",
        "ΙΚΑ_Εργοδ",
        "ΤΕΚΑ_Εργ",
        "ΤΕΚΑ_Εργοδ",
        "Σύνολο_Εισφ",
        "ΦΜΥ",
        "Καθαρές",
        "Τακτικές_Αποδ",
        "Υπερωρίες",
        "Δώρο_Πάσχα",
        "Δώρο_Χριστουγέννων",
        "Επίδομα_Άδειας",
        "Λοιπά_Αποδ",
        "Σύνολο_Αποδ",
        "ΟΠΣΚΕ"
    ]

    fin_df = load_data(FINANCIALS_FILE, fin_cols)

    for col in fin_cols:

        if col not in fin_df.columns:
            fin_df[col] = 0.0

    ext_fin = fin_df[fin_df['ID_Κλειδί'] == fin_key]

    default_values = {}

    for col in fin_cols:

        if col == "ID_Κλειδί":
            continue

        if not ext_fin.empty and col in ext_fin.columns:
            default_values[col] = float(ext_fin[col].iloc[0])
        else:
            default_values[col] = 0.0

    # ================= OCR =================
    ocr_data = {}

    if uploaded_file is not None:

        file_fingerprint = f"{uploaded_file.name}_{uploaded_file.size}"

        trigger_key = f"ocr_data_{fin_key}_{file_fingerprint}"

        if st.button(
            "🤖 AI Ανάλυση",
            type="primary",
            use_container_width=True
        ):

            with st.spinner("⏳ Ανάλυση αρχείου..."):

                ocr_data = extract_financials_with_ai_stage3(
                    uploaded_file,
                    emp_data['Ονοματεπώνυμο']
                )

                if ocr_data:

                    st.session_state[trigger_key] = ocr_data

                    st.rerun()

        if trigger_key in st.session_state:
            ocr_data = st.session_state[trigger_key]

    # ================= TABS =================
    tabs = st.tabs([
        "Τακτικές αποδοχές",
        "Δώρο Πάσχα",
        "Δώρο Χριστουγέννων",
        "Επίδομα Αδείας"
    ])

    with tabs[0]:

        v_tak_ap = st.number_input(
            "Βασικός Μισθός",
            value=float(
                ocr_data.get(
                    "Τακτικές_Αποδ",
                    default_values["Τακτικές_Αποδ"]
                )
            ),
            format="%.2f"
        )

        (
            v_ika_erg,
            v_ika_ergo,
            v_teka_erg,
            v_teka_ergo,
            v_sum_eisf,
            v_fmy,
            v_net,
            v_opske

        ) = render_financial_fields(
            "tab0",
            default_values,
            ocr_data
        )

    with tabs[1]:

        v_doro_pasxa = st.number_input(
            "Δώρο Πάσχα",
            value=float(
                ocr_data.get(
                    "Δώρο_Πάσχα",
                    default_values["Δώρο_Πάσχα"]
                )
            ),
            format="%.2f"
        )

    with tabs[2]:

        v_doro_xrist = st.number_input(
            "Δώρο Χριστουγέννων",
            value=float(
                ocr_data.get(
                    "Δώρο_Χριστουγέννων",
                    default_values["Δώρο_Χριστουγέννων"]
                )
            ),
            format="%.2f"
        )

    with tabs[3]:

        v_epidoma_ad = st.number_input(
            "Επίδομα Αδείας",
            value=float(
                ocr_data.get(
                    "Επίδομα_Άδειας",
                    default_values["Επίδομα_Άδειας"]
                )
            ),
            format="%.2f"
        )

    # ================= EXTRA =================
    v_yp_ap = float(
        ocr_data.get(
            "Υπερωρίες",
            default_values["Υπερωρίες"]
        )
    )

    v_loip_ap = float(
        ocr_data.get(
            "Λοιπά_Αποδ",
            default_values["Λοιπά_Αποδ"]
        )
    )

    v_total_ap = (
        v_tak_ap +
        v_doro_pasxa +
        v_doro_xrist +
        v_epidoma_ad +
        v_yp_ap +
        v_loip_ap
    )

    st.info(f"Σύνολο Αποδοχών: € {v_total_ap:,.2f}")

    # ================= SAVE =================
    if st.button(
        "💾 Αποθήκευση",
        use_container_width=True
    ):

        fin_row = {

            "ID_Κλειδί": fin_key,

            "ΙΚΑ_Εργ": v_ika_erg,
            "ΙΚΑ_Εργοδ": v_ika_ergo,

            "ΤΕΚΑ_Εργ": v_teka_erg,
            "ΤΕΚΑ_Εργοδ": v_teka_ergo,

            "Σύνολο_Εισφ": v_sum_eisf,

            "ΦΜΥ": v_fmy,

            "Καθαρές": v_net,

            "Τακτικές_Αποδ": v_tak_ap,

            "Υπερωρίες": v_yp_ap,

            "Δώρο_Πάσχα": v_doro_pasxa,

            "Δώρο_Χριστουγέννων": v_doro_xrist,

            "Επίδομα_Άδειας": v_epidoma_ad,

            "Λοιπά_Αποδ": v_loip_ap,

            "Σύνολο_Αποδ": v_total_ap,

            "ΟΠΣΚΕ": v_opske
        }

        fin_df = fin_df[
            fin_df['ID_Κλειδί'] != fin_key
        ]

        fin_df = pd.concat(
            [
                fin_df,
                pd.DataFrame([fin_row])
            ],
            ignore_index=True
        )

        save_to_csv(fin_df, FINANCIALS_FILE)

        st.success("✅ Αποθηκεύτηκε!")

        st.rerun()


# ========================= MAIN APP =========================
st.title("🛡️ Payroll Verifier Pro")

projects_df = load_data(
    PROJECTS_FILE,
    ["Επωνυμία", "ΑΦΜ"]
)

if projects_df.empty:

    st.warning("⚠️ Δεν υπάρχουν επιχειρήσεις.")

else:

    selected_name = st.selectbox(
        "Επιχείρηση",
        projects_df['Επωνυμία']
    )

    selected_afm = str(
        projects_df[
            projects_df['Επωνυμία'] == selected_name
        ]['ΑΦΜ'].iloc[0]
    )

    emp_cols = [
        "ID",
        "Ονοματεπώνυμο",
        "ΑΦΜ",
        "ΑΜΚΑ"
    ]

    emp_df = load_data(
        EMPLOYEES_FILE,
        emp_cols
    )

    if emp_df.empty:

        st.warning("⚠️ Δεν υπάρχουν υπάλληλοι.")

    else:

        emp_options = {}

        for _, row in emp_df.iterrows():

            label = f"{row['Ονοματεπώνυμο']} ({row['ΑΜΚΑ']})"

            emp_options[label] = {
                "ID": row["ID"],
                "Ονοματεπώνυμο": row["Ονοματεπώνυμο"],
                "ΑΦΜ": row["ΑΦΜ"],
                "ΑΜΚΑ": row["ΑΜΚΑ"]
            }

        selected_emp = st.selectbox(
            "Υπάλληλος",
            list(emp_options.keys())
        )

        emp_data = emp_options[selected_emp]

        months = [
            "Ιανουάριος",
            "Φεβρουάριος",
            "Μάρτιος",
            "Απρίλιος",
            "Μάιος",
            "Ιούνιος",
            "Ιούλιος",
            "Αύγουστος",
            "Σεπτέμβριος",
            "Οκτώβριος",
            "Νοέμβριος",
            "Δεκέμβριος"
        ]

        selected_month = st.selectbox(
            "Μήνας",
            months
        )

        selected_year = st.number_input(
            "Έτος",
            value=2026,
            min_value=2020,
            max_value=2035
        )

        period = f"{selected_month} {selected_year}"

        fin_key = f"{emp_data['ID']}_{selected_month}_{selected_year}"

        render_stage_3(
            fin_key,
            emp_data,
            selected_month,
            selected_year,
            period,
            selected_afm
        )
```
