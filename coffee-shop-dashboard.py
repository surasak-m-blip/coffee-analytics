import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ---------------------------------------------------------
# 1. การตั้งค่าหน้าจอ Streamlit (Page Configuration)
# ---------------------------------------------------------
st.set_page_config(
    page_title="Coffee Shop Analytics Dashboard",
    page_icon="☕",
    layout="wide"
)

# ---------------------------------------------------------
# 2. ฟังก์ชันสร้างข้อมูลจำลอง (Mock Data Generator)
# ---------------------------------------------------------
@st.cache_data
def generate_mock_data():
    np.random.seed(42)
    n_rows = 1000
    
    locations = ['Siam Square', 'Ari', 'Thonglor', 'Asok']
    categories = ['Coffee', 'Non-Coffee', 'Bakery', 'Coffee Beans']
    
    products = {
        'Coffee': [('Espresso', 60), ('Americano', 70), ('Latte', 80), ('Cappuccino', 80), ('Mocha', 90)],
        'Non-Coffee': [('Matcha Latte', 90), ('Thai Tea', 70), ('Chocolate', 85), ('Lemon Tea', 65)],
        'Bakery': [('Croissant', 75), ('Cheesecake', 120), ('Brownie', 65), ('Muffin', 55)],
        'Coffee Beans': [('House Blend 250g', 350), ('Single Origin 250g', 480)]
    }
    
    start_date = datetime(2026, 1, 1)
    
    data = []
    for i in range(1, n_rows + 1):
        loc = np.random.choice(locations, p=[0.35, 0.25, 0.20, 0.20])
        cat = np.random.choice(categories, p=[0.50, 0.25, 0.20, 0.05])
        
        prod_info = products[cat][np.random.choice(len(products[cat]))]
        prod_name, unit_price = prod_info
        
        # จำลองช่วงเวลาที่คนมักจะซื้อกาแฟ (Peak ช่วง 08:00 - 10:00 น.)
        hour_weights = [0,0,0,0,0,0, 0.02, 0.10, 0.25, 0.20, 0.10, 0.08, 0.07, 0.05, 0.04, 0.04, 0.03, 0.02, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00]
        hour = np.random.choice(range(24), p=hour_weights)
        minute = np.random.randint(0, 60)
        day_offset = np.random.randint(0, 90)
        
        tx_time = start_date + timedelta(days=day_offset, hours=int(hour), minutes=int(minute))
        qty = np.random.choice([1, 2, 3], p=[0.75, 0.20, 0.05])
        
        data.append({
            'transaction_id': f'TX{10000 + i}',
            'transaction_datetime': tx_time,
            'date': tx_time.date(),
            'hour': tx_time.hour,
            'day_of_week': tx_time.strftime('%A'),
            'store_location': loc,
            'product_category': cat,
            'product_name': prod_name,
            'unit_price': unit_price,
            'quantity': qty,
            'total_revenue': unit_price * qty
        })
        
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    return df

# โหลดข้อมูล
df_raw = generate_mock_data()

# ---------------------------------------------------------
# 3. ส่วนควบคุมด้านข้าง (Sidebar Controls & Filters)
# ---------------------------------------------------------
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2935/2935413.png", width=100)
st.sidebar.title("☕ Coffee Analytics Filter")

# ตัวกรองไฟล์ข้อมูล
uploaded_file = st.sidebar.file_uploader("อัปโหลดไฟล์ CSV (ถ้ามี)", type=['csv'])
if uploaded_file is not None:
    df_raw = pd.read_csv(uploaded_file)
    df_raw['transaction_datetime'] = pd.to_datetime(df_raw['transaction_datetime'])
    df_raw['date'] = pd.to_datetime(df_raw['date'])

# ตัวกรองวันที่
min_date = df_raw['date'].min().date()
max_date = df_raw['date'].max().date()
selected_date_range = st.sidebar.date_input("เลือกช่วงเวลา", [min_date, max_date], min_value=min_date, max_value=max_date)

# ตัวกรองสาขา
selected_locations = st.sidebar.multiselect("เลือกสาขา", options=df_raw['store_location'].unique(), default=df_raw['store_location'].unique())

