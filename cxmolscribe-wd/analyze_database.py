import sys
import torch
import rdkit.Chem as Chem
from rdkit.Chem import Draw
import os
import pandas as pd
import numpy as np
import time
import cv2
from pathlib import Path
from openpyxl import load_workbook

"""
This file can be used to easily quanitfy user analysis on images with the "Molecular Images" classification
if the same nuances and classifications have been used as presented in this C-MAGE.
To expand this script beyond molecular images, some code will need to be commented out, these lines will be marked accordingly
"""

#Creates a dataframe from an organized and annotated sheet
#This organization is done by organize_category.py 
df = pd.read_excel("DECIMER-Image-Segmentation/CMAGE_mol.xlsx")#CHANGE WITH EACH CLASSIFICATION

#Takes correctness categorization from manual annotations of user dataset and puts it in a list
correctness_list = []
for num,correctness in enumerate(df["Holistic Molecule Interpretation"]):#CHECK TO MAKE SURE THIS IS THE RIGHT COLUMN TITLE
    correctness_list.append(correctness)
    if correctness == "":
        print("Blank at " +str(num))#Identifies any ungraded segmentations


#Puts Confidence classifications from user dataset in a list
ci_list = []
for ci in df["Confidence Classification"]:
    ci_list.append(ci)


#Takes the nuances in the molecular structures from the user dataset and puts them in a list
#If nuances are not present in the segmentation classification, or that analysis is not wished for, this code block will need to be commented out
nuance_list = []
for nuance in df["Nuances"]:        
    nuance_list.append(nuance)


#Quantifies confidence classifications
hc_count = 0
dis_count = 0
for interval in ci_list:
    if interval == "High Confidence of SMILES being correct":
        hc_count += 1
    elif interval == "Discard this SMILES prediction":
        dis_count += 1

print("==============================================")
print("High Confidence Count = " + str(hc_count))
print("Discarded Count = " + str(dis_count))
print("==============================================")
print("")

#Variables for each grade are established and the extracted grades are iterated through in order to compute their values

y = 0
s = 0
a = 0
n = 0
ns = 0
ys = 0
inval = 0
nm = 0

for term in correctness_list:
    if term == "Y":
        y += 1
    if term == "S":
        s += 1
    if term == "A":
        a += 1
    if term == "N":
        n += 1
    if term == "NS":
        ns += 1
    if term == "YS":
        ys += 1

#Computes the total molecular structures present
total_mol = y + n + a + s + ys + ns + inval

#Computes the total structures with only skeletal structure present
total_only_structure = ys+ns

#Computes the total structures with an appendix present
total_appendix = y + n + a + s

print("==============================================")
print("       Molecule Segmentations Grading         ")#"Molecule" will change depending on the classifcation being analyzed
print("==============================================")
print("Total Y, Holistically Correct = " + str(y))
print("Total S, Skeletal Structure Correct Only = " + str(s))
print("Total A, Appendix Correct Only = " + str(a))
print("Total N, Got Both S and A Wrong = " + str(n))
print("Total YS, got S right but no A = " + str(ys))
print("Total NS, got S wrong but no A = " + str(ns))
print("Total Molecules: " + str(total_mol))
print("Total Examples with Only Skeletal Structure = " + str(total_only_structure))
print("Total Examples with an Appendix: " + str(total_appendix))


#Values for each one of the grading metrics and their confidence classifications now become established
y_hc = 0
y_dis = 0
s_hc = 0
s_dis = 0
a_hc = 0
a_dis = 0
n_hc = 0
n_dis = 0
ns_hc = 0
ns_dis = 0
ys_hc = 0
ys_dis = 0

#The list of grades for each translation is iterated through and the grades relation the the confidence classification is stored
count = 0
for value in correctness_list:
        if correctness_list[count] =="Y" and ci_list[count] == "High Confidence of SMILES being correct":
            y_hc += 1
        elif correctness_list[count] =="S" and ci_list[count] == "High Confidence of SMILES being correct":
            s_hc += 1
        elif correctness_list[count] =="A" and ci_list[count] == "High Confidence of SMILES being correct":
            a_hc += 1
        elif correctness_list[count] =="N" and ci_list[count] == "High Confidence of SMILES being correct":
            n_hc += 1
        elif correctness_list[count] =="NS" and ci_list[count] == "High Confidence of SMILES being correct":
            ns_hc += 1
        elif correctness_list[count] =="YS" and ci_list[count] == "High Confidence of SMILES being correct":
            ys_hc += 1


        elif correctness_list[count]  =="Y" and ci_list[count] == "Discard this SMILES prediction":
            y_dis +=1
        elif correctness_list[count]  =="S" and ci_list[count] == "Discard this SMILES prediction":
            s_dis +=1
        elif correctness_list[count]  =="A" and ci_list[count] == "Discard this SMILES prediction":
            a_dis +=1
        elif correctness_list[count]  =="N" and ci_list[count] == "Discard this SMILES prediction":
            n_dis +=1
        elif correctness_list[count]  =="NS" and ci_list[count] == "Discard this SMILES prediction":
            ns_dis +=1
        elif correctness_list[count]  =="YS" and ci_list[count] == "Discard this SMILES prediction":
            ys_dis +=1
        count +=1

#Each translation grade and confidence classification is returned
print("Total Y & HC = " +str(y_hc))
print("Total S & HC = " +str(s_hc))
print("Total A & HC = " +str(a_hc))
print("Total N & HC = " +str(n_hc))
print("Total NS & HC = " +str(ns_hc))
print("Total YS & HC = " +str(ys_hc))
print("----------------------------------------------")
print("Total Y & DIS = " +str(y_dis))
print("Total S & DIS = " +str(s_dis))
print("Total A & DIS = " +str(a_dis))
print("Total N & DIS = " +str(n_dis))
print("Total NS & DIS = " +str(ns_dis))
print("Total YS & DIS = " +str(ys_dis))

print("")

