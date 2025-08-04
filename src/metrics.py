from collections import deque
from datetime import datetime
from processor import BufferedFileWriter
import threading
import time

class MetricsCalculator:
    """A class for calculating metrics over a sliding time window.
    
    This class maintains a window of recent data points and computes various metrics
    based on the data within the specified time window.
    """
    
    def __init__(self, window_seconds=10):
        """Initialize the MetricsCalculator with a time window.
        
        Args:
            window_seconds (int, optional): The duration of the sliding time window 
                in seconds. Defaults to 10 seconds.
        """
        self.data_window = deque()
        self.last_calculation_time = None
        self.window_seconds = window_seconds
        self.metrics = ['bar', 'hai', 'tar', 'tbr', 'wi']
        self.writer = BufferedFileWriter("metrics", header=self.metrics)
        self.start_flush_threads()

    def start_flush_threads(self):
        """Starts a thread to periodically flush the buffered data to disk."""
        def flush_periodically(writer, interval=5):
            while True:
                time.sleep(interval)
                writer.flush()
        threading.Thread(target=flush_periodically, args=(self.writer,), daemon=True).start()

    def process(self, timestamp: str, alpha: float, beta: float, gamma: float, theta: float, delta: float):
        """Process a new data point and calculate metrics if needed.
        
        Handles a new data point by:
        1. Adding it to the sliding window
        2. Removing outdated data points
        3. Calculating metrics if the window period has elapsed
        
        Args:
            timestamp (str): ISO format timestamp string for the data point
            alpha (float): Alpha parameter value
            beta (float): Beta parameter value
            gamma (float): Gamma parameter value
            theta (float): Theta parameter value
            delta (float): Delta parameter value
            
        Returns:
            tuple: A tuple containing five calculated metrics (bar, hai, tar, tbr, wi) 
                if calculations were performed, otherwise (None, None, None, None, None).
                The metrics are:
                - bar: Beta to Alpha ratio
                - hai: (Beta + Gamma) to Alpha ratio
                - tar: Theta to Alpha ratio
                - tbr: Theta to Beta ratio
                - wi: (Delta + Theta) to Alpha ratio
        """
        now = datetime.fromisoformat(timestamp)
        self.data_window.append((now, alpha, beta, gamma, theta, delta))

        # Remove data outside the time window
        while self.data_window and (now - self.data_window[0][0]).total_seconds() > self.window_seconds:
            self.data_window.popleft()

        # Compute metrics if enough time has passed
        if self.last_calculation_time is None or (now - self.last_calculation_time).total_seconds() >= self.window_seconds:
            if len(self.data_window) > 0:
                alpha_vals = [a for _, a, _, _, _, _ in self.data_window]
                beta_vals = [b for _, _, b, _, _, _ in self.data_window]
                gamma_vals = [g for _, _, _, g, _, _ in self.data_window]
                theta_vals = [t for _, _, _, _, t, _ in self.data_window]
                delta_vals = [d for _, _, _, _, _, d in self.data_window]

                mean_alpha = sum(alpha_vals) / len(alpha_vals)
                mean_beta = sum(beta_vals) / len(beta_vals)
                mean_gamma = sum(gamma_vals) / len(gamma_vals)
                mean_theta = sum(theta_vals) / len(theta_vals)
                mean_delta = sum(delta_vals) / len(delta_vals)

                # Calculations
                bar = mean_beta / mean_alpha if mean_alpha != 0 else None
                hai = (mean_beta + mean_gamma) / mean_alpha if mean_alpha != 0 else None
                tar = mean_theta / mean_alpha if mean_alpha != 0 else None
                tbr = mean_theta / mean_beta if mean_beta != 0 else None
                wi = (mean_delta + mean_theta) / mean_alpha if mean_alpha != 0 else None

                # Save to file
                msg = f"{now},{bar},{hai},{tar},{tbr},{wi}\n"
                self.writer.write(msg)
                
                self.last_calculation_time = now
                return bar, hai, tar, tbr, wi

        return None, None, None, None, None