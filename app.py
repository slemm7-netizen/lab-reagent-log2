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
        # 파일이 없으면 빈 데이터프레임 생성
        return pd.DataFrame(columns=[
            '조제 번호', '조제 일자', '작업자', 
            'Basal Media_Lot', 'FBS_Lot', 'Antibiotics_Lot', 
            '비고'
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
    today_batches = df[df['조제 번호'].astype(str).str.startswith(prefix)]
    
    if today_batches.empty:
        return f"{prefix}01"
    else:
        # 기존 번호 중 가장 큰 숫자를 찾아 +1
        last_ids = today_batches['조제 번호'].apply(lambda x: int(x.split('-')[-1]))
        next_num = last_ids.max() + 1
        return f"{prefix}{next_num:02d}"

def main():
    st.set_page_config(page_title="배양배지 조제 기록 관리", layout="wide")
    
    st.title("🧫 배양배지 조제 관리 시스템")

    # 데이터 로드
    df = load_data()

    # 탭 구성
    tab1, tab2 = st.tabs(["📝 배양배지 조제 정보 입력", "📋 사용 기록 및 수정"])

    # --- Sheet 1: 입력 ---
    with tab1:
        st.subheader("배양배지 조제 정보 입력")
        
        with st.form("media_form", clear_on_submit=True):
            # 1. 조제 번호 자동 생성 안내
            auto_batch_id = generate_batch_id(df)
            st.info(f"💡 이번에 생성될 조제 번호는 **{auto_batch_id}** 입니다.")
            
            col1, col2 = st.columns(2)
            with col1:
                date = st.date_input("조제 일자", datetime.now())
            with col2:
                operator = st.text_input("작업자 이름")
            
            st.markdown("---")
            st.write("#### 원료 Lot No.")
            
            lot_basal = st.text_input("1. 기본 배지 (Basal Media)")
            lot_fbs = st.text_input("2. FBS (Fetal Bovine Serum)")
            lot_antibiotics = st.text_input("3. Antibiotics (항생제)")
            
            st.markdown("---")
            notes = st.text_area("비고 (특이사항)")
            
            submitted = st.form_submit_button("저장하기", use_container_width=True)
            
            if submitted:
                if not operator:
                    st.error("작업자 이름을 입력해주세요.")
                else:
                    new_data = {
                        '조제 번호': auto_batch_id,
                        '조제 일자': date.strftime("%Y-%m-%d"),
                        '작업자': operator,
                        'Basal Media_Lot': lot_basal,
                        'FBS_Lot': lot_fbs,
                        'Antibiotics_Lot': lot_antibiotics,
                        '비고': notes
                    }
                    
                    new_df = pd.DataFrame([new_data])
                    df = pd.concat([df, new_df], ignore_index=True)
                    save_data(df)
                    
                    st.success(f"[{auto_batch_id}] 기록이 성공적으로 저장되었습니다!")
                    st.rerun()

    # --- Sheet 2: 기록 및 수정 ---
    with tab2:
        st.subheader("최근 사용 기록 (수정 가능)")
        
        if not df.empty:
            st.caption("1. 내용을 수정하려면 표를 더블 클릭하세요. / 2. 행을 삭제하려면 왼쪽 체크박스를 선택 후 Delete 키를 누르세요.")
            
            # 데이터 에디터
            edited_df = st.data_editor(
                df,
                column_config={
                    "조제 번호": st.column_config.TextColumn(disabled=True),
                    "Basal Media_Lot": "기본 배지 Lot",
                    "FBS_Lot": "FBS Lot",
                    "Antibiotics_Lot": "Antibiotics Lot",
                },
                use_container_width=True,
                num_rows="dynamic",
                key="data_editor"
            )
            
            col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 3])
            
            # 수정 저장 버튼
            with col_btn1:
                if st.button("💾 수정사항 저장", type="primary"):
                    save_data(edited_df)
                    st.success("수정 완료!")
                    st.rerun()
            
            # 전체 초기화 버튼 (테스트 후 사용)
            with col_btn2:
                if st.button("🗑️ 전체 데이터 삭제"):
                    # 빈 데이터프레임으로 덮어쓰기
                    empty_df = pd.DataFrame(columns=[
                        '조제 번호', '조제 일자', '작업자', 
                        'Basal Media_Lot', 'FBS_Lot', 'Antibiotics_Lot', 
                        '비고'
                    ])
                    save_data(empty_df)
                    st.warning("모든 데이터가 삭제되었습니다.")
                    st.rerun()

            # CSV 다운로드
            with col_btn3:
                csv = edited_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 CSV 다운로드",
                    data=csv,
                    file_name='culture_media_log.csv',
                    mime='text/csv',
                )

        else:
            st.info("데이터가 없습니다. 입력 탭에서 데이터를 추가하세요.")

if __name__ == "__main__":
    main()