#If the Molecular Image segmentation classification is not being analyzed, or not being analyzed using the same nuances established in the C-MAGE manuscript, comment out all of the nuance analysis.  This code goes until the trend analyssi block of code.
"""
print("==============================================")
print("~~~~~~      Nuance Analysis             ~~~~~~")
print("==============================================")


#Variables for all molecular image nuances presented in C-MAGE are created
col = 0
var = 0
screw = 0
ion = 0
cion = 0
bridge = 0
macro = 0
colcirc = 0
isotope = 0
bracket = 0
norm = 0
n3 = 0
arring = 0
radical = 0
squig = 0

#All nuances for the molecular image classification (inclduing when multiple are present in one image) are iterated through and their count is increased accordingly
for term2 in nuance_list:
    if term2 == "var":
        var += 1
    if term2 == "var&col":
        var += 1
        col += 1
    if term2 == "var&screw":
        var += 1
        screw += 1
    if term2 == "screw":
        screw += 1
    if term2 == "colcirc&screw":
        colcirc += 1
        screw += 1
    if term2 == "col&screw":
        col += 1
        screw += 1
    if term2 == "colcirc&screw&ion":
        colcirc += 1
        screw += 1
        ion += 1
    if term2 == "screw&bridge":
        bridge += 1
        screw += 1
    if term2 == "col&ion":
        col += 1
        ion += 1
    if term2 == "col&arring":
        col += 1
        arring += 1
    if term2 == "col&bridge":
        col += 1
        bridge += 1
    if term2 == "col&isotope":
        col += 1
        isotope += 1
    if term2 == "col&isotope&var":
        col += 1
        isotope += 1
        var += 1
    if term2 == "col&ion&cion":
        col += 1
        ion += 1
        cion += 1
    if term2 == "col&isotope&ion":
        col += 1
        isotope += 1
        ion += 1
    if term2 == "col&bracket":
        col += 1
        bracket += 1
    if term2 == "col&macro":
        col += 1
        macro += 1
    if term2 == "bridge&macro":
        bridge += 1
        macro += 1
    if term2 == "colcirc&bridge":
        bridge += 1
        colcirc += 1
    if term2 == "col&isotope&ion&var":
        col += 1
        isotope += 1
        ion += 1
        var += 1
    if term2 == "cion&bridge":
        cion += 1
        bridge += 1
    if term2 == "norm":
        norm += 1
    if term2 == "N3":
        n3 += 1
    if term2 == "isotope":
        isotope += 1
    if term2 == "col":
        col += 1
    if term2 == "colcirc":
        colcirc += 1
    if term2 == "arring":
        arring += 1
    if term2 == "bridge":
        bridge += 1
    if term2 == "cion":
        cion += 1
    if term2 == "ion":
        ion += 1
    if term2 == "bracket":
        bracket += 1
    if term2 == "radical":
        radical += 1
    if term2 == "macro":
        macro += 1
    if term2 == "squig":
        squig += 1
    if term2 == "squig&color":
        squig += 1
        col += 1
    if term2 == "squig&var":
        squig += 1
        var += 1
    if term2 == "squig&bridge":
        squig += 1
        bridge += 1

#The appearence values of each nuance is listed
print("Total Normal MoleculeAppearences = " +str(norm))
print("Total Variabe Text Appearences = " +str(var))
print("Total Colored Molecule Appearences = " +str(col))
print("Total Colored Circle Around Atom Appearences = " +str(colcirc))
print("Total Ion  Appearences = " +str(ion))
print("Total Isotope Appearences = " +str(isotope))
print("Total Counterion Appearences = " +str(cion))
print("Total Bridged Ring Appearences = " +str(bridge))
print("Total Bracket Group Repetition Appearences = " +str(bracket))
print("Total Text Inside of Ring Appearences = " +str(arring))
print("Total Macrocycles Appearences = " +str(macro))
print("Total Radical Appearences = " +str(radical))
print("Total Ring Stereochemistry Appearences = " +str(screw))
print("Total N3 Superatom Appearences = " +str(n3))
print("Total Undefined Stereochemistry Appearences = " +str(squig))

print("")

print("==============================================")
print("~~~~~~    Nuance Grade Analysis    ~~~~~~")
print("==============================================")

count2 = 0

#Variables for each nuance and its respective grade are established
var_y = 0
var_n = 0
var_a = 0
var_s = 0
var_ys = 0
var_ns = 0

screw_y = 0
screw_n = 0
screw_a = 0
screw_s = 0
screw_ys = 0
screw_ns = 0

col_y = 0
col_n = 0
col_a = 0
col_s = 0
col_ys = 0
col_ns = 0

ion_y = 0
ion_n = 0
ion_a = 0
ion_s = 0
ion_ys = 0
ion_ns = 0

cion_y = 0
cion_n = 0
cion_a = 0
cion_s = 0
cion_ys = 0
cion_ns = 0

bridge_y = 0
bridge_n = 0
bridge_a = 0
bridge_s = 0
bridge_ys = 0
bridge_ns = 0

macro_y = 0
macro_n = 0
macro_a = 0
macro_s = 0
macro_ys = 0
macro_ns = 0

colcirc_y = 0
colcirc_n = 0
colcirc_a = 0
colcirc_s = 0
colcirc_ys = 0
colcirc_ns = 0

isotope_y = 0
isotope_n = 0
isotope_a = 0
isotope_s = 0
isotope_ys = 0
isotope_ns = 0

bracket_y = 0
bracket_n = 0
bracket_a = 0
bracket_s = 0
bracket_ys = 0
bracket_ns = 0

norm_y = 0
norm_n = 0
norm_a = 0
norm_s = 0
norm_ys = 0
norm_ns = 0

n3_y = 0
n3_n = 0
n3_a = 0
n3_s = 0
n3_ys = 0
n3_ns = 0

arring_y = 0
arring_n = 0
arring_a = 0
arring_s = 0
arring_ys = 0
arring_ns = 0

radical_y = 0
radical_n = 0
radical_a = 0
radical_s = 0
radical_ys = 0
radical_ns = 0

squig_y = 0
squig_n = 0
squig_a = 0
squig_s = 0
squig_ys = 0
squig_ns = 0

#Each nuance and its grade are iterated through and their count is increased if present
for value2 in nuance_list:
        if correctness_list[count2] =="Y" and nuance_list[count2] == "var":
            var_y += 1
        elif correctness_list[count2] =="S" and nuance_list[count2] == "var":
            var_s += 1
        elif correctness_list[count2] =="A" and nuance_list[count2] == "var":
            var_a += 1
        elif correctness_list[count2] =="N" and nuance_list[count2] == "var":
            var_n += 1
        elif correctness_list[count2] =="NS" and nuance_list[count2] == "var":
            var_ns += 1
        elif correctness_list[count2] =="YS" and nuance_list[count2] == "var":
            var_ys += 1
        
        elif correctness_list[count2] =="Y" and nuance_list[count2] == "var&screw":
            var_y += 1
            screw_y += 1
        elif correctness_list[count2] =="S" and nuance_list[count2] == "var&screw":
            var_s += 1
            screw_s += 1
        elif correctness_list[count2] =="A" and nuance_list[count2] == "var&screw":
            var_a += 1
            screw_a += 1
        elif correctness_list[count2] =="N" and nuance_list[count2] == "var&screw":
            var_n += 1
            screw_n += 1
        elif correctness_list[count2] =="NS" and nuance_list[count2] == "var&screw":
            var_ns += 1
            screw_ns += 1
        elif correctness_list[count2] =="YS" and nuance_list[count2] == "var&screw":
            var_ys += 1
            screw_ys += 1

        elif correctness_list[count2] =="Y" and nuance_list[count2] == "var&col":
            var_y += 1
            col_y += 1
        elif correctness_list[count2] =="N" and nuance_list[count2] == "var&col":
            var_n += 1
            col_n += 1
        elif correctness_list[count2] =="A" and nuance_list[count2] == "var&col":
            var_a += 1
            col_a += 1
        elif correctness_list[count2] =="S" and nuance_list[count2] == "var&col":
            var_s += 1
            col_s += 1
        elif correctness_list[count2] =="YS" and nuance_list[count2] == "var&col":
            var_ys += 1
            col_ys += 1
        elif correctness_list[count2] =="NS" and nuance_list[count2] == "var&col":
            var_ns += 1
            col_ns += 1

        elif correctness_list[count2] =="Y" and nuance_list[count2] == "col":
            col_y += 1
        elif correctness_list[count2] =="N" and nuance_list[count2] == "col":
            col_n += 1
        elif correctness_list[count2] =="A" and nuance_list[count2] == "col":
            col_a += 1
        elif correctness_list[count2] =="S" and nuance_list[count2] == "col":
            col_s += 1
        elif correctness_list[count2] =="YS" and nuance_list[count2] == "col":
            col_ys += 1
        elif correctness_list[count2] =="NS" and nuance_list[count2] == "col":
            col_ns += 1

        elif correctness_list[count2] =="Y" and nuance_list[count2] == "norm":
            norm_y += 1
        elif correctness_list[count2] =="N" and nuance_list[count2] == "norm":
            norm_n += 1
        elif correctness_list[count2] =="A" and nuance_list[count2] == "norm":
            norm_a += 1
        elif correctness_list[count2] =="S" and nuance_list[count2] == "norm":
            norm_s += 1
        elif correctness_list[count2] =="YS" and nuance_list[count2] == "norm":
            norm_ys += 1
        elif correctness_list[count2] =="NS" and nuance_list[count2] == "norm":
            norm_ns += 1

        elif correctness_list[count2] =="Y" and nuance_list[count2] == "bracket":
            bracket_y += 1
        elif correctness_list[count2] =="N" and nuance_list[count2] == "bracket":
            bracket_n += 1
        elif correctness_list[count2] =="A" and nuance_list[count2] == "bracket":
            bracket_a += 1
        elif correctness_list[count2] =="S" and nuance_list[count2] == "bracket":
            bracket_s += 1
        elif correctness_list[count2] =="YS" and nuance_list[count2] == "bracket":
            bracket_ys += 1
        elif correctness_list[count2] =="NS" and nuance_list[count2] == "bracket":
            bracket_ns += 1

        elif correctness_list[count2] =="Y" and nuance_list[count2] == "isotope":
            isotope_y += 1
        elif correctness_list[count2] =="N" and nuance_list[count2] == "isotope":
            isotope_n += 1
        elif correctness_list[count2] =="A" and nuance_list[count2] == "isotope":
            isotope_a += 1
        elif correctness_list[count2] =="S" and nuance_list[count2] == "isotope":
            isotope_s += 1
        elif correctness_list[count2] =="YS" and nuance_list[count2] == "isotope":
            isotope_ys += 1
        elif correctness_list[count2] =="NS" and nuance_list[count2] == "isotope":
            isotope_ns += 1

        elif correctness_list[count2] =="Y" and nuance_list[count2] == "radical":
            radical_y += 1
        elif correctness_list[count2] =="N" and nuance_list[count2] == "radical":
            radical_n += 1
        elif correctness_list[count2] =="A" and nuance_list[count2] == "radical":
            radical_a += 1
        elif correctness_list[count2] =="S" and nuance_list[count2] == "radical":
            radical_s += 1
        elif correctness_list[count2] =="YS" and nuance_list[count2] == "radical":
            radical_ys += 1
        elif correctness_list[count2] =="NS" and nuance_list[count2] == "radical":
            radical_ns += 1

        elif correctness_list[count2] =="Y" and nuance_list[count2] == "macro":
            macro_y += 1
        elif correctness_list[count2] =="N" and nuance_list[count2] == "macro":
            macro_n += 1
        elif correctness_list[count2] =="A" and nuance_list[count2] == "macro":
            macro_a += 1
        elif correctness_list[count2] =="S" and nuance_list[count2] == "macro":
            macro_s += 1
        elif correctness_list[count2] =="YS" and nuance_list[count2] == "macro":
            macro_ys += 1
        elif correctness_list[count2] =="NS" and nuance_list[count2] == "macro":
            macro_ns += 1

        elif correctness_list[count2] =="Y" and nuance_list[count2] == "colcirc":
            colcirc_y += 1
        elif correctness_list[count2] =="N" and nuance_list[count2] == "colcirc":
            colcirc_n += 1
        elif correctness_list[count2] =="A" and nuance_list[count2] == "colcirc":
            colcirc_a += 1
        elif correctness_list[count2] =="S" and nuance_list[count2] == "colcirc":
            colcirc_s += 1
        elif correctness_list[count2] =="YS" and nuance_list[count2] == "colcirc":
            colcirc_ys += 1
        elif correctness_list[count2] =="NS" and nuance_list[count2] == "colcirc":
            colcirc_ns += 1

        elif correctness_list[count2] =="Y" and nuance_list[count2] == "arring":
            arring_y += 1
        elif correctness_list[count2] =="N" and nuance_list[count2] == "arring":
            arring_n += 1
        elif correctness_list[count2] =="A" and nuance_list[count2] == "arring":
            arring_a += 1
        elif correctness_list[count2] =="S" and nuance_list[count2] == "arring":
            arring_s += 1
        elif correctness_list[count2] =="YS" and nuance_list[count2] == "arring":
            arring_ys += 1
        elif correctness_list[count2] =="NS" and nuance_list[count2] == "arring":
            arring_ns += 1

        elif correctness_list[count2] =="Y" and nuance_list[count2] == "bridge":
            bridge_y += 1
        elif correctness_list[count2] =="N" and nuance_list[count2] == "bridge":
            bridge_n += 1
        elif correctness_list[count2] =="A" and nuance_list[count2] == "bridge":
            bridge_a += 1
        elif correctness_list[count2] =="S" and nuance_list[count2] == "bridge":
            bridge_s += 1
        elif correctness_list[count2] =="YS" and nuance_list[count2] == "bridge":
            bridge_ys += 1
        elif correctness_list[count2] =="NS" and nuance_list[count2] == "bridge":
            bridge_ns += 1

        elif correctness_list[count2] =="Y" and nuance_list[count2] == "N3":
            n3_y += 1
        elif correctness_list[count2] =="N" and nuance_list[count2] == "N3":
            n3_n += 1
        elif correctness_list[count2] =="A" and nuance_list[count2] == "N3":
            n3_a += 1
        elif correctness_list[count2] =="S" and nuance_list[count2] == "N3":
            n3_s += 1
        elif correctness_list[count2] =="YS" and nuance_list[count2] == "N3":
            n3_ys += 1
        elif correctness_list[count2] =="NS" and nuance_list[count2] == "N3":
            n3_ns += 1

        elif correctness_list[count2] =="Y" and nuance_list[count2] == "ion":
            ion_y += 1
        elif correctness_list[count2] =="N" and nuance_list[count2] == "ion":
            ion_n += 1
        elif correctness_list[count2] =="A" and nuance_list[count2] == "ion":
            ion_a += 1
        elif correctness_list[count2] =="S" and nuance_list[count2] == "ion":
            ion_s += 1
        elif correctness_list[count2] =="YS" and nuance_list[count2] == "ion":
            ion_ys += 1
        elif correctness_list[count2] =="NS" and nuance_list[count2] == "ion":
            ion_ns += 1

        elif correctness_list[count2] =="Y" and nuance_list[count2] == "cion":
            cion_y += 1
        elif correctness_list[count2] =="N" and nuance_list[count2] == "cion":
            cion_n += 1
        elif correctness_list[count2] =="A" and nuance_list[count2] == "cion":
            cion_a += 1
        elif correctness_list[count2] =="S" and nuance_list[count2] == "cion":
            cion_s += 1
        elif correctness_list[count2] =="YS" and nuance_list[count2] == "cion":
            cion_ys += 1
        elif correctness_list[count2] =="NS" and nuance_list[count2] == "cion":
            cion_ns += 1

        elif correctness_list[count2] =="Y" and nuance_list[count2] == "screw":
            screw_y += 1
        elif correctness_list[count2] =="N" and nuance_list[count2] == "screw":
            screw_n += 1
        elif correctness_list[count2] =="A" and nuance_list[count2] == "screw":
            screw_a += 1
        elif correctness_list[count2] =="S" and nuance_list[count2] == "screw":
            screw_s += 1
        elif correctness_list[count2] =="YS" and nuance_list[count2] == "screw":
            screw_ys += 1
        elif correctness_list[count2] =="NS" and nuance_list[count2] == "screw":
            screw_ns += 1

        elif correctness_list[count2] =="Y" and nuance_list[count2] == "colcirc&screw":
            screw_y += 1
            colcirc_y += 1
        elif correctness_list[count2] =="N" and nuance_list[count2] == "colcirc&screw":
            screw_n += 1
            colcirc_n += 1
        elif correctness_list[count2] =="A" and nuance_list[count2] == "colcirc&screw":
            screw_a += 1
            colcirc_a += 1
        elif correctness_list[count2] =="S" and nuance_list[count2] == "colcirc&screw":
            screw_s += 1
            colcirc_s += 1
        elif correctness_list[count2] =="YS" and nuance_list[count2] == "colcirc&screw":
            screw_ys += 1
            colcirc_ys += 1
        elif correctness_list[count2] =="NS" and nuance_list[count2] == "colcirc&screw":
            screw_ns += 1
            colcirc_ns += 1

        elif correctness_list[count2] =="Y" and nuance_list[count2] == "col&screw":
            screw_y += 1
            col_y += 1
        elif correctness_list[count2] =="N" and nuance_list[count2] == "col&screw":
            screw_n += 1
            col_n += 1
        elif correctness_list[count2] =="A" and nuance_list[count2] == "col&screw":
            screw_a += 1
            col_a += 1
        elif correctness_list[count2] =="S" and nuance_list[count2] == "col&screw":
            screw_s += 1
            col_s += 1
        elif correctness_list[count2] =="YS" and nuance_list[count2] == "col&screw":
            screw_ys += 1
            col_ys += 1
        elif correctness_list[count2] =="NS" and nuance_list[count2] == "col&screw":
            screw_ns += 1
            col_ns += 1

        elif correctness_list[count2] =="Y" and nuance_list[count2] == "colcirc&screw&ion":
            screw_y += 1
            colcirc_y += 1
            ion_y += 1
        elif correctness_list[count2] =="N" and nuance_list[count2] == "colcirc&screw&ion":
            screw_n += 1
            colcirc_n += 1
            ion_n += 1
        elif correctness_list[count2] =="A" and nuance_list[count2] == "colcirc&screw&ion":
            screw_a += 1
            colcirc_a += 1
            ion_a += 1
        elif correctness_list[count2] =="S" and nuance_list[count2] == "colcirc&screw&ion":
            screw_s += 1
            colcirc_s += 1
            ion_s += 1
        elif correctness_list[count2] =="YS" and nuance_list[count2] == "colcirc&screw&ion":
            screw_ys += 1
            colcirc_ys += 1
            ion_ys += 1
        elif correctness_list[count2] =="NS" and nuance_list[count2] == "colcirc&screw&ion":
            screw_ns += 1
            colcirc_ns += 1
            ion_ns += 1

        elif correctness_list[count2] =="Y" and nuance_list[count2] == "col&ion":
            col_y += 1
            ion_y += 1
        elif correctness_list[count2] =="N" and nuance_list[count2] == "col&ion":
            col_n += 1
            ion_n += 1
        elif correctness_list[count2] =="A" and nuance_list[count2] == "col&ion":
            col_a += 1
            ion_a += 1
        elif correctness_list[count2] =="S" and nuance_list[count2] == "col&ion":
            col_s += 1
            ion_s += 1
        elif correctness_list[count2] =="YS" and nuance_list[count2] == "col&ion":
            col_ys += 1
            ion_ys += 1
        elif correctness_list[count2] =="NS" and nuance_list[count2] == "col&ion":
            col_ns += 1
            ion_ns += 1

        elif correctness_list[count2] =="Y" and nuance_list[count2] == "col&ion&cion":
            col_y += 1
            ion_y += 1
            cion_y += 1
        elif correctness_list[count2] =="N" and nuance_list[count2] == "col&ion&cion":
            col_n += 1
            ion_n += 1
            cion_n += 1
        elif correctness_list[count2] =="A" and nuance_list[count2] == "col&ion&cion":
            col_a += 1
            ion_a += 1
            cion_a += 1
        elif correctness_list[count2] =="S" and nuance_list[count2] == "col&ion&cion":
            col_s += 1
            ion_s += 1
            cion_s += 1
        elif correctness_list[count2] =="YS" and nuance_list[count2] == "col&ion&cion":
            col_ys += 1
            ion_ys += 1
            cion_ys += 1
        elif correctness_list[count2] =="NS" and nuance_list[count2] == "col&ion&cion":
            col_ns += 1
            ion_ns += 1
            cion_ns += 1

        elif correctness_list[count2] =="Y" and nuance_list[count2] == "col&isotope&ion&var":
            col_y += 1
            ion_y += 1
            isotope_y += 1
            var_y += 1
        elif correctness_list[count2] =="N" and nuance_list[count2] == "col&isotope&ion&var":
            col_n += 1
            ion_n += 1
            isotope_n += 1
            var_n += 1
        elif correctness_list[count2] =="A" and nuance_list[count2] == "col&isotope&ion&var":
            col_a += 1
            ion_a += 1
            isotope_a += 1
            var_a += 1
        elif correctness_list[count2] =="S" and nuance_list[count2] == "col&isotope&ion&var":
            col_s += 1
            ion_s += 1
            isotope_s += 1
            var_s += 1
        elif correctness_list[count2] =="YS" and nuance_list[count2] == "col&isotope&ion&var":
            col_ys += 1
            ion_ys += 1
            isotope_ys += 1
            var_ys += 1
        elif correctness_list[count2] =="NS" and nuance_list[count2] == "col&isotope&ion&var":
            col_ns += 1
            ion_ns += 1
            isotope_ns += 1
            var_ns += 1

        elif correctness_list[count2] =="Y" and nuance_list[count2] == "col&isotope&ion":
            col_y += 1
            ion_y += 1
            isotope_y += 1
        elif correctness_list[count2] =="N" and nuance_list[count2] == "col&isotope&ion":
            col_n += 1
            ion_n += 1
            isotope_n += 1
        elif correctness_list[count2] =="A" and nuance_list[count2] == "col&isotope&ion":
            col_a += 1
            ion_a += 1
            isotope_a += 1
        elif correctness_list[count2] =="S" and nuance_list[count2] == "col&isotope&ion":
            col_s += 1
            ion_s += 1
            isotope_s += 1
        elif correctness_list[count2] =="YS" and nuance_list[count2] == "col&isotope&ion":
            col_ys += 1
            ion_ys += 1
            isotope_ys += 1
        elif correctness_list[count2] =="NS" and nuance_list[count2] == "col&isotope&ion":
            col_ns += 1
            ion_ns += 1
            isotope_ns += 1

        elif correctness_list[count2] =="Y" and nuance_list[count2] == "col&isotope&var":
            col_y += 1
            isotope_y += 1
            var_y += 1
        elif correctness_list[count2] =="N" and nuance_list[count2] == "col&isotope&var":
            col_n += 1
            isotope_n += 1
            var_n += 1
        elif correctness_list[count2] =="A" and nuance_list[count2] == "col&isotope&var":
            col_a += 1
            isotope_a += 1
            var_a += 1
        elif correctness_list[count2] =="S" and nuance_list[count2] == "col&isotope&var":
            col_s += 1
            isotope_s += 1
            var_s += 1
        elif correctness_list[count2] =="YS" and nuance_list[count2] == "col&isotope&var":
            col_ys += 1
            isotope_ys += 1
            var_ys += 1
        elif correctness_list[count2] =="NS" and nuance_list[count2] == "col&isotope&var":
            col_ns += 1
            isotope_ns += 1
            var_ns += 1

        elif correctness_list[count2] =="Y" and nuance_list[count2] == "col&isotope":
            col_y += 1
            isotope_y += 1
        elif correctness_list[count2] =="N" and nuance_list[count2] == "col&isotope":
            col_n += 1
            isotope_n += 1
        elif correctness_list[count2] =="A" and nuance_list[count2] == "col&isotope":
            col_a += 1
            isotope_a += 1
        elif correctness_list[count2] =="S" and nuance_list[count2] == "col&isotope":
            col_s += 1
            isotope_s += 1
        elif correctness_list[count2] =="YS" and nuance_list[count2] == "col&isotope":
            col_ys += 1
            isotope_ys += 1
        elif correctness_list[count2] =="NS" and nuance_list[count2] == "col&isotope":
            col_ns += 1
            isotope_ns += 1

        elif correctness_list[count2] =="Y" and nuance_list[count2] == "col&arring":
            col_y += 1
            arring_y += 1
        elif correctness_list[count2] =="N" and nuance_list[count2] == "col&arring":
            col_n += 1
            arring_n += 1
        elif correctness_list[count2] =="A" and nuance_list[count2] == "col&arring":
            col_a += 1
            arring_a += 1
        elif correctness_list[count2] =="S" and nuance_list[count2] == "col&arring":
            col_s += 1
            arring_s += 1
        elif correctness_list[count2] =="YS" and nuance_list[count2] == "col&arring":
            col_ys += 1
            arring_ys += 1
        elif correctness_list[count2] =="NS" and nuance_list[count2] == "col&arring":
            col_ns += 1
            arring_ns += 1

        elif correctness_list[count2] =="Y" and nuance_list[count2] == "col&macro":
            col_y += 1
            macro_y += 1
        elif correctness_list[count2] =="N" and nuance_list[count2] == "col&macro":
            col_n += 1
            macro_n += 1
        elif correctness_list[count2] =="A" and nuance_list[count2] == "col&macro":
            col_a += 1
            macro_a += 1
        elif correctness_list[count2] =="S" and nuance_list[count2] == "col&macro":
            col_s += 1
            macro_s += 1
        elif correctness_list[count2] =="YS" and nuance_list[count2] == "col&macro":
            col_ys += 1
            macro_ys += 1
        elif correctness_list[count2] =="NS" and nuance_list[count2] == "col&macro":
            col_ns += 1
            macro_ns += 1

        elif correctness_list[count2] =="Y" and nuance_list[count2] == "col&bracket":
            col_y += 1
            bracket_y += 1
        elif correctness_list[count2] =="N" and nuance_list[count2] == "col&bracket":
            col_n += 1
            bracket_n += 1
        elif correctness_list[count2] =="A" and nuance_list[count2] == "col&bracket":
            col_a += 1
            bracket_a += 1
        elif correctness_list[count2] =="S" and nuance_list[count2] == "col&bracket":
            col_s += 1
            bracket_s += 1
        elif correctness_list[count2] =="YS" and nuance_list[count2] == "col&bracket":
            col_ys += 1
            bracket_ys += 1
        elif correctness_list[count2] =="NS" and nuance_list[count2] == "col&bracket":
            col_ns += 1
            bracket_ns += 1

        elif correctness_list[count2] =="Y" and nuance_list[count2] == "col&bridge":
            col_y += 1
            bridge_y += 1
        elif correctness_list[count2] =="N" and nuance_list[count2] == "col&bridge":
            col_n += 1
            bridge_n += 1
        elif correctness_list[count2] =="A" and nuance_list[count2] == "col&bridge":
            col_a += 1
            bridge_a += 1
        elif correctness_list[count2] =="S" and nuance_list[count2] == "col&bridge":
            col_s += 1
            bridge_s += 1
        elif correctness_list[count2] =="YS" and nuance_list[count2] == "col&bridge":
            col_ys += 1
            bridge_ys += 1
        elif correctness_list[count2] =="NS" and nuance_list[count2] == "col&bridge":
            col_ns += 1
            bridge_ns += 1

        elif correctness_list[count2] =="Y" and nuance_list[count2] == "colcirc&bridge":
            colcirc_y += 1
            bridge_y += 1
        elif correctness_list[count2] =="N" and nuance_list[count2] == "colcirc&bridge":
            colcirc_n += 1
            bridge_n += 1
        elif correctness_list[count2] =="A" and nuance_list[count2] == "colcirc&bridge":
            colcirc_a += 1
            bridge_a += 1
        elif correctness_list[count2] =="S" and nuance_list[count2] == "colcirc&bridge":
            colcirc_s += 1
            bridge_s += 1
        elif correctness_list[count2] =="YS" and nuance_list[count2] == "colcirc&bridge":
            colcirc_ys += 1
            bridge_ys += 1
        elif correctness_list[count2] =="NS" and nuance_list[count2] == "colcirc&bridge":
            colcirc_ns += 1
            bridge_ns += 1

        elif correctness_list[count2] =="Y" and nuance_list[count2] == "screw&bridge":
            screw_y += 1
            bridge_y += 1
        elif correctness_list[count2] =="N" and nuance_list[count2] == "screw&bridge":
            screw_n += 1
            bridge_n += 1
        elif correctness_list[count2] =="A" and nuance_list[count2] == "screw&bridge":
            screw_a += 1
            bridge_a += 1
        elif correctness_list[count2] =="S" and nuance_list[count2] == "screw&bridge":
            screw_s += 1
            bridge_s += 1
        elif correctness_list[count2] =="YS" and nuance_list[count2] == "screw&bridge":
            screw_ys += 1
            bridge_ys += 1
        elif correctness_list[count2] =="NS" and nuance_list[count2] == "screw&bridge":
            screw_ns += 1
            bridge_ns += 1

        elif correctness_list[count2] =="Y" and nuance_list[count2] == "cion&bridge":
            cion_y += 1
            bridge_y += 1
        elif correctness_list[count2] =="N" and nuance_list[count2] == "cion&bridge":
            cion_n += 1
            bridge_n += 1
        elif correctness_list[count2] =="A" and nuance_list[count2] == "cion&bridge":
            cion_a += 1
            bridge_a += 1
        elif correctness_list[count2] =="S" and nuance_list[count2] == "cion&bridge":
            cion_s += 1
            bridge_s += 1
        elif correctness_list[count2] =="YS" and nuance_list[count2] == "cion&bridge":
            cion_ys += 1
            bridge_ys += 1
        elif correctness_list[count2] =="NS" and nuance_list[count2] == "cion&bridge":
            cion_ns += 1
            bridge_ns += 1

        elif correctness_list[count2] =="Y" and nuance_list[count2] == "bridge&macro":
            bridge_y += 1
            macro_y += 1
        elif correctness_list[count2] =="N" and nuance_list[count2] == "bridge&macro":
            bridge_n += 1
            macro_n += 1
        elif correctness_list[count2] =="A" and nuance_list[count2] == "bridge&macro":
            bridge_a += 1
            macro_a += 1
        elif correctness_list[count2] =="S" and nuance_list[count2] == "bridge&macro":
            bridge_s += 1
            macro_s += 1
        elif correctness_list[count2] =="YS" and nuance_list[count2] == "bridge&macro":
            bridge_ys += 1
            macro_ys += 1
        elif correctness_list[count2] =="NS" and nuance_list[count2] == "bridge&macro":
            bridge_ns += 1
            macro_ns += 1

        elif correctness_list[count2] =="Y" and nuance_list[count2] == "squig&color":
            squig_y += 1
            col_y += 1
        elif correctness_list[count2] =="N" and nuance_list[count2] == "squig&color":
            squig_n += 1
            col_n += 1
        elif correctness_list[count2] =="A" and nuance_list[count2] == "squig&color":
            squig_a += 1
            col_a += 1
        elif correctness_list[count2] =="S" and nuance_list[count2] == "squig&color":
            squig_s += 1
            col_s += 1
        elif correctness_list[count2] =="YS" and nuance_list[count2] == "squig&color":
            squig_ys += 1
            col_ys += 1
        elif correctness_list[count2] =="NS" and nuance_list[count2] == "squig&color":
            squig_ns += 1
            col_ns += 1

        elif correctness_list[count2] =="Y" and nuance_list[count2] == "squig&bridge":
            squig_y += 1
            bridge_y += 1
        elif correctness_list[count2] =="N" and nuance_list[count2] == "squig&bridge":
            squig_n += 1
            bridge_n += 1
        elif correctness_list[count2] =="A" and nuance_list[count2] == "squig&bridge":
            squig_a += 1
            bridge_a += 1
        elif correctness_list[count2] =="S" and nuance_list[count2] == "squig&bridge":
            squig_s += 1
            bridge_s += 1
        elif correctness_list[count2] =="YS" and nuance_list[count2] == "squig&bridge":
            squig_ys += 1
            bridge_ys += 1
        elif correctness_list[count2] =="NS" and nuance_list[count2] == "squig&bridge":
            squig_ns += 1
            bridge_ns += 1

        elif correctness_list[count2] =="Y" and nuance_list[count2] == "squig&var":
            squig_y += 1
            var_y += 1
        elif correctness_list[count2] =="N" and nuance_list[count2] == "squig&var":
            squig_n += 1
            var_n += 1
        elif correctness_list[count2] =="A" and nuance_list[count2] == "squig&var":
            squig_a += 1
            var_a += 1
        elif correctness_list[count2] =="S" and nuance_list[count2] == "squig&var":
            squig_s += 1
            var_s += 1
        elif correctness_list[count2] =="YS" and nuance_list[count2] == "squig&var":
            squig_ys += 1
            var_ys += 1
        elif correctness_list[count2] =="NS" and nuance_list[count2] == "squig&var":
            squig_ns += 1
            var_ns += 1

        elif correctness_list[count2] =="Y" and nuance_list[count2] == "squig":
            squig_y += 1
        elif correctness_list[count2] =="N" and nuance_list[count2] == "squig":
            squig_n += 1
        elif correctness_list[count2] =="A" and nuance_list[count2] == "squig":
            squig_a += 1
        elif correctness_list[count2] =="S" and nuance_list[count2] == "squig":
            squig_s += 1
        elif correctness_list[count2] =="YS" and nuance_list[count2] == "squig":
            squig_ys += 1
        elif correctness_list[count2] =="NS" and nuance_list[count2] == "squig":
            squig_ns += 1

        count2 += 1

#Nuances and their grade counts are listed
print("Var as Y: " +str(var_y))
print("Var as N: " +str(var_n))
print("Var as A: " +str(var_a))
print("Var as S: " +str(var_s))
print("Var as YS: " +str(var_ys))
print("Var as NS: " +str(var_ns))
print("-----------------------------------")

print("SCREW as Y: " +str(screw_y))
print("SCREW as N: " +str(screw_n))
print("SCREW as A: " +str(screw_a))
print("SCREW as S: " +str(screw_s))
print("SCREW as YS: " +str(screw_ys))
print("SCREW as NS: " +str(screw_ns))
print("-----------------------------------")

print("COL as Y: " +str(col_y))
print("COL as N: " +str(col_n))
print("COL as A: " +str(col_a))
print("COL as S: " +str(col_s))
print("COL as YS: " +str(col_ys))
print("COL as NS: " +str(col_ns))
print("-----------------------------------")

print("ION as Y: " +str(ion_y))
print("ION as N: " +str(ion_n))
print("ION as A: " +str(ion_a))
print("ION as S: " +str(ion_s))
print("ION as YS: " +str(ion_ys))
print("ION as NS: " +str(ion_ns))
print("-----------------------------------")

print("CION as Y: " +str(cion_y))
print("CION as N: " +str(cion_n))
print("CION as A: " +str(cion_a))
print("CION as S: " +str(cion_s))
print("CION as YS: " +str(cion_ys))
print("CION as NS: " +str(cion_ns))
print("-----------------------------------")

print("BRIDGE as Y: " +str(bridge_y))
print("BRIDGE as N: " +str(bridge_n))
print("BRIDGE as A: " +str(bridge_a))
print("BRIDGE as S: " +str(bridge_s))
print("BRIDGE as YS: " +str(bridge_ys))
print("BRIDGE as NS: " +str(bridge_ns))
print("-----------------------------------")

print("MACRO as Y: " +str(macro_y))
print("MACRO as N: " +str(macro_n))
print("MACRO as A: " +str(macro_a))
print("MACRO as S: " +str(macro_s))
print("MACRO as YS: " +str(macro_ys))
print("MACRO as NS: " +str(macro_ns))
print("-----------------------------------")

print("COLCIRC as Y: " +str(colcirc_y))
print("COLCIRC as N: " +str(colcirc_n))
print("COLCIRC as A: " +str(colcirc_a))
print("COLCIRC as S: " +str(colcirc_s))
print("COLCIRC as YS: " +str(colcirc_ys))
print("COLCIRC as NS: " +str(colcirc_ns))
print("-----------------------------------")

print("ISOTOPE as Y: " +str(isotope_y))
print("ISOTOPE as N: " +str(isotope_n))
print("ISOTOPE as A: " +str(isotope_a))
print("ISOTOPE as S: " +str(isotope_s))
print("ISOTOPE as YS: " +str(isotope_ys))
print("ISOTOPE as NS: " +str(isotope_ns))
print("-----------------------------------")

print("BRACKET as Y: " +str(bracket_y))
print("BRACKET as N: " +str(bracket_n))
print("BRACKET as A: " +str(bracket_a))
print("BRACKET as S: " +str(bracket_s))
print("BRACKET as YS: " +str(bracket_ys))
print("BRACKET as NS: " +str(bracket_ns))
print("-----------------------------------")

print("NORM as Y: " +str(norm_y))
print("NORM as N: " +str(norm_n))
print("NORM as A: " +str(norm_a))
print("NORM as S: " +str(norm_s))
print("NORM as YS: " +str(norm_ys))
print("NORM as NS: " +str(norm_ns))
print("-----------------------------------")

print("N3 as Y: " +str(n3_y))
print("N3 as N: " +str(n3_n))
print("N3 as A: " +str(n3_a))
print("N3 as S: " +str(n3_s))
print("N3 as YS: " +str(n3_ys))
print("N3 as NS: " +str(n3_ns))
print("-----------------------------------")

print("ARRING as Y: " +str(arring_y))
print("ARRING as N: " +str(arring_n))
print("ARRING as A: " +str(arring_a))
print("ARRING as S: " +str(arring_s))
print("ARRING as YS: " +str(arring_ys))
print("ARRING as NS: " +str(arring_ns))
print("-----------------------------------")

print("RADICAL as Y: " +str(radical_y))
print("RADICAL as N: " +str(radical_n))
print("RADICAL as A: " +str(radical_a))
print("RADICAL as S: " +str(radical_s))
print("RADICAL as YS: " +str(radical_ys))
print("RADICAL as NS: " +str(radical_ns))
print("-----------------------------------")


print("Undefined Stereochemistry as Y: " +str(squig_y))
print("Undefined Stereochemistry as N: " +str(squig_n))
print("Undefined Stereochemistry as A: " +str(squig_a))
print("Undefined Stereochemistry as S: " +str(squig_s))
print("Undefined Stereochemistry as YS: " +str(squig_ys))
print("Undefined Stereochemistry as NS: " +str(squig_ns))

print("")
"""


