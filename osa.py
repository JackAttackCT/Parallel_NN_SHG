import socket
import time
import subprocess
import platform
import matplotlib.pyplot as plt
import numpy as np
import csv

class OSA:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = None

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((self.host, self.port))
            # Check the OS type
            param = "-n" if platform.system().lower() == "windows" else "-c"
            # Use the system's ping command
            output = subprocess.check_output(
                ["ping", param, "1", self.host],
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            print(f"{self.host} is reachable, Connected to OSA")
        except subprocess.CalledProcessError:
            print(f"{self.host} is not reachable")
        except socket.error as e:
            print(f"Failed to connect to OSA: {e}")

    def autenticate(self):
        self.send_command('OPEN "anonymous"')
        response = self.receive_response()

        if response == 'AUTHENTICATE CRAM-MD5.\r\n':
            self.send_command('')
            response = self.receive_response()
            if response == 'ready\r\n':
                print('Successfully login!')
                return 1
            else:
                return -1
            
    def set_measurement_parameters(self, center_wavelength: str = "1200nm", span: str = "1080nm", sensitivity: str = "mid", spacing: str = "log", level: int = 10, resolution: float = 0.05):
        """
        Sets the measurement parameters for the OSA.

        :param center_wavelength: Center wavelength for the sweep (e.g., "1200nm").
        :param span: Span of the wavelength sweep (e.g., "1080nm").
        :param sensitivity: Sensitivity mode (e.g., "mid").
        """
        self.send_command("*RST")  # Reset the OSA
        self.send_command("CFORM1")  # Set command mode to AQ637X
        self.send_command(f":sens:wav:cent {center_wavelength}")
        self.send_command(f":sens:wav:span {span}")
        self.send_command(f":sens:sens {sensitivity}")
        self.send_command(f":disp:wind:trac:y1:scale:spac {spacing}")
        self.send_command(f":disp:wind:trac:y1:scale:rlev {level}uw")
        #self.send_command(":sens:sweep:points:auto on")  # Set sampling points to AUTO
        self.send_command(f":sens:band:res {resolution}nm")

    def perform_sweep(self):
        """
        Executes a single sweep on the OSA and waits for completion.
        """
        self.send_command(":init:smode 1")  # Single sweep mode
        self.send_command("*CLS")  # Clear status
        self.send_command(":init")  # Start sweep

        while True:
            self.send_command(":stat:oper:even?")
            response = self.receive_response()
            int_data = int(response.strip())
            if int_data & 1 == 1:  # Check if sweep is done (bit 0)
                break
            time.sleep(1)  # Wait before checking again
        print('Sweep complete.')

    def analyze_spectrum(self):
        """
        Analyzes the spectrum and retrieves the mean wavelength and spectrum width.
        
        :return: A tuple containing (mean_wavelength, spectrum_width).
        """
        self.send_command(":calc:category swth")  # Set analysis category to spectrum width
        self.send_command(":calc")  # Execute analysis
        self.send_command(":calc:data?")  # Request analysis data
        response = self.receive_response()

        # Extract and convert analysis results
        mean_wavelength = float(response[:16].strip())
        spectrum_width_str = response[18:34].strip().replace(',', '')

        try:
            spectrum_width = float(spectrum_width_str)
        except ValueError as e:
            print(f"Error converting spectrum width to float: {e}")
            spectrum_width = None

        return mean_wavelength, spectrum_width
    
    def get_trace(self):
        """
        Captures and plots the trace data from the OSA.
        """
        self.send_command(':TRACe:ACTive TRA')

        self.send_command(':TRACE:X? TRA')
        response = self.receive_response()
        wavelengths = [float(num) for num in response.split(',')]

        self.send_command(':TRACE:Y? TRA')
        response = self.receive_response()
        power = [float(num) for num in response.split(',')]

        return wavelengths, power
    
    def plot_trace(self, wavelengths, power):
        plt.figure()
        plt.plot(wavelengths, power)
        plt.xlabel('Wavelength (nm)')
        plt.ylabel('Power (W)')
        plt.title('OSA Trace')
        plt.grid(True)
        plt.show()

    def send_command(self, command):
        if self.sock:
            command += '\n'  # Add newline character to the command
            try:
                self.sock.sendall(command.encode('utf-8'))
            except socket.error as e:
                print(f"Error sending command: {e}")
        else:
            print("Connection not established. Please call connect() first.")

    def receive_response(self):
        if self.sock:
            data = b""
            while True:
                try:
                    chunk = self.sock.recv(1024)
                    data += chunk
                    if b'\n' in chunk:  # End of response
                        break
                except socket.error as e:
                    print(f"Error receiving response: {e}")
                    break
            return data.decode('utf-8')
        else:
            print("Connection not established. Please call connect() first.")
            return None
        
    def save_image(self, folder, name):
        """
        Captures and plots the trace data from the OSA and saves it to a CSV file.

        Args:
            filename (str, optional): The filename for the CSV file. Defaults to "trace_data.csv".
        """
        self.send_command(':TRACe:ACTive TRA')

        self.send_command(':TRACE:X? TRA')
        response = self.receive_response()
        wavelengths = [float(num) for num in response.split(',')]

        self.send_command(':TRACE:Y? TRA')
        response = self.receive_response()
        power = [float(num) for num in response.split(',')]

        # Plotting remains the same (optional)
        plt.figure()
        plt.plot(wavelengths, power)
        plt.xlabel('Wavelength (nm)')
        plt.ylabel('Power (W)')
        plt.title(f'{name}')
        plt.grid(True)
        plt.savefig(f'./{folder}/{name}.png')  # Save the figure
        plt.close()
        # plt.show()  # Comment out if you don't want to display the plot

        return power


    def save_trace(self, filename="trace_data.csv", show_plot = False):
        """
        Captures and plots the trace data from the OSA and saves it to a CSV file.

        Args:
            filename (str, optional): The filename for the CSV file. Defaults to "trace_data.csv".
        """
        self.send_command(':TRACe:ACTive TRA')

        self.send_command(':TRACE:X? TRA')
        response = self.receive_response()
        wavelengths = [float(num) for num in response.split(',')]

        self.send_command(':TRACE:Y? TRA')
        response = self.receive_response()
        power = [float(num) for num in response.split(',')]

        # Open the CSV file in write mode
        with open(filename, 'w', newline='') as csvfile:
            # Create a CSV writer object
            writer = csv.writer(csvfile)

            # Write the header row (optional)
            writer.writerow(["Wavelength (nm)", "Power (W)"])

            # Write each data point as a new row
            for i in range(len(wavelengths)):
                writer.writerow([wavelengths[i], power[i]])

        # Plotting remains the same (optional)
        if show_plot==True:
            plt.figure()
            plt.plot(wavelengths, power)
            plt.xlabel('Wavelength (nm)')
            plt.ylabel('Power (W)')
            plt.title('OSA Trace')
            plt.grid(True)
        
        # plt.show()  # Comment out if you don't want to display the plot

        return power

    def close_connection(self):
        if self.sock:
            try:
                self.sock.close()
                print("Connection closed")
            except socket.error as e:
                print(f"Error closing connection: {e}")
        else:
            print("Connection not established.")


    def perform_measurement_OSA(self, center, span, level, sensitivity = "high3", resolution = 0.02, spacing = "lin"):
        # === Set the measurement parameters ===
        self.set_measurement_parameters(center_wavelength = f"{center}nm", span = f"{span}nm", sensitivity=sensitivity, spacing = spacing, level = level, resolution=resolution)
            
        # === Sweep execute ===
        self.perform_sweep()

        # === Analysis ===
        #dbl_mean_wl, dbl_spec_wd = self.analyze_spectrum()
        #print(f"MEAN WL: {dbl_mean_wl * 1e9:.2f} nm")
        #print(f"SPEC WD: {dbl_spec_wd * 1e9:.2f} nm")

        wavelengths, power = self.get_trace()

        return wavelengths, power