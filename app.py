# Entry point for Streamlit Cloud
# (Code copied from your latest budget_app.py)

import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# --- SETTINGS & THEME ---
# --- GOOGLE SHEETS CONFIG ---
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
CREDS = Credentials.from_service_account_file(
    '.streamlit/secrets.json', scopes=SCOPE
)
gc = gspread.authorize(CREDS)

MAIN_EMAIL = "fluxiondm2024@gmail.com"

def get_or_create_folder(folder_name):
    drive = gc.auth.service
    from googleapiclient.discovery import build
    drive_service = build('drive', 'v3', credentials=CREDS)
    # Search for folder
    results = drive_service.files().list(q=f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}'",
                                        spaces='drive', fields='files(id, name)').execute()
    items = results.get('files', [])
    if items:
        folder_id = items[0]['id']
    else:
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = drive_service.files().create(body=file_metadata, fields='id').execute()
        folder_id = folder.get('id')
    return folder_id

def get_monthly_sheet(month_name):
    folder_id = get_or_create_folder('D-Budgets')
    # Try to open, else create a new sheet for the month in the folder
    try:
        sh = gc.open(f"Budget_{month_name}")
    except gspread.SpreadsheetNotFound:
        sh = gc.create(f"Budget_{month_name}")
        # Move sheet to folder
        drive = gc.auth.service
        from googleapiclient.discovery import build
        drive_service = build('drive', 'v3', credentials=CREDS)
        file_id = sh.id
        drive_service.files().update(fileId=file_id, addParents=folder_id, removeParents=None, fields='id, parents').execute()
        # Share with main email
        sh.share(MAIN_EMAIL, perm_type='user', role='writer')
    return sh

def save_transaction_to_sheet(month_name, transaction_df):
    sh = get_monthly_sheet(month_name)
    worksheet = sh.sheet1
    worksheet.clear()
    worksheet.update([transaction_df.columns.values.tolist()] + transaction_df.values.tolist())
st.set_page_config(page_title="Fintraa Budget Tracker", layout="wide")

