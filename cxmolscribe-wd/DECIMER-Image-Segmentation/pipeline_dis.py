import os
import pandas as pd
import numpy as np
import tensorflow as tf
from pdf2image import convert_from_path
from pathlib import Path
from PyPDF2 import PdfWriter, PdfReader
from PIL import Image
from decimer_segmentation import (
    segment_chemical_structures,
    segment_chemical_structures_from_file,
    load_model
        )
import time
import argparse
import img2pdf

#This script runs DECIMER-Image-Segmentation on images created from VisualHeist-Base

#Every path defaults to a location derived from this file rather than from
#$HOME or the working directory, so the repository can live anywhere and the
#script can be launched from anywhere. Overriding the defaults is what lets a
#single run be pointed at its own job directory.
DIS_DIR = Path(__file__).resolve().parent

parser = argparse.ArgumentParser(
    description="Segment chemical structures out of VisualHeist figure images.")
parser.add_argument("--input-dir", type=Path, default=DIS_DIR / "CMAGE_VH_RESULTS",
                    help="Directory of figure images produced by VisualHeist (stage 1).")
parser.add_argument("--output-dir", type=Path, default=DIS_DIR / "CMAGE_DIS_RESULTS",
                    help="Directory to write the segmented structure images into.")
parser.add_argument("--results-excel", type=Path, default=DIS_DIR / "DIS_CMAGE_results.xlsx",
                    help="Spreadsheet of segment paths, read by stage 3 (CXMolScribe).")
args = parser.parse_args()

#Establishes input and output directories for running DECIMER-Image-Segmentation
imgdir = str(args.input_dir)
outputdir = str(args.output_dir)

if not os.path.isdir(imgdir):
    raise SystemExit(
        f"Input directory does not exist: {imgdir}\n"
        "Run stage 1 (VisualHeist) first, or pass --input-dir.")

#The output directory is not part of the repository, so create it before the
#first segment is written.
os.makedirs(outputdir, exist_ok=True)
os.makedirs(args.results_excel.parent, exist_ok=True)

#Only real image files are handed to the segmenter. Dotfiles (.gitkeep, NFS
#silly-rename artifacts) and any stray non-image file are skipped, and the
#listing is sorted so repeated runs process pages in the same order.
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}

#Takes the images in the VisualHeist output directory and creates file paths for them
file_paths = []
for filename in sorted(os.listdir(imgdir)):
    if filename.startswith("."):
        continue
    fp = os.path.join(imgdir,filename)
    if not os.path.isfile(fp):
        continue
    if Path(filename).suffix.lower() not in IMAGE_SUFFIXES:
        continue
    file_paths.append(fp)

vh_file = 0

#Runs DECIMER-Image-Segmentation on the file paths establsihed in the previous step
starttime= time.time()

page_number = []
dis_results_fps = []
for paths in file_paths:
    #A string for the file path is created, this is used as the input to DECIMER-Image-Segmentation
    path: str = os.path.abspath(paths)
    segments = segment_chemical_structures_from_file(path, expand=True)
    
    #The name of the VisualHeist image, which DECIMER-Image-Segmentation is running on, is saved without the extension so that is can be implemented in the output's file name
    name = Path(paths)
    name_without_extension = name.stem
    if segments is None or len(segments) == 0:
    	print("FAILED NO SEGMENT = " + str(name_without_extension))
    vh_file += 1
    #For loop which creates an image from the DECIMER-Image-Segmentation and keeps its original document name in new image name
    for numeral,img in enumerate(segments):
        img_var = Image.fromarray(img)
        image_pathy = "Image_DIS_:VH_File:"+str(name_without_extension)+ "_molecule_"+ str(numeral)+ ".png"
        full_path = os.path.join(outputdir,image_pathy)
        img_var.save(full_path)
        #The image is saved with its respective file path in the output directory established above
        dis_results_fps.append(full_path)

endtime = time.time()
totaltime = endtime - starttime
print("Total DECIMER-Image-Segmentation Time = " +str(totaltime)+ " seconds!")

#A dataframe is created and the DECIMER-Image-Segmentation result's file paths are inserted under the "DIS Result File Paths" column header
#This dataframe is then turned into an excel file which is the input for CXMolScribe
dis_df = pd.DataFrame(dis_results_fps, columns = ["DIS Result File Paths"])
dis_df.to_excel(args.results_excel)

print("DECIMER-Image-Segmentation PIPELINE RESULTS COMPLETE!")

