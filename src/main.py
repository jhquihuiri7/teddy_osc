import flet as ft
import socket
from pythonosc import dispatcher, osc_server
from threading import Thread
from utils import generate_plot
from flet.plotly_chart import PlotlyChart
import logging
import time
from collections import deque

BACKGROUND_COLOR = "#111827"
CARD_COLOR = "#1f2937"
CARD_RADIUS = 10
CARD_PADDING = ft.padding.symmetric(horizontal=20, vertical=10)
BUTTON_PADDING = ft.padding.symmetric(horizontal=20, vertical=0)
ROW_ALIGNMENT = ft.MainAxisAlignment.SPACE_BETWEEN

MAX_LOG_LINES = 1000
log_buffer = deque(maxlen=MAX_LOG_LINES)
osc_servers = {}
log_box = None

# Función para obtener IP local
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

# Manejo de mensajes OSC
def osc_handler(address, *args):
    msg = f"{address} -> {args}"
    log_buffer.append(msg)
    with open("log.txt", "a") as file:
        file.write(msg + "\n")

# Hilo que actualiza la UI desde el buffer
def log_updater():
    while True:
        if log_box and log_buffer:
            while log_buffer:
                msg = log_buffer.popleft()
                if len(log_box.controls) >= MAX_LOG_LINES:
                    log_box.controls.pop(0)
                log_box.controls.append(ft.Text(msg, size=12, color="#267443", font_family="Roboto Mono"))
            log_box.update()
        time.sleep(0.2)

def start_osc_server(port):
    if port in osc_servers:
        return
    disp = dispatcher.Dispatcher()
    disp.set_default_handler(osc_handler)
    server = osc_server.ThreadingOSCUDPServer(("0.0.0.0", port), disp)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    osc_servers[port] = server

def stop_osc_server(port):
    if port in osc_servers:
        osc_servers[port].shutdown()
        del osc_servers[port]

