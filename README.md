# Fentanyl-Hunter

**Fentanyl-Hunter** is a platform for screening and annotating members of the fentanyl family based on MS/MS data. It has been successfully applied to identify fentanyl, its analogues, and metabolites in biological and environmental samples.

The methodology is described in the research article *"Machine Learning and Molecular Network-Assisted Screening Reveals Unknown Compounds in the Fentanyl Family"* (in preparation).

First authors: **Changzhi Shi** and **Wanli Li**

---

## 🔍 Key Components

The platform consists of two main Python-based modules:

1. **Fentanyl_Finder** – Screening of MS features  
2. **Fentanyl_ID** – Auxiliary structure identification

Additional utility scripts used in the research are also provided in this repository.

---

## 📁 Repository Structure

### 1. `Fentanyl_Finder`

This folder contains two sub-applications based on the machine learning model `Fentanyl_Finder.pkl`.

- **Metabolite Screening**
  - A case study for screening in vitro fentanyl metabolites.
  - Input MS file: `Met-fentanyl.txt`
  - Includes peak cleaning (`clean_peak.ipynb`) and screening (`Fentanyl_Finder.ipynb`)
  - MS preprocessing recommended using **MS-DIAL**: [MS-DIAL website](http://prime.psc.riken.jp/compms/msdial/main.html)

- **Confusion Matrix**
  - Demonstrates screening for unknown fentanyls in human urine samples.

---

### 2. `Fentanyl_ID`

The `Fentanyl_ID.ipynb` script builds a multi-layer network linking screened fentanyl candidates to known analogues, using **Paired Mass Distance (PMD)** and a curated `PMD.xlsx`.

- Includes a wastewater sample example
- **Fentanyl Library** (`Fentanyllibrary.msp`, 772 spectra) supports MS-DIAL-based annotation using its “Identification” module

---

### 3. `Fentanyl Cluster`

This script visualizes chemical space using:

- **Tanimoto coefficient matrix** (Morgan fingerprints)
- **Multi-Dimensional Scaling (MDS)**
- **K-means** clustering for identifying core structures

> **Note**: Fentanyl structures are not directly included. Contact the authors for access.

---

### 4. `Suspect Screening for Fentanyl`

This homemade script performs **suspect screening** using MS2 spectral characteristics.  
Reference data: `MS2 list.xlsx`

---

### 5. `Fentanyl LC RT Prediction`

This script predicts retention times (RT) in LC for fentanyl compounds using a modified **GNN-RT** model:

- Original repo: [GNN-RT GitHub](https://github.com/Qiong-Yang/GNNRT)
- Calibrated using fentanyl standards from the same LC setup

---

## 🖥️ 6. GUI Version

The **graphical user interface (GUI)** version of *Fentanyl-Hunter*, developed using **Electron**, offers a desktop application experience, organized into two main tabs mirroring the script-based workflow.

### Backend

- Developed with **Flask**
- Handles all data processing and algorithm execution
- Source code located in the **[`main` branch](https://github.com/FangLabNTU/Fentanyl-Hunter/GUI_version/Backend_master)**

### Frontend

- Built with **Electron + Vue 3**
- Compiled into a **Windows desktop application**
- Due to size, the frontend is in the **[`master` branch](https://github.com/FangLabNTU/Fentanyl-Hunter)**

---

## ⚙️ 7. How to Set Up the GUI Version

Please refer to the platform-specific setup instructions in the README files located in the corresponding branches:

- [`main` branch](https://github.com/FangLabNTU/Fentanyl-Hunter/GUI_version_setup/Backend_master) – Backend setup  
- [`main` branch](https://github.com/FangLabNTU/Fentanyl-Hunter/GUI_version_setup/Fentanyl-Hunter_master) – Frontend build & Electron app usage

---

## 📬 Contact

For questions or collaboration, feel free to reach out:

- **Changzhi Shi**: [czshi22@m.fudan.edu.cn](mailto:czshi22@m.fudan.edu.cn)

---

**April 2025**  
FangLab, **Fudan University**  
DengLab, **Shanghai Institute for Doping Analyses**, Shanghai University of Sport