# ตัวกรองหมวดหมู่สินค้า
selected_categories = st.sidebar.multiselect("เลือกหมวดหมู่สินค้า", options=df_raw['product_category'].unique(), default=df_raw['product_category'].unique())

# การกรองข้อมูลตามคำสั่ง
if len(selected_date_range) == 2:
    start_date, end_date = selected_date_range
    df_filtered = df_raw[
        (df_raw['date'].dt.date >= start_date) & 
        (df_raw['date'].dt.date <= end_date) &
        (df_raw['store_location'].isin(selected_locations)) &
        (df_raw['product_category'].isin(selected_categories))
    ]
else:
    df_filtered = df_raw.copy()

# ---------------------------------------------------------
# 4. ส่วนแสดงผลหลัก (Main Dashboard Layout)
# ---------------------------------------------------------
st.title("📊 Coffee Shop Sales & Behavior Analytics Dashboard")
st.markdown("แดชบอร์ดวิเคราะห์ยอดขาย พฤติกรรมผู้บริโภค และช่วงเวลาขายดีสำหรับธุรกิจร้านกาแฟ")
st.markdown("---")

# สร้าง แท็บแบ่งหน้าการวิเคราะห์
tab1, tab2, tab3 = st.tabs(["📈 ภาพรวมยอดขาย (Overview)", "☕ เจาะลึกสินค้า (Product)", "⏰ ช่วงเวลา & พฤติกรรม (Peak Hours)"])

# =========================================================
# TAB 1: EXECUTIVE OVERVIEW
# =========================================================
with tab1:
    # 1.1 KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    
    total_revenue = df_filtered['total_revenue'].sum()
    total_orders = df_filtered['transaction_id'].nunique()
    aov = total_revenue / total_orders if total_orders > 0 else 0
    total_qty = df_filtered['quantity'].sum()
    
    col1.metric("ยอดขายรวม (Total Revenue)", f"฿{total_revenue:,.2f}")
    col2.metric("จำนวนบิลรวม (Total Orders)", f"{total_orders:,} บิล")
    col3.metric("ยอดซื้อเฉลี่ย/บิล (AOV)", f"฿{aov:,.2f}")
    col4.metric("จำนวนชิ้นที่ขายได้ (Total Items)", f"{total_qty:,} ชิ้น")
    
    st.markdown("---")
    
    # 1.2 Sales Trend & Location Comparison
    c1, c2 = st.columns([2, 1])
    
    with c1:
        daily_sales = df_filtered.groupby('date')['total_revenue'].sum().reset_index()
        fig_trend = px.line(daily_sales, x='date', y='total_revenue', 
                            title='แนวโน้มยอดขายรายวัน (Daily Sales Trend)',
                            labels={'date': 'วันที่', 'total_revenue': 'ยอดขาย (บาท)'},
                            markers=True, color_discrete_sequence=['#4A2C2A'])
        st.plotly_chart(fig_trend, use_container_width=True)
        
    with c2:
        loc_sales = df_filtered.groupby('store_location')['total_revenue'].sum().reset_index().sort_values(by='total_revenue', ascending=False)
        fig_loc = px.bar(loc_sales, x='store_location', y='total_revenue',
                         title='ยอดขายแบ่งตามสาขา (Revenue by Location)',
                         labels={'store_location': 'สาขา', 'total_revenue': 'ยอดขาย (บาท)'},
                         color='store_location', color_discrete_sequence=px.colors.sequential.YlOrBr)
        st.plotly_chart(fig_loc, use_container_width=True)

    # 1.3 Category Revenue Breakdown
    cat_sales = df_filtered.groupby('product_category')['total_revenue'].sum().reset_index()
    fig_cat = px.pie(cat_sales, values='total_revenue', names='product_category', hole=0.4,
                     title='สัดส่วนรายได้ตามหมวดหมู่สินค้า (Revenue Share by Category)',
                     color_discrete_sequence=px.colors.sequential.RdBu)
    st.plotly_chart(fig_cat, use_container_width=True)