# --- THEME TOGGLE & MODERN XERO-INSPIRED CSS ---
with open("assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- MOCK DATA LOADER (Connects to your sheet logic) ---
@st.cache_data
def load_data():
    # Try to load from Google Sheets for the current month
    month_name = pd.Timestamp.today().strftime('%B %Y')
    try:
        sh = get_monthly_sheet(month_name)
        worksheet = sh.sheet1
        records = worksheet.get_all_records()
        if records:
            df = pd.DataFrame(records)
            df['Date'] = pd.to_datetime(df['Date'])
            return df
    except Exception:
        pass
    # Fallback to mock data if sheet not found or empty
    data = {
        'Date': pd.to_datetime(['2024-03-01', '2024-03-02', '2024-03-05', '2024-03-10']),
        'Description': ['Salary', 'Rent', 'Groceries', 'Internet'],
        'Amount': [25000.00, 8500.00, 1200.00, 600.00],
        'Category': ['Income', 'Housing', 'Food', 'Utilities'],
        'Type': ['Income', 'Expense', 'Expense', 'Pending'],
        'Month': ['March 2024', 'March 2024', 'March 2024', 'March 2024']
    }
    return pd.DataFrame(data)

if 'df' not in st.session_state:
    st.session_state.df = load_data()
df = st.session_state.df


# --- Sidebar Navigation with Custom Button and Icon ---

# --- Responsive Header Menu (Desktop) and Mobile Menu ---
import streamlit.components.v1 as components
import sys

def is_mobile():
    return st.session_state.get('is_mobile', False)

if 'is_mobile' not in st.session_state:
    st.session_state.is_mobile = False
    # Use JS to detect mobile and set session state
    components.html("""
    <script>
    const isMobile = window.innerWidth < 600;
    window.parent.postMessage({isMobile}, '*');
    </script>
    """, height=0)

if not is_mobile():
    # Desktop header menu
    col1, col2, col3 = st.columns([1,1,1])
    if 'tab' not in st.session_state:
        st.session_state.tab = 'Dashboard'
    with col1:
        if st.button('🏠 Dashboard'):
            st.session_state.tab = 'Dashboard'
    with col2:
        if st.button('📄 Transactions'):
            st.session_state.tab = 'Transactions'
    with col3:
        if st.button('🗄️ Archives'):
            st.session_state.tab = 'Archives'
    page = st.session_state.tab
else:
    # Mobile sidebar menu
    if 'tab' not in st.session_state:
        st.session_state.tab = 'Dashboard'
    st.sidebar.markdown("<div class='mobile-sidebar-menu' style='background:#f4f7fa;border-radius:12px;padding:16px 0;margin-bottom:24px;'>", unsafe_allow_html=True)
    if st.sidebar.button('🏠 Dashboard'):
        st.session_state.tab = 'Dashboard'
    if st.sidebar.button('📄 Transactions'):
        st.session_state.tab = 'Transactions'
    if st.sidebar.button('🗄️ Archives'):
        st.session_state.tab = 'Archives'
    st.sidebar.markdown("</div>", unsafe_allow_html=True)
    page = st.session_state.tab

if page == "Dashboard":
    st.title("Monthly Overview")
    if 'show_form' not in st.session_state:
        st.session_state.show_form = False
    if st.button("➕ Add Transaction"):
        st.session_state.show_form = True
    if st.session_state.show_form:
        with st.expander("New Transaction Details", expanded=True):
            with st.form("add_form"):
                t_date = st.date_input("Date")
                t_desc = st.text_input("Description")
                t_amt = st.number_input("Amount (R)", min_value=0.0)
                existing_categories = df['Category'].unique().tolist()
                new_category_option = "Add new category..."
                category_options = existing_categories + [new_category_option]
                t_cat_select = st.selectbox("Category", category_options)
                t_cat = t_cat_select
                if t_cat_select == new_category_option:
                    t_cat = st.text_input("Enter new category name")
                t_type = st.selectbox("Status", ["Income", "Expense", "Pending"])
                col_save, col_cancel = st.columns([1,1])
                save_clicked = col_save.form_submit_button("Save Transaction")
                cancel_clicked = col_cancel.form_submit_button("Cancel")
                if save_clicked:
                    if t_cat and t_cat != new_category_option:
                        new_transaction = pd.DataFrame([{
                            'Date': pd.to_datetime(t_date),
                            'Description': t_desc,
                            'Amount': t_amt,
                            'Category': t_cat,
                            'Type': t_type,
                            'Month': pd.to_datetime(t_date).strftime('%B %Y')
                        }])
                        st.session_state.df = pd.concat([st.session_state.df, new_transaction], ignore_index=True)
                        # Save to Google Sheet for the month
                        save_transaction_to_sheet(pd.to_datetime(t_date).strftime('%B %Y'), st.session_state.df)
                        st.success("Transaction Saved!")
                        st.session_state.show_form = False
                        st.rerun()
                    else:
                        st.error("Please select or enter a category.")
                if cancel_clicked:
                    st.session_state.show_form = False
                    st.rerun()
    total_inc = df[df['Type'] == 'Income']['Amount'].sum()
    total_exp = df[df['Type'] == 'Expense']['Amount'].sum()
    pending = df[df['Type'] == 'Pending']['Amount'].sum()
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Income", f"R {total_inc:,.2f}")
    m2.metric("Total Expenses", f"R {total_exp:,.2f}", delta_color="inverse")
    m3.metric("Pending (Debit Orders)", f"R {pending:,.2f}")
    c1, c2 = st.columns(2)
    with c1:
        fig_pie = px.pie(df[df['Type'] != 'Income'], values='Amount', names='Category', title="Expense Breakdown")
        st.plotly_chart(fig_pie, width='stretch')
    with c2:
        fig_bar = px.bar(df, x='Date', y='Amount', color='Type', title="Daily Cash Flow")
        st.plotly_chart(fig_bar, width='stretch')
    # Category breakdown vertical bar chart
    st.header("Category Breakdown")
    cat_df = df[df['Type'] != 'Income'].groupby('Category', as_index=False)['Amount'].sum()
    fig_cat_breakdown = px.bar(cat_df, x='Category', y='Amount', title="Expenses by Category", orientation='v', color='Category', text='Amount')
    st.plotly_chart(fig_cat_breakdown, width='stretch')
elif page == "Transactions":
    st.title("Transaction History")
    filter_option = st.selectbox(
        "View",
        ["All", "Income Only", "Expenses Only", "Current Month", "Month to Date"],
        index=0
    )
    show_date_picker = filter_option in ["All", "Income Only", "Expenses Only"]
    if show_date_picker:
        date_range = st.date_input("Select Date Range", [df['Date'].min(), df['Date'].max()], key="transactions_date_picker")
    filtered_df = df.copy()
    today = pd.Timestamp.today()
    current_month = today.strftime('%B %Y')
    if filter_option == "Current Month":
        filtered_df = filtered_df[filtered_df['Month'] == current_month]
    elif filter_option == "Month to Date":
        filtered_df = filtered_df[(filtered_df['Date'] >= today.replace(day=1)) & (filtered_df['Date'] <= today)]
    else:
        if show_date_picker and len(date_range) == 2:
            start_date = pd.to_datetime(date_range[0])
            end_date = pd.to_datetime(date_range[1])
            filtered_df = filtered_df[(filtered_df['Date'] >= start_date) & (filtered_df['Date'] <= end_date)]
        if filter_option == "Income Only":
            filtered_df = filtered_df[filtered_df['Type'] == 'Income']
        elif filter_option == "Expenses Only":
            filtered_df = filtered_df[filtered_df['Type'].isin(['Expense', 'Pending'])]
    # Format date as '28-Feb-2026'
    filtered_df['Date'] = filtered_df['Date'].dt.strftime('%d-%b-%Y')
    st.dataframe(filtered_df.style.format({"Amount": "R {:,.2f}"}), width='stretch')
    st.header("Edit Transactions")
    edited_df = st.data_editor(df, num_rows="dynamic")
    if st.button("Save Changes"):
        st.session_state.df = edited_df
        st.success("Changes saved!")
        st.rerun()
elif page == "Archives":
    st.title("Budget Archives")
    selected_month = st.selectbox("Select Previous Month", df['Month'].unique())
    archive_data = df[df['Month'] == selected_month].copy()
    st.write(f"Showing data for: {selected_month}")
    # Format date as '28-Feb-2026'
    archive_data['Date'] = archive_data['Date'].dt.strftime('%d-%b-%Y')
    st.table(archive_data)
    @st.cache_data
    def convert_df(df_to_save):
        return df_to_save.to_csv().encode('utf-8')
    csv = convert_df(archive_data)
    st.download_button(
        label="📥 Export Month to Excel (CSV)",
        data=csv,
        file_name=f'Budget_{selected_month}.csv',
        mime='text/csv',
    )
