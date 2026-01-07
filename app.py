import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# =========================================================
# [사용자 설정] 연결할 시트 ID 확인!
# =========================================================
# 주소창의 https://docs.google.com/spreadsheets/d/ 뒤에 있는 값
TARGET_SHEET_ID = "11716I3GkYFuB-lLEpD_Ciy76a9EAHwj69jGWsLMLpEc"
# =========================================================

# ---------------------------------------------------------
# [설정] 구글 시트 연동 함수
# ---------------------------------------------------------
def get_google_sheet_connection():
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        # Secrets 줄바꿈 문자 처리
        secrets_dict = dict(st.secrets["gcp_service_account"])
        if "private_key" in secrets_dict:
            secrets_dict["private_key"] = secrets_dict["private_key"].replace("\\n", "\n")

        credentials = Credentials.from_service_account_info(
            secrets_dict,
            scopes=scopes,
        )
        gc = gspread.authorize(credentials)
        return gc
    except Exception as e:
        st.error(f"⚠️ 구글 연결(인증) 실패! Secrets를 확인하세요.\n에러: {e}")
        st.stop()

# ---------------------------------------------------------
# [메인] 앱 화면 구성
# ---------------------------------------------------------
st.set_page_config(page_title="팀 시약 관리 시스템", page_icon="🧪", layout="wide")
st.title("🧪 팀 시약 조제 및 사용 기록")

# 구글 연결
gc = get_google_sheet_connection()

# ---------------------------------------------------------
# [핵심] 시트 연결 및 정밀 진단
# ---------------------------------------------------------
try:
    sh = gc.open_by_key(TARGET_SHEET_ID)
    # 연결 성공하면 조용히 넘어감
except Exception as e:
    # 연결 실패 시 상세 리포트 출력
    st.error("❌ 기존 시트에 연결할 수 없습니다!")
    
    # 1. 봇 정보 보여주기
    bot_email = gc.auth.service_account_email
    st.warning(f"🤖 **현재 봇의 이메일:**\n\n`{bot_email}`")
    
    st.markdown("""
    **👇 해결 방법 (순서대로 확인해보세요)**
    1. 위 **봇 이메일**을 복사하세요.
    2. 구글 스프레드시트 우측 상단 **[공유]** 버튼을 누르세요.
    3. 목록에 이 이메일이 있는지, **[편집자]** 권한인지 확인하세요. (없으면 다시 초대!)
    4. 시트 ID(`11716...`)가 정확한지 주소창을 다시 확인하세요.
    """)
    
    # 2. 에러 원인 분석
    error_msg = str(e)
    st.markdown("---")
    st.markdown(f"**🔍 상세 에러 메시지:**\n`{error_msg}`")
    
    if "403" in error_msg:
        st.info("💡 **힌트:** [403 Forbidden] 에러는 **'공유가 안 됨'** 뜻입니다. 공유 설정을 다시 확인하세요.")
    elif "404" in error_msg:
        st.info("💡 **힌트:** [404 Not Found] 에러는 **'시트 ID가 틀림'** 뜻입니다. ID를 다시 확인하세요.")
    
    st.stop()

# ---------------------------------------------------------
# [워크시트 확인 및 탭 구성] - 연결 성공 시 실행됨
# ---------------------------------------------------------
try:
    # 조제기록 시트
    try:
        ws_prep = sh.worksheet("조제기록")
    except:
        ws_prep = sh.add_worksheet(title="조제기록", rows=100, cols=20)
        ws_prep.append_row(["작성일시", "물질명", "조제자", "기본배지 Lot", "FBS Lot", "Antibiotics Lot", "사용기한", "비고"])
        
    # 사용기록 시트
    try:
        ws_usage = sh.worksheet("사용기록")
    except:
        ws_usage = sh.add_worksheet(title="사용기록", rows=100, cols=20)
        ws_usage.append_row(["사용일시", "물질명", "사용자", "사용량/내용", "비고"])

except Exception as e:
    st.error(f"워크시트 탭 설정 중 오류: {e}")
    st.stop()

# 탭 나누기
tab1, tab2 = st.tabs(["📝 시약 조제 (Preparation)", "사용 기록 (Usage)"])

# [Tab 1] 시약 조제 기록
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
                st.success(f"✅ [{name}] 조제 기록 저장 완료!")

    st.divider()
    st.subheader("6. 최근 조제 기록")
    try:
        data_prep = ws_prep.get_all_records()
        if data_prep:
            df_prep = pd.DataFrame(data_prep)
            if "작성일시" in df_prep.columns:
                df_prep = df_prep.sort_values(by="작성일시", ascending=False)
            st.dataframe(df_prep, use_container_width=True)
        else:
            st.info("기록 없음")
    except:
        st.info("데이터를 불러오는 중입니다...")

# [Tab 2] 시약 사용 기록
with tab2:
    st.subheader("시약 사용 대장")
    with st.form("usage_form", clear_on_submit=True):
        u_col1, u_col2 = st.columns(2)
        with u_col1:
            u_name = st.text_input("물질명")
            u_user = st.text_input("사용자")
        with u_col2:
            u_amount = st.text_input("사용량/내용")
            u_memo = st.text_input("비고")
        submitted_use = st.form_submit_button("사용 기록 저장")
        
        if submitted_use:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            row_data = [now_str, u_name, u_user, u_amount, u_memo]
            ws_usage.append_row(row_data)
            st.success("✅ 사용 기록 저장 완료!")
            
    st.divider()
    st.subheader("7. 최근 사용 기록")
    try:
        data_use = ws_usage.get_all_records()
        if data_use:
            df_use = pd.DataFrame(data_use)
            if "사용일시" in df_use.columns:
                df_use = df_use.sort_values(by="사용일시", ascending=False)
            st.dataframe(df_use, use_container_width=True)
        else:
            st.info("기록 없음")
    except:
         st.info("데이터를 불러오는 중입니다...")
