import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# --- Page Configuration (must be the first Streamlit command) ---
st.set_page_config(
    page_title="Online Retail Recommendation System",
    page_icon="🛒",
    layout="wide"
)

# --- Caching Data Loading and Cleaning ---
@st.cache_data
def load_and_clean_data(path):
    # This function loads and cleans the data
    # @st.cache_data ensures this expensive operation runs only once
    df = pd.read_excel(path)
    
    # --- Data Cleaning Steps from your notebook ---
    df.dropna(subset=['CustomerID', 'Description'], inplace=True)
    df['InvoiceNo'] = df['InvoiceNo'].astype(str)
    df = df[~df['InvoiceNo'].str.startswith('C', na=False)]
    df = df[df['Quantity'] > 0]
    df = df[df['UnitPrice'] > 0.001]
    
    non_product_codes = ['POST', 'D', 'M', 'BANK CHARGES', 'CRUK', 'S', 'AMAZONFEE', 'DOT']
    df = df[~df['StockCode'].astype(str).isin(non_product_codes)]
    df = df[~df['Description'].astype(str).str.contains('POSTAGE|CARRIAGE|Manual|Discount', case=False, na=False)]

    # --- Feature Engineering ---
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
    df['Year'] = df['InvoiceDate'].dt.year
    df['Month'] = df['InvoiceDate'].dt.month
    
    return df

# --- Recommendation Functions (from your notebook) ---
def get_global_recommendations(data, top_n=10):
    popular_items = data.groupby('Description')['Quantity'].sum().sort_values(ascending=False)
    return popular_items.head(top_n)

def get_country_recommendations(data, country, top_n=10):
    country_data = data[data['Country'] == country]
    if country_data.empty:
        return pd.Series(dtype='float64', name=f"No data available for country: {country}")
    popular_items = country_data.groupby('Description')['Quantity'].sum().sort_values(ascending=False)
    return popular_items.head(top_n)

def get_month_recommendations(data, year, month_num, top_n=10):
    month_name = datetime(2000, month_num, 1).strftime('%B')
    month_data = data[(data['Year'] == year) & (data['Month'] == month_num)]
    if month_data.empty:
        return pd.Series(dtype='float64', name=f"No data available for {month_name} {year}")
    popular_items = month_data.groupby('Description')['Quantity'].sum().sort_values(ascending=False)
    return popular_items.head(top_n)

# --- Main App Logic ---
# Load the data
try:
    df = load_and_clean_data('data/Online_Retail.xlsx') # Assumes your xlsx is in a 'data' subfolder
except FileNotFoundError:
    st.error("Error: 'Online_Retail.csv' not found. Please place it in a 'data' subfolder.")
    st.stop()

# --- UI Layout ---
st.title("🛒 Online Retail Recommendation System")
st.markdown("This app analyzes historical sales data to provide popularity-based product recommendations.")

st.sidebar.title("Navigation")
app_mode = st.sidebar.selectbox("Choose a Recommendation Type", 
                                ["Global", "Country-Wise", "Month-Wise"])

# --- Global Recommendations ---
if app_mode == "Global":
    st.header("🌍 Top Globally Popular Products")
    st.markdown("These are the most sold products across all countries and time periods.")
    
    global_recs = get_global_recommendations(df)
    st.dataframe(global_recs)

    # Visualization
    fig, ax = plt.subplots(figsize=(12, 7))
    sns.barplot(x=global_recs.values, y=global_recs.index, palette='viridis', ax=ax)
    ax.set_title('Top 10 Globally Popular Products')
    ax.set_xlabel('Total Quantity Sold')
    ax.set_ylabel('Product Description')
    st.pyplot(fig)

# --- Country-Wise Recommendations ---
elif app_mode == "Country-Wise":
    st.header("🗺️ Top Products by Country")
    
    # Country selection dropdown
    country_list = sorted(df['Country'].unique())
    selected_country = st.selectbox("Select a Country", country_list)
    
    st.markdown(f"Displaying top 10 most popular products for **{selected_country}**.")
    
    country_recs = get_country_recommendations(df, selected_country)
    
    if country_recs.empty or country_recs.name.startswith("No data"):
        st.warning(f"No sales data available for {selected_country}.")
    else:
        st.dataframe(country_recs)
        
        # Visualization
        fig, ax = plt.subplots(figsize=(12, 7))
        sns.barplot(x=country_recs.values, y=country_recs.index, palette='mako', ax=ax)
        ax.set_title(f'Top 10 Popular Products in {selected_country}')
        ax.set_xlabel('Total Quantity Sold')
        ax.set_ylabel('Product Description')
        st.pyplot(fig)

# --- Month-Wise Recommendations ---
elif app_mode == "Month-Wise":
    st.header("📅 Top Products by Month")

    # Year and Month selection
    col1, col2 = st.columns(2)
    with col1:
        year_list = sorted(df['Year'].unique(), reverse=True)
        selected_year = st.selectbox("Select a Year", year_list)
    with col2:
        month_map = {1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June', 
                     7: 'July', 8: 'August', 9: 'September', 10: 'October', 11: 'November', 12: 'December'}
        # Filter months available for the selected year
        available_months = sorted(df[df['Year'] == selected_year]['Month'].unique())
        selected_month_name = st.selectbox("Select a Month", [month_map[m] for m in available_months])
        # Convert month name back to number
        selected_month_num = [k for k, v in month_map.items() if v == selected_month_name][0]
        
    st.markdown(f"Displaying top 10 most popular products for **{selected_month_name}, {selected_year}**.")
    
    month_recs = get_month_recommendations(df, selected_year, selected_month_num)
    
    if month_recs.empty or month_recs.name.startswith("No data"):
        st.warning(f"No sales data available for {selected_month_name}, {selected_year}.")
    else:
        st.dataframe(month_recs)
        
        # Visualization
        fig, ax = plt.subplots(figsize=(12, 7))
        sns.barplot(x=month_recs.values, y=month_recs.index, palette='crest', ax=ax)
        ax.set_title(f'Top 10 Popular Products in {selected_month_name}, {selected_year}')
        ax.set_xlabel('Total Quantity Sold')
        ax.set_ylabel('Product Description')
        st.pyplot(fig)

st.sidebar.markdown("---")
st.sidebar.info("This app was created as part of a Data Science internship project.")

