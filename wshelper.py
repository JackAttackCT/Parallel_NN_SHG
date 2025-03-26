import numpy as np
import wsapi
from typing import Union, TextIO, BinaryIO, Optional, Callable, Tuple

ws_name = 'ws0'
ws_config = './WS200224_4x16.wsconfig'
configs = {
    1: './WS200224_1x19.wsconfig', 
    4: './WS200224_4x16.wsconfig', 
    8: './WS200224_8x12.wsconfig', 
    10: './WS200224_10x10.wsconfig'
}

def create_wsp(arr: np.ndarray, file: Optional[Union[str, TextIO, BinaryIO]] = None) -> Union[str, TextIO, BinaryIO]:
    # Error checking
    assert len(arr.shape) == 2, "Expecting a rank-2 array, got rank-{rank}.".format(rank=len(arr.shape))
    assert arr.shape[1] == 4, "Expecting 4 parameters for each frequency, got {n}.".format(n=arr.shape[1])
    
    output = '\n'.join(map(lambda x: '\t'.join(map(lambda y: '%0.3f' % (y), x)), arr))
    if isinstance(file, TextIO) or isinstance(file, BinaryIO):
        # If given a file handle, write directly
        file.write(output)
    elif isinstance(file, str):
        # Otherwise create and write to file
        with open(file, 'w') as open_file:
            open_file.write(output)
    else:
        file = output
    return file

def np2bytes(arr: np.ndarray) -> bytes:
    buf = len(arr.shape).to_bytes(4, 'big', signed=False)
    for i in arr.shape:
        buf += i.to_bytes(4, 'big', signed=False)
    buf += arr.tobytes()
    return buf

def bytes2np(buf: bytes) -> np.ndarray:
    l = int.from_bytes(buf[0:4], byteorder='big', signed=False)
    shape = []
    for i in range(l):
        shape.append(int.from_bytes(buf[4 * (i + 1): 4 * (i + 2)], byteorder='big', signed=False))
    arr = np.frombuffer(buf[4 * (l + 1):])
    arr = arr.reshape(shape)
    return arr

def createWS(ws_config):
    print("Creating waveshaper...   ", end='')
    rc = wsapi.ws_create_waveshaper(ws_name, ws_config)
    print(wsapi.ws_get_result_description(rc).decode('UTF-8'))

def deleteWS():
    print("Deliting waveshaper...   ", end='')
    rc = wsapi.ws_delete_waveshaper(ws_name)
    print(wsapi.ws_get_result_description(rc).decode('UTF-8'))

def connect():
    print("Connecting to waveshaper...   ", end='')
    rc = wsapi.ws_open_waveshaper(ws_name)
    print(wsapi.ws_get_result_description(rc).decode('UTF-8'))

def disconnect():
    print("Disconnecting from waveshaper...   ", end='')
    rc = wsapi.ws_close_waveshaper(ws_name)
    print(wsapi.ws_get_result_description(rc).decode('UTF-8'))

def get_profile():
    print("Retrieving current profile...   ", end='')
    current_profile = wsapi.ws_get_profile(ws_name)
    if isinstance(current_profile, str):
        print('success')
        parsed_profile = np.array(
            [y for y in map(lambda x: np.fromstring(x, dtype=np.float64, sep='\t'), current_profile.split('\n')) if
             np.size(y) == 4]
        )
        return parsed_profile
    else:
        print(wsapi.ws_get_result_description(current_profile).decode('UTF-8'))
        return None

def apply_profile(arr: np.ndarray):
    try:
        print("Applying profile...   ", end='')
        rc = wsapi.ws_load_profile(ws_name, create_wsp(arr))
        print(wsapi.ws_get_result_description(rc).decode('UTF-8'))
    except Exception as e:
        print("Error: ", str(e))




def nm2thz(nm: float) -> float:
    """ Converts wavelength in nm to frequency in Hz. """
    return 299792.45 / nm

def db2ln(db: float) -> float:
    """ Converts dB to linear scale. """
    return np.pow(10, db / 10)

def ln2db(ln: float) -> float:
    """ Converts linear scale to dB. """
    try:
        if ln > 0:
            return np.log10(ln) * 10
        else:
            return -np.inf
    except:
        return -np.inf

def ln2db_clipped(ln: float) -> float:
    """ Converts linear scale to dB clipped at -50 dB. """
    return np.clip(ln2db(ln), -75, 0)

