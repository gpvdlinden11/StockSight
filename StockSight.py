import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import zipfile

# Function to load and process data
def load_data(file_path):
    with zipfile.ZipFile(file_path, 'r') as zipf:
        # List files in the ZIP archive
        file_names = zipf.namelist()

        # Assuming there is only one file in the ZIP
        data_file = [file for file in file_names if 'MACOSX' not in file][0]
        with zipf.open(data_file) as f:
            df = pd.read_pickle(f)

    df['event_time'] = pd.to_datetime(df['event_time'])
    df['main_category'] = df['category_code'].apply(lambda x: x.split('.')[0] if pd.notnull(x) else None)
    df['year_month'] = df['event_time'].dt.to_period('M').astype(str)
    return df

# Function to calculate general statistics
def calculate_statistics(df):
    total_products = df['product_id'].nunique()
    total_views = df['view'].sum()
    total_purchases = df['purchase'].sum()
    total_brands = df['brand'].nunique()
    total_categories = df['category_code'].str.split('.').str[0].nunique()
    total_subcategories = df['category_code'].nunique()
    return total_products, total_views, total_purchases, total_brands, total_categories, total_subcategories

# Function to prepare visualization data
def prepare_visualization_data(df):
    monthly_data = df.groupby('year_month').agg({'view': 'sum', 'purchase': 'sum'}).reset_index()
    product_stats = df.groupby('product_id').agg(
        total_views=('view', 'sum'),
        total_purchases=('purchase', 'sum')
    ).reset_index()
    product_stats['view_to_purchase_ratio'] = product_stats['total_views'] / (product_stats['total_purchases'] + 1)
    at_risk_products = product_stats[product_stats['view_to_purchase_ratio'] > 10]
    return monthly_data, at_risk_products

# Load and process data
df = load_data('sample_final.pkl.zip')
unique_categories = df['main_category'].dropna().unique()
monthly_data, at_risk_products = prepare_visualization_data(df)
total_products, total_views, total_purchases, total_brands, total_categories, total_subcategories = calculate_statistics(df)

# Theme setup
theme = {
    "background_page": "#F5D995",
    "background_content": "#F2E9DD",
    "font_family": "Abel",
    "font_size": "17px"
}

# Streamlit app layout
st.set_page_config(layout="wide")

st.title("Group 5 Dashboard")

st.sidebar.header("Filter Options")
selected_category = st.sidebar.selectbox("Select Category", options=[None] + list(unique_categories))

# Display general statistics
st.header("General Statistics")
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Products", total_products)
col2.metric("Total Views", total_views)
col3.metric("Total Purchases", total_purchases)
col4.metric("Total Brands", total_brands)
col5.metric("Total Categories", f"{total_categories} Categories / {total_subcategories} Subcategories")

# Tabs for different sections
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Monthly Totals", "Top Categories", "Purchase Analysis", "At Risk Products", "Purchases and Views Overview"])

with tab1:
    st.header("Monthly Totals")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Total Views per Month")
        fig_monthly_views = px.line(monthly_data, x='year_month', y='view', title='Total Views per Month')
        fig_monthly_views.update_layout(paper_bgcolor=theme.get('background_page'), plot_bgcolor=theme.get('background_content'))
        st.plotly_chart(fig_monthly_views, use_container_width=True)
    with col2:
        st.subheader("Total Purchases per Month")
        fig_monthly_purchases = px.line(monthly_data, x='year_month', y='purchase', title='Total Purchases per Month')
        fig_monthly_purchases.update_layout(paper_bgcolor=theme.get('background_page'), plot_bgcolor=theme.get('background_content'))
        st.plotly_chart(fig_monthly_purchases, use_container_width=True)

with tab2:
    st.header("Top Categories")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Top 5 Categories with Most Purchases")
        top_5_purchases = df.groupby('category_code')['purchase'].sum().nlargest(5).reset_index()
        fig_bubble_purchases = px.scatter(top_5_purchases, x='category_code', y='purchase', size='purchase', color='category_code',
                                          title='Top 5 Categories with Most Purchases')
        fig_bubble_purchases.update_layout(paper_bgcolor=theme.get('background_page'), plot_bgcolor=theme.get('background_content'))
        st.plotly_chart(fig_bubble_purchases, use_container_width=True)
    with col2:
        st.subheader("Top 5 Categories with Most Views")
        top_5_views = df.groupby('category_code')['view'].sum().nlargest(5).reset_index()
        fig_bubble_views = px.scatter(top_5_views, x='category_code', y='view', size='view', color='category_code',
                                      title='Top 5 Categories with Most Views')
        fig_bubble_views.update_layout(paper_bgcolor=theme.get('background_page'), plot_bgcolor=theme.get('background_content'))
        st.plotly_chart(fig_bubble_views, use_container_width=True)

with tab3:
    st.header("Purchase Analysis")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Total Purchases per Day")
        daily_purchases = df.groupby(df['event_time'].dt.date)['purchase'].sum().reset_index()
        fig_bar = px.bar(daily_purchases, x='event_time', y='purchase', title='Total Purchases per Day')
        fig_bar.update_layout(paper_bgcolor=theme.get('background_page'), plot_bgcolor=theme.get('background_content'))
        st.plotly_chart(fig_bar, use_container_width=True)
    with col2:
        st.subheader(f"Purchase Frequency for User ID: 568782581")
        user_id = 568782581
        user_data = df[df['user_id'] == user_id]
        purchase_frequency = user_data[['event_time', 'purchase']].set_index('event_time').resample('D').sum().reset_index()
        fig_user = px.line(purchase_frequency, x='event_time', y='purchase', title=f'Purchase Frequency for User ID: {user_id}')
        fig_user.update_layout(paper_bgcolor=theme.get('background_page'), plot_bgcolor=theme.get('background_content'))
        st.plotly_chart(fig_user, use_container_width=True)

with tab4:
    st.header("At Risk Products")
    st.dataframe(at_risk_products)

with tab5:
    st.header("Purchases and Views Overview")
    
    start_date = st.date_input("Start Date", df['event_time'].min())
    end_date = st.date_input("End Date", df['event_time'].max())
    
    categories = st.multiselect("Select Categories", options=unique_categories)
    
    display_option = st.radio("Choose to Display", ('purchase', 'view'))
    
    if start_date and end_date:
        st.write(f"Selected start date: {start_date}")
        st.write(f"Selected end date: {end_date}")
        
        converted_start_date = pd.to_datetime(start_date)
        converted_end_date = pd.to_datetime(end_date)
        
        st.write(f"Converted start date: {converted_start_date}")
        st.write(f"Converted end date: {converted_end_date}")
        
        filtered_df = df[(df['event_time'] >= converted_start_date) & (df['event_time'] <= converted_end_date)]
        
        if categories:
            filtered_df = filtered_df[filtered_df['main_category'].isin(categories)]
        
        grouped_data = filtered_df.groupby(['category_code', 'brand', 'price'])[display_option].sum().reset_index()
        grouped_data = grouped_data.sort_values(by=display_option, ascending=False)
        
        if not grouped_data.empty:
            st.dataframe(
                grouped_data[['category_code', 'brand', 'price', display_option]]
                .rename(columns={display_option: display_option.capitalize()})
            )
        
        if grouped_data.empty:
            st.write("No data available for the selected filters.")
