import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from numpy.polynomial.chebyshev import Chebyshev


def find_local_minima(x, y):
    """
    Find local minima in the data using scipy's find_peaks on inverted y-values.
    
    Parameters:
        x (list or array): The x-coordinates of the points (domain).
        y (list or array): The y-coordinates of the points (image).
    
    Returns:
        minima_x (array): x-values corresponding to the local minima.
        minima_y (array): y-values of the local minima.
    """
    # Invert y-values to find peaks which correspond to minima in the original data
    inverted_y = -np.array(y)
    
    # Use scipy's find_peaks to find local maxima in the inverted signal (i.e., local minima in original)
    minima_indices, _ = find_peaks(inverted_y, distance=10)

    # Get the corresponding x-values and y-values for the local minima
    minima_x = np.array(x)[minima_indices]
    minima_y = np.array(y)[minima_indices]

    return minima_x, minima_y


def fit_polynomial(x, y, order):
    """
    Fits a polynomial of a given order to the provided points.
    
    Parameters:
        x (list or array): x-coordinates of the points.
        y (list or array): y-coordinates of the points.
        order (int): The order of the polynomial to fit.

    Returns:
        p (ndarray): Polynomial coefficients, highest degree first.
        y_fit (ndarray): y-values of the fitted polynomial.
    """
    # Fit the polynomial to the data
    #p = np.polyfit(x, y, order)
    cheb_coeffs = Chebyshev.fit(x, y, order)
    
    # Generate the fitted polynomial's y-values using the coefficients
    
    return cheb_coeffs

def plot_polynomial_fit(x_orig, y_orig, x_fit, y_fit, order):
    """
    Plots the original points and the polynomial fit.
    
    Parameters:
        x (list or array): x-coordinates of the points.
        y (list or array): y-coordinates of the points.
        y_fit (list or array): y-values of the fitted polynomial.
        order (int): The order of the fitted polynomial.
    """
    y_fit=np.array(y_fit)
    y_fit[y_fit>np.max(y_orig)]=np.max(y_orig)
    y_fit[y_fit<np.min(y_orig)]=np.min(y_orig)
    plt.plot(x_orig, y_orig, color='red', label='Data Points')  # Original points
    #plt.scatter(x_opt, y_opt, color='blue', label='Opt Points')  # Original points
    plt.plot(x_fit, y_fit, color='green', label=f'Polynomial Fit (order {order})')  # Fitted polynomial
    
    plt.title(f'Polynomial Fit of Order {order}')
    plt.xlabel('wavelenght')
    plt.ylabel('power')
    plt.legend()
    plt.grid(True)
    plt.show()



def do_calibration(osa, center=775, span=2, order = 20, level=10, sensitivity = "high3", resolution = 0.02, spacing='lin'):
    wavelength, power = osa.perform_measurement_OSA(center, span, level, sensitivity, resolution, spacing=spacing)
    if spacing == 'log':
        power = np.array(power)
        power[power<-79]=-79
        power = power.tolist()
    x,y = find_local_minima(wavelength, power)

    # Fit polynomial and get the fitted y-values
    return wavelength, power, fit_polynomial(x, y, order)

def set_measurement_outside_range_to_zero(wavelength, measurement, min_wavelength, max_wavelength):
    """
    Sets values in the measurement array to zero where corresponding wavelength values are outside the specified range.
    
    Parameters:
    - wavelength (np.ndarray): Array of wavelength values.
    - measurement (np.ndarray): Array of measurement values corresponding to the wavelength array.
    - min_wavelength (float): Minimum wavelength for the valid range.
    - max_wavelength (float): Maximum wavelength for the valid range.
    
    Returns:
    - np.ndarray: Modified measurement array with values outside the wavelength range set to zero.
    """
    # Create a boolean mask where wavelength is within the specified range
    within_range = (wavelength >= min_wavelength) & (wavelength <= max_wavelength)
    
    # Set values in measurement array to zero where wavelength is outside the range
    measurement_outside_range = np.copy(measurement)
    measurement_outside_range[~within_range] = 0
    
    return measurement_outside_range
