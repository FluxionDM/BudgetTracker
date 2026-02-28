import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# --- SETTINGS & THEME ---
st.set_page_config(page_title="ZAR Budget Tracker", layout="wide")

# --- THEME TOGGLE & MODERN XERO-INSPIRED CSS ---
theme = st.sidebar.selectbox("Theme", ["Light", "Dark"], index=0)
if theme == "Light":
    st.markdown("""
        <style>
        body, .main { background-color: #f4f7fa; color: #222; }
        .stMetric { background: #fff; padding: 18px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.07); }
        .stButton>button, .stDownloadButton>button {
            border-radius: 8px; background: linear-gradient(90deg,#2ec4b6 0,#00b2ff 100%); color: #fff; font-weight: 600; border: none; box-shadow: 0 1px 4px rgba(0,0,0,0.08); transition: background 0.2s;
        }
        .stButton>button:hover, .stDownloadButton>button:hover { background: linear-gradient(90deg,#00b2ff 0,#2ec4b6 100%); }
        .stExpander { background: #fff; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
        .stDataFrame, .stTable { background: #fff; border-radius: 10px; }
        @media (max-width: 600px) {
            .stMetric, .stExpander, .stDataFrame, .stTable { padding: 8px; font-size: 15px; }
            .stButton>button, .stDownloadButton>button { font-size: 15px; }
        }
        </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
        body, .main { background: #1a222b; color: #eaf6fb; }
        .stMetric { background: #232e3c; color: #eaf6fb; padding: 18px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.12); }
        .stButton>button, .stDownloadButton>button {
            border-radius: 8px; background: linear-gradient(90deg,#00b2ff 0,#2ec4b6 100%); color: #fff; font-weight: 600; border: none; box-shadow: 0 1px 4px rgba(0,0,0,0.12); transition: background 0.2s;
        }
        .stButton>button:hover, .stDownloadButton>button:hover { background: linear-gradient(90deg,#2ec4b6 0,#00b2ff 100%); }
        .stExpander { background: #232e3c; color: #eaf6fb; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.12); }
        .stDataFrame, .stTable { background: #232e3c; color: #eaf6fb; border-radius: 10px; }
        @media (max-width: 600px) {
            .stMetric, .stExpander, .stDataFrame, .stTable { padding: 8px; font-size: 15px; }
            .stButton>button, .stDownloadButton>button { font-size: 15px; }
        }
        </style>
    """, unsafe_allow_html=True)

# --- MOCK DATA LOADER (Connects to your sheet logic) ---
@st.cache_data
def load_data():
    # In a real app, use: pd.read_csv("your_sheet_data.csv")
    data = {
        'Date': pd.to_datetime(['2024-03-01', '2024-03-02', '2024-03-05', '2024-03-10']),
        'Description': ['Salary', 'Rent', 'Groceries', 'Internet'],
        'Amount': [25000.00, 8500.00, 1200.00, 600.00],
        'Category': ['Income', 'Housing', 'Food', 'Utilities'],
        'Type': ['Income', 'Expense', 'Expense', 'Pending'],
        'Month': ['March 2024', 'March 2024', 'March 2024', 'March 2024']
    }
    return pd.DataFrame(data)

# --- SESSION STATE INITIALIZATION ---
if 'df' not in st.session_state:
    st.session_state.df = load_data()

df = st.session_state.df

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("💰 Budget Menu")
page = st.sidebar.radio("Go to", ["Home / Dashboard", "Transactions", "Archives"])

# --- PAGE 1: HOME / DASHBOARD ---
if page == "Home / Dashboard":
    st.title("Monthly Overview")
    
    # Add Transaction Pop-up (Streamlit Modal style)
    # Transaction form visibility state
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

    # Metrics
    total_inc = df[df['Type'] == 'Income']['Amount'].sum()
    total_exp = df[df['Type'] == 'Expense']['Amount'].sum()
    pending = df[df['Type'] == 'Pending']['Amount'].sum()
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Income", f"R {total_inc:,.2f}")
    m2.metric("Total Expenses", f"R {total_exp:,.2f}", delta_color="inverse")
    m3.metric("Pending (Debit Orders)", f"R {pending:,.2f}")

    # Graphs
    c1, c2 = st.columns(2)
    with c1:
        fig_pie = px.pie(df[df['Type'] != 'Income'], values='Amount', names='Category', title="Expense Breakdown")
        st.plotly_chart(fig_pie, width='stretch')
    with c2:
        fig_bar = px.bar(df, x='Date', y='Amount', color='Type', title="Daily Cash Flow")
        st.plotly_chart(fig_bar, width='stretch')

    st.header("Transactions by Category")
    for category in sorted(df['Category'].unique()):
        with st.expander(f"**{category}**"):
            category_df = df[df['Category'] == category]
            st.dataframe(category_df.style.format({"Amount": "R {:,.2f}"}), width='stretch')
            # Add category graph
            if not category_df.empty:
                fig_cat = px.bar(category_df, x='Date', y='Amount', color='Type', title=f"{category} Transactions")
                st.plotly_chart(fig_cat, width='stretch')

# --- PAGE 2: TRANSACTIONS ---
elif page == "Transactions":
    st.title("Transaction History")
    # Unified filter dropdown
    filter_option = st.selectbox(
        "View",
        ["All", "Income Only", "Expenses Only", "Current Month", "Month to Date"],
        index=0
    )
    # Date picker only shown for All/Income/Expenses views
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
    st.dataframe(filtered_df.style.format({"Amount": "R {:,.2f}"}), width='stretch')
    st.header("Edit Transactions")
    edited_df = st.data_editor(df, num_rows="dynamic")
    if st.button("Save Changes"):
        st.session_state.df = edited_df
        st.success("Changes saved!")
        st.rerun()

# --- PAGE 3: ARCHIVES ---
elif page == "Archives":
    st.title("Budget Archives")
    selected_month = st.selectbox("Select Previous Month", df['Month'].unique())
    
    archive_data = df[df['Month'] == selected_month]
    st.write(f"Showing data for: {selected_month}")
    st.table(archive_data)
    
    # Export Functionality
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