import numpy as np
import pandas as pd
import io
from os import path

from django.core.files.base import ContentFile


def process_pressure_csv(analysis_instance):
    # Calculate shape of expected csv based on equipment resolution
    frame_cols = analysis_instance.reading_equipment.product_info.resolution_width
    frame_rows = analysis_instance.reading_equipment.product_info.resolution_height
    sensors_per_frame = frame_rows * frame_cols
    sensor_area = 1.0  # Need to calculate

    csv_path = analysis_instance.pressure_reading.path
    chunk_frames = 500
    rows_per_chunk = chunk_frames * frame_rows

    pressure_threshold = analysis_instance.reading_equipment.user.personalised_threshold

    # Precompute coordinate grid for CoP
    y_coords, x_coords = np.indices((frame_rows, frame_cols))
    x_coords = x_coords.astype(np.float32)
    y_coords = y_coords.astype(np.float32)

    buffer = io.StringIO()

    columns = [
        "frame",
        "peak_pressure",
        "mean_pressure",
        "std_pressure",
        "peak_pressure_index",
        "coefficient_of_variation",
        "contact_area",
        "contact_area_percent",
        "cop_x",
        "cop_y"
    ]

    # Write CSV header
    buffer.write(",".join(columns) + "\n")

    frame_offset = 0

    # Read the CSV in chunks to handle large files without consuming too much memory
    for chunk in pd.read_csv(
            csv_path,
            header=None,
            chunksize=rows_per_chunk,
            dtype=np.float32
    ):

        data = chunk.values
        rows, cols = data.shape

        if cols != frame_cols:
            raise ValueError(f"CSV must have {frame_cols} columns")

        # Drop incomplete frames at the end of the chunk
        valid_rows = (rows // frame_rows) * frame_rows
        data = data[:valid_rows]

        num_frames = valid_rows // frame_rows

        frames = data.reshape(num_frames, frame_rows, frame_cols)

        flat = frames.reshape(num_frames, -1)

        # PRESSURE METRICS
        peak_pressure = np.max(flat, axis=1)
        mean_pressure = np.mean(flat, axis=1)
        std_pressure = np.std(flat, axis=1)

        ppi = peak_pressure / mean_pressure
        cv = std_pressure / mean_pressure

        # CONTACT AREA
        contact_mask = frames > pressure_threshold
        active_sensors = contact_mask.sum(axis=(1, 2))

        contact_area = active_sensors * sensor_area
        contact_percent = (active_sensors / sensors_per_frame) * 100

        # CENTER OF PRESSURE
        pressure_sum = np.sum(frames, axis=(1, 2))

        cop_x = np.sum(frames * x_coords, axis=(1, 2)) / pressure_sum
        cop_y = np.sum(frames * y_coords, axis=(1, 2)) / pressure_sum

        cop_x = np.nan_to_num(cop_x)
        cop_y = np.nan_to_num(cop_y)

        # STREAM RESULTS
        for i in range(num_frames):
            row = [
                frame_offset + i,
                peak_pressure[i],
                mean_pressure[i],
                std_pressure[i],
                ppi[i],
                cv[i],
                contact_area[i],
                contact_percent[i],
                cop_x[i],
                cop_y[i]
            ]

            buffer.write(",".join(map(str, row)) + "\n")

        frame_offset += num_frames

    raw_name = path.basename(analysis_instance.pressure_reading.name)
    name, ext = path.splitext(raw_name)

    metrics_filename = f"{name}_metrics{ext}"

    # Add metrics file to the model instance
    analysis_instance.metrics.save(
        metrics_filename,
        ContentFile(buffer.getvalue()),
        save=False
    )

    # Mark as processed and save
    analysis_instance.processed = True
    analysis_instance.save()
