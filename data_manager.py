"""가계부 데이터 생성·검증·가공 기능을 모아 둔 파일입니다."""

from __future__ import annotations

from datetime import date
from io import StringIO

import pandas as pd


# 가계부에서 항상 사용할 열 이름을 한곳에서 관리합니다.
REQUIRED_COLUMNS = ["날짜", "구분", "카테고리", "내용", "금액"]


def create_sample_data() -> pd.DataFrame:
    """
    앱을 처음 실행할 때 빈 가계부 데이터를 만듭니다.

    예시 수입·지출 데이터를 넣지 않기 때문에
    총수입, 총지출, 현재 잔액이 모두 0원에서 시작합니다.
    """

    # 데이터 행은 없고 열 이름만 있는 빈 표를 만듭니다.
    empty_df = pd.DataFrame(columns=REQUIRED_COLUMNS)

    # 날짜 열을 날짜 형식으로 설정합니다.
    empty_df["날짜"] = pd.to_datetime(empty_df["날짜"])

    # 금액 열을 정수 형식으로 설정합니다.
    empty_df["금액"] = empty_df["금액"].astype(int)

    return empty_df


def prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """데이터 형식을 통일하고 잘못된 행을 정리합니다."""

    cleaned = df.copy()

    # 필요한 열이 빠졌는지 먼저 확인합니다.
    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in cleaned.columns
    ]

    if missing_columns:
        raise ValueError(
            f"필수 열이 없습니다: {', '.join(missing_columns)}"
        )

    # 필요한 열만 정해진 순서로 사용합니다.
    cleaned = cleaned[REQUIRED_COLUMNS]

    # 날짜와 금액을 계산 가능한 자료형으로 변환합니다.
    cleaned["날짜"] = pd.to_datetime(
        cleaned["날짜"],
        errors="coerce",
    )

    cleaned["금액"] = pd.to_numeric(
        cleaned["금액"],
        errors="coerce",
    )

    # 날짜 또는 금액 변환에 실패한 행은 제거합니다.
    cleaned = cleaned.dropna(
        subset=["날짜", "금액"]
    )

    cleaned["금액"] = cleaned["금액"].astype(int)

    # 구분은 수입과 지출만 허용합니다.
    cleaned = cleaned[
        cleaned["구분"].isin(["수입", "지출"])
    ]

    # 최신 내역이 위에 보이도록 정렬합니다.
    return cleaned.sort_values(
        "날짜",
        ascending=False,
    ).reset_index(drop=True)


def add_transaction(
    df: pd.DataFrame,
    transaction_date: date,
    transaction_type: str,
    category: str,
    description: str,
    amount: int,
) -> pd.DataFrame:
    """입력받은 한 건의 거래를 기존 데이터에 추가합니다."""

    if amount <= 0:
        raise ValueError("금액은 0보다 커야 합니다.")

    if not description.strip():
        raise ValueError("내용을 입력해 주세요.")

    new_row = pd.DataFrame(
        [
            [
                transaction_date,
                transaction_type,
                category,
                description.strip(),
                amount,
            ]
        ],
        columns=REQUIRED_COLUMNS,
    )

    return prepare_dataframe(
        pd.concat(
            [df, new_row],
            ignore_index=True,
        )
    )


def calculate_summary(df: pd.DataFrame) -> dict[str, int]:
    """총수입, 총지출, 잔액을 계산합니다."""

    income = int(
        df.loc[
            df["구분"] == "수입",
            "금액",
        ].sum()
    )

    expense = int(
        df.loc[
            df["구분"] == "지출",
            "금액",
        ].sum()
    )

    return {
        "총수입": income,
        "총지출": expense,
        "잔액": income - expense,
    }


def filter_transactions(
    df: pd.DataFrame,
    transaction_type: str,
    category: str,
) -> pd.DataFrame:
    """구분과 카테고리 선택값에 따라 데이터를 걸러냅니다."""

    filtered = df.copy()

    if transaction_type != "전체":
        filtered = filtered[
            filtered["구분"] == transaction_type
        ]

    if category != "전체":
        filtered = filtered[
            filtered["카테고리"] == category
        ]

    return filtered.reset_index(drop=True)


def dataframe_to_csv(df: pd.DataFrame) -> bytes:
    """다운로드 버튼에서 사용할 UTF-8 CSV 데이터를 만듭니다."""

    return df.to_csv(
        index=False,
        date_format="%Y-%m-%d",
    ).encode("utf-8-sig")


def csv_bytes_to_dataframe(
    file_bytes: bytes,
) -> pd.DataFrame:
    """사용자가 업로드한 CSV 파일을 DataFrame으로 변환합니다."""

    text = file_bytes.decode("utf-8-sig")

    return prepare_dataframe(
        pd.read_csv(
            StringIO(text)
        )
    )