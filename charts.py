"""가계부 그래프 생성 기능을 모아 둔 파일입니다."""

from __future__ import annotations

import altair as alt
import pandas as pd


def create_monthly_chart(df: pd.DataFrame) -> alt.Chart:
    """월별 수입과 지출을 비교하는 막대그래프를 만듭니다."""
    chart_data = df.copy()

    # 날짜에서 '연도-월' 문자열을 새로 만들어 월별 집계 기준으로 사용합니다.
    chart_data["월"] = chart_data["날짜"].dt.strftime("%Y-%m")

    # 같은 월과 같은 구분의 금액을 모두 더합니다.
    chart_data = (
        chart_data.groupby(["월", "구분"], as_index=False)["금액"]
        .sum()
        .sort_values("월")
    )

    # Altair는 데이터와 화면 표현 방식을 분리하여 그래프를 작성합니다.
    return (
        alt.Chart(chart_data)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("월:N", title="월"),
            y=alt.Y("금액:Q", title="금액(원)"),
            color=alt.Color("구분:N", title="구분"),
            xOffset="구분:N",
            tooltip=["월:N", "구분:N", alt.Tooltip("금액:Q", format=",")],
        )
        .properties(title="월별 수입·지출 비교", height=360)
    )
