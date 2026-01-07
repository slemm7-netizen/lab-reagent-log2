import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# =========================================================
# [사용자 설정] 이메일 적용 완료
# =========================================================
# 봇이 시트를 새로 만들면 이 주소로 공유해줍니다.
MY_GOOGLE_EMAIL = "slemm7@gmail.com"

# 기존 시트 ID (일단 이걸로 찾기 시도)
TARGET_SHEET_ID = "11716I3GkYFuB-lLEpD_Ciy76a9EAHwj69jGWsLMLpEc"
# =========================================================

# ---------------------------------------------------------
# [설정] 구글 시트 연동 함수
# ---------------------------------------------------------
def get_google_sheet_connection():
    try:
        # 봇이 파일을 생성하고 공유하려면 'drive' 권한이 필수입니다.
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        
        # Secrets 처리 (줄바꿈 문자 에러 방지)
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
        st.error(f"⚠️ 구글 연결 실패! Secrets 설정을 확인해주세요.\n에러 내용: {e}")
        st.stop()

# ---------------------------------------------------------
# [메인] 앱 화면 구성
# ---------------------------------------------------------
st.set_page_config(page_title="팀 시약 관리 시스템", page_icon="🧪", layout="wide")
st.title("🧪 팀 시약 조제 및 사용 기록")

# 구글 연결
gc = get_google_sheet_connection()

# ---------------------------------------------------------
# [핵심] 시트 연결 (없으면 생성하는 로직)
# ---------------------------------------------------------
try:
    # 1단계: 기존 ID로 연결 시도
    sh = gc.open_by_key(TARGET_SHEET_ID)
    
except Exception:
    # 2단계: 실패 시 (권한 문제 등), 봇이 직접 새로 생성
    st.warning(f"⚠️ 기존 시트({TARGET_SHEET_ID})에 접근할 수 없어, 봇이 새로운 시트를 생성합니다...")
    
    try:
        # 새 시트 생성
        new_sheet_name = "팀_시약관리_대장(봇생성)"
        sh = gc.create(new_sheet_name)
        
        # 사용자에게 공유 (편집 권한 부여)
        sh.share(MY_GOOGLE_EMAIL, perm_type='user', role='writer')
        
        st.success(f"""
        ✅ **새로운 시트가 생성되었습니다!**
        
        1. 구글 드라이브(Drive)에 가시면 **[{new_sheet_name}]** 파일이 생겼을 겁니다.
        2. 봇이 **{MY_GOOGLE_EMAIL}** 계정으로 편집 권한을 공유했습니다.
        """)
    except Exception as e_create:
        st.error(f"❌ 새 시트 생성 실패! Google Drive API가 켜져 있는지 확인하세요.\n에러: {e_create}")
        st.stop()

# ---------------------------------------------------------
# [워크시트 확인 및 탭 구성]
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
    st.error(f"워크시트 설정 중 오류 발생: {e}")
    st.stop
