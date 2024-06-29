import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import zipfile
import io

# Function to load and process data
def load_data(zip_file):
    with zipfile.ZipFile(zip_file, 'r') as zipf:
        # List files in the ZIP archive
        file_names = zipf.namelist()

        # Assuming there is only one file in the ZIP
        data_file = file_names[0]
        with zipf.open(data_file) as f:
            df = pd.read_pickle(f)

    df['event_time'] = pd.to_datetime(df['event_time'])
    df['main_category'] = df['category_code'].apply(lambda x: x.split('.')[0] if pd.notnull(x) else None)
    df['year_month'] = df['event_time'].dt.to_period('M').astype(str)
    return df

# Streamlit app layout
st.title("Group 5 Dashboard")

# File uploader
uploaded_file = st.sidebar.file_uploader("Upload ZIP file containing sample_final.pkl", type="zip")

if uploaded_file:
    df = load_data(uploaded_file)
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
    tab1, tab2, tab3, tab4 = st.tabs(["Monthly Totals", "Top Categories", "Purchase Analysis", "At Risk Products"])

    with tab1:
        st.header("Monthly Totals")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Total Views per Month")
            fig_monthly_views = px.line(monthly_data, x='year_month', y='view', title='Total Views per Month')
            fig_monthly_views.update_layout(paper_bgcolor=theme.get('background_page'), plot_bgcolor=theme.get('background_content'))
            st.plotly_chart(fig_monthly_views)
        with col2:
            st.subheader("Total Purchases per Month")
            fig_monthly_purchases = px.line(monthly_data, x='year_month', y='purchase', title='Total Purchases per Month')
            fig_monthly_purchases.update_layout(paper_bgcolor=theme.get('background_page'), plot_bgcolor=theme.get('background_content'))
            st.plotly_chart(fig_monthly_purchases)

    with tab2:
        st.header("Top Categories")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Top 5 Categories with Most Purchases")
            top_5_purchases = df.groupby('category_code')['purchase'].sum().nlargest(5).reset_index()
            fig_bubble_purchases = px.scatter(top_5_purchases, x='category_code', y='purchase', size='purchase', color='category_code',
                                              title='Top 5 Categories with Most Purchases')
            fig_bubble_purchases.update_layout(paper_bgcolor=theme.get('background_page'), plot_bgcolor=theme.get('background_content'))
            st.plotly_chart(fig_bubble_purchases)
        with col2:
            st.subheader("Top 5 Categories with Most Views")
            top_5_views = df.groupby('category_code')['view'].sum().nlargest(5).reset_index()
            fig_bubble_views = px.scatter(top_5_views, x='category_code', y='view', size='view', color='category_code',
                                          title='Top 5 Categories with Most Views')
            fig_bubble_views.update_layout(paper_bgcolor=theme.get('background_page'), plot_bgcolor=theme.get('background_content'))
            st.plotly_chart(fig_bubble_views)

    with tab3:
        st.header("Purchase Analysis")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Total Purchases per Day")
            daily_purchases = df.groupby(df['event_time'].dt.date)['purchase'].sum().reset_index()
            fig_bar = px.bar(daily_purchases, x='event_time', y='purchase', title='Total Purchases per Day')
            fig_bar.update_layout(paper_bgcolor=theme.get('background_page'), plot_bgcolor=theme.get('background_content'))
            st.plotly_chart(fig_bar)
        with col2:
            st.subheader(f"Purchase Frequency for User ID: 568782581")
            user_id = 568782581
            user_data = df[df['user_id'] == user_id]
            purchase_frequency = user_data[['event_time', 'purchase']].set_index('event_time').resample('D').sum().reset_index()
            fig_user = px.line(purchase_frequency, x='event_time', y='purchase', title=f'Purchase Frequency for User ID: {user_id}')
            fig_user.update_layout(paper_bgcolor=theme.get('background_page'), plot_bgcolor=theme.get('background_content'))
            st.plotly_chart(fig_user)

    with tab4:
        st.header("At Risk Products")
        st.dataframe(at_risk_products)

    # Sidebar filters
    st.sidebar.subheader("Date Range Filter")
    start_date = st.sidebar.date_input("Start Date", df['event_time'].min().date())
    end_date = st.sidebar.date_input("End Date", df['event_time'].max().date())

    st.sidebar.subheader("Category Filter")
    categories = st.sidebar.multiselect("Select Categories", options=unique_categories)

    st.sidebar.subheader("Display Options")
    display_option = st.sidebar.radio("Choose to Display", ('Purchases', 'Views'))

    # Convert start_date and end_date to datetime
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    # Filter and display data
    filtered_df = df[(df['event_time'] >= start_date) & (df['event_time'] <= end_date)]
    if categories:
        filtered_df = filtered_df[filtered_df['main_category'].isin(categories)]

    grouped_data = filtered_df.groupby(['category_code', 'brand', 'price'])[display_option.lower()].sum().reset_index()
    grouped_data = grouped_data.sort_values(by=display_option.lower(), ascending=False)

    st.header("Purchases and Views Overview")
    fig_filtered = go.Figure(data=[go.Table(
        header=dict(values=list(grouped_data.columns),
                    fill_color='lightgrey',
                    align='left'),
        cel