#After all of the above variables are established, trend analysis is conducted for relevant metrics
print("==============================================")
print("~~~~~~       Trend  Analysis            ~~~~~~")
print("==============================================")

#Accuracy of Appendix in CXSMILES
appendix_acc = (y+a)/total_appendix
print("Appendix Accuracy = " +str(appendix_acc))
print("Y + A = / Total Appendix ")
print("-----------------------------------")

#Accuracy of Appendix when those Molecules Have a High Confidence
appendix_hc_acc = (y_hc+a_hc)/total_appendix
print("Appendix Accuracy that have High Confidence = " +str(appendix_hc_acc))
print("Y_hc + A_hc = / Total Appendix ")
print("-----------------------------------")

#Holisic Accuracy of Every Translated Molecule
structure_acc = (s+ys+y)/total_mol
print("Structure Accuracy = " + str(structure_acc))
print("Y + YS + S / Total Molecule")
print("-----------------------------------")

#Accuracy of Skeletal Structures when No Appendix Was Present
just_struc_acc = ys/(ys+ns)
print("Molecule Structure Accuracy (No Appendix Present) = " + str(just_struc_acc))
print("YS / YS + NS ")
print("-----------------------------------")

#Accuracy when Molecule Had Both CXSMILES Components
both_acc = y/(y+n)
print("Input that had both a Skeletal Structure and Appendix and got both correct = " + str(both_acc))
print("Y / Y + N")
print("-----------------------------------")

