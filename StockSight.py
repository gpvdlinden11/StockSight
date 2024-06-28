import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import zipfile

# File uploader widget
uploaded_file = st.file_uploader("Choose a zip file containing the dataset", type="zip")

if uploaded_file is not None:
    # Extract the zip file
    try:
        with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
            zip_ref.extractall()
            extracted_file_path = [name for name in zip_ref.namelist() if name.endswith('.pkl')][0]
    except zipfile.BadZipFile:
        st.error("The zip file is corrupted or not a valid zip file.")
        st.stop()

    # Load data with error handling
    try:
        df = pd.read_pickle(extracted_file_path)
    except (pd.errors.UnpickleError, FileNotFoundError) as e:
        st.error(f"Error loading pickle file: {e}")
        st.stop()

    df['event_time'] = pd.to_datetime(df['event_time'])

    # Processing data
    df['main_category'] = df['category_code'].apply(lambda x: x.split('.')[0] if pd.notnull(x) else None)
    unique_categories = df['main_category'].dropna().unique()
    category_options = [{'label': cat, 'value': cat} for cat in unique_categories if cat is not None]

    df['year_month'] = df['event_time'].dt.to_period('M').astype(str)
    monthly_data = df.groupby('year_month').agg({'view': 'sum', 'purchase': 'sum'}).reset_index()

    product_stats = df.groupby('product_id').agg(
        total_views=('view', 'sum'),
        total_purchases=('purchase', 'sum')
    ).reset_index()
    product_stats['view_to_purchase_ratio'] = product_stats['total_views'] / (product_stats['total_purchases'] + 1)
    at_risk_products = product_stats[product_stats['view_to_purchase_ratio'] > 10]

    total_products = df['product_id'].nunique()
    total_views = df['view'].sum()
    total_purchases = df['purchase'].sum()
    total_brands = df['brand'].nunique()
    total_categories = df['category_code'].str.split('.').str[0].nunique()
    total_subcategories = df['category_code'].nunique()

    # Theme setup
    theme = {
        "accent": "#232323",
        "accent_negative": "#ff2c6d",
        "accent_positive": "#33ffe6",
        "background_content": "#F2E9DD",
        "background_page": "#E8DAC5",
        "border": "#d3bd98",
        "border_style": {
            "name": "underlined",
            "borderTopWidth": 0,
            "borderRightWidth": 0,
            "borderLeftWidth": 0,
            "borderBottomWidth": "1px",
            "borderBottomStyle": "solid",
            "borderRadius": 0,
            "inputFocus": {
                "outline": "transparent"
            }
        },
        "breakpoint_font": "1200px",
        "breakpoint_stack_blocks": "700px",
        "colorway": [
            "#232323",
            "#d95f02",
            "#1b9e77",
            "#7570b3",
            "#e7298a",
            "#66a61e",
            "#e6ab02",
            "#a6761d"
        ],
        "colorscale": [
            "#232323",
            "#363636",
            "#4b4b4b",
            "#606060",
            "#777777",
            "#8e8e8e",
            "#a6a6a6",
            "#bebebe",
            "#d7d7d7",
            "#f1f1f1"
        ],
        "font_family": "Abel",
        "font_size": "17px",
        "font_size_smaller_screen": "15px",
        "font_family_header": "PT Serif",
        "font_size_header": "24px",
        "font_family_headings": "PT Serif",
        "text": "#493D32",
        "report_font_family": "Computer Modern",
        "report_font_size": "12px",
        "report_background_page": "white",
        "report_background_content": "#FAFBFC",
        "report_text": "black"
    }

    # Streamlit app layout
    st.title("Group 5")

    st.sidebar.header("Filter Options")
    selected_category = st.sidebar.selectbox("Select Category", options=[None] + list(unique_categories))

    # Display statistics
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
            fig_monthly_views.update_layout(paper_bgcolor=theme['background_page'], plot_bgcolor=theme['background_content'])
            st.plotly_chart(fig_monthly_views)
        with col2:
            st.subheader("Total Purchases per Month")
            fig_monthly_purchases = px.line(monthly_data, x='year_month', y='purchase', title='Total Purchases per Month')
            fig_monthly_purchases.update_layout(paper_bgcolor=theme['background_page'], plot_bgcolor=theme['background_content'])
            st.plotly_chart(fig_monthly_purchases)

    with tab2:
        st.header("Top Categories")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Top 5 Categories with Most Purchases")
            top_5_purchases = df.groupby('category_code')['purchase'].sum().nlargest(5).reset_index()
            fig_bubble_purchases = px.scatter(top_5_purchases, x='category_code', y='purchase', size='purchase', color='category_code',
                                              title='Top 5 Categories with Most Purchases')
            fig_bubble_purchases.update_layout(paper_bgcolor=theme['background_page'], plot_bgcolor=theme['background_content'])
            st.plotly_chart(fig_bubble_purchases)
        with col2:
            st.subheader("Top 5 Categories with Most Views")
            top_5_views = df.groupby('category_code')['view'].sum().nlargest(5).reset_index()
            fig_bubble_views = px.scatter(top_5_views, x='category_code', y='view', size='view', color='category_code',
                                          title='Top 5 Categories with Most Views')
            fig_bubble_views.update_layout(paper_bgcolor=theme['background_page'], plot_bgcolor=theme['background_content'])
            st.plotly_chart(fig_bubble_views)

    with tab3:
        st.header("Purchase Analysis")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Total Purchases per Day")
            daily_purchases = df.groupby(df['event_time'].dt.date)['purchase'].sum().reset_index()
            fig_bar = px.bar(daily_purchases, x='event_time', y='purchase', title='Total Purchases per Day')
            fig_bar.update_layout(paper_bgcolor=theme['background_page'], plot_bgcolor=theme['background_content'])
            st.plotly_chart(fig_bar)
        with col2:
            st.subheader(f"Purchase Frequency for User ID: 568782581")
            user_id = 568782581
            user_data = df[df['user_id'] == user_id]
            purchase_frequency = user_data[['event_time', 'purchase']].set_index('event_time').resample('D').sum().reset_index()
            fig_user = px.line(purchase_frequency, x='event_time', y='purchase', title=f'Purchase Frequency for User ID: {user_id}')
            fig_user.update_layout(paper_bgcolor=theme['background_page'], plot_bgcolor=theme['background_content'])
            st.plotly_chart(fig_user)

    with tab4:
        st.header("At Risk Products")
        st.dataframe(at_risk_products)

    # Date range filter
    st.sidebar.subheader("Date Range Filter")
    start_date = st.sidebar.date_input("Start Date", df['event_time'].min())
    end_date = st.sidebar.date_input("End Date", df['event_time'].max())

    # Category filter
    st.sidebar.subheader("Category Filter")
    categories = st.sidebar.multiselect("Select Categories", options=unique_categories)

    # Display options
    st.sidebar.subheader("Display Options")
    display_option = st.sidebar.radio("Choose to Display", ('Purchases', 'Views'))

    # Filter and display data
    filtered_df = df[(df['event_time'] >= pd.to_datetime(start_date)) & (df['event_time'] <= pd.to_datetime(end_date))]
    if categories:
        filtered_df = filtered_df[filtered_df['main_category'].isin(categories)]

    grouped_data = filtered_df.groupby(['category_code', 'brand', 'price'])[display_option.lower()].sum().reset_index()
    grouped_data = grouped_data.sort_values(by=display_option.lower(), ascending=False)

    st.header("Purchases and Views overview")
    fig_filtered = go.Figure(data=[go.Table(
        header=dict(values=list(grouped_data.columns),
                    fill_color='lightgrey',
                    align='left'),
        cells=dict(values=[grouped_data[col] for col in grouped_data.columns],
                   fill_color='lightsteelblue',
                   align='left'))
    ])
    fig_filtered.update_layout(paper_bgcolor=theme['background_page'], plot_bgcolor=theme['background_content'])
    st.plotly_chart(fig_filtered)
