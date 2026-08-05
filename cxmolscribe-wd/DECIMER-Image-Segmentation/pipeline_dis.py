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
import img2pdf

BASE_dir = Path.home()

#This script runs DECIMER-Image-Segmentation on images created from VisualHeist-Base

#Establishes input and output directories for running DECIMER-Image-Segmentation
imgdir = str(BASE_dir) + "/C-MAGE/cxmolscribe-wd/DECIMER-Image-Segmentation/CMAGE_VH_RESULTS/"
outputdir = str(BASE_dir) + "/C-MAGE/cxmolscribe-wd/DECIMER-Image-Segmentation/CMAGE_DIS_RESULTS/"

#The output directory is not part of the repository, so create it before the
#first segment is written.
os.makedirs(outputdir, exist_ok=True)

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
dis_df.to_excel("DIS_CMAGE_results.xlsx")

print("DECIMER-Image-Segmentation PIPELINE RESULTS COMPLETE!")

