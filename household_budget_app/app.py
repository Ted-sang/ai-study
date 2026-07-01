"""Streamlit으로 만든 초보자용 가계부 웹 애플리케이션입니다."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from charts import create_monthly_chart
from data_manager import (
    add_transaction,
    calculate_summary,
    create_sample_data,
    csv_bytes_to_dataframe,
    dataframe_to_csv,
    filter_transactions,
)


# 웹 브라우저 탭 제목과 화면 폭을 설정합니다.
st.set_page_config(
    page_title="나의 가계부",
    page_icon="💰",
    layout="wide",
)


# Streamlit은 버튼을 누를 때마다 파일 전체를 다시 실행합니다.
# 따라서 session_state에 데이터를 보관하여 현재 가계부 내역을 유지합니다.
if "transactions" not in st.session_state:
    st.session_state.transactions = create_sample_data()


st.title("💰 나의 가계부 웹")
st.caption("Python · Pandas · Streamlit으로 만든 수입·지출 관리 프로그램")


# =========================================================
# 1단계: 수입·지출 입력 영역
# =========================================================
st.subheader("1. 수입·지출 입력")


# 수입·지출 선택은 form 밖에 둡니다.
# 선택값이 바뀌면 Streamlit 화면이 즉시 다시 실행되기 때문에
# 수입과 지출에 맞는 카테고리가 바로 나타납니다.
transaction_type = st.selectbox(
    "구분",
    ["지출", "수입"],
    key="transaction_type",
)


# 수입과 지출에서 사용할 카테고리를 각각 구분합니다.
category_options = {
    "지출": [
        "식비",
        "교통",
        "생활",
        "통신",
        "문화",
        "교육",
        "기타",
    ],
    "수입": [
        "급여",
        "부수입",
        "용돈",
        "기타",
    ],
}


# 나머지 입력 항목은 form 안에 넣습니다.
# 등록 버튼을 누를 때 한 번에 처리됩니다.
with st.form(
    "transaction_form",
    clear_on_submit=True,
):
    col1, col2, col3 = st.columns(3)

    with col1:
        transaction_date = st.date_input("날짜")

    with col2:
        # 선택한 구분이 수입인지 지출인지에 따라
        # 서로 다른 카테고리 목록을 보여 줍니다.
        category = st.selectbox(
            "카테고리",
            category_options[transaction_type],
            key=f"category_{transaction_type}",
        )

        amount = st.number_input(
            "금액(원)",
            min_value=0,
            step=1000,
        )

    with col3:
        description = st.text_input(
            "내용",
            placeholder="예: 점심 식사",
        )

        submitted = st.form_submit_button(
            "내역 등록",
            type="primary",
        )


# 등록 버튼을 눌렀을 때만 데이터 추가 함수를 실행합니다.
if submitted:
    try:
        st.session_state.transactions = add_transaction(
            st.session_state.transactions,
            transaction_date,
            transaction_type,
            category,
            description,
            int(amount),
        )

        st.success("가계부 내역이 등록되었습니다.")

    except ValueError as error:
        st.error(str(error))


# =========================================================
# 2단계: 가계 현황 요약
# =========================================================
st.divider()
st.subheader("2. 가계 현황 요약")


summary = calculate_summary(
    st.session_state.transactions
)

metric1, metric2, metric3 = st.columns(3)

metric1.metric(
    "총수입",
    f"{summary['총수입']:,}원",
)

metric2.metric(
    "총지출",
    f"{summary['총지출']:,}원",
)

metric3.metric(
    "현재 잔액",
    f"{summary['잔액']:,}원",
)


# =========================================================
# 3단계: 월별 수입·지출 그래프
# =========================================================
st.divider()
st.subheader("3. 월별 수입·지출 그래프")


if st.session_state.transactions.empty:
    st.info("그래프를 표시할 데이터가 없습니다.")

else:
    st.altair_chart(
        create_monthly_chart(
            st.session_state.transactions
        ),
        use_container_width=True,
    )


# =========================================================
# 4단계: 가계부 내역 조회 및 삭제
# =========================================================
st.divider()
st.subheader("4. 가계부 내역 조회")


filter_col1, filter_col2 = st.columns(2)


with filter_col1:
    selected_type = st.selectbox(
        "조회할 구분",
        ["전체", "수입", "지출"],
    )


with filter_col2:
    # 데이터가 없을 때도 오류가 발생하지 않도록 처리합니다.
    if st.session_state.transactions.empty:
        categories = []

    else:
        categories = sorted(
            st.session_state.transactions["카테고리"]
            .dropna()
            .unique()
            .tolist()
        )

    selected_category = st.selectbox(
        "조회할 카테고리",
        ["전체"] + categories,
    )


# 선택한 조건에 해당하는 데이터만 가져옵니다.
filtered_df = filter_transactions(
    st.session_state.transactions,
    selected_type,
    selected_category,
)


# 조회 결과가 없으면 안내 문구를 표시합니다.
if filtered_df.empty:
    st.info("조회 조건에 해당하는 가계부 내역이 없습니다.")

else:
    # 화면 표시용 복사본을 만듭니다.
    display_df = filtered_df.copy()

    # 날짜를 연도-월-일 형식으로 표시합니다.
    display_df["날짜"] = display_df[
        "날짜"
    ].dt.strftime("%Y-%m-%d")

    # 금액에 천 단위 쉼표를 표시합니다.
    display_df["금액"] = display_df[
        "금액"
    ].map(lambda value: f"{value:,}")

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )


# 원본 데이터의 행 번호를 선택하여 삭제합니다.
if not st.session_state.transactions.empty:

    delete_options = {
        (
            f"{index}번 | "
            f"{row['날짜']:%Y-%m-%d} | "
            f"{row['구분']} | "
            f"{row['내용']} | "
            f"{row['금액']:,}원"
        ): index
        for index, row
        in st.session_state.transactions.iterrows()
    }

    selected_delete_label = st.selectbox(
        "삭제할 내역 선택",
        ["선택하지 않음"]
        + list(delete_options.keys()),
    )

    if st.button("선택 내역 삭제"):

        if selected_delete_label == "선택하지 않음":
            st.warning(
                "삭제할 내역을 먼저 선택해 주세요."
            )

        else:
            delete_index = delete_options[
                selected_delete_label
            ]

            st.session_state.transactions = (
                st.session_state.transactions
                .drop(index=delete_index)
                .reset_index(drop=True)
            )

            st.success(
                "선택한 내역을 삭제했습니다."
            )

            st.rerun()


# =========================================================
# 5단계: CSV 저장 및 불러오기
# =========================================================
st.divider()
st.subheader("5. 데이터 저장·불러오기")


left, right = st.columns(2)


with left:
    st.download_button(
        label="CSV 파일로 다운로드",
        data=dataframe_to_csv(
            st.session_state.transactions
        ),
        file_name="가계부_데이터.csv",
        mime="text/csv",
    )


with right:
    uploaded_file = st.file_uploader(
        "기존 CSV 불러오기",
        type=["csv"],
    )

    if (
        uploaded_file is not None
        and st.button("업로드 파일 적용")
    ):
        try:
            st.session_state.transactions = (
                csv_bytes_to_dataframe(
                    uploaded_file.getvalue()
                )
            )

            st.success(
                "CSV 데이터를 불러왔습니다."
            )

            st.rerun()

        except (
            ValueError,
            UnicodeDecodeError,
            pd.errors.ParserError,
        ) as error:
            st.error(
                f"CSV 파일을 확인해 주세요: {error}"
            )


# 데이터 저장 방식에 대한 안내입니다.
st.info(
    "이 발표용 버전은 데이터를 브라우저 세션에 보관합니다. "
    "새로고침이나 연결 종료 시 초기화될 수 있으므로 "
    "중요한 데이터는 CSV로 다운로드하세요."
)
