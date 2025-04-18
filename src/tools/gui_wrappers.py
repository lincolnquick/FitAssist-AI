# src/tools/gui_wrappers.py
from src.visualize.plot_metrics import plot_metrics
import tempfile
import os
from PIL import Image

def generate_and_load_plots(df, periods, use_imperial=False):
    with tempfile.TemporaryDirectory() as tmpdir:
        plot_metrics(df, output_dir=tmpdir, periods=periods, use_imperial_units=use_imperial)

        plot_dict = {}
        for group in ["weight", "calories", "activity"]:
            images = []
            group_dir = os.path.join(tmpdir, group)
            if not os.path.exists(group_dir):
                continue
            for file in sorted(os.listdir(group_dir)):
                if file.endswith(".png"):
                    path = os.path.join(group_dir, file)
                    images.append((file, Image.open(path)))
            plot_dict[group] = images
        return plot_dict