import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# ---------------------------------------------------------
# [설정] 구글 시트 연동 함수
# ---------------------------------------------------------
# Streamlit Secrets에서 인증 정보를 가져옵니다.
def get_google_sheet_connection():
    try:
        # Secrets에 저장된 정보를 이용해 인증
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
        ]
        credentials = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=scopes,
        )
        gc = gspread.authorize(credentials)
        return gc
    except Exception as e:
        st.error("⚠️ 구글 시트 연결 실패! Secrets 설정을 확인해주세요.")
        st.stop()

# ---------------------------------------------------------
# [메인] 앱 화면 구성
# ---------------------------------------------------------
st.set_page_config(page_title="팀 시약 관리 시스템", page_icon="🧪", layout="wide")
st.title("🧪 팀 시약 조제 및 사용 기록")

# 구글 시트 연결 (연결 실패 시 멈춤)
gc = get_google_sheet_connection()

# 사용할 스프레드시트 주소 (URL) - *나중에 본인 시트 주소로 교체 필요*
# 예: https://docs.google.com/spreadsheets/d/Tvxxxx...
# 일단 코드가 작동하도록 '시트 이름'으로 찾거나 URL을 Secrets에 넣는 방식 추천
spreadsheet_url = st.secrets["private_gsheets_url"] 

try:
    sh = gc.open_by_url(spreadsheet_url)
    # 워크시트가 없으면 생성 (조제기록/사용기록)
    try:
        ws_prep = sh.worksheet("조제기록")
    except:
        ws_prep = sh.add_worksheet(title="조제기록", rows=100, cols=20)
        ws_prep.append_row(["작성일시", "물질명", "조제자", "기본배지 Lot", "FBS Lot", "Antibiotics Lot", "사용기한", "비고"])
        
    try:
        ws_usage = sh.worksheet("사용기록")
    except:
        ws_usage = sh.add_worksheet(title="사용기록", rows=100, cols=20)
        ws_usage.append_row(["사용일시", "물질명", "사용자", "사용량/내용", "비고"])
        
except Exception as e:
    st.error(f"스프레드시트를 찾을 수 없습니다. URL을 확인하세요.\n에러: {e}")
    st.stop()

# 탭 나누기 (조제 vs 사용)
tab1, tab2 = st.tabs(["📝 시약 조제 (Preparation)", "사용 기록 (Usage)"])

# =========================================================
# [Tab 1] 시약 조제 기록
# =========================================================
with tab1:
    st.subheader("1-5. 시약 조제 정보 입력")
    
    with st.form("prep_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("1. 물질명 (Name)")
            maker = st.text_input("2. 조제자 (User)")
            expiry = st.date_input("4. 사용 기한 (Exp. Date)")
        
        with col2:
            st.markdown("**3. 원료 Lot No.**")
            lot_base = st.text_input("3-1. 기본 배지 (Basal Media)")
            lot_fbs = st.text_input("3-2. FBS (Fetal Bovine Serum)")
            lot_anti = st.text_input("3-3. Antibiotics")
            
        memo = st.text_area("5. 특이사항 및 비고")
        
        submitted_prep = st.form_submit_button("조제 기록 저장")
        
        if submitted_prep:
            if not name or not maker:
                st.warning("물질명과 조제자는 필수 입력입니다.")
            else:
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                row_data = [now_str, name, maker, lot_base, lot_fbs, lot_anti, str(expiry), memo]
                ws_prep.append_row(row_data)
                st.success(f"✅ [{name}] 조제 기록이 구글 시트에 저장되었습니다!")

    st.divider()
    st.subheader("6. 최근 조제 기록 (Recent Prep Records)")
    # 데이터 가져오기
    data_prep = ws_prep.get_all_records()
    if data_prep:
        df_prep = pd.DataFrame(data_prep)
        # 최신순 정렬 (작성일시 기준 내림차순)
        if "작성일시" in df_prep.columns:
            df_prep = df_prep.sort_values(by="작성일시", ascending=False)
        st.dataframe(df_prep, use_container_width=True)
    else:
        st.info("아직 조제 기록이 없습니다.")

# =========================================================
# [Tab 2] 시약 사용 기록
# =========================================================
with tab2:
    st.subheader("시약 사용 대장")
    
    with st.form("usage_form", clear_on_submit=True):
        u_col1, u_col2 = st.columns(2)
        with u_col1:
            u_name = st.text_input("물질명 (사용하려는 시약)")
            u_user = st.text_input("사용자")
        with u_col2:
            u_amount = st.text_input("사용량/내용 (예: 50ml, 실험A 사용)")
            u_memo = st.text_input("비고")
            
        submitted_use = st.form_submit_button("사용 기록 저장")
        
        if submitted_use:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            row_data = [now_str, u_name, u_user, u_amount, u_memo]
            ws_usage.append_row(row_data)
            st.success("✅ 사용 기록이 저장되었습니다.")
            
    st.divider()
    st.subheader("7. 최근 사용 기록 (Recent Usage Records)")
    data_use = ws_usage.get_all_records()
    if data_use:
        df_use = pd.DataFrame(data_use)
        if "사용일시" in df_use.columns:
            df_use = df_use.sort_values(by="사용일시", ascending=False)
        st.dataframe(df_use, use_container_width=True)
    else:
        st.info("아직 사용 기록이 없습니다.")