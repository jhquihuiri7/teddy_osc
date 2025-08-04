# Teddy OSC Data Monitor

Teddy OSC is a user-friendly desktop application designed for real-time monitoring and visualization of Open Sound Control (OSC) data. It is particularly tailored for researchers, developers, and biofeedback enthusiasts working with EEG devices like the Muse headset. The application provides a graphical interface to inspect brainwave data streams, log them to files, and visualize different frequency bands (Delta, Theta, Alpha, Beta, Gamma) as they are received.

## Key Features

- **Real-Time Data Visualization**: View live charts of raw EEG signals and processed frequency bands.
- **Multi-Port Listening**: Configure the application to listen for OSC data on multiple network ports simultaneously.
- **Data Logging**: Automatically save incoming EEG and frequency band data to CSV files for offline analysis.
- **Intuitive UI**: A clean and responsive user interface built with the Flet framework.
- **Cross-Platform**: Built with Python and Flet, making it compatible with Windows, macOS, and Linux.
- **Core Technologies**: Python, Flet for the GUI, and `python-osc` for handling OSC messages.

## Project Structure

The project is organized to separate the user interface from the data processing logic.

```
.
├── src/
│   ├── assets/             # Icons and images for the application.
│   ├── main.py             # Main application entry point, UI, and OSC server logic.
│   ├── preprocess.py       # Pre-processing modules for OSC data.
│   ├── processor.py        # Core data processing and file writing logic.
│   ├── metrics.py          # Calculates metrics from the data.
│   ├── server.py           # (If used for server-side logic, seems empty/unused currently).
│   └── utils.py            # Utility functions, such as chart generation.
├── .gitignore
├── README.md               # This file.
├── requirements.txt        # Project dependencies.
└── pyproject.toml          # Project metadata and build configuration.
```

## Prerequisites

- Python 3.9 or higher.

## Setup Instructions

To run the Teddy OSC Data Monitor locally, follow these steps:

1.  **Clone the repository:**
    ```sh
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Create a virtual environment:**
    ```sh
    python -m venv venv
    ```

3.  **Activate the virtual environment:**
    -   **On Windows:**
        ```sh
        venv\Scripts\activate
        ```
    -   **On Linux/macOS:**
        ```sh
        source venv/bin/activate
        ```

4.  **Install dependencies:**
    The project dependencies are listed in `requirements.txt`. Install them using pip:
    ```sh
    pip install -r requirements.txt
    ```

5.  **Run the application:**
    ```sh
    flet run src/main.py
    ```

## Example Usage

Once the application is running:

1.  Your local IP address will be displayed at the top right. Configure your OSC data source (e.g., the Muse Direct application) to send data to this IP address.
2.  Use the "Connection Settings" panel to add the port your OSC source is broadcasting on (e.g., 3333, 8338). Click "Add Port".
3.  The application will start listening for data. You should see the "Live Log" updating with incoming messages.
4.  The charts will display the data in real-time. You can switch between the raw **EEG** signal view and the processed **CHANNELS** (frequency bands) view using the buttons at the top.
5.  Data is automatically logged into `.csv` files in the `eeg_data` and `channels_data` directories, created in the root of the project.
