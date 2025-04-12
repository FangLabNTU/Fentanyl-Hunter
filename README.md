# Fentanyl-Hunter

**Fentanyl-Hunter** is a program designed for the screening and annotation of members of the fentanyl family based on MS/MS data. This platform has demonstrated its ability to identify fentanyl, its analogues, and metabolites in both biological and environmental samples. The methodology is detailed in the research article *"Machine Learning and Molecular Network-Assisted Screening Reveals Unknown Compounds in the Fentanyl Family"* (In preparation).

### Key Components
The platform consists of two primary modules:
1. **Fentanyl_Finder** – Screening of MS features.
2. **Fentanyl_ID** – Auxiliary structure identification.

Both modules are fully written in Python. Additional scripts used in the research are included in this repository. The first authors are **Changzhi Shi** and **Wanli Li**.

---

## Repository Structure

The repository contains 5 main subfolders:

### 1. Fentanyl_Finder
This folder contains two subfolders, corresponding to different applications of the trained **Fentanyl-Hunter** machine learning model (`Fentanyl_Finder.pkl`):

- **Metabolite Screening**: 
  - Demonstrates a case study of screening for in vitro metabolites of fentanyl. The input MS data file is provided as `Met-fentanyl.txt`. This is followed by peak cleaning (`clean_peak.ipynb`) and fentanyl candidate screening (`Fentanyl_Finder.ipynb`).
  - We recommend using the **MS-DIAL** software for preliminary processing of raw MS data in TXT format. [MS-DIAL website](http://prime.psc.riken.jp/compms/msdial/main.html)
  
- **Confusion Matrix**: 
  - Provides a case study of screening for unknown fentanyls in a human urine sample.

### 2. Fentanyl_ID
The main script `Fentanyl_ID.ipynb` is used to develop a multi-layer network between fentanyl candidates (after screening with Fentanyl-Hunter) and known fentanyl analogues. This is achieved by utilizing a **Paired Mass Distance (PMD)** network, which relies on a PMD list (`PMD.xlsx`).

- A wastewater sample is provided as an example for the network development.
- Additionally, the **Fentanyl Library** (`Fentanyllibrary.msp`, 772 spectra) is available for annotating seed fentanyls using MS-DIAL's "Identification" module.

### 3. Fentanyl Cluster
This script is used for chemical space visualization based on the **Tanimoto coefficient matrix** (Morgan fingerprints). The matrix is reduced via **Multi-Dimensional Scaling (MDS)**, where each point represents a structure and distances reflect structural similarities. The central structure is clustered using **K-means**.

- For compound control reasons, the structures of all fentanyls are not provided directly. Please contact the authors for more information.

### 4. Suspect Screening for Fentanyl
This homemade script is used for **suspect screening** of fentanyls in MS data, utilizing **MS2 spectral characteristics**. The relevant data can be found in `MS2 list.xlsx`.

### 5. Fentanyl LC RT Prediction
This script predicts the retention time (RT) for fentanyls in **Liquid Chromatography (LC)**. The algorithm is a modified version of **GNN-RT** ([GNN-RT GitHub](https://github.com/Qiong-Yang/GNNRT)) and was calibrated using fentanyl standards measured in the same LC system.

---

## Contact Information

For more details or inquiries, please contact:

- Changzhi Shi: [czshi22@m.fudan.edu.cn](mailto:czshi22@m.fudan.edu.cn)

---

**October 2024**

FangLab at **Fudan University** & DengLab at **Shanghai Institute for Doping Analyses, Shanghai University of Sport**

