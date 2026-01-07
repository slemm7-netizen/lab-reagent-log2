import streamlit as st
import pandas as pd
from datetime import datetime
import os

# 데이터 파일 경로 설정
DATA_FILE = 'culture_media_log.csv'

# 데이터 불러오기 함수
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        # 파일이 없으면 빈 데이터프레임 생성 (컬럼 정의)
        return pd.DataFrame(columns=[
            '조제 번호', '조제 일자', '작업자', 
            '원료1_Lot', '원료2_Lot', '원료3_Lot', 
            'pH', '멸균 여부', '비고'
        ])

# 데이터 저장 함수
def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# 조제 번호 자동 생성 함수 (YYYYMMDD-CM-NN 형식)
def generate_batch_id(df):
    today_str = datetime.now().strftime("%Y%m%d") # 예: 20260107
    prefix = f"{today_str}-CM-"
    
    # 데이터가 비어있으면 첫 번째 번호 부여
    if df.empty:
        return f"{prefix}01"
    
    # 오늘 날짜로 생성된 번호가 있는지 확인
    # '조제 번호' 컬럼에서 오늘 날짜 prefix를 포함하는 행만 필터링
    today_batches = df[df['조제 번호'].astype(str).str.startswith(prefix)]
    
    if today_batches.empty:
        return f"{prefix}01"
    else:
        # 기존 번호 중 가장 큰 숫자를 찾아 +1 (순번 추출)
        # 예: 20260107-CM-02 -> 뒤의 02를 가져옴
        last_ids = today_batches['조제 번호'].apply(lambda x: int(x.split('-')[-1]))
        next_num = last_ids.max() + 1
        return f"{prefix}{next_num:02d}"

def main():
    st.set_page_config(page_title="배양배지 조제 기록 관리", layout="wide")
    
    st.title("🧫 배양배지 조제 관리 시스템")

    # 데이터 로드
    df = load_data()

    # --- 사이드바: 데이터 입력 ---
    with st.sidebar:
        st.header("배양배지 조제 정보 입력") # (나) 명칭 변경 반영
        
        with st.form("media_form", clear_on_submit=True):
            # (가) 조제 번호 자동 생성 로직 적용
            auto_batch_id = generate_batch_id(df)
            st.info(f"생성될 조제 번호: **{auto_batch_id}**")
            
            # 기본 정보
            date = st.date_input("조제 일자", datetime.now())
            operator = st.text_input("작업자 이름")
            
            st.markdown("---")
            
            # (다) & (라) 원료 Lot No. 입력 섹션 수정
            st.write("**원료 Lot No.**") 
            # 실제 사용하시는 원료명으로 아래 label을 수정하세요
            lot_1 = st.text_input("1. Glucose (글루코스)") 
            lot_2 = st.text_input("2. Yeast Extract (효모 추출물)")
            lot_3 = st.text_input("3. Peptone (펩톤)")
            
            st.markdown("---")
            
            # 기타 정보
            ph_value = st.number_input("pH 측정값", min_value=0.0, max_value=14.0, value=7.0, step=0.1)
            sterilization = st.selectbox("멸균 여부 (Autoclave)", ["Y", "N"])
            notes = st.text_area("비고 (특이사항)")
            
            submitted = st.form_submit_button("저장하기")
            
            if submitted:
                if not operator:
                    st.error("작업자 이름을 입력해주세요.")
                else:
                    # 새로운 데이터 추가
                    new_data = {
                        '조제 번호': auto_batch_id,
                        '조제 일자': date.strftime("%Y-%m-%d"),
                        '작업자': operator,
                        '원료1_Lot': lot_1,
                        '원료2_Lot': lot_2,
                        '원료3_Lot': lot_3,
                        'pH': ph_value,
                        '멸균 여부': sterilization,
                        '비고': notes
                    }
                    
                    # DataFrame에 추가 및 저장 (concat 사용 권장)
                    new_df = pd.DataFrame([new_data])
                    df = pd.concat([df, new_df], ignore_index=True)
                    save_data(df)
                    
                    st.success(f"[{auto_batch_id}] 기록이 저장되었습니다!")
                    st.rerun() # 데이터 갱신을 위해 리런

    # --- 메인 화면: 데이터 조회 ---
    # (마) 명칭 변경 반영
    st.subheader("최근 사용 기록") 

    if not df.empty:
        # 최신순으로 정렬 (인덱스 역순)
        st.dataframe(df.sort_index(ascending=False), use_container_width=True)
        
        # 다운로드 버튼
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="CSV로 다운로드",
            data=csv,
            file_name='culture_media_log.csv',
            mime='text/csv',
        )
    else:
        st.info("아직 저장된 기록이 없습니다. 사이드바에서 첫 번째 기록을 입력해주세요.")

if __name__ == "__main__":
    main()
