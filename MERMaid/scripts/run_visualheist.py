import json
import sys
import os
import torch
import argparse
from visualheist.methods_visualheist import batch_pdf_to_figures_and_tables
from pathlib import Path
import time

#Relative paths in startup.json are resolved against the repository root
#Absolute paths are passed through untouched
REPO_ROOT = Path(__file__).resolve().parents[2]

def resolve_path(value, base=REPO_ROOT):
    """Return an absolute Path, resolving relative values against base."""
    path = Path(value).expanduser()
    return path if path.is_absolute() else (base / path)

starttime= time.time()

def load_config(config_file):
    """Load configurations from config_file

    :param config_file: Path to config file
    :type config_file: str
    :return: Returns a dictionary of fields from config_file
    :rtype: dict
    """
    config_file = Path(config_file)
    with open(config_file, 'r') as f:
        config = json.load(f)
    script_dir = config_file.parent
    parent_dir = script_dir.parent
    
    for key in ['default_image_dir', 'default_json_dir', 'default_graph_dir']:
        val = config.get(key)
        if val and not Path(val).is_absolute():
            config[key] = str((parent_dir / val).resolve())
    return config

def main():
    """
    This function orchestrates loading the configuration, reading the input PDF directory, and
    calling the batch PDF processing function to extract images from PDFs.

    :return: None
    """
    parser = argparse.ArgumentParser(description="Extract tables and figures from PDFs using VisualHeist.")
    parser.add_argument("--config", type=str, help="Path to the configuration file", default=None)
    parser.add_argument("--pdf_dir", type=str, help="Path to the input PDF directory", default=None)
    parser.add_argument("--image_dir", type=str, help="Path to the output image directory", default=None)
    parser.add_argument("--model_size", type=str, choices=["base", "large"], help="Model size to use", default=None)
    args = parser.parse_args()

    if args.config:
        config = load_config(Path(args.config))
    else:
        package_dir = Path(__file__).resolve().parent.parent
        config_path = package_dir / "scripts" / "startup.json"
        config = load_config(config_path) if config_path.exists() else {}

    pdf_dir = str(resolve_path(args.pdf_dir or config.get("pdf_dir", "./pdfs")))
    image_dir = str(resolve_path(
        args.image_dir or config.get("image_dir") or config.get("default_image_dir", "./images")))
    os.makedirs(image_dir, exist_ok=True)
    model_size = args.model_size or config.get('model_size', "base")
    print(f"Model size: {model_size}")
    use_large_model = model_size == "large"

    print(f"Processing PDFs in: {pdf_dir}")
    print(f"Saving images to: {image_dir}")
    print(f"Using {'LARGE' if use_large_model else 'BASE'} model.")

    batch_pdf_to_figures_and_tables(pdf_dir, image_dir, large_model=use_large_model)


if __name__ == "__main__":
    main()
     
endtime = time.time()
totaltime = endtime - starttime
print("Total VisualHeist Time = " +str(totaltime)+ " seconds!")

