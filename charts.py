"""
charts.py — Configurações visuais para Plotly
"""
import plotly.graph_objects as go
import plotly.express as px

DARK_BG    = "#0a0e1a"
CARD_BG    = "#0f1729"
BORDER     = "#1e2d40"
CYAN       = "#00d4ff"
GREEN      = "#00e676"
RED        = "#ff4d6d"
YELLOW     = "#ffd60a"
PURPLE     = "#b388ff"
ORANGE     = "#ff9100"
MUTED      = "#6b8aaa"
TEXT       = "#e0e6f0"

PALETTE = [CYAN, GREEN, YELLOW, ORANGE, PURPLE, RED, "#40c4ff", "#69f0ae"]

LAYOUT_BASE = dict(
    paper_bgcolor=DARK_BG,
    plot_bgcolor=CARD_BG,
    font=dict(family="IBM Plex Mono, monospace", color=TEXT, size=11),
    margin=dict(l=50, r=20, t=40, b=40),
    xaxis=dict(gridcolor=BORDER, zeroline=False, linecolor=BORDER),
    yaxis=dict(gridcolor=BORDER, zeroline=False, linecolor=BORDER),
    legend=dict(bgcolor=DARK_BG, bordercolor=BORDER, borderwidth=1),
)

def apply_theme(fig):
    fig.update_layout(**LAYOUT_BASE)
    return fig

def line_chart(df, title="", y_fmt=None):
    fig = go.Figure()
    for i, col in enumerate(df.columns):
        fig.add_trace(go.Scatter(
            x=df.index, y=df[col], name=col,
            line=dict(color=PALETTE[i % len(PALETTE)], width=1.5),
            hovertemplate=f"<b>{col}</b><br>%{{x}}<br>%{{y:.4f}}<extra></extra>"
        ))
    fig.update_layout(title=dict(text=title, font=dict(color=CYAN, size=13)), **LAYOUT_BASE)
    return fig

def bar_chart(x, y, title="", color=CYAN, orientation="v"):
    colors = [GREEN if v >= 0 else RED for v in y]
    if orientation == "v":
        fig = go.Figure(go.Bar(x=x, y=y, marker_color=colors))
    else:
        fig = go.Figure(go.Bar(x=y, y=x, orientation="h", marker_color=colors))
    fig.update_layout(title=dict(text=title, font=dict(color=CYAN, size=13)), **LAYOUT_BASE)
    return fig

def histogram(data, title="", color=CYAN, var_line=None, bins=80):
    fig = go.Figure(go.Histogram(
        x=data, nbinsx=bins,
        marker_color=color, opacity=0.75,
        hovertemplate="%{x:.4f}<br>Count: %{y}<extra></extra>"
    ))
    if var_line is not None:
        fig.add_vline(x=-var_line, line_color=RED, line_dash="dash",
                      annotation_text="VaR", annotation_font_color=RED)
    fig.update_layout(title=dict(text=title, font=dict(color=CYAN, size=13)), **LAYOUT_BASE)
    return fig

def heatmap(matrix, title=""):
    fig = go.Figure(go.Heatmap(
        z=matrix.values,
        x=matrix.columns.tolist(),
        y=matrix.index.tolist(),
        colorscale=[[0, RED], [0.5, DARK_BG], [1, GREEN]],
        zmid=0,
        text=matrix.round(2).values,
        texttemplate="%{text}",
        hovertemplate="%{y} × %{x}<br>%{z:.3f}<extra></extra>",
    ))
    fig.update_layout(title=dict(text=title, font=dict(color=CYAN, size=13)), **LAYOUT_BASE)
    return fig