#Percentage of Holistically Correct Molecules from Entire Dataset
totalgood = (y+ys)/total_mol
print("Total Holistic Correct Molecules = " + str(totalgood))
print("Y +YS / Total Molecules ")
print("-----------------------------------")

#Holsitic Accuracy when an Appendix is Present
present = y/total_appendix
print("Total Skeletal Structure & Appendix Correct When Both are Present = " +str(present))
print("Y / Total Appendix ")
print("-----------------------------------")

#Percentage of Y's being High Conidence 
y_hc_acc = y_hc/total_mol
y_hc_acc2 = y_hc/y
print("Total Y as HC Accuracy = " + str(y_hc_acc2))
print("Y_hc / Y")
print("Total Y as HC % of Y grades = " + str(y_hc_acc))
print("-----------------------------------")

#Percentage of S's being High Confidence
s_hc_acc = s_hc/s
print("Total S as HC Accuracy = " + str(s_hc_acc))
print("-----------------------------------")

#Percentage of YS's being High Confidence
ys_hc_acc = ys_hc/ys
print("Total YS as HC Accuracy = " + str(ys_hc_acc))
print("-----------------------------------")

#Percentage of N's being Low Confidence
n_dis_acc = n_dis/n
print("Total N as DIS Accuracy = " + str(n_dis_acc))
print("-----------------------------------")

#Percentage of A's being Low Confidence
a_dis_acc = a_dis/a
print("Total A as DIS Accuracy = " + str(a_dis_acc))
print("-----------------------------------")

#Percentage of NS's being Low Confidence
ns_dis_acc = ns_dis/ns
print("Total NS as DIS Accuracy = " + str(ns_dis_acc))
print("-----------------------------------")

#Percentage of Holistically Correct Molecules being High Confidence
totalgoodhc = (y_hc+ys_hc)/(y+ys)
print("Total Correct and High Confidence of Total Correct % = " + str(totalgoodhc))
print("y_hc +ys_hc / Y + YS")
print("-----------------------------------")

#Percentage of Holistically Correct Molecules with High Confidence from Entire Molecule Set
totalgoodhc2 = (y_hc+ys_hc)/(total_mol)
print("Total Correct and High Confidence of Entire Dataset = " + str(totalgoodhc2))
print("y_hc +ys_hc / Total Molecules")
print("-----------------------------------")

#Percentage of Incorrect Molecules being Low Confidence
totalbaddis = (n_dis+ns_dis+a_dis+s_dis)/(ns+n+a+s)
print("Total Incorrect and Low Confidence of Total Incorrect % = " + str(totalbaddis))
print("n_dis + ns_dis + a_dis + s_dis / N + NS + A + S")
print("-----------------------------------")

#Percentage of Incorrect Molecules with Low Confidence from Entire Molecule Set
totalbaddis2 = (n_dis+ns_dis+a_dis+s_dis)/(total_mol)
print("Total Incorrect and Low Confidence of Entire Dataset = " + str(totalbaddis2))
print("n_dis + ns_dis + a_dis + s_dis / Total Molecules")
print("-----------------------------------")


print("Trend Analysis Complete")


