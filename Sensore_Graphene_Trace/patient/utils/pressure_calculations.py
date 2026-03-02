import numpy as np
import pandas as pd

LOWER_THRESHOLD = 100
MIN_REGION_SIZE = 10
FRAME_SIZE = 32


def load_csv_frames(filepath):
    df = pd.read_csv(filepath, header=None)
    values = df.values.flatten()

    total_pixels = FRAME_SIZE * FRAME_SIZE
    num_frames = len(values) // total_pixels

    frames = []
    for i in range(num_frames):
        frame_data = values[i * total_pixels: (i + 1) * total_pixels]
        frame = frame_data.reshape(FRAME_SIZE, FRAME_SIZE).astype(int)
        frames.append(frame)

    return frames


def calculate_peak_pressure_index(frame):
    from scipy import ndimage

    threshold = np.percentile(frame, 75)
    high_pressure_mask = frame > threshold

    labeled_array, num_features = ndimage.label(high_pressure_mask)

    valid_peak = 1
    for region_id in range(1, num_features + 1):
        region_mask = labeled_array == region_id
        region_size = np.sum(region_mask)

        if region_size >= MIN_REGION_SIZE:
            region_max = np.max(frame[region_mask])
            if region_max > valid_peak:
                valid_peak = int(region_max)

    return valid_peak


def calculate_contact_area_percent(frame):
    total_pixels = FRAME_SIZE * FRAME_SIZE
    contact_pixels = np.sum(frame > LOWER_THRESHOLD)
    percentage = (contact_pixels / total_pixels) * 100
    return int(round(percentage))


def process_frame(frame):
    peak = calculate_peak_pressure_index(frame)
    contact = calculate_contact_area_percent(frame)
    return peak, contact