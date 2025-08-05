import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio


def generate_plot(height=100):
    """Generates a line chart widget with customizable height and default styling.
    
    Creates a Flet LineChart widget with the following characteristics:
    - No animation (instant rendering)
    - Empty data series (to be populated later)
    - Subtle border styling
    - Configured axes with label sizing
    - Tooltip styling
    - Expandable to fill available space
    
    Args:
        height (int, optional): The height of the chart in pixels. Defaults to 100.
        
    Returns:
        ft.LineChart: A configured Flet LineChart widget ready for data population.
    """
    import flet as ft
    return ft.LineChart(
        animate=ft.Animation(duration=0, curve=ft.AnimationCurve.LINEAR),
        data_series=[],
        border=ft.border.all(1, ft.Colors.with_opacity(0.2, ft.Colors.ON_SURFACE)),
        left_axis=ft.ChartAxis(
            labels_size=40,
        ),
        bottom_axis=ft.ChartAxis(
            labels_size=40,
        ),
        tooltip_bgcolor=ft.Colors.with_opacity(0.8, ft.Colors.BLUE_GREY),
        expand=True,
        height=height
    )


def process_csv_file(file_path):
    try:
        # Leer el archivo CSV
        df = pd.read_csv(file_path)
        
        # Limpiar datos
        df = df.dropna()
        if len(df) == 0:
            raise ValueError("El archivo CSV no contiene datos válidos")
        
        # Convertir timestamp
        try:
            df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%H:%M:%S')
        except:
            pass
        
        # Crear figura
        fig = go.Figure()
        
        columns = df.columns[1:]  # Excluir la columna de timestamp
        # Añadir cada serie al gráfico
        for i, col in enumerate(columns):
            fig.add_trace(go.Scatter(
                    x=df['timestamp'],
                    y=df[col],
                    name=col.upper(),
                    line=dict(width=2),
                    #mode='lines+markers'
                    )
                )
                
        # Configuración del layout
        fig.update_layout(
            title='Metrics Over Time',
            xaxis_title='Time',
            yaxis_title='Values',
            hovermode='x unified',
            height=700,
            xaxis=dict(
                tickangle=45,
                tickmode='auto',
                nticks=10,  # Número máximo de ticks en el eje X
                rangeslider=dict(visible=True)
            ),
        )
        
        # Guardar como HTML y abrir en navegador
        html_file = 'plotly_chart.html'
        pio.write_html(fig, file=html_file, auto_open=True)
        
    except Exception as e:
        print(f"Error processing CSV file: {e}")
        raise
