import logging
from datetime import datetime
#from utils.logger import log_buffer
#from utils.charts import update_chart
from preprocess import ChanelProcessor

# Instancia única del procesador de canales
chanelProcessor = ChanelProcessor()

def osc_handler(address, *args):
    from utils import write_to_file  # evitar dependencia circular
    timestamp = datetime.now().isoformat()
    args_str = ', '.join(str(arg) for arg in args)
    msg = None

    try:
        if address.startswith("/muse/eeg"):
            msg = f"{timestamp},{args_str}"
            if len(args) >= 2:
                y_values = [float(arg) for arg in args]
                log_buffer.append(msg)
                update_chart(timestamp, y_values, type="eeg")

        elif address.startswith("/muse/elements/"):
            data = chanelProcessor.process_data(args_str)
            if data:
                args_str = ','.join(str(arg) for arg in data)
                msg = f"{timestamp},{args_str}"
                y_values = [float(value) for value in data[:5]]
                log_buffer.append(msg)
                update_chart(timestamp, y_values, type="channels")

        if msg:
            write_to_file("egg_new.txt", msg + "\n")

    except Exception as e:
        logging.error(f"Error processing OSC message: {e}")