def main(page: ft.Page):
    page.title = "OSC Data Monitor"
    page.bgcolor = BACKGROUND_COLOR
    page.horizontal_alignment = "center"
    page.scroll = ft.ScrollMode.AUTO
    page.padding = CARD_PADDING

    global log_box
    log_box = ft.Column(auto_scroll=True, expand=True, scroll=ft.ScrollMode.ADAPTIVE)

    ip_text = ft.Text(f"{get_local_ip()}", size=14, color="#7e8bc0", weight="bold")

    common_ports = ft.Dropdown(
        width=160,
        options=[ft.dropdown.Option(str(p)) for p in [3333, 8338, 8000, 9000]],
        value="3333",
        bgcolor=ft.Colors.BLUE_GREY_800,
        color=ft.Colors.WHITE,
        border_color=ft.Colors.TRANSPARENT
    )

    listening_ports = ft.Dropdown(
        width=160,
        hint_text="Now Listening...",
        bgcolor=ft.Colors.BLUE_GREY_800,
        color=ft.Colors.WHITE,
        border_color=ft.Colors.TRANSPARENT
    )

    def update_layout(e=None):
        page_width = page.window.width
        top_controls.width = page_width / 2 - 40
        osc_graph.width = page_width / 2 - 40
        live_log.width = page_width / 2 - 80
        page.update()

    def add_port_click(e):
        try:
            port = int(common_ports.value)
            start_osc_server(port)
            if str(port) not in [opt.key for opt in listening_ports.options]:
                listening_ports.options.append(ft.dropdown.Option(str(port)))
                listening_ports.update()
                log_buffer.append(f"Listening to port: {port}")
        except Exception as ex:
            log_buffer.append(f"Error: {ex}")

    def stop_port_click(e):
        if listening_ports.value:
            port = int(listening_ports.value)
            stop_osc_server(port)
            listening_ports.options = [opt for opt in listening_ports.options if opt.key != str(port)]
            listening_ports.update()
            log_buffer.append(f"Stopped listening to port: {port}")

    top_controls = ft.Container(
        content=ft.Column([
            ft.Text("Connection Settings", size=16, weight="bold", color=ft.Colors.WHITE),
            ft.Row([
                ft.Text("List with common OSC ports:", color=ft.Colors.BLUE_GREY_200),
                common_ports,
                ft.CupertinoButton("Add Port", on_click=add_port_click, bgcolor="#4f46e5", color="white", icon=ft.Icons.ADD, icon_color="white", padding=BUTTON_PADDING, border_radius=CARD_RADIUS)
            ], alignment=ROW_ALIGNMENT),
            ft.Row([
                ft.Text("Now listening to OSC ports:", color=ft.Colors.BLUE_GREY_200),
                listening_ports,
                ft.CupertinoButton("Stop Listening", on_click=stop_port_click, bgcolor="#dc2626", color="white", icon=ft.Icons.STOP_CIRCLE, icon_color="white", padding=BUTTON_PADDING, border_radius=CARD_RADIUS)
            ], alignment=ROW_ALIGNMENT),
        ]),
        bgcolor=CARD_COLOR,
        padding=CARD_PADDING,
        border_radius=CARD_RADIUS,
        width=page.window.width / 2 - 40
    )

    live_log = ft.Container(
        content=log_box,
        bgcolor=ft.Colors.BLACK,
        padding=10,
        border_radius=5,
        height=300,
        width=page.window.width / 2 - 80
    )

    osc_graph = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("OSC Message Visualization (Placeholder)", color=ft.Colors.CYAN_200, size=14),
                PlotlyChart(generate_plot(), expand=True)
            ]
        ),
        bgcolor=CARD_COLOR,
        padding=CARD_PADDING,
        border_radius=CARD_RADIUS,
        height=460,
        width=page.window.width / 2 - 40
    )

    is_downloading = False

    def toggle_download(e):
        nonlocal is_downloading
        is_downloading = not is_downloading
        download_button.text = "Stop Downloading" if is_downloading else "Start Downloading"
        log_buffer.append("Started downloading log..." if is_downloading else "Stopped downloading log.")
        download_button.update()

    download_button = ft.CupertinoButton(
        "Start Downloading",
        bgcolor=ft.Colors.GREEN_600,
        color="white",
        icon=ft.Icons.DOWNLOAD,
        icon_color="white",
        border_radius=CARD_RADIUS,
        padding=BUTTON_PADDING,
        on_click=toggle_download
    )

    page.on_resized = update_layout

    page.add(
        ft.Column([
            ft.Container(
                bgcolor=CARD_COLOR,
                padding=CARD_PADDING,
                border_radius=CARD_RADIUS,
                content=ft.Row([
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.SETTINGS_INPUT_ANTENNA, size=20, color="#808bf7"),
                            ft.Text("Teddy OSC Data Monitor", size=20, weight="bold", color=ft.Colors.WHITE),
                        ]
                    ),
                    ft.Row(
                        controls=[
                            ft.Text("IP ADDRESS:", size=14, color=ft.Colors.WHITE),
                            ft.Container(content=ip_text, alignment=ft.alignment.center_right, expand=True, bgcolor="#374151", padding=5, border_radius=5)
                        ]
                    ),

                ], alignment="spaceBetween"),
            ),
            ft.Row([
                ft.Container(
                    content=ft.Column(
                        controls=[
                            top_controls,
                            ft.Container(
                                bgcolor=CARD_COLOR,
                                padding=CARD_PADDING,
                                border_radius=CARD_RADIUS,
                                content=ft.Column(
                                    controls=[
                                        ft.Text("Live Log", size=16, color=ft.Colors.WHITE),
                                        live_log,
                                    ]
                                )
                            )
                        ]
                    ),
                ),
                ft.Container(
                    content=ft.Column(
                        controls=[
                            osc_graph,
                            ft.Container(content=download_button, alignment=ft.alignment.center_right, padding=10)
                        ]
                    ),
                ),

            ], alignment="spaceBetween", vertical_alignment="start", spacing=20),
        ], spacing=20, expand=True),
    )

    # Inicia el hilo que actualiza el log en la UI
    Thread(target=log_updater, daemon=True).start()

if __name__ == "__main__":
    # Forzar modo desktop para evitar problemas
    ft.app(target=main, view=ft.AppView.FLET_APP)
