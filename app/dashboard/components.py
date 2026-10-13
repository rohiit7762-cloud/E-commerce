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
        fig.update_layout(
            title=dict(text="No Monthly Sales Data Available", font=dict(color="#94A3B8")),
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        return fig

    fig = go.Figure()

    # Gross Revenue Bars
    fig.add_trace(
        go.Bar(
            x=df["year_month"],
            y=df["gross_revenue"],
            name="Gross Revenue",
            marker=dict(color="#3B82F6", line=dict(color="#60A5FA", width=1)),
            opacity=0.9,
            hovertemplate="<b>Gross Revenue</b>: £%{y:,.2f}<extra></extra>",
        )
    )

    # Net Revenue Line
    fig.add_trace(
        go.Scatter(
            x=df["year_month"],
            y=df["net_revenue"],
            name="Net Revenue",
            mode="lines+markers",
            line=dict(color="#10B981", width=3),
            marker=dict(size=8, color="#34D399", line=dict(color="#065F46", width=2)),
            hovertemplate="<b>Net Revenue</b>: £%{y:,.2f}<extra></extra>",
        )
    )

    # Refund Bars (negative)
    if "refund_amount" in df.columns:
        fig.add_trace(
            go.Bar(
                x=df["year_month"],
                y=df["refund_amount"],
                name="Refunds / Returns",
                marker=dict(color="#EF4444", line=dict(color="#F87171", width=1)),
                opacity=0.85,
                hovertemplate="<b>Refunds</b>: £%{y:,.2f}<extra></extra>",
            )
        )

    fig.update_layout(
        title=dict(
            text="Monthly Revenue & Returns Trend",
            font=dict(size=16, color="#F8FAFC", family="Inter, sans-serif"),
            x=0.02,
            y=0.96,
        ),
        xaxis=dict(
            type="category",
            title=dict(text="Billing Period", font=dict(color="#94A3B8", size=12)),
            categoryorder="category ascending",
            gridcolor="rgba(255, 255, 255, 0.05)",
            tickfont=dict(color="#CBD5E1", size=11),
        ),
        yaxis=dict(
            title=dict(text="Amount (£)", font=dict(color="#94A3B8", size=12)),
            tickprefix="£",
            gridcolor="rgba(255, 255, 255, 0.07)",
            tickfont=dict(color="#CBD5E1", size=11),
        ),
        barmode="relative",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,23,42,0.45)",
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.22,
            xanchor="center",
            x=0.5,
            font=dict(size=12, color="#E2E8F0"),
            bgcolor="rgba(15,23,42,0.6)",
            bordercolor="rgba(255,255,255,0.1)",
            borderwidth=1,
        ),
        margin=dict(l=40, r=20, t=50, b=70),
        hovermode="x unified",
    )
    return fig


def build_top_products_chart(df: pd.DataFrame) -> go.Figure:
    """Create a horizontal bar chart of top products by net revenue."""
    if df.empty:
        fig = go.Figure()
        fig.update_layout(
            title=dict(text="No Product Performance Data Available", font=dict(color="#94A3B8")),
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        return fig

    display_df = df.head(10).sort_values("net_revenue", ascending=True).copy()
    display_df["label"] = display_df["description"].str.slice(0, 24) + " (" + display_df["stock_code"] + ")"

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
        text=display_df["net_revenue"].apply(lambda v: f"£{v:,.0f}"),
    )
    fig.update_traces(
        textposition="outside",
        textfont=dict(color="#E2E8F0", size=10),
        cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>Net Revenue: £%{x:,.2f}<extra></extra>",
    )
    fig.update_layout(
        title=dict(font=dict(size=15, color="#F8FAFC", family="Inter, sans-serif"), x=0.02),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,23,42,0.45)",
        margin=dict(l=20, r=50, t=40, b=30),
        coloraxis_showscale=False,
        xaxis=dict(
            title=dict(text="Net Revenue (£)", font=dict(color="#94A3B8", size=11)),
            tickprefix="£",
            gridcolor="rgba(255, 255, 255, 0.07)",
            tickfont=dict(color="#94A3B8", size=10),
        ),
        yaxis=dict(
            title="",
            tickfont=dict(color="#F8FAFC", size=11),
        ),
    )
    return fig


def build_regional_chart(df: pd.DataFrame) -> go.Figure:
    """Create a horizontal regional revenue distribution bar chart."""
    if df.empty:
        fig = go.Figure()
        fig.update_layout(
            title=dict(text="No Regional Data Available", font=dict(color="#94A3B8")),
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        return fig

    top_regions = df.head(10).sort_values("net_revenue", ascending=True).copy()
    fig = px.bar(
        top_regions,
        x="net_revenue",
        y="country",
        orientation="h",
        title="Top 10 International Markets by Net Revenue",
        labels={"country": "Country", "net_revenue": "Net Revenue (£)"},
        color="net_revenue",
        color_continuous_scale="Tealgrn",
        template="plotly_dark",
        text=top_regions["net_revenue"].apply(lambda v: f"£{v:,.0f}"),
    )
    fig.update_traces(
        textposition="outside",
        textfont=dict(color="#E2E8F0", size=10),
        cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>Net Revenue: £%{x:,.2f}<extra></extra>",
    )
    fig.update_layout(
        title=dict(font=dict(size=15, color="#F8FAFC", family="Inter, sans-serif"), x=0.02),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,23,42,0.45)",
        margin=dict(l=20, r=50, t=40, b=30),
        coloraxis_showscale=False,
        xaxis=dict(
            title=dict(text="Net Revenue (£)", font=dict(color="#94A3B8", size=11)),
            tickprefix="£",
            gridcolor="rgba(255, 255, 255, 0.07)",
            tickfont=dict(color="#94A3B8", size=10),
        ),
        yaxis=dict(
            title="",
            tickfont=dict(color="#F8FAFC", size=11),
        ),
    )
    return fig


def build_rejection_donut_chart(reasons_dict: Dict[str, int]) -> go.Figure:
    """Create a donut chart illustrating data quality quarantine reasons."""
    if not reasons_dict:
        fig = go.Figure()
        fig.update_layout(
            title=dict(text="Zero Rejections Recorded (100% Quality Score)", font=dict(color="#10B981")),
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        return fig

    labels = list(reasons_dict.keys())
    values = list(reasons_dict.values())

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.6,
                marker=dict(
                    colors=["#EF4444", "#F59E0B", "#8B5CF6", "#3B82F6", "#EC4899"],
                    line=dict(color="#0F172A", width=2),
                ),
                textinfo="label+percent",
                insidetextorientation="radial",
                hovertemplate="<b>%{label}</b><br>Rejected Records: %{value:,} (%{percent})<extra></extra>",
            )
        ]
    )
    fig.update_layout(
        title=dict(
            text="Data Quality Quarantine Reason Breakdown",
            font=dict(size=15, color="#F8FAFC", family="Inter, sans-serif"),
            x=0.02,
        ),
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.15,
            xanchor="center",
            x=0.5,
            font=dict(size=11, color="#CBD5E1"),
        ),
        margin=dict(l=10, r=10, t=50, b=60),
    )
    return fig
