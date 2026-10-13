"""Dashboard chart and UI visualization components using Plotly."""

from typing import Dict

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def format_currency(val: float) -> str:
    """Format floating point numbers into GBP currency strings."""
    return f"£{val:,.2f}"


def build_monthly_trends_chart(df: pd.DataFrame) -> go.Figure:
    """Create a dual-axis line/bar chart displaying gross revenue and refunds over time."""
    if df.empty:
        fig = go.Figure()
        fig.update_layout(title="No Monthly Sales Data Available")
        return fig

    fig = go.Figure()

    # Gross Revenue Bars
    fig.add_trace(
        go.Bar(
            x=df["year_month"],
            y=df["gross_revenue"],
            name="Gross Revenue",
            marker_color="#2563EB",  # Electric Blue
            opacity=0.85,
        )
    )

    # Net Revenue Line
    fig.add_trace(
        go.Scatter(
            x=df["year_month"],
            y=df["net_revenue"],
            name="Net Revenue",
            mode="lines+markers",
            line=dict(color="#10B981", width=3),  # Emerald Green
            marker=dict(size=8),
        )
    )

    # Refund Bars (negative)
    if "refund_amount" in df.columns:
        fig.add_trace(
            go.Bar(
                x=df["year_month"],
                y=df["refund_amount"],
                name="Refunds / Returns",
                marker_color="#EF4444",  # Crimson Red
                opacity=0.75,
            )
        )

    fig.update_layout(
        title="Monthly Revenue & Returns Trend",
        xaxis_title="Billing Month",
        yaxis_title="Amount (£)",
        barmode="relative",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,23,42,0.6)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=50, b=20),
        hovermode="x unified",
    )
    return fig


def build_top_products_chart(df: pd.DataFrame) -> go.Figure:
    """Create a horizontal bar chart of top products by net revenue."""
    if df.empty:
        fig = go.Figure()
        fig.update_layout(title="No Product Performance Data Available")
        return fig

    display_df = df.head(10).sort_values("net_revenue", ascending=True)
    # Truncate long descriptions
    display_df["label"] = display_df["description"].str.slice(0, 25) + " (" + display_df["stock_code"] + ")"

    fig = px.bar(
        display_df,
        x="net_revenue",
        y="label",
        orientation="h",
        title="Top 10 Products by Net Revenue",
        labels={"net_revenue": "Net Revenue (£)", "label": "Product"},
        color="net_revenue",
        color_continuous_scale="Viridis",
        template="plotly_dark",
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,23,42,0.6)",
        margin=dict(l=20, r=20, t=50, b=20),
        coloraxis_showscale=False,
    )
    return fig


def build_regional_chart(df: pd.DataFrame) -> go.Figure:
    """Create a regional revenue distribution bar chart."""
    if df.empty:
        fig = go.Figure()
        fig.update_layout(title="No Regional Data Available")
        return fig

    top_regions = df.head(10)
    fig = px.bar(
        top_regions,
        x="country",
        y="net_revenue",
        title="Top 10 International Markets by Net Revenue",
        labels={"country": "Country", "net_revenue": "Net Revenue (£)"},
        color="net_revenue",
        color_continuous_scale="Tealgrn",
        template="plotly_dark",
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,23,42,0.6)",
        margin=dict(l=20, r=20, t=50, b=20),
        coloraxis_showscale=False,
    )
    return fig


def build_rejection_donut_chart(reasons_dict: Dict[str, int]) -> go.Figure:
    """Create a donut chart illustrating data quality quarantine reasons."""
    if not reasons_dict:
        fig = go.Figure()
        fig.update_layout(title="Zero Rejections Recorded (100% Quality Score)")
        return fig

    labels = list(reasons_dict.keys())
    values = list(reasons_dict.values())

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.55,
                marker=dict(colors=["#EF4444", "#F59E0B", "#8B5CF6", "#3B82F6", "#EC4899"]),
            )
        ]
    )
    fig.update_layout(
        title="Data Quality Quarantine Reason Breakdown",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=40, b=10),
    )
    return fig
