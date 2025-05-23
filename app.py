
import streamlit as st
import pandas as pd
import datetime
import matplotlib.pyplot as plt
import os

st.set_page_config(page_title="Dashboard ตรวจสอบลูกหนี้", layout="wide")

st.title("Dashboard ตรวจสอบรายงานลูกหนี้รายตัว")

uploaded_file = st.file_uploader("อัปโหลดไฟล์ Excel", type=["xlsx"])

# ✅ แปลงคอลัมน์ปัญหาให้เป็น str
#    if 'ICD-9' in df.columns:
#        df['ICD-9'] = df['ICD-9'].astype(str)


if uploaded_file:
    df = pd.read_excel(uploaded_file)

# ✅ แปลงคอลัมน์ปัญหาให้เป็น str
    if 'ICD-9' in df.columns:
        df['ICD-9'] = df['ICD-9'].astype(str)

    for col in ["เรียกเก็บ", "ชำระแล้ว", "คงค้าง"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    if 'วันรับบริการ' in df.columns:
        df['วันรับบริการ'] = pd.to_datetime(df['วันรับบริการ'], errors='coerce')

    tabs = st.tabs(["หน้าหลัก", "สรุปตามวัน", "กราฟสถิติ"])

    filter_type = None
    selected = None
    start_date = None
    end_date = None

    with tabs[0]:
        st.subheader("ตัวกรอง")

        col1, col2, col3 = st.columns([1.2, 2, 2])

        with col1:
            filter_type = st.radio("เลือกประเภทสิทธิ", ["สิทธิรักษา", "สิทธิลูกหนี้"])

        with col2:
            if filter_type in df.columns:
                options = sorted(df[filter_type].dropna().unique())
                selected = st.selectbox(f"เลือก {filter_type}", options)
                df = df[df[filter_type] == selected]

        with col3:
            if 'วันรับบริการ' in df.columns:
                min_date = df['วันรับบริการ'].min()
                max_date = df['วันรับบริการ'].max()
                if pd.isna(min_date):
                    min_date = datetime.date.today()
                else:
                    min_date = min_date.date()
                if pd.isna(max_date):
                    max_date = datetime.date.today()
                else:
                    max_date = max_date.date()
                start_date = st.date_input("ตั้งแต่วันที่", value=min_date, min_value=min_date, max_value=max_date)
                end_date = st.date_input("ถึงวันที่", value=max_date, min_value=min_date, max_value=max_date)
                df = df[(df['วันรับบริการ'].dt.date >= start_date) & (df['วันรับบริการ'].dt.date <= end_date)]


        st.subheader("ข้อมูลดิบ (เฉพาะที่เลือก)")
        st.dataframe(df, use_container_width=True)

        st.subheader("สรุปยอดรวม")
        col1, col2, col3 = st.columns(3)
        col1.metric("ยอดเรียกเก็บรวม", f"{df['เรียกเก็บ'].sum():,.2f} บาท")
        col2.metric("ยอดชำระแล้ว", f"{df['ชำระแล้ว'].sum():,.2f} บาท")
        col3.metric("ยอดคงค้าง", f"{df['คงค้าง'].sum():,.2f} บาท")

        st.download_button(
            "ดาวน์โหลดไฟล์สรุป (CSV)",
            df.to_csv(index=False).encode('utf-8-sig'),
            file_name="filtered_summary.csv",
            mime="text/csv"
        )

    with tabs[1]:
        title = "สรุปข้อมูลตามวันที่รับบริการ"
        if selected:
            title += f" ({filter_type}: {selected})"
        st.subheader(title)

        if 'วันรับบริการ' in df.columns:
            daily_summary = df.groupby(df['วันรับบริการ'].dt.date).agg(
                ราย=('HN', 'count'),
                ค่ารักษา=('เรียกเก็บ', 'sum'),
                ชำระจริง=('ชำระแล้ว', 'sum'),
                ค่ารักษาคงเหลือ=('คงค้าง', 'sum')
            ).reset_index()
            daily_summary.columns = ['วันที่', 'ราย', 'ค่ารักษา', 'ชำระจริง', 'ค่ารักษาคงเหลือ']

            summary_row = {
                "วันที่": "รวม",
                "ราย": daily_summary["ราย"].sum(),
                "ค่ารักษา": daily_summary["ค่ารักษา"].sum(),
                "ชำระจริง": daily_summary["ชำระจริง"].sum(),
                "ค่ารักษาคงเหลือ": daily_summary["ค่ารักษาคงเหลือ"].sum()
            }
            daily_summary = pd.concat([daily_summary, pd.DataFrame([summary_row])], ignore_index=True)

            for col in ["ค่ารักษา", "ชำระจริง", "ค่ารักษาคงเหลือ"]:
                daily_summary[col] = daily_summary[col].apply(lambda x: f"{x:,.2f}" if pd.notnull(x) else "")

            st.dataframe(daily_summary, use_container_width=True)

            st.download_button(
                "ดาวน์โหลดสรุปตามวัน (CSV)",
                daily_summary.to_csv(index=False).encode('utf-8-sig'),
                file_name="daily_summary.csv",
                mime="text/csv"
            )

    with tabs[2]:
        st.subheader("กราฟสถิติรายวัน")
        if 'วันรับบริการ' in df.columns:
            chart_df = df.groupby(df['วันรับบริการ'].dt.date).agg(
                ค่ารักษา=('เรียกเก็บ', 'sum'),
                ชำระจริง=('ชำระแล้ว', 'sum'),
                ค่ารักษาคงเหลือ=('คงค้าง', 'sum')
            ).reset_index()
            chart_df.columns = ['วันที่', 'ค่ารักษา', 'ชำระจริง', 'คงค้าง']
            chart_df = chart_df.sort_values(by="วันที่")

            st.line_chart(chart_df.set_index('วันที่'))

else:
    st.info("กรุณาอัปโหลดไฟล์ Excel เพื่อเริ่มต้น")