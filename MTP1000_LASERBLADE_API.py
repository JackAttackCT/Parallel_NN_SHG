import pyvisa

class MTP1000_LASERBLADE_API:
    def __init__(self, ip, timeout=5000):
        """Initialize the VISA connection to the MTP1000 device."""
        self.ip = ip
        self.timeout = timeout
        self.resource_string = f"TCPIP::{self.ip}::INSTR"
        self.rm = pyvisa.ResourceManager('@py')
        self.connect()

    def connect(self):
        """Establish a connection to the device using VISA."""
        try:
            self.device = self.rm.open_resource(self.resource_string)
            self.device.timeout = self.timeout
            print(f"Connected to {self.ip}")
        except Exception as e:
            print(f"Error connecting to device: {e}")
            self.device = None

    def send_command(self, command):
        """Send an SCPI command to the device and return the response."""
        try:
            # Send the command with a terminator and get the response
            response = self.device.query(command)
            return response.strip()
        except pyvisa.VisaIOError as e:
            print(f"VISA I/O Error: {e}")
            return None
        except Exception as e:
            print(f"Error sending command: {e}")
            return None

    def send_write(self, command):
        """Send an SCPI command without expecting a response."""
        try:
            self.device.write(command)
        except pyvisa.VisaIOError as e:
            print(f"VISA I/O Error: {e}")
        except Exception as e:
            print(f"Error sending command: {e}")

    def close(self):
        """Close the VISA connection."""
        if self.device:
            self.device.close()
            print("Connection closed")

    def clear_status(self):
        """Send *CLS command to clear message queues."""
        return self.send_command("*CLS")

    def get_device_info(self):
        """Send *IDN? command to query device information."""
        return self.send_command("*IDN?")

    def check_operation_complete(self):
        """Send *OPC? command to check if operations are complete."""
        return self.send_command("*OPC?")

    def query_modules(self):
        """Send *OPT? command to query installed modules."""
        return self.send_command("*OPT?")

    def slot_idn(self, n):
        """Query the identifier for the slot."""
        return self.send_command(f":SLOT{n}:IDN?")

    def get_power(self, slot, channel):
        """Query the laser power on the specified slot and channel."""
        return self.send_command(f":SOURce{slot}:CHANnel{channel}:POWer?")

    def set_power(self, slot, channel, power):
        """Set the laser power on the specified slot and channel."""
        self.send_write(f":SOURce{slot}:CHANnel{channel}:POWer {power}")

    def get_output_state(self, slot, channel):
        """Query the output state of the laser."""
        return self.send_command(f":OUTPut{slot}:CHANnel{channel}:STATE?")

    def set_output_state(self, slot, channel, state):
        """Set the output state of the laser (ON or OFF)."""
        if state not in ["ON", "OFF"]:
            raise ValueError("State must be 'ON' or 'OFF'.")
        self.send_write(f":OUTPut{slot}:CHANnel{channel}:STATE {state}")

    def get_power_unit(self, slot, channel):
        """Query the power unit for the specified slot and channel."""
        return self.send_command(f":OUTPut{slot}:CHANnel{channel}:POWer:UNIT?")
    
    def get_wavelength(self, slot: int, channel: int) -> str:
        """Query the laser wavelength on the specified slot and channel."""
        command = f":SOURce{slot}:CHANnel{channel}:WAVElength?"
        return self.send_command(command)

    def set_wavelength(self, slot: int, channel: int, wavelength: float):
        """Set the laser wavelength on the specified slot and channel."""
        command = f":SOURce{slot}:CHANnel{channel}:WAVElength {wavelength}"
        self.send_write(command)

if __name__ == "__main__":
    # Example usage
    device_ip = "192.168.97.201"  # Replace with your device IP
    api = MTP1000_LASERBLADE_API(device_ip)

    # Set laser power
    api.set_power(1, 1, 10.5)
    print("Laser power set to 10.5")

    # Query actual power
    actual_power = api.get_power(1, 1)
    print(f"Actual Power: {actual_power}")

    # Query power unit
    power_unit = api.get_power_unit(1, 1)
    print(f"Power Unit: {power_unit}")

    # Set and query output state
    api.set_output_state(1, 1, "ON")
    print(f"Output State: {api.get_output_state(1, 1)}")

    # Close the connection
    api.close()
