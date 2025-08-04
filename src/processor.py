import csv
from collections import deque
from threading import Lock
import time
import os
from datetime import datetime

MAX_BUFFER_SIZE = 100  # Number of records in memory before writing to disk
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB maximum per file
LOG_DIRECTORY = "logs"

class BufferedFileWriter:
    """
    A thread-safe buffered file writer that writes data to CSV files with rotation.
    
    Attributes:
        file_prefix (str): Prefix for the log files
        buffer (deque): In-memory buffer to store records before writing to disk
        current_file (str): Path to the current active log file
        current_file_size (int): Size of the current log file in bytes
        header (list): Optional header for the CSV file
        lock (Lock): Thread lock for synchronization
    """
    
    def __init__(self, file_prefix, header=None):
        """Initialize the buffered file writer.
        
        Args:
            file_prefix (str): Prefix for the log files
            header (list, optional): Header row for the CSV file
        """
        self.file_prefix = file_prefix
        self.buffer = deque(maxlen=MAX_BUFFER_SIZE)
        self.current_file = None
        self.current_file_size = 0
        self.header = header
        self.lock = Lock()
        self.ensure_log_directory()
        self.rotate_file()
        
    def ensure_log_directory(self):
        """Ensure the log directory exists, create it if necessary"""
        if not os.path.exists(LOG_DIRECTORY):
            os.makedirs(LOG_DIRECTORY)
    
    def rotate_file(self):
        """Create a new log file with timestamp in the filename"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{LOG_DIRECTORY}/{self.file_prefix}_{timestamp}.csv"
        self.current_file = filename
        self.current_file_size = 0
        
        # Write headers if the file is new
        with open(filename, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", *self.header])  # Header for EEG
            # For channels.csv you could use a different header if preferred
    
    def write(self, data):
        """Add data to the buffer and write to disk if necessary
        
        Args:
            data: Data to be written to the log file
        """
        with self.lock:
            self.buffer.append(data)
            
            # Write to disk if buffer is full
            if len(self.buffer) >= MAX_BUFFER_SIZE:
                self.flush()
    
    def flush(self):
        """Write the buffer contents to the current file"""
        if not self.buffer:
            return
            
        with self.lock:
            try:
                # Check file size
                if self.current_file_size > MAX_FILE_SIZE:
                    self.rotate_file()
                
                # Write buffer to file
                with open(self.current_file, 'a', newline='') as f:
                    f.write("".join(self.buffer))
                    self.current_file_size = f.tell()  # Get current size
                
                self.buffer.clear()
            except Exception as e:
                print(f"Error writing to {self.file_prefix} file: {e}")