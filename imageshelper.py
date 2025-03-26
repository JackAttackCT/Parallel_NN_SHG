import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import glob
import re

# Function to extract numerical parts for sorting
def numerical_sort_key(filename):
    return [int(part) for part in re.findall(r'\d+', filename)]

# Load data from a CSV file into a NumPy array
def load_csv_to_numpy(filename):
    data = np.genfromtxt(filename, delimiter=',', skip_header=1)  # Assuming the CSV has a header
    return data

# Plot data and save each plot as an image
def plot_data_and_save(data, filename):
    plt.figure()
    plt.plot(data[:, 0], data[:, 1])  # Modify this based on the structure of your data
    plt.xlabel('X-axis label')  # Set labels accordingly
    plt.ylabel('Y-axis label')
    plt.title(f'Trace {filename}')
    plt.savefig(filename)
    plt.close()

# Generate plots for multiple CSV files
def create_images_from_csvs(file_pattern, folder):
    # Get and sort files based on numerical parts in the filename
    files = sorted(glob.glob(file_pattern), key=numerical_sort_key)
    for i, csv_file in enumerate(files):
        data_array = load_csv_to_numpy(csv_file)
        image_filename = f'./{folder}/{csv_file}.png'
        plot_data_and_save(data_array, image_filename)
        print(f"Saved {image_filename}")

# Create a GIF from saved images
def create_gif(image_pattern, output_filename, duration=500):
    images = []
    files = sorted(glob.glob(image_pattern), key=numerical_sort_key)
    print(files)
    for filename in files:
        img = Image.open(filename)
        images.append(img)
        

    images[0].save(output_filename, save_all=True, append_images=images[1:], duration=duration, loop=0)
    print(f"GIF saved as {output_filename}")