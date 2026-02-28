# Entry point for Streamlit Cloud
# (Code copied from your latest budget_app.py)

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# --- SETTINGS & THEME ---
st.set_page_config(page_title="Fintraa Budget Tracker", layout="wide")

# --- THEME TOGGLE & MODERN XERO-INSPIRED CSS ---
with open("assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- MOCK DATA LOADER (Connects to your sheet logic) ---
@st.cache_data
def load_data():
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
    st.markdown("""
    <div class='header-menu' style='display:flex;justify-content:center;align-items:center;margin-bottom:32px;'>
        <a href='#' id='dashboard-link' style='margin:0 32px;font-weight:600;font-size:20px;color:#1a222b;text-decoration:none;'>Dashboard</a>
        <a href='#' id='transactions-link' style='margin:0 32px;font-weight:600;font-size:20px;color:#1a222b;text-decoration:none;'>Transactions</a>
        <a href='#' id='archives-link' style='margin:0 32px;font-weight:600;font-size:20px;color:#1a222b;text-decoration:none;'>Archives</a>
    </div>
    <script>
    document.getElementById('dashboard-link').onclick = function() { window.parent.postMessage({tab: 'Dashboard'}, '*'); return false; };
    document.getElementById('transactions-link').onclick = function() { window.parent.postMessage({tab: 'Transactions'}, '*'); return false; };
    document.getElementById('archives-link').onclick = function() { window.parent.postMessage({tab: 'Archives'}, '*'); return false; };
    </script>
    """, unsafe_allow_html=True)
    if 'tab' not in st.session_state:
        st.session_state.tab = 'Dashboard'
    page = st.session_state.tab
else:
    # Mobile sidebar menu
    st.sidebar.markdown("""
    <div class='mobile-sidebar-menu' style='background:#f4f7fa;border-radius:12px;padding:16px 0;margin-bottom:24px;'>
        <a href='#' id='sidebar-dashboard-link' style='color:#00b2ff;font-weight:700;font-size:18px;text-decoration:none;display:block;padding:12px 0;'>🏠 Dashboard</a>
        <a href='#' id='sidebar-transactions-link' style='color:#00b2ff;font-weight:700;font-size:18px;text-decoration:none;display:block;padding:12px 0;'>📄 Transactions</a>
        <a href='#' id='sidebar-archives-link' style='color:#00b2ff;font-weight:700;font-size:18px;text-decoration:none;display:block;padding:12px 0;'>🗄️ Archives</a>
    </div>
    <script>
    document.getElementById('sidebar-dashboard-link').onclick = function() { window.parent.postMessage({tab: 'Dashboard'}, '*'); return false; };
    document.getElementById('sidebar-transactions-link').onclick = function() { window.parent.postMessage({tab: 'Transactions'}, '*'); return false; };
    document.getElementById('sidebar-archives-link').onclick = function() { window.parent.postMessage({tab: 'Archives'}, '*'); return false; };
    </script>
    """, unsafe_allow_html=True)
    if 'tab' not in st.session_state:
        st.session_state.tab = 'Dashboard'
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