# =========================================================
# TAB 2: PRODUCT PERFORMANCE
# =========================================================
with tab2:
    st.subheader("การวิเคราะห์ประสิทธิภาพของสินค้า")
    
    col_p1, col_p2 = st.columns(2)
    
    with col_p1:
        top_products = df_filtered.groupby('product_name')['quantity'].sum().reset_index().sort_values(by='quantity', ascending=False).head(10)
        fig_top = px.bar(top_products, x='quantity', y='product_name', orientation='h',
                         title='10 อันดับสินค้าขายดีที่สุด (Top 10 Best Sellers - Qty)',
                         labels={'quantity': 'จำนวนที่ขายได้ (ชิ้น)', 'product_name': 'ชื่อสินค้า'},
                         color='quantity', color_continuous_scale='blugrn')
        fig_top.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_top, use_container_width=True)
        
    with col_p2:
        bottom_products = df_filtered.groupby('product_name')['quantity'].sum().reset_index().sort_values(by='quantity', ascending=True).head(5)
        fig_bottom = px.bar(bottom_products, x='quantity', y='product_name', orientation='h',
                            title='5 อันดับสินค้าขายได้น้อยที่สุด (Bottom 5 Low Performers)',
                            labels={'quantity': 'จำนวนที่ขายได้ (ชิ้น)', 'product_name': 'ชื่อสินค้า'},
                            color='quantity', color_continuous_scale='Reds_r')
        fig_bottom.update_layout(yaxis={'categoryorder': 'total descending'})
        st.plotly_chart(fig_bottom, use_container_width=True)

    # Scatter Plot: Price vs Quantity
    product_stats = df_filtered.groupby('product_name').agg({
        'unit_price': 'mean',
        'quantity': 'sum',
        'total_revenue': 'sum'
    }).reset_index()
    
    fig_scatter = px.scatter(product_stats, x='unit_price', y='quantity', size='total_revenue', color='product_name',
                             hover_name='product_name', title='ความสัมพันธ์ระหว่างราคากับปริมาณการขาย (Price vs. Quantity Sold)',
                             labels={'unit_price': 'ราคาต่อหน่วย (บาท)', 'quantity': 'ปริมาณการขาย (ชิ้น)'})
    st.plotly_chart(fig_scatter, use_container_width=True)

# =========================================================
# TAB 3: PEAK HOURS & BEHAVIOR
# =========================================================
with tab3:
    st.subheader("วิเคราะห์ช่วงเวลาขายดีและพฤติกรรมลูกค้า")
    
    # 3.1 Peak Hours Heatmap
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    heatmap_data = df_filtered.pivot_table(index='day_of_week', columns='hour', values='transaction_id', aggfunc='count', fill_value=0)
    heatmap_data = heatmap_data.reindex(day_order)
    
    fig_heatmap = px.imshow(heatmap_data, 
                            labels=dict(x="ชั่วโมงของวัน (Hour)", y="วันในสัปดาห์ (Day)", color="จำนวนธุรกรรม"),
                            x=heatmap_data.columns,
                            y=heatmap_data.index,
                            title="Heatmap ช่วงเวลาที่มีผู้ใช้บริการหนาแน่น (Peak Hours Heatmap)",
                            color_continuous_scale='YlOrRd')
    st.plotly_chart(fig_heatmap, use_container_width=True)
    
    # 3.2 Time Block Analysis
    def get_time_block(hour):
        if 6 <= hour < 11:
            return '1. เช้า (06:00 - 11:00)'
        elif 11 <= hour < 14:
            return '2. เที่ยง/สาย (11:00 - 14:00)'
        elif 14 <= hour < 17:
            return '3. บ่าย (14:00 - 17:00)'
        else:
            return '4. เย็น/ค่ำ (17:00 เป็นต้นไป)'

    df_filtered['time_block'] = df_filtered['hour'].apply(get_time_block)
    time_block_sales = df_filtered.groupby('time_block')['total_revenue'].sum().reset_index()
    
    fig_block = px.bar(time_block_sales, x='time_block', y='total_revenue',
                       title='ยอดขายแบ่งตามช่วงเวลาของวัน (Sales by Time Block)',
                       labels={'time_block': 'ช่วงเวลา', 'total_revenue': 'ยอดขาย (บาท)'},
                       color='time_block', color_discrete_sequence=px.colors.qualitative.Pastel)
    st.plotly_chart(fig_block, use_container_width=True)
