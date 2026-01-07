import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. 앱 제목 및 설명
st.set_page_config(page_title="팀 시약 조제 기록", page_icon="🧪")
st.title("🧪 팀 시약 조제 기록 시스템")
st.write("시약을 조제한 후 아래 양식을 작성해주세요.")

# 2. 입력 양식 (Form)
with st.form("reagent_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        reagent_name = st.text_input("시약명 (Name)")
        concentration = st.text_input("농도 (Conc.)")
        lot_no = st.text_input("원료 Lot No.")
        
    with col2:
        maker = st.text_input("조제자 (User)")
        expiry_date = st.date_input("유효기간 설정")
        ph_value = st.number_input("최종 pH", step=0.1)

    memo = st.text_area("특이사항 및 비고")
    submitted = st.form_submit_button("기록 저장하기")

# 3. 데이터 처리 로직 (CSV 저장)
file_path = 'reagent_log.csv'

if submitted:
    new_data = {
        "작성일시": [datetime.now().strftime("%Y-%m-%d %H:%M")],
        "시약명": [reagent_name],
        "농도": [concentration],
        "Lot No.": [lot_no],
        "조제자": [maker],
        "유효기간": [expiry_date],
        "pH": [ph_value],
        "비고": [memo]
    }
    df = pd.DataFrame(new_data)
    
    if not os.path.exists(file_path):
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
    else:
        df.to_csv(file_path, mode='a', header=False, index=False, encoding='utf-8-sig')
    
    st.success(f"✅ '{reagent_name}' 기록 완료!")

# 4. 기록 보여주기
st.divider()
st.subheader("📋 최근 조제 기록")
if os.path.exists(file_path):
    history_df = pd.read_csv(file_path)
    st.dataframe(history_df.sort_values(by="작성일시", ascending=False))
else:
    st.info("아직 기록된 데이터가 없습니다.")