def np2bytes(arr: np.ndarray) -> bytes:
    """ Encode a numpy array into a byte array. """
    buf = len(arr.shape).to_bytes(4, 'big', signed=False)
    for i in arr.shape:
        buf += i.to_bytes(4, 'big', signed=False)
    buf += arr.tobytes()
    return buf

def bytes2np(buf: bytes) -> np.ndarray:
    """ Decode a byte array into a numpy array. """
    l = int.from_bytes(buf[0:4], byteorder='big', signed=False)
    shape = []
    for i in range(l):
        shape.append(int.from_bytes(buf[4 * (i + 1): 4 * (i + 2)], byteorder='big', signed=False))
    arr = np.frombuffer(buf[4 * (l + 1):])
    arr = arr.reshape(shape)
    return arr

class BoundFunc:
    """ A function with a domain. Inputs outside of the domain return None. """
    def __init__(self, _func: Callable[[float], Optional[Tuple[float, float]]], _min: float = -np.inf, _max: float = np.inf, _port: int = 1) -> None:
        self.func = _func
        self.min = _min
        self.max = _max
        self.port = _port
    
    def __call__(self, input: float) -> Optional[Tuple[float, float]]:
        if self.min <= input < self.max:
            return self.func(input)
        else:
            return None

def compose_func(default: Tuple[float, float, int], min:float, max:float, step: float, *funcs: BoundFunc) -> np.ndarray:
    """
    Combine multiple `BoundFunc`s and generate an array of input/output pairs

    Parameters
    ----------
    default : Tuple[float, float, int]
        the default output for values outside function domains
    min : float
        the lower bound of the input frequency (hz)
    max : float
        the upper bound of the input frequency (hz)
    step : float
        the distance between each input frequency (hz)
    *funcs : BoundFunc
        one of more bound functions that takes in put in frequency (hz) and outputs attenuation (linear), phase shift, and port

    Returns
    -------
    np.ndarray
        the resulting input/output pairs with

        frequency(hz) | attenuation (dB) | phase(radian) | port
    """
    domain = np.arange(min, max, step)
    result = np.tile(np.array([-ln2db_clipped(default[0]), default[1], default[2]]), (np.size(domain), 1))
    for func in funcs:
        discrete = list(map(func, domain))
        masked = np.ma.array(list(map(lambda x: np.array(default) if x is None else [-ln2db_clipped(x[0]), x[1], func.port], discrete))
                    , mask=list(map(lambda x: np.repeat(x is None, (3, )), discrete)))
        result[~np.ma.getmaskarray(masked)] = masked[~np.ma.getmaskarray(masked)]
        
    concat = np.concatenate([np.expand_dims(domain, -1), result], axis=1)
    return concat


def discretize_func(arr1: np.ndarray, arr2: np.ndarray, start: float, step: float, offset: int, port: int) -> BoundFunc:
    """ Create a `BoundFunc` using two arrays. """
    n = arr1.shape[0] - offset
    return BoundFunc(
        lambda x: (arr1[int(np.floor((x - start) / step + offset))], arr2[int(np.floor((x - start) / step + offset))]),
        _min=min(start, start + step * n),
        _max=max(start, start + step * n),
        _port=port
    )

def gaussian(mu, peak, phase, sigma):
    """ Define Gaussian signal generator """
    return lambda x: (peak * np.exp(-(x - mu)**2 / (2 * sigma**2)), phase)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Waveshaper utility')
    parser.add_argument('-c', '--config', metavar='path', required=False, type=str,
                        help='path to config file, will override other settings')
    parser.add_argument('-i', '--input', metavar='inputs', required=False, type=int,
                        help='number of inputs')

    args = parser.parse_args()
    if args.config is not None:
        ws_config = args.config
    elif args.input is not None:
        if args.input not in configs:
            raise argparse.ArgumentError(f'No default config file found for {args.input} inputs.')
        else:
            ws_config = configs[args.input]

    print("Creating waveshaper...   ", end='')
    rc = wsapi.ws_create_waveshaper(ws_name, ws_config)
    print(wsapi.ws_get_result_description(rc).decode('UTF-8'))

    try:
        connect()
        # Example usage
        profile = get_profile()
        if profile is not None:
            apply_profile(profile)
        disconnect()
    except KeyboardInterrupt:
        print("Deleting waveshaper...   ", end='')
        rc = wsapi.ws_delete_waveshaper(ws_name)
        print(wsapi.ws_get_result_description(rc).decode('UTF-8'))
        exit(0)
