import re
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import time

def preprocess_log_to_csv():
    """
    Preprocesses a log file to extract EEG and elements data, 
    writing them to separate CSV files with timestamps.
    """
    
    # Archivos de entrada y salida
    input_file = 'log.txt'
    output_eeg_csv = 'eeg_data.csv'
    output_elements_csv = 'elements_data.csv'

    # Expresión regular para extraer números
    pattern = r'[-+]?\d*\.\d+|\d+'

    # Obtener el timestamp actual y configurar el incremento
    start_time = datetime.now()
    timestamp = start_time

    # Procesamiento
    with open(input_file, 'r') as file, \
         open(output_eeg_csv, 'w') as eeg_csv, \
         open(output_elements_csv, 'w') as elements_csv:

        # Escribir encabezados (incluyendo columna 'timestamp')
        eeg_csv.write('timestamp,TP9,Fp1,Fp2,TP10,DRL,REF\n')  # EEG + timestamp
        elements_csv.write('data\n')                          # Elements (sin cambios)

        for line in file:
            line = line.strip()

            # Procesar líneas /muse/eeg
            if line.startswith('/muse/eeg'):
                numbers = re.findall(pattern, line.split('->')[1])
                # Formato: timestamp,TP9,Fp1,Fp2,TP10,DRL,REF
                eeg_csv.write(f'"{timestamp.isoformat()}",{",".join(numbers)}\n')
                timestamp += timedelta(seconds=1)  # Incremento de 1 segundo

            # Procesar líneas /muse/elements/ (sin timestamp)
            elif line.startswith('/muse/elements/'):
                numbers = re.findall(pattern, line.split('->')[1])
                elements_csv.write(','.join(numbers) + '\n')

    print("¡Archivos CSV generados con timestamps!")
    print(f"- EEG: {output_eeg_csv} (columnas: timestamp, TP9, Fp1, Fp2, TP10, DRL, REF)")
    print(f"- Elements: {output_elements_csv} (columna: data)")

def plot_eeg_data():
    """
    Genera subplots verticales para cada canal EEG.
    """
    # Cargar datos
    df = pd.read_csv("eeg_data.csv")
    df = df.head(500)
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

    # Canales a graficar
    channels = ['TP9', 'Fp1', 'Fp2', 'TP10', 'DRL', 'REF']
    num_channels = len(channels)
    
    # Crear figura con subplots verticales
    fig, axes = plt.subplots(nrows=num_channels, ncols=1, figsize=(15, 10), sharex=True)
    fig.suptitle('EEG Signals Over Time', fontsize=16, y=1.02)

    # Graficar cada canal en su propio subplot
    for i, channel in enumerate(channels):
        ax = axes[i]
        ax.plot(df['timestamp'], df[channel], color='blue', linewidth=1)
        ax.set_ylabel(channel, rotation=0, ha='right', va='center')
        ax.grid(True)

    # Configuración común
    plt.xlabel('Timestamp')
    plt.tight_layout()
    plt.show()

class ChanelProcessor:
    def __init__(self):
        self.buffer = []
        self.current_record = []
        self.expecting_data = False
        self.data_count = 0

    def process_data(self, data):
        # Si recibimos una lista de 3 elementos (ej. "1.0,1.0,1.0")
        if ',' in data:
            parts = data.split(',')
            if len(parts) == 3:  # Fin del registro
                if self.current_record:
                    self.current_record = []
                self.expecting_data = False
                self.data_count = 0
            return
        
        # Convertimos el dato a número
        try:
            num = float(data)
            # Si es entero (como 1.0 lo consideramos como entero)
            if num.is_integer():
                num = int(num)
        except ValueError:
            return  # No es un número, lo ignoramos
        
        # Si es un entero, comenzamos a esperar los siguientes 5 elementos
        if isinstance(num, int):
            self.expecting_data = True
            self.data_count = 0
            return

        # Si estamos esperando datos y es un float
        if self.expecting_data and isinstance(num, float):
            self.current_record.append(num)
            self.data_count += 1
            
            # Si ya tenemos 5 elementos, guardamos el registro
            if self.data_count == 5:
                self.expecting_data = False
                data = self.current_record.copy()
                self.current_record = []   
                self.data_count = 0
                return data
