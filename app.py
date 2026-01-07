import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- 구글 시트 연동 설정 ---
SHEET_NAME = 'culture_media_log'

def connect_google_sheet():
    # 인증 범위
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    
    try:
        # [변경점] 파일 대신 Streamlit Secrets에서 정보를 가져옵니다.
        # secrets.toml에 적은 [gcp_service_account] 섹션을 읽어옵니다.
        creds_dict = dict(st.secrets["gcp_service_account"])
        
        # 딕셔너리 정보를 이용해 인증
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open(SHEET_NAME)
        return spreadsheet.sheet1
        
    except KeyError:
        st.error("🚨 Secrets 설정이 안 되어 있습니다. Streamlit Cloud Settings -> Secrets에 [gcp_service_account] 정보를 넣어주세요.")
        st.stop()
    except Exception as e:
        st.error(f"🚨 구글 시트 연결 실패: {e}")
        st.stop()

# 데이터 불러오기
def load_data(worksheet):
    data = worksheet.get_all_records()
    if not data:
        return pd.DataFrame(columns=[
            '조제 번호', '조제 일자', '작업자', 
            'Basal Media_Lot', 'FBS_Lot', 'Antibiotics_Lot', 
            '비고'
        ])
    return pd.DataFrame(data)

# 데이터 저장하기
def add_data(worksheet, new_row_list):
    worksheet.append_row(new_row_list)

# 데이터 수정하기
def update_all_data(worksheet, df):
    worksheet.clear()
    worksheet.append_row(df.columns.tolist())
    worksheet.update('A2', df.values.tolist())

# 조제 번호 자동 생성
def generate_batch_id(df):
    today_str = datetime.now().strftime("%Y%m%d")
    prefix = f"{today_str}-CM-"
    
    if df.empty:
        return f"{prefix}01"
    
    today_batches = df[df['조제 번호'].astype(str).str.startswith(prefix)]
    
    if today_batches.empty:
        return f"{prefix}01"
    else:
        last_ids = today_batches['조제 번호'].apply(lambda x: int(str(x).split('-')[-1]))
        next_num = last_ids.max() + 1
        return f"{prefix}{next_num:02d}"

def main():
    st.set_page_config(page_title="배양배지 조제 관리", layout="wide")
    st.title("🧫 배양배지 조제 관리 시스템")

    # 1. 구글 시트 연결
    sheet = connect_google_sheet()
    
    # 2. 데이터 불러오기
    df = load_data(sheet)

    # 탭 구성
    tab1, tab2 = st.tabs(["📝 입력", "📋 기록 및 수정"])

    # --- Sheet 1: 입력 ---
    with tab1:
        st.subheader("새로운 배지 등록")
        with st.form("media_form", clear_on_submit=True):
            auto_batch_id = generate_batch_id(df)
            st.info(f"생성될 번호: **{auto_batch_id}**")
            
            col1, col2 = st.columns(2)
            date = col1.date_input("조제 일자", datetime.now())
            operator = col2.text_input("작업자")
            
            st.markdown("---")
            lot_basal = st.text_input("1. Basal Media Lot")
            lot_fbs = st.text_input("2. FBS Lot")
            lot_anti = st.text_input("3. Antibiotics Lot")
            notes = st.text_area("비고")
            
            submitted = st.form_submit_button("저장하기", use_container_width=True)
            
            if submitted:
                if not operator:
                    st.error("작업자를 입력하세요.")
                else:
                    new_row = [
                        auto_batch_id,
                        date.strftime("%Y-%m-%d"),
                        operator,
                        lot_basal,
                        lot_fbs,
                        lot_anti,
                        notes
                    ]
                    with st.spinner("저장 중..."):
                        add_data(sheet, new_row)
                    st.success("저장 완료!")
                    st.rerun()

    # --- Sheet 2: 수정 ---
    with tab2:
        st.subheader("기록 확인 및 수정")
        if not df.empty:
            edited_df = st.data_editor(
                df,
                use_container_width=True,
                num_rows="dynamic",
                key="editor"
            )
            if st.button("💾 수정사항 반영하기", type="primary"):
                with st.spinner("업데이트 중..."):
                    update_all_data(sheet, edited_df)
                st.success("수정 완료!")
                st.rerun()
        else:
            st.info("데이터가 없습니다.")

if __name__ == "__main__":
    main()
