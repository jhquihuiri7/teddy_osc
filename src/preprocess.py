class ChanelProcessor:
    """
    Processes and buffers EEG frequency band data from Muse headset.
    
    The class handles:
    - Buffering of 5 different frequency bands (delta, theta, alpha, beta, gamma)
    - Detection of complete data records (when all 5 bands are received)
    - Data validation and type conversion
    - State management for data reception
    
    Usage:
    1. Create instance: processor = ChanelProcessor()
    2. Feed data: result = processor.process_data(data, channel_name)
    3. Complete records return as lists, otherwise returns None
    """
    
    def __init__(self):
        """Initializes the processor with empty buffers and state variables."""
        self.buffer = [None] * 5
        self.channel_received = set()
        self.current_record = []
        self.expecting_data = False
        self.data_count = 0
        self.channel_dict = {
            'delta_absolute': 0,
            'theta_absolute': 1,
            'alpha_absolute': 2,
            'beta_absolute': 3,
            'gamma_absolute': 4
        }


    def process_data(self, data, channel=None):
        """
        Processes incoming EEG frequency band data.
        
        Args:
            data (str): The data string to process (can be single value or comma-separated)
            channel (str, optional): The frequency band channel name
            
        Returns:
            list or None: Returns complete 5-element record when all bands are received,
                          otherwise returns None
                          
        Handles:
        - Comma-separated values (resets state if 3 values received)
        - Integer markers (signals start of new data sequence)
        - Floating point values (stores in appropriate buffer position)
        - Automatic record completion when all 5 bands are received
        """
        # If we receive a list of 3 elements (e.g. "1.0,1.0,1.0")
        if ',' in data:
            parts = data.split(',')
            if len(parts) == 3:  # End of record
                if self.current_record:
                    self.current_record = []
                self.expecting_data = False
                self.data_count = 0
            return
        
        # Convert the data to a number
        try:
            num = float(data)
            # If it's an integer (we consider 1.0 as integer)
            if num.is_integer():
                num = int(num)
        except ValueError:
            return  # Not a number, we ignore it
        
        # If it's an integer, we start expecting the next 5 elements
        if isinstance(num, int):
            self.expecting_data = True
            self.data_count = 0
            return

        # If we're expecting data and it's a float
        if self.expecting_data and isinstance(num, float):
            index = self.channel_dict[channel]
            self.buffer[index] = num
            self.channel_received.add(channel)
            
            # If we already have 5 elements, we save the record
            if len(self.channel_received) == 5:
                self.expecting_data = False
                data = self.buffer.copy()
                self.buffer = [None] * 5
                self.channel_received.clear()
                return data