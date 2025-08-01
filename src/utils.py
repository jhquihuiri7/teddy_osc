import numpy as np
import plotly.express as px
import pandas as pd

def generate_plot():
    # Datos ficticios
    np.random.seed(0)
    x = np.linspace(0, 50, 200)
    y1 = np.sin(x / 2) * 30 + np.random.normal(0, 5, size=len(x)) + 50
    y2 = np.cos(x / 3) * 25 + np.random.normal(0, 5, size=len(x)) + 50

    # Crear DataFrame
    df = pd.DataFrame({
        "x": np.concatenate([x, x]),
        "value": np.concatenate([y1, y2]),
        "signal": ["Signal 1"] * len(x) + ["Signal 2"] * len(x)
    })

    # Crear gráfico con Plotly Express
    fig = px.line(
        df,
        x="x",
        y="value",
        color="signal",
        color_discrete_map={"Signal 1": "#00bcd4", "Signal 2": "#66ffcc"},
        template="plotly_dark"
    )

    fig.update_layout(
        showlegend=True,
        margin=dict(l=0, r=0, t=20, b=20),
        xaxis=dict(showticklabels=False),
        yaxis=dict(showticklabels=False),
        plot_bgcolor="#0d0d0d",
        paper_bgcolor="#0d0d0d",
    )

    return fig