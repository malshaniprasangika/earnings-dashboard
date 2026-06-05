import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Setup Page
st.set_page_config(page_title="Earnings Tracker", layout="wide")
st.title("📈 Earnings Reaction Dashboard")

# 2. Data Loading & Cleaning
@st.cache_data
def load_data():
    # Use latin1 to handle special characters from Excel
    df = pd.read_csv("earnings_data.csv", encoding='latin1')
    
    # Strip whitespace from columns to handle hidden characters
    df.columns = df.columns.str.strip() 
    
    # Helper to find columns by partial name (handles "time", "spaces", etc)
    def get_col(partial_name):
        matches = [c for c in df.columns if partial_name in c]
        if not matches:
            raise ValueError(f"Could not find column containing: '{partial_name}'")
        return matches[0]

    # Dynamically find the correct column names
    col_price_ann = get_col("Price at Announcement")
    col_359 = get_col("3:59:00 PM")
    col_eps_act = get_col("EPS Actual")
    col_eps_con = get_col("EPS Consensus")

    # Clean numeric data
    df[col_eps_act] = pd.to_numeric(df[col_eps_act], errors='coerce')
    df[col_eps_con] = pd.to_numeric(df[col_eps_con], errors='coerce')
    df[col_price_ann] = pd.to_numeric(df[col_price_ann], errors='coerce')
    df[col_359] = pd.to_numeric(df[col_359], errors='coerce')
    
    # Calculate metrics using dynamic column variables
    df['EPS_Surprise_Pct'] = ((df[col_eps_act] - df[col_eps_con]) / df[col_eps_con]) * 100
    df['Intraday_Move_Pct'] = ((df[col_359] - df[col_price_ann]) / df[col_price_ann]) * 100
    
    return df

try:
    df = load_data()

    # 3. Sidebar Filters
    st.sidebar.header("Filter Data")
    tickers = st.sidebar.multiselect("Select Ticker", options=df['Ticker'].unique(), default=df['Ticker'].unique())
    filtered_df = df[df['Ticker'].isin(tickers)]

    # 4. KPIs
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Stocks", len(filtered_df))
    
    avg_surprise = filtered_df['EPS_Surprise_Pct'].mean() if not filtered_df.empty else 0
    col2.metric("Avg EPS Surprise", f"{avg_surprise:.2f}%")
    
    avg_move = filtered_df['Intraday_Move_Pct'].mean() if not filtered_df.empty else 0
    col3.metric("Avg Intraday Move", f"{avg_move:.2f}%")

    # 5. Charts
    st.subheader("Analysis")

    # Scatter Plot
    fig1 = px.scatter(
        filtered_df, 
        x="EPS_Surprise_Pct", 
        y="Intraday_Move_Pct", 
        color="Ticker", 
        size_max=15,
        title="EPS Surprise % vs. Price Reaction"
    )
    st.plotly_chart(fig1, use_container_width=True)

    # Line Chart
    time_cols = ['9:29:00 AM', '10:00:00 AM', '11:00:00 AM', '3:45:00 PM', '3:59:00 PM']
    # Filter only columns that exist in the dataframe
    existing_time_cols = [c for c in time_cols if c in df.columns]
    melted_df = filtered_df.melt(id_vars=['Ticker'], value_vars=existing_time_cols, var_name='Time', value_name='Price')

    fig2 = px.line(melted_df, x="Time", y="Price", color="Ticker", title="Intraday Price Trajectory")
    st.plotly_chart(fig2, use_container_width=True)

    # 6. Raw Data Table
    st.subheader("Raw Data")
    st.dataframe(filtered_df)

except Exception as e:
    st.error(f"Application Error: {e}")
    st.write("If you see this, check if 'earnings_data.csv' is in the folder and has the required headers.")