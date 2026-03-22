!pip install --quiet SimpleITK tqdm
!pip install --quiet umap-learn

!pip install --quiet \
  "pandas>=2.2.3" \
  "matplotlib>=3.9.2" \
  "scikit-image>=0.24.0" \
  "segmentation-models-pytorch>=0.3.3" \
  "SimpleITK>=2.4.0" \
  "torch>=2.3.0" \
  "torchvision>=0.18.0"


import os, math, random, time
import torch
import numpy as np
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
import segmentation_models_pytorch as smp
from PIL import Image
from tqdm.notebook import tqdm
from torch import nn
from torchvision.io import read_image
from torchvision.models.detection import fasterrcnn_resnet50_fpn
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
from torchvision.ops import box_iou
from torchvision.utils import draw_bounding_boxes
import torchvision.transforms.functional as TF
import torchvision.transforms as T
import torchvision.models as models
from scipy.optimize import curve_fit
from scipy.signal import find_peaks
import torch.nn.functional as F
from torchvision.ops import box_iou
from sklearn.cluster import KMeans
from torch.utils.data import Dataset, DataLoader

import SimpleITK as sitk
from pathlib import Path
from tqdm.notebook import tqdm
import pandas as pd
import matplotlib.pyplot as plt
import random
import cv2
import torch.optim as optim
import pickle
import ast
from sklearn.preprocessing import StandardScaler
import matplotlib.patches as patches
import json
from scipy.stats import pearsonr
import seaborn as sns

device = "cuda" if torch.cuda.is_available() else "cpu"
print("✅ Device utilisé :", device)

# --- Paths ---
DATA_ROOT = Path("/kaggle/input/ram-w600-local")     # change if needed
RAW_DIR = DATA_ROOT / "RAM-W600" / "BoneSegmentation"
OUT_ROOT = Path("/kaggle/working/data/preprocessed")
OUT_512 = OUT_ROOT / "512"
OUT_224 = OUT_ROOT / "224"
for p in [OUT_512, OUT_224]:
    p.mkdir(parents=True, exist_ok=True)

# --- List all images ---
img_exts = [".png", ".jpg", ".jpeg", ".tif", ".bmp"]
files = sorted([p for p in RAW_DIR.rglob("*") if p.suffix.lower() in img_exts])
print(f"{len(files)} images found in BoneSegmentation.")
print("Example:", files[0])

# Sélection aléatoire de 3 images
sample_files = random.sample(files, 3)

# Création de la figure
fig, axes = plt.subplots(1, 3, figsize=(12, 4))

for ax, img_path in zip(axes, sample_files):
    img = Image.open(img_path)
    ax.imshow(img, cmap="gray")
    ax.set_title(img_path.name, fontsize=9)
    ax.axis("off")

plt.tight_layout()
plt.show()

def preprocess_sitk(img_path, out512, out224, alpha=0.3, beta=0.3):
    try:
        img = sitk.ReadImage(str(img_path))

        # Convertir en grayscale si multi-canaux
        if img.GetNumberOfComponentsPerPixel() > 1:
            img = sitk.VectorMagnitude(img)
            img = sitk.Cast(img, sitk.sitkUInt16)

        # Égalisation adaptative
        img_eq = sitk.AdaptiveHistogramEqualization(img, alpha=alpha, beta=beta)

        # Redimensionnements
        resampler = sitk.ResampleImageFilter()
        resampler.SetInterpolator(sitk.sitkLinear)

        # 512x512
        resampler.SetSize([512,512])
        img512 = resampler.Execute(img_eq)

        # 224x224
        resampler.SetSize([224,224])
        img224 = resampler.Execute(img_eq)

        # Sauvegarde en .png 16 bits
        out512_path = out512 / (img_path.stem + ".png")
        out224_path = out224 / (img_path.stem + ".png")
        sitk.WriteImage(img512, str(out512_path))
        sitk.WriteImage(img224, str(out224_path))

        return (img_path.name, str(out512_path), str(out224_path))

    except Exception as e:
        print(f"⚠️  Erreur sur {img_path.name}: {e}")
        return None
        
records = []
for f in tqdm(files, desc="Prétraitement SimpleITK"):
    rec = preprocess_sitk(f, OUT_512, OUT_224)
    if rec:
        records.append(tuple(rec))   # ✅ conversion explicite

manifest = pd.DataFrame(records, columns=["filename", "path_512", "path_224"])
manifest.to_csv(OUT_ROOT / "preprocessed_manifest.csv", index=False)

print("✅ Prétraitement terminé.")
print("Images sauvegardées dans :", OUT_ROOT)
manifest.head()

samples = random.sample(list(manifest.index), 3)
fig, axes = plt.subplots(len(samples), 2, figsize=(10, 12))

for i, idx in enumerate(samples):
    row = manifest.loc[idx]
    img_224 = sitk.GetArrayFromImage(sitk.ReadImage(row.path_224))
    img_512 = sitk.GetArrayFromImage(sitk.ReadImage(row.path_512))

    axes[i, 0].imshow(img_224, cmap='gray')
    axes[i, 0].set_title(f"Image (224×224)")
    axes[i, 0].axis('off')

    axes[i, 1].imshow(img_512, cmap='gray')
    axes[i, 1].set_title("Image prétraitée (512×512)")
    axes[i, 1].axis('off')

plt.tight_layout()
plt.show()

META_PATH = "/kaggle/input/ram-w600-local/RAM-W600/Metadata.xlsx"

# Load the Excel metadata
metadata = pd.read_excel(META_PATH)
print("Metadata loaded:", metadata.shape)


metadata["Mapped Image Stem"] = metadata["Mapped Image Stem"].astype(str)
# 2) Extract stem from filenames (with side indicator)
manifest["stem"] = manifest["filename"].apply(lambda x: Path(x).stem)
# 3) Extract side information (L or R)
def get_side(s):
    if s.endswith("_L"):
        return "L"
    if s.endswith("_R"):
        return "R"
    return "?"

manifest["side"] = manifest["stem"].apply(get_side)

# 4) Remove _L or _R to match metadata stems
def remove_side_suffix(s):
    if s.endswith("_L") or s.endswith("_R"):
        return s[:-2]   # remove last 2 chars ("_L" or "_R")
    return s

manifest["stem_clean"] = manifest["stem"].apply(remove_side_suffix)

print("\nExample filename / stem / side / stem_clean:")
print(manifest[["filename", "stem", "side", "stem_clean"]].head())

# 5) Merge manifest with metadata
df = manifest.merge(
    metadata,
    left_on="stem_clean",
    right_on="Mapped Image Stem",
    how="inner"
)

print("\nMerged dataset size:", df.shape)
df.head()

dataset_stats = {
    "Num Images": len(df),
    "Num Patients": df["NormalizedPatientID"].nunique(),
    "Num Studies": df["NormalizedStudyID"].nunique(),
    "Num Institutions": df["InstitutionName"].nunique(),
    "RA Images": (df["IsRA"] == 1).sum(),
    "Non-RA Images": (df["IsRA"] == 0).sum(),
}

table1 = pd.DataFrame.from_dict(dataset_stats, orient="index", columns=["Count"])
table1

institution_dist = (
    df["InstitutionName"]
    .value_counts()
    .rename_axis("Institution")
    .reset_index(name="NumImages")
)

institution_dist

df["PatientAge"].value_counts().head(10)


df["PatientAge_num"] = pd.to_numeric(df["PatientAge"], errors="coerce")

age_stats = df["PatientAge_num"].describe()
age_stats

# Regrouper O → M
df["PatientSex_grouped"] = df["PatientSex"].replace({"O": "M"})
sex_dist_grouped = (
    df["PatientSex_grouped"]
    .value_counts()
    .rename_axis("Sex")
    .reset_index(name="Count")
)

sex_dist_grouped


# Calcul des pourcentages
sex_dist_grouped["Percentage"] = (
    100 * sex_dist_grouped["Count"] / sex_dist_grouped["Count"].sum()
)

# Plot
plt.figure(figsize=(6, 6))
plt.pie(
    sex_dist_grouped["Count"],
    labels=sex_dist_grouped["Sex"],
    autopct="%.1f%%",
    startangle=90,
    counterclock=False
)
plt.title("Sex Distribution of Patients")
plt.tight_layout()
plt.show()


# Global SvdH (Left + Right)
svdh_long = df[["SvdH_L", "SvdH_R"]].melt(
    value_vars=["SvdH_L", "SvdH_R"],
    var_name="Side",
    value_name="SvdH"
)

svdh_long["SvdH"] = pd.to_numeric(svdh_long["SvdH"], errors="coerce")

svdh_dist = (
    svdh_long["SvdH"]
    .value_counts()
    .sort_index()
    .rename_axis("SvdH Score")
    .reset_index(name="Count")
)


svdh_dist["Percentage"] = (
    100 * svdh_dist["Count"] / svdh_dist["Count"].sum()
)

plt.figure(figsize=(8, 5))

plt.barh(
    svdh_dist["SvdH Score"].astype(str),
    svdh_dist["Percentage"]
)

plt.xlabel("Percentage of Observations (%)")
plt.ylabel("SvdH Score")
plt.title("Distribution of Global SvdH Scores (Left + Right)")

# Optionnel : afficher la valeur % sur chaque barre
for i, v in enumerate(svdh_dist["Percentage"]):
    plt.text(v + 0.5, i, f"{v:.1f}%", va="center")

plt.tight_layout()
plt.show()


svdh_joints_L = df[
    ["1st MC_L", "Trapz_L", "Sc_L", "Lu_L", "DR_L", "DU_L"]
].melt(
    var_name="Joint",
    value_name="SvdH"
)

svdh_joints_L["Side"] = "Left"

svdh_joints_R = df[
    ["1st MC_R", "Trapz_R", "Sc_R", "Lu_R", "DR_R", "DU_R"]
].melt(
    var_name="Joint",
    value_name="SvdH"
)

svdh_joints_R["Side"] = "Right"

svdh_joints = pd.concat([svdh_joints_L, svdh_joints_R], ignore_index=True)
svdh_joints["SvdH"] = pd.to_numeric(svdh_joints["SvdH"], errors="coerce")

svdh_joint_dist = (
    svdh_joints["SvdH"]
    .value_counts()
    .sort_index()
    .rename_axis("Joint-level SvdH Score")
    .reset_index(name="Count")
)


svdh_joint_dist["Percentage"] = (
    100 * svdh_joint_dist["Count"] / svdh_joint_dist["Count"].sum()
)

plt.figure(figsize=(8, 5))

plt.barh(
    svdh_joint_dist["Joint-level SvdH Score"].astype(str),
    svdh_joint_dist["Percentage"]
)

plt.xlabel("Percentage of Observations (%)")
plt.ylabel("Joint-level SvdH Score")
plt.title("Distribution of Joint-level SvdH Scores (All Joints, Left + Right)")

# Afficher les pourcentages sur les barres
for i, v in enumerate(svdh_joint_dist["Percentage"]):
    plt.text(v + 0.5, i, f"{v:.1f}%", va="center")

plt.tight_layout()
plt.show()


followup_dist = (
    df.groupby("NormalizedPatientID")
      .size()
      .value_counts()
      .sort_index()
      .rename_axis("NumStudiesPerPatient")
      .reset_index(name="NumPatients")
)


followup_dist["Percentage"] = (
    100 * followup_dist["NumPatients"] / followup_dist["NumPatients"].sum()
)

plt.figure(figsize=(8, 5))

plt.barh(
    followup_dist["NumStudiesPerPatient"].astype(str),
    followup_dist["Percentage"]
)

plt.xlabel("Percentage of Patients (%)")
plt.ylabel("Number of Studies per Patient")
plt.title("Distribution of Longitudinal Follow-ups per Patient")

# Afficher les pourcentages sur les barres
for i, v in enumerate(followup_dist["Percentage"]):
    plt.text(v + 0.5, i, f"{v:.1f}%", va="center")

plt.tight_layout()
plt.show()


# --------------------------
# Transform for ResNet input
# --------------------------
resnet_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485], std=[0.229]),  # grayscale, we will repeat channels
])

# --------------------------
# Dataset for embeddings
# --------------------------
class EmbeddingDataset(Dataset):
    def __init__(self, df):
        self.df = df.reset_index(drop=True)

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]

        path = row["path_224"]
        img = Image.open(path).convert("L")

        img = resnet_transform(img)
        img = img.repeat(3, 1, 1)

        # Convert pandas Series → dict (VERY IMPORTANT)
        meta = row.to_dict()

        return img, meta


# ------------------------------------
# Create a function to modify ResNet
# ------------------------------------
def make_resnet(model_name="resnet50"):
    if model_name == "resnet50":
        net = models.resnet50(weights="IMAGENET1K_V1")
        feature_dim = 2048
    elif model_name == "resnet18":
        net = models.resnet18(weights="IMAGENET1K_V1")
        feature_dim = 512
    else:
        raise ValueError("Choose resnet18 or resnet50")

    # Replace classifier (fc) with Identity → output is embedding
    net.fc = nn.Identity()

    return net.to(device), feature_dim
    
resnet18, dim18 = make_resnet("resnet18")
resnet18.eval()
print("ResNet-18 ready. Output dim =", dim18)

resnet50, dim50 = make_resnet("resnet50")
resnet50.eval()
print("ResNet-50 ready. Output dim =", dim50)

def collate_meta(batch):
    images = []
    metas = []
    for img, meta in batch:
        images.append(img)
        metas.append(meta)   # keep as a dict

    images = torch.stack(images)   # batch images normally
    return images, metas           # metas stays list-of-dicts

# -----------------------------------
# Create Datasets and DataLoaders
# -----------------------------------
dataset = EmbeddingDataset(df)

loader18 = DataLoader(dataset, batch_size=32, shuffle=False, num_workers=2,
                      collate_fn=collate_meta)


# -----------------------------------
# Function to extract embeddings
# -----------------------------------
def extract_features(model, loader, feature_dim):
    features = []

    with torch.no_grad():
        for images, rows in tqdm(loader):
            images = images.to(device)
            feats = model(images).cpu().numpy()

            for f, r in zip(feats, rows):
                r = r.copy()       # avoid overwriting original meta
                r["feature"] = f   # attach embedding
                features.append(r)

    return pd.DataFrame(features)

# -----------------------------------
# Extract ResNet-18 features
# -----------------------------------
print("Extracting ResNet18 embeddings...")
df_feat18 = extract_features(resnet18, loader18, dim18)

with open("/kaggle/working/features_resnet18.pkl", "wb") as f:
    pickle.dump(df_feat18, f)

print("Saved ResNet18:", df_feat18.shape)


# -----------------------------------
# Extract ResNet-50 features
# -----------------------------------

loader50 = DataLoader(dataset, batch_size=16, shuffle=False, num_workers=0,
                      collate_fn=collate_meta)

print("Extracting ResNet50 embeddings...")
df_feat50 = extract_features(resnet50, loader50, dim50)

with open("/kaggle/working/features_resnet50.pkl", "wb") as f:
    pickle.dump(df_feat50, f)

print("Saved ResNet50:", df_feat50.shape)


# Load the extracted features
with open("/kaggle/working/features_resnet18.pkl", "rb") as f:
    df18 = pickle.load(f)

with open("/kaggle/working/features_resnet50.pkl", "rb") as f:
    df50 = pickle.load(f)

print(df18.shape, df50.shape)
print(df18.columns)

# Convert feature columns (numpy arrays) into a 2D matrix
X18 = np.vstack(df18["feature"].values)   # shape: (618, 512)
X50 = np.vstack(df50["feature"].values)   # shape: (618, 2048)

print("ResNet18 matrix:", X18.shape)
print("ResNet50 matrix:", X50.shape)


import umap.umap_ as umap
from sklearn.preprocessing import StandardScaler


scaler18 = StandardScaler()
X18_scaled = scaler18.fit_transform(X18)

scaler50 = StandardScaler()
X50_scaled = scaler50.fit_transform(X50)

print(X18_scaled.shape, X50_scaled.shape)

# 2D UMAP
umap2d_18 = umap.UMAP(
    n_neighbors=20,
    min_dist=0.1,
    metric="euclidean",
    n_components=2,
    random_state=42,
)
U18_2d = umap2d_18.fit_transform(X18_scaled)

umap2d_50 = umap.UMAP(
    n_neighbors=20,
    min_dist=0.1,
    metric="euclidean",
    n_components=2,
    random_state=42,
)
U50_2d = umap2d_50.fit_transform(X50_scaled)

print("U18_2d:", U18_2d.shape, "U50_2d:", U50_2d.shape)

# 3D UMAP
umap3d_18 = umap.UMAP(
    n_neighbors=20,
    min_dist=0.1,
    metric="euclidean",
    n_components=3,
    random_state=42,
)
U18_3d = umap3d_18.fit_transform(X18_scaled)

umap3d_50 = umap.UMAP(
    n_neighbors=20,
    min_dist=0.1,
    metric="euclidean",
    n_components=3,
    random_state=42,
)
U50_3d = umap3d_50.fit_transform(X50_scaled)

print("U18_3d:", U18_3d.shape, "U50_3d:", U50_3d.shape)


import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


def plot_umap_2d(U18, U50, labels, label_name, is_categorical=True):
    """
    U18, U50: 2D embeddings (N, 2)
    labels: array-like (N,)
    label_name: string for titles
    is_categorical: choose discrete colormap + legend behavior
    """
    labels = np.array(labels)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Left: ResNet18
    ax = axes[0]
    if is_categorical:
        # map unique labels to integers
        uniques = np.unique(labels)
        cmap = plt.get_cmap("tab10")
        for i, v in enumerate(uniques):
            mask = labels == v
            ax.scatter(U18[mask, 0], U18[mask, 1], s=10, alpha=0.8,
                       label=str(v), color=cmap(i % 10))
        ax.legend(title=label_name, fontsize=8)
    else:
        sc = ax.scatter(U18[:, 0], U18[:, 1], c=labels, s=10, alpha=0.8, cmap="viridis")
        cb = plt.colorbar(sc, ax=ax)
        cb.set_label(label_name)

    ax.set_title(f"UMAP 2D – ResNet18 – {label_name}")
    ax.set_xlabel("UMAP-1")
    ax.set_ylabel("UMAP-2")

    # Right: ResNet50
    ax = axes[1]
    if is_categorical:
        uniques = np.unique(labels)
        cmap = plt.get_cmap("tab10")
        for i, v in enumerate(uniques):
            mask = labels == v
            ax.scatter(U50[mask, 0], U50[mask, 1], s=10, alpha=0.8,
                       label=str(v), color=cmap(i % 10))
        ax.legend(title=label_name, fontsize=8)
    else:
        sc = ax.scatter(U50[:, 0], U50[:, 1], c=labels, s=10, alpha=0.8, cmap="viridis")
        cb = plt.colorbar(sc, ax=ax)
        cb.set_label(label_name)

    ax.set_title(f"UMAP 2D – ResNet50 – {label_name}")
    ax.set_xlabel("UMAP-1")
    ax.set_ylabel("UMAP-2")

    plt.tight_layout()
    plt.show()


def plot_umap_3d(U18, U50, labels, label_name, is_categorical=True):
    labels = np.array(labels)

    fig = plt.figure(figsize=(12, 5))

    # Left: ResNet18
    ax = fig.add_subplot(1, 2, 1, projection="3d")
    if is_categorical:
        uniques = np.unique(labels)
        cmap = plt.get_cmap("tab10")
        for i, v in enumerate(uniques):
            mask = labels == v
            ax.scatter(U18[mask, 0], U18[mask, 1], U18[mask, 2],
                       s=10, alpha=0.8, label=str(v), color=cmap(i % 10))
        ax.legend(title=label_name, fontsize=8)
    else:
        sc = ax.scatter(U18[:, 0], U18[:, 1], U18[:, 2],
                        c=labels, s=10, alpha=0.8, cmap="viridis")
        cb = plt.colorbar(sc, ax=ax, shrink=0.6)
        cb.set_label(label_name)

    ax.set_title(f"UMAP 3D – ResNet18 – {label_name}")
    ax.set_xlabel("UMAP-1")
    ax.set_ylabel("UMAP-2")
    ax.set_zlabel("UMAP-3")

    # Right: ResNet50
    ax = fig.add_subplot(1, 2, 2, projection="3d")
    if is_categorical:
        uniques = np.unique(labels)
        cmap = plt.get_cmap("tab10")
        for i, v in enumerate(uniques):
            mask = labels == v
            ax.scatter(U50[mask, 0], U50[mask, 1], U50[mask, 2],
                       s=10, alpha=0.8, label=str(v), color=cmap(i % 10))
        ax.legend(title=label_name, fontsize=8)
    else:
        sc = ax.scatter(U50[:, 0], U50[:, 1], U50[:, 2],
                        c=labels, s=10, alpha=0.8, cmap="viridis")
        cb = plt.colorbar(sc, ax=ax, shrink=0.6)
        cb.set_label(label_name)

    ax.set_title(f"UMAP 3D – ResNet50 – {label_name}")
    ax.set_xlabel("UMAP-1")
    ax.set_ylabel("UMAP-2")
    ax.set_zlabel("UMAP-3")

    plt.tight_layout()
    plt.show()


from torchvision import models, transforms


# -----------------------------
# Transform for ResNet input
# -----------------------------
transform_resnet = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485], std=[0.229]),   # grayscale → convert below
])

# -----------------------------
# Load pretrained ResNet50
# -----------------------------
resnet = models.resnet50(weights="IMAGENET1K_V1")
resnet.fc = nn.Identity()            # output = 2048-dim embedding
resnet = resnet.to(device)
resnet.eval()

# -----------------------------
# Feature extraction function
# -----------------------------
def extract_embedding(img_path):
    img = Image.open(img_path).convert("L")  # grayscale

    # convert to 3-channel for ResNet
    img = transform_resnet(img)
    img = img.repeat(3, 1, 1)               # (1,H,W) → (3,H,W)

    img = img.unsqueeze(0).to(device)

    with torch.no_grad():
        feat = resnet(img).cpu().numpy().flatten()

    return feat  # shape 2048

# -----------------------------
# Extract embeddings for all images
# -----------------------------
all_features = []

for i, row in tqdm(df.iterrows(), total=len(df)):
    feat = extract_embedding(row["path_224"])

    all_features.append({
        "filename": row["filename"],
        "stem_clean": row["stem_clean"],
        "side": row["side"],
        "IsRA": row["IsRA"],
        "Age": row["PatientAge"],
        "Sex": row["PatientSex"],
        "Institution": row["InstitutionName"],
        "StudyDate": row["StudyDate (Days)"],
        # add others if needed
        "feature": feat
    })

# convert to DataFrame with numpy arrays
features_df = pd.DataFrame(all_features)

# Save
import pickle
with open("/kaggle/working/features.pkl", "wb") as f:
    pickle.dump(features_df, f)

print("Saved embeddings:", features_df.shape)
features_df.head()

labels_IsRA = df18["IsRA"].values

plot_umap_2d(U18_2d, U50_2d, labels_IsRA, "IsRA", is_categorical=True)
plot_umap_3d(U18_3d, U50_3d, labels_IsRA, "IsRA", is_categorical=True)

labels_sex = df18["PatientSex"].values

plot_umap_2d(U18_2d, U50_2d, labels_sex, "PatientSex", is_categorical=True)
plot_umap_3d(U18_3d, U50_3d, labels_sex, "PatientSex", is_categorical=True)

labels_svdh_L = df18["SvdH_L"].values

plot_umap_2d(U18_2d, U50_2d, labels_svdh_L, "SvdH_L (Left)", is_categorical=False)
plot_umap_3d(U18_3d, U50_3d, labels_svdh_L, "SvdH_L (Left)", is_categorical=False)

labels_svdh_R = df18["SvdH_R"].values

plot_umap_2d(U18_2d, U50_2d, labels_svdh_R, "SvdH_R (Right)", is_categorical=False)
plot_umap_3d(U18_3d, U50_3d, labels_svdh_R, "SvdH_R (Right)", is_categorical=False)


labels_institution = df18["InstitutionName"].values

plot_umap_2d(
    U18_2d, U50_2d,
    labels_institution,
    "Institution",
    is_categorical=True
)

plot_umap_3d(
    U18_3d, U50_3d,
    labels_institution,
    "Institution",
    is_categorical=True
)

# we'll work on df18 as the reference table
dfm = df18.copy()

# --- Parse ImagerPixelSpacing "[0.149, 0.149]" → px_row, px_col
def parse_vec2(x):
    try:
        v = ast.literal_eval(str(x))
        if isinstance(v, (list, tuple)) and len(v) == 2:
            return float(v[0]), float(v[1])
    except Exception:
        pass
    return np.nan, np.nan

px_vals = dfm["ImagerPixelSpacing"].apply(parse_vec2)
dfm["px_row"] = px_vals.apply(lambda v: v[0])
dfm["px_col"] = px_vals.apply(lambda v: v[1])

# --- Parse [Rows, Columns] "[1670, 2010]" → rows, cols
def parse_int2(x):
    try:
        v = ast.literal_eval(str(x))
        if isinstance(v, (list, tuple)) and len(v) == 2:
            return int(v[0]), int(v[1])
    except Exception:
        pass
    return np.nan, np.nan

rc_vals = dfm["[Rows, Columns]"].apply(parse_int2)
dfm["rows"] = rc_vals.apply(lambda v: v[0])
dfm["cols"] = rc_vals.apply(lambda v: v[1])



# --- continuous metadata columns
meta_cont_cols = [
    "PatientAge",
    "StudyDate (Days)",
    "px_row", "px_col",
    "rows", "cols",
]

meta_cat_cols = [
    "PatientSex",
    "InstitutionName",  # used as feature but we won't plot it
    "side",
]

# 1) Make sure all continuous columns are numeric
for col in meta_cont_cols:
    # turn things like "Unknown", "", etc. into NaN
    dfm[col] = pd.to_numeric(dfm[col], errors="coerce")

# 2) Now we can safely fill NaNs with the column mean
dfm[meta_cont_cols] = dfm[meta_cont_cols].fillna(dfm[meta_cont_cols].mean())

# 3) Categorical: replace NaN with "Unknown"
dfm[meta_cat_cols] = dfm[meta_cat_cols].fillna("Unknown")

# 4) One-hot encode categorical
meta_cat = pd.get_dummies(dfm[meta_cat_cols], drop_first=False)

# 5) Standardize continuous metadata
from sklearn.preprocessing import StandardScaler
scaler_meta = StandardScaler()
meta_cont_scaled = scaler_meta.fit_transform(dfm[meta_cont_cols])

# 6) Final metadata matrix
META = np.hstack([meta_cont_scaled, meta_cat.values])
print("META shape:", META.shape)


Z50 = np.hstack([X50_scaled, META])

print("Z50:", Z50.shape)

def plot_umap2d(pts, labels, title, cmap="viridis", categorical=False):
    plt.figure(figsize=(8,6))
    if categorical:
        plt.scatter(pts[:,0], pts[:,1], c=labels, cmap="coolwarm", s=12)
    else:
        plt.scatter(pts[:,0], pts[:,1], c=labels, cmap=cmap, s=12)
    plt.colorbar()
    plt.title(title)
    plt.show()

# Fit UMAP 2D
umap2d = umap.UMAP(
    n_neighbors=20,
    min_dist=0.1,
    metric="euclidean",
    n_components=2,
    random_state=42
).fit_transform(Z50)

print("UMAP 2D:", umap2d.shape)

plot_umap2d(umap2d, dfm["IsRA"], "Hybrid UMAP 2D — RA vs Non-RA", categorical=True)


plot_umap2d(umap2d, dfm["SvdH_L"], "Hybrid UMAP 2D — Left Erosion Severity (SvdH_L)")

from sklearn.manifold import Isomap
# Labels RA
labels_ra = dfm["IsRA"].values   # 0 = Non-RA, 1 = RA

# Isomap 2D
iso2d_ra = Isomap(
    n_neighbors=20,
    n_components=2
).fit_transform(Z50)

# Plot
plt.figure(figsize=(8,6))
scatter = plt.scatter(
    iso2d_ra[:,0],
    iso2d_ra[:,1],
    c=labels_ra,
    cmap="coolwarm",
    s=15,
    alpha=0.8
)

plt.xlabel("Isomap-1")
plt.ylabel("Isomap-2")
plt.title("Isomap 2D — RA vs Non-RA (Pretrained Features)")
plt.colorbar(scatter, label="IsRA (0 = Non-RA, 1 = RA)")
plt.tight_layout()
plt.show()


from mpl_toolkits.mplot3d import Axes3D

iso3d_ra = Isomap(
    n_neighbors=20,
    n_components=3
).fit_transform(Z50)

fig = plt.figure(figsize=(9,7))
ax = fig.add_subplot(111, projection='3d')

p = ax.scatter(
    iso3d_ra[:,0],
    iso3d_ra[:,1],
    iso3d_ra[:,2],
    c=labels_ra,
    cmap="coolwarm",
    s=20,
    alpha=0.8
)

ax.set_xlabel("Isomap-1")
ax.set_ylabel("Isomap-2")
ax.set_zlabel("Isomap-3")
ax.set_title("Isomap 3D — RA vs Non-RA")

fig.colorbar(p, label="IsRA")
plt.tight_layout()
plt.show()


from mpl_toolkits.mplot3d import Axes3D

umap3d = umap.UMAP(
    n_neighbors=20,
    min_dist=0.1,
    metric="euclidean",
    n_components=3,
    random_state=42
).fit_transform(Z50)

print("UMAP 3D:", umap3d.shape)

def plot_umap3d(pts, labels, title):
    fig = plt.figure(figsize=(9,7))
    ax = fig.add_subplot(111, projection='3d')
    p = ax.scatter(pts[:,0], pts[:,1], pts[:,2],
                   c=labels, cmap="viridis", s=20)
    fig.colorbar(p)
    ax.set_title(title)
    plt.show()

plot_umap3d(umap3d, dfm["SvdH_L"], "Hybrid UMAP 3D — Left Erosion Severity")

from sklearn.manifold import Isomap


iso2d = Isomap(
    n_neighbors=20,
    n_components=2
).fit_transform(Z50)

plot_umap2d(iso2d, dfm["SvdH_L"], "Isomap 2D — Left Erosion Severity")


iso3d = Isomap(
    n_neighbors=20,
    n_components=3
).fit_transform(Z50)

plot_umap3d(iso3d, dfm["SvdH_L"], "Isomap 3D — Left Erosion Severity")


# ================== CHEMINS CORRIGÉS ==================
BASE_MASK_DIR = Path("/kaggle/input/ram-w600-local/RAM-W600/BoneSegmentation/masks")
RAW_DIR = Path("/kaggle/input/ram-w600-local/RAM-W600/BoneSegmentation/images")

OUT_512 = Path("/kaggle/working/preprocessed_512")
OUT_ROIS = Path("/kaggle/working/joint_rois_224")

OUT_512.mkdir(parents=True, exist_ok=True)
OUT_ROIS.mkdir(parents=True, exist_ok=True)

# ================== 1. Récupérer TOUS les masques dans tous les splits ==================
all_mask_paths = list(BASE_MASK_DIR.rglob("*.npy"))
print(f"{len(all_mask_paths)} masques .npy trouvés dans train/val/test")

stems_with_mask = [p.stem for p in all_mask_paths]
print(f"{len(stems_with_mask)} stems uniques avec masque GT")

# ================== 2. Préprocessing 512x512 avec contraste fort ==================
def preprocess_image(stem):
    # Recherche l'image correspondante (extension variable)
    possible_imgs = list(RAW_DIR.glob(f"{stem}.*"))
    if not possible_imgs:
        return None
    img_path = possible_imgs[0]
    
    out_path = OUT_512 / (stem + ".png")
    if out_path.exists():
        return str(out_path)
    
    img = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        return None
    
    img_resized = cv2.resize(img, (512, 512), interpolation=cv2.INTER_LINEAR)
    
    clahe = cv2.createCLAHE(clipLimit=5.0, tileGridSize=(8,8))
    img_eq = clahe.apply(img_resized)
    
    cv2.imwrite(str(out_path), img_eq)
    return str(out_path)

preprocessed_paths = {}
for stem in tqdm(stems_with_mask, desc="Préprocessing images avec masque GT"):
    path_512 = preprocess_image(stem)
    if path_512:
        preprocessed_paths[stem] = path_512

print(f"{len(preprocessed_paths)} images prétraitées avec succès.")

# ================== 3. Extraction des 3 ROIs ==================
def extract_3_joint_rois(stem, img_512_path):
    img = cv2.imread(img_512_path, cv2.IMREAD_GRAYSCALE)
    
    # Recherche le masque correspondant dans tous les splits
    possible_masks = list(BASE_MASK_DIR.rglob(f"{stem}.npy"))
    if not possible_masks:
        return []
    mask_path = possible_masks[0]
    
    mask = np.load(mask_path)
    if mask.ndim == 3:  # multi-canal
        mask_bin = (mask.sum(axis=0) > 0).astype(np.uint8)
    else:
        mask_bin = (mask > 0).astype(np.uint8)
    
    mask_255 = mask_bin * 255
    
    contours, _ = cv2.findContours(mask_255, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return []
    
    c = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(c)
    
    pad = 80
    x1 = max(0, x - pad)
    y1 = max(0, y - pad)
    x2 = min(512, x + w + pad)
    y2 = min(512, y + h + pad)
    
    crop = img[y1:y2, x1:x2]
    
    clahe = cv2.createCLAHE(clipLimit=5.0, tileGridSize=(8,8))
    crop_clahe = clahe.apply(crop)
    crop_final = cv2.normalize(crop_clahe, None, 0, 255, cv2.NORM_MINMAX)
    
    H, W = crop_final.shape
    xs = np.linspace(0, W, 4, dtype=int)
    
    records = []
    for i in range(3):
        sx1, sx2 = xs[i], xs[i+1]
        if sx2 - sx1 < 40:
            continue
        
        sub = crop_final[:, sx1:sx2]
        sub_resized = cv2.resize(sub, (224, 224), interpolation=cv2.INTER_LINEAR)
        
        roi_name = f"{stem}_joint{i+1}.png"
        cv2.imwrite(str(OUT_ROIS / roi_name), sub_resized)
        
        records.append({
            "stem": stem,
            "roi_filename": roi_name,
            "joint_index": i+1,
            "roi_path": str(OUT_ROIS / roi_name)
        })
    
    return records
    

# ================== 4. Extraction ==================
all_roi_records = []
for stem, path_512 in tqdm(preprocessed_paths.items(), desc="Extraction 3 ROIs"):
    recs = extract_3_joint_rois(stem, path_512)
    all_roi_records.extend(recs)

print(f"{len(all_roi_records)} ROIs extraits au total (devrait être ~1854 si 618 masques)")


df_rois = pd.DataFrame(all_roi_records)
df_rois.to_csv("/kaggle/working/joint_rois_manifest_final.csv", index=False)

# ================== 5. Vérification visuelle ==================
if len(df_rois) > 0:
    samples = df_rois.sample(min(9, len(df_rois)), random_state=42)
    
    fig, axes = plt.subplots(3, 3, figsize=(12, 12))
    axes = axes.ravel()
    
    for i, row in enumerate(samples.itertuples()):
        img = cv2.imread(row.roi_path, cv2.IMREAD_GRAYSCALE)
        axes[i].imshow(img, cmap="gray")
        axes[i].set_title(f"{row.roi_filename}\nJoint {row.joint_index}")
        axes[i].axis("off")
    
    for j in range(i+1, 9):
        axes[j].axis("off")
    
    plt.suptitle("9 extracted ROIs – bones and joint spaces")
    plt.tight_layout()
    plt.show()
else:
    print("Aucun ROI extrait – vérifie les chemins.")

# Fonction pour séparer les layers (upper / lower bone)
def separate_bone_layers(roi_img):
    # Binarisation simple + distance transform
    _, binary = cv2.threshold(roi_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    distance = distance_transform_edt(binary)
    
    # Local maxima pour markers
    local_maxi = peak_local_max(distance, min_distance=20, labels=binary)
    markers = np.zeros(binary.shape, dtype=np.int32)
    markers[tuple(local_maxi.T)] = np.arange(1, len(local_maxi) + 1)
    
    # Watershed
    labels = watershed(-distance, markers, mask=binary)
    
    # Sépare en 2 layers (la plus haute et la plus basse)
    upper = np.zeros_like(roi_img)
    lower = np.zeros_like(roi_img)
    
    # Assume layer 1 = upper, layer 2 = lower (basé sur position y)
    if len(np.unique(labels)) >= 2:
        props = []
        for lbl in np.unique(labels)[1:]:
            mask_lbl = (labels == lbl)
            y_mean = np.mean(np.where(mask_lbl)[0])
            props.append((y_mean, mask_lbl))
        
        props.sort(key=lambda x: x[0])  # tri par position y (haut → bas)
        upper = props[0][1] * roi_img
        lower = props[1][1] * roi_img if len(props) > 1 else np.zeros_like(roi_img)
    
    reconstructed = upper + lower
    return upper, lower, reconstructed

# Fonction pour générer synthetic JSN
def generate_synthetic_jsn(roi_img, upper, lower, shift_pixels=4):
    # Shift la lower layer vers le haut (rétrécit l'espace)
    shifted_lower = np.roll(lower, shift_pixels, axis=0)
    shifted_lower[:shift_pixels, :] = 0  # nettoie le haut
    
    synthetic = upper + shifted_lower
    return synthetic

# Chemins (inchangés)
ROI_DIR = Path("/kaggle/working/joint_rois_224")
FIGURE_DIR = Path("/kaggle/working/figures")
FIGURE_DIR.mkdir(parents=True, exist_ok=True)

df_rois = pd.read_csv("/kaggle/working/joint_rois_manifest_final.csv")  # ou ton nom exact

# Fonction bone layer separation (inchangée)
def separate_bone_layers(roi_img):
    _, binary = cv2.threshold(roi_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    distance = distance_transform_edt(binary)
    
    local_maxi = peak_local_max(distance, min_distance=20, labels=binary)
    markers = np.zeros(binary.shape, dtype=np.int32)
    markers[tuple(local_maxi.T)] = np.arange(1, len(local_maxi) + 1)
    
    labels = watershed(-distance, markers, mask=binary)
    
    upper = np.zeros_like(roi_img)
    lower = np.zeros_like(roi_img)
    
    if len(np.unique(labels)) >= 2:
        props = []
        for lbl in np.unique(labels)[1:]:
            mask_lbl = (labels == lbl)
            y_mean = np.mean(np.where(mask_lbl)[0])
            props.append((y_mean, mask_lbl))
        
        props.sort(key=lambda x: x[0])
        upper = props[0][1] * roi_img
        lower = props[1][1] * roi_img if len(props) > 1 else np.zeros_like(roi_img)
    
    reconstructed = upper + lower
    return upper.astype(np.uint8), lower.astype(np.uint8), reconstructed.astype(np.uint8)

# Fonction synthetic JSN (inchangée)
def generate_synthetic_jsn(roi_img, upper, lower, shift_pixels=4):
    shifted_lower = np.roll(lower, -shift_pixels, axis=0)  # négatif pour rétrécir vers le haut
    shifted_lower[-shift_pixels:, :] = 0
    synthetic = upper + shifted_lower
    return synthetic.astype(np.uint8)

# 1. Figure bone layer separation → PNG
fig, axes = plt.subplots(3, 4, figsize=(16, 12))
axes = axes.ravel()

samples = df_rois.sample(3, random_state=42)

for i, row in enumerate(samples.itertuples()):
    roi = cv2.imread(str(ROI_DIR / row.roi_filename), cv2.IMREAD_GRAYSCALE)
    
    upper, lower, recon = separate_bone_layers(roi)
    
    images = [roi, upper, lower, recon]
    titles = ["Original", "Upper layer", "Lower layer", "Reconstructed"]
    
    for j in range(4):
        axes[i*4 + j].imshow(images[j], cmap='gray')
        axes[i*4 + j].set_title(titles[j])
        axes[i*4 + j].axis('off')

plt.suptitle("Bone Layer Separation Examples", fontsize=16)
plt.tight_layout()
plt.savefig(FIGURE_DIR / "bone_layer_separation_examples.png", dpi=300, bbox_inches='tight')
plt.show()

# 2. Figure synthetic JSN → PNG
fig, axes = plt.subplots(1, 5, figsize=(20, 5))

sample_roi = cv2.imread(str(ROI_DIR / samples.iloc[0].roi_filename), cv2.IMREAD_GRAYSCALE)
upper, lower, _ = separate_bone_layers(sample_roi)

shifts = [0, 2, 4, 6, 8]
titles = ["Original", "Mild (2px)", "Moderate (4px)", "Severe (6px)", "Extreme (8px)"]

for i, shift in enumerate(shifts):
    synth = generate_synthetic_jsn(sample_roi, upper, lower, shift)
    axes[i].imshow(synth, cmap='gray')
    axes[i].set_title(titles[i])
    axes[i].axis('off')

plt.suptitle("Synthetic JSN Generation – Progressive Narrowing", fontsize=16)
plt.tight_layout()
plt.savefig(FIGURE_DIR / "synthetic_jsn_progression.png", dpi=300, bbox_inches='tight')
plt.show()

# 3. Figure shift vs JSW → PNG
jsn_deltas = []
shifts_test = [0, 2, 4, 6, 8]

for row in df_rois.sample(100, random_state=123).itertuples():
    roi = cv2.imread(str(ROI_DIR / row.roi_filename), cv2.IMREAD_GRAYSCALE)
    upper, lower, _ = separate_bone_layers(roi)
    
    # JSW original (distance moyenne entre bords)
    mask_upper = upper > 50
    mask_lower = lower > 50
    if mask_upper.any() and mask_lower.any():
        y_upper_max = np.max(np.where(mask_upper)[0])
        y_lower_min = np.min(np.where(mask_lower)[0])
        jsw_orig = y_lower_min - y_upper_max
        
        deltas = []
        for shift in shifts_test[1:]:
            synth_lower = np.roll(lower, -shift, axis=0)
            synth_lower[-shift:, :] = 0
            mask_synth = synth_lower > 50
            if mask_synth.any():
                y_synth_min = np.min(np.where(mask_synth)[0])
                jsw_synth = y_synth_min - y_upper_max
                deltas.append(jsw_orig - jsw_synth)
        
        jsn_deltas.append(deltas)

# Moyenne sur 100 ROIs
mean_deltas = np.mean(jsn_deltas, axis=0)

plt.figure(figsize=(8, 6))
plt.plot(shifts_test[1:], mean_deltas, 'o-', label='Measured reduction')
plt.plot(shifts_test[1:], shifts_test[1:], 'r--', label='Theoretical (1:1)')
plt.xlabel("Imposed pixel shift")
plt.ylabel("Mean JSW reduction (pixels)")
plt.title("Imposed shift vs Measured JSW Reduction")
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig(FIGURE_DIR / "jsn_shift_vs_jsw.png", dpi=300, bbox_inches='tight')
plt.show()

import scipy.ndimage as ndimage
from skimage.morphology import skeletonize
from scipy.optimize import curve_fit

base_path = Path("/kaggle/input/ram-w600-local/RAM-W600")
masks_test_path = base_path / "BoneSegmentation" / "masks" / "test"

pixel_spacing = 0.15

JOINT_PAIRS = [(1,6),(1,4),(6,0),(4,0),(0,8),(0,11)]

bone_name_dict = {0: "Capitate", 1: "DistalRadius", 2: "DistalUlna", 3: "Hamate", 4: "Lunate",
                  5: "Pisiform&Triquetrum", 6: "Scaphoid", 7: "Trapezium", 8: "Trapezoid",
                  9: "metacarpal1st", 10: "metacarpal2nd", 11: "metacarpal3rd",
                  12: "metacarpal4th", 13: "metacarpal5th"}

def measure_jsw_subpixel(mask1, mask2):
    dist1 = ndimage.distance_transform_edt(~mask1)
    dist2 = ndimage.distance_transform_edt(~mask2)
    contact = (dist1 > 0) & (dist2 > 0)
    if not np.any(contact):
        return None
    
    distances = dist1[contact] + dist2[contact]
    min_jsw = distances.min()
    min_jsw = max(min_jsw, 0.0)
    
    skeleton = skeletonize(contact)
    if np.any(skeleton):
        profile = (dist1 + dist2)[skeleton]
        if len(profile) >= 3:
            idx_min = np.argmin(profile)
            x = np.arange(len(profile))
            try:
                popt, _ = curve_fit(lambda x,a,b,c: a*(x-b)**2 + c, 
                                    x[max(0,idx_min-5):idx_min+6], 
                                    profile[max(0,idx_min-5):idx_min+6], 
                                    p0=[1.0, idx_min, profile[idx_min]], maxfev=2000)
                sub_min = popt[2]
                min_jsw = max(sub_min, min_jsw)
            except:
                pass
    
    return {"min_mm": min_jsw * pixel_spacing}

test_files = sorted([f for f in os.listdir(masks_test_path) if f.endswith('.npy')])

results = []
for fname in test_files:
    gt_masks = np.load(masks_test_path / fname)
    if gt_masks.shape[0] != 14:
        gt_masks = gt_masks.transpose(2,0,1)
    
    for b1, b2 in JOINT_PAIRS:
        joint = f"{bone_name_dict[b1]}-{bone_name_dict[b2]}"
        res = measure_jsw_subpixel(gt_masks[b1]>0.5, gt_masks[b2]>0.5)
        if res:
            results.append({"fname": fname, "joint": joint, "min_mm": res["min_mm"]})

df_jsw_gt = pd.DataFrame(results)
df_jsw_gt.to_csv("/kaggle/working/jsw_gt_results.csv", index=False)

table_gt = df_jsw_gt.groupby("joint")["min_mm"].agg(["mean", "std"]).round(3)
print("Table JSW min sur annotations expertes (mm)")
print(table_gt)

results = []
for fname in test_files:
    gt_masks = np.load(masks_test_path / fname)
    if gt_masks.shape[0] != 14:
        gt_masks = gt_masks.transpose(2,0,1)
    
    for b1, b2 in JOINT_PAIRS:
        joint = f"{bone_name_dict[b1]}-{bone_name_dict[b2]}"
        res = measure_jsw_subpixel(gt_masks[b1]>0.5, gt_masks[b2]>0.5)
        if res:
            results.append({"fname": fname, "joint": joint, "min_mm": res["min_mm"]})

df_jsw_gt = pd.DataFrame(results)
table_gt = df_jsw_gt.groupby("joint")["min_mm"].agg(["mean", "std"]).round(3)
print(table_gt)

# Chemins (adaptés à ton dataset Kaggle)
base_path = Path("/kaggle/input/ram-w600-local/RAM-W600")
masks_test_path = base_path / "BoneSegmentation" / "masks" / "test"

pixel_spacing = 0.15  # mm/pixel

JOINT_PAIRS = [(1,6), (1,4), (6,0), (4,0), (0,8), (0,11)]

bone_name_dict = {
    0: "Capitate", 1: "DistalRadius", 2: "DistalUlna", 3: "Hamate", 4: "Lunate",
    5: "Pisiform&Triquetrum", 6: "Scaphoid", 7: "Trapezium", 8: "Trapezoid",
    9: "metacarpal1st", 10: "metacarpal2nd", 11: "metacarpal3rd",
    12: "metacarpal4th", 13: "metacarpal5th"
}

def measure_jsw_subpixel(mask1, mask2):
    """
    Mesure sub-pixel du Joint Space Width (min seulement, car c'est le plus pertinent cliniquement)
    """
    dist1 = ndimage.distance_transform_edt(~mask1)
    dist2 = ndimage.distance_transform_edt(~mask2)
    contact = (dist1 > 0) & (dist2 > 0)
    
    if not np.any(contact):
        return None
    
    distances = dist1[contact] + dist2[contact]
    min_jsw = distances.min()
    min_jsw = max(min_jsw, 0.0)  # jamais négatif
    
    # Tentative d'affinage sub-pixel sur le profil du squelette
    skeleton = skeletonize(contact)
    if np.any(skeleton):
        profile = (dist1 + dist2)[skeleton]
        if len(profile) >= 3:
            idx_min = np.argmin(profile)
            x = np.arange(len(profile))
            # Plage plus large pour éviter covariance warning
            fit_range = slice(max(0, idx_min-5), idx_min+6)
            try:
                popt, _ = curve_fit(
                    lambda x, a, b, c: a*(x-b)**2 + c,
                    x[fit_range],
                    profile[fit_range],
                    p0=[1.0, idx_min, profile[idx_min]],
                    maxfev=3000
                )
                subpixel_min = popt[2]
                if subpixel_min > 0:
                    min_jsw = subpixel_min  # on prend l'affinage si positif
            except Exception:
                pass  # on garde le min classique si fit échoue
    
    return {"min_mm": min_jsw * pixel_spacing}

# Liste des fichiers test
test_files = sorted([f for f in os.listdir(masks_test_path) if f.endswith('.npy')])

print(f"Nombre de masques test trouvés : {len(test_files)}")

results = []
for fname in test_files:
    gt_masks = np.load(masks_test_path / fname)
    if gt_masks.shape[0] != 14:
        gt_masks = gt_masks.transpose(2, 0, 1)  # → (14, H, W)
    
    for b1, b2 in JOINT_PAIRS:
        joint = f"{bone_name_dict[b1]}-{bone_name_dict[b2]}"
        res = measure_jsw_subpixel(gt_masks[b1] > 0.5, gt_masks[b2] > 0.5)
        if res is not None:
            results.append({
                "fname": fname,
                "joint": joint,
                "min_mm": res["min_mm"]
            })

df_jsw_gt = pd.DataFrame(results)

if df_jsw_gt.empty:
    print("Aucun résultat valide calculé. Vérifie les masques / paires de joints.")
else:
    # Tableau récapitulatif
    table_gt = df_jsw_gt.groupby("joint")["min_mm"].agg(["mean", "std", "min", "max", "count"]).round(3)
    print("\nTable JSW min sur annotations expertes (GT) - test set")
    print(table_gt)
    
    # Sauvegarde
    df_jsw_gt.to_csv("/kaggle/working/jsw_gt_results.csv", index=False)
    print("\nRésultats sauvegardés dans /kaggle/working/jsw_gt_results.csv")

import os, json, random
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

import torchvision
from torchvision import transforms
from torchvision.models import resnet50, ResNet50_Weights

from sklearn.metrics import (
    roc_auc_score, average_precision_score,
    confusion_matrix, precision_recall_fscore_support,
    balanced_accuracy_score, matthews_corrcoef,
    roc_curve, precision_recall_curve
)
import matplotlib.pyplot as plt

# ------------------------
# 0) Reproducibility
# ------------------------
def seed_everything(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = False
    torch.backends.cudnn.benchmark = True

seed_everything(42)

device = "cuda" if torch.cuda.is_available() else "cpu"
print("Device:", device)

# ------------------------
# 1) Build dataset table
# ------------------------
BASE = Path("/kaggle/input/ram-w600-local/RAM-W600/SvdHBEScoreClassification")
JSON_GT = BASE / "JointBE_SvdH_GT.json"

SPLITS = ["train", "val", "test"]
BONES  = ["DistalRadius", "DistalUlna", "Lunate", "Metacarpal1st", "Scaphoid", "Trapzium"]

print("BASE exists:", BASE.exists())
print("JSON exists:", JSON_GT.exists())

with open(JSON_GT, "r") as f:
    data = json.load(f)

label_dict = {e["identifier"]: e["joints"] for e in data}

records, missing_ids, missing_files = [], 0, 0

for split in SPLITS:
    split_dir = BASE / split
    if not split_dir.exists():
        print("Missing split dir:", split_dir)
        continue

    for case_dir in split_dir.iterdir():
        if not case_dir.is_dir():
            continue
        identifier = case_dir.name

        if identifier not in label_dict:
            missing_ids += 1
            continue

        joints = label_dict[identifier]

        for bone in BONES:
            img_path = case_dir / f"{bone}.bmp"
            if not img_path.exists():
                missing_files += 1
                continue
            if bone not in joints:
                continue

            ero_label = int(joints[bone])
            records.append({
                "split": split,
                "identifier": identifier,
                "bone": bone,
                "image_path": str(img_path),
                "ero_label": ero_label,
                "ero_bin": int(ero_label > 0)   # binary target: erosion present?
            })


df = pd.DataFrame(records)
print("Rows:", len(df))
print("Missing identifiers in JSON:", missing_ids)
print("Missing BMP files:", missing_files)

print("\nBinary label distribution (global):")
print(df["ero_bin"].value_counts())

print("\nBinary label distribution by split:")
print(df.groupby(["split", "ero_bin"]).size().unstack(fill_value=0))

OUT_CSV = Path("/kaggle/working/ero_bone_dataset.csv")
df.to_csv(OUT_CSV, index=False)
print("\nSaved:", OUT_CSV)

print("\n🔹 Distribution des classes originales (SvH) par split:")
dist_ero_label = (
    df.groupby(["split", "ero_label"])
      .size()
      .unstack(fill_value=0)
      .sort_index(axis=1)
)
print(dist_ero_label)

df_train = df[df["split"] == "train"].reset_index(drop=True)
df_val   = df[df["split"] == "val"].reset_index(drop=True)
df_test  = df[df["split"] == "test"].reset_index(drop=True)

# ------------------------
# 2) Compute TRAIN mean/std (recommended in several medical imaging pipelines)
#    (We compute on resized tensors, before normalization.)
# ------------------------
class RawTensorDataset(Dataset):
    def __init__(self, df, size=224):
        self.df = df.reset_index(drop=True)
        self.tf = transforms.Compose([
            transforms.Resize((size, size)),
            transforms.ToTensor()
        ])
    def __len__(self):
        return len(self.df)
    def __getitem__(self, idx):
        img = Image.open(self.df.loc[idx, "image_path"]).convert("L").convert("RGB")
        return self.tf(img)

def compute_mean_std(df_train, batch_size=64):
    loader = DataLoader(
        RawTensorDataset(df_train),
        batch_size=batch_size, shuffle=False
    )
    n = 0
    mean = torch.zeros(3)
    var  = torch.zeros(3)

    for x in loader:
        b = x.size(0)
        x = x.view(b, 3, -1)
        mean += x.mean(dim=2).sum(dim=0)
        var  += x.var(dim=2).sum(dim=0)
        n += b

    mean /= n
    std = torch.sqrt(var / n)
    return mean.tolist(), std.tolist()

train_mean, train_std = compute_mean_std(df_train)
print("TRAIN mean:", train_mean)
print("TRAIN std :", train_std)

class EROBoneDataset(Dataset):
    def __init__(self, df, augment=False, mean=None, std=None):
        self.df = df.reset_index(drop=True)
        self.augment = augment
        self.mean = mean
        self.std = std

        self.base = transforms.Resize((224, 224))

        self.aug = transforms.Compose([
            transforms.RandomRotation(5),
            transforms.RandomAffine(
                degrees=0, translate=(0.01, 0.01), scale=(0.98, 1.02)
            ),
            transforms.ColorJitter(brightness=0.05, contrast=0.05),
        ])

        self.norm = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(self.mean, self.std)
        ])

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        r = self.df.iloc[idx]
        img = Image.open(r["image_path"]).convert("L").convert("RGB")
        img = self.base(img)
        if self.augment:
            img = self.aug(img)
        x = self.norm(img)
        y = torch.tensor(r["ero_bin"], dtype=torch.float32)
        return x, y


# ------------------------
# 4) DataLoaders
#    Best practice for imbalance: use pos_weight (simple) or WeightedRandomSampler.
#    We'll keep pos_weight (stable + simple) + report balanced metrics.
# ------------------------
train_loader = DataLoader(
    EROBoneDataset(df_train, augment=True, mean=train_mean, std=train_std),
    batch_size=32, shuffle=True
)


val_loader = DataLoader(
    EROBoneDataset(df_val, augment=False, mean=train_mean, std=train_std),
    batch_size=64, shuffle=False
)

test_loader = DataLoader(
    EROBoneDataset(df_test, augment=False, mean=train_mean, std=train_std),
    batch_size=64, shuffle=False
)


class EROBinaryResNet18(nn.Module):
    def __init__(self, dropout=0.6):
        super().__init__()
        self.backbone = models.resnet18(weights="IMAGENET1K_V1")
        in_features = self.backbone.fc.in_features
        self.backbone.fc = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(in_features, 1)
        )

    def forward(self, x):
        return self.backbone(x).squeeze(1)

model = EROBinaryResNet18(dropout=0.6).to(device)

for p in model.backbone.parameters():
    p.requires_grad = False

# on entraîne UNIQUEMENT la tête
for p in model.backbone.fc.parameters():
    p.requires_grad = True

class FocalLoss(nn.Module):
    def __init__(self, alpha=0.85, gamma=1.5):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.bce = nn.BCEWithLogitsLoss(reduction="none")

    def forward(self, logits, targets):
        bce = self.bce(logits, targets)
        p = torch.sigmoid(logits)
        pt = targets * p + (1 - targets) * (1 - p)
        loss = self.alpha * (1 - pt) ** self.gamma * bce
        return loss.mean()

criterion = FocalLoss(alpha=0.75, gamma=2.0)

# ------------------------
# 6) Loss + optimizer + scheduler (AdamW + OneCycle-like is common)
# ------------------------
n_pos = (df_train["ero_bin"] == 1).sum()
n_neg = (df_train["ero_bin"] == 0).sum()

pos_weight = torch.tensor([n_neg / max(n_pos, 1)]).to(device)
print("pos_weight:", pos_weight.item())


optimizer = torch.optim.AdamW(
    model.backbone.fc.parameters(),
    lr=1e-4,
    weight_decay=1e-3
)

scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
    optimizer,
    mode="min",
    factor=0.5,
    patience=2,
    min_lr=1e-6,
    verbose=True
)

# ------------------------
# 7) Metrics helpers (robust to single-class edge cases)
# ------------------------
@torch.no_grad()
def predict_proba(loader):
    model.eval()
    ys, ps = [], []
    for x, y in loader:
        x = x.to(device, non_blocking=True)
        logits = model(x)
        probs = torch.sigmoid(logits).detach().cpu().numpy()
        ys.extend(y.numpy())
        ps.extend(probs)
    return np.array(ys).astype(int), np.array(ps)

def compute_binary_metrics(y_true, p, thr=0.314):
    # handle degenerate cases
    out = {}
    if len(np.unique(y_true)) == 2:
        out["AUC"] = float(roc_auc_score(y_true, p))
        out["PR_AUC"] = float(average_precision_score(y_true, p))
    else:
        out["AUC"] = np.nan
        out["PR_AUC"] = np.nan

    y_pred = (p >= thr).astype(int)
    cm = confusion_matrix(y_true, y_pred, labels=[0,1])
    tn, fp, fn, tp = cm.ravel()

    sens = tp / (tp + fn + 1e-8)
    spec = tn / (tn + fp + 1e-8)
    bal_acc = balanced_accuracy_score(y_true, y_pred) if len(np.unique(y_true))==2 else np.nan

    prec, rec, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="binary", zero_division=0
    )
    mcc = matthews_corrcoef(y_true, y_pred) if len(np.unique(y_true))==2 else np.nan

    out.update({
        "Sensitivity": float(sens),
        "Specificity": float(spec),
        "BalancedAcc": float(bal_acc),
        "Precision": float(prec),
        "Recall": float(rec),
        "F1": float(f1),
        "MCC": float(mcc),
        "TN": int(tn), "FP": int(fp), "FN": int(fn), "TP": int(tp),
    })
    return out, cm


# ------------------------
# 8) Train with early stopping on VAL loss (patience)
#    Best checkpoint = min val_loss (coherent with early stopping)
# ------------------------
def train_one_epoch():
    model.train()
    total = 0
    for x, y in train_loader:
        x, y = x.to(device), y.to(device)
        optimizer.zero_grad()
        loss = criterion(model(x), y)
        loss.backward()
        optimizer.step()
        total += loss.item()
    return total / len(train_loader)


@torch.no_grad()
def eval_loss(loader):
    model.eval()
    total = 0
    for x, y in loader:
        x, y = x.to(device), y.to(device)
        total += criterion(model(x), y).item()
    return total / len(loader)

BEST_PATH = "/kaggle/working/best_resnet18_ero.pt"

best_val = float("inf")   # meilleure validation loss observée
patience = 4
wait = 0
n_epoch = 30

train_losses, val_losses = [], []

for epoch in range(1, n_epoch + 1):

    # ----- TRAIN -----
    tr_loss = train_one_epoch()

    # ----- VALIDATION LOSS -----
    va_loss = eval_loss(val_loader)

    train_losses.append(tr_loss)
    val_losses.append(va_loss)

    # ----- LR scheduling (ReduceLROnPlateau) -----
    scheduler.step(va_loss)

    # ----- METRICS (monitoring uniquement) -----
    y_val, p_val = predict_proba(val_loader)
    metrics_val, _ = compute_binary_metrics(y_val, p_val, thr=0.314)

    print(
        f"Epoch {epoch:02d} | "
        f"train={tr_loss:.4f} | "
        f"val={va_loss:.4f} | "
        f"lr={optimizer.param_groups[0]['lr']:.2e} | "
        f"AUC={metrics_val['AUC']:.3f} | "
        f"PR-AUC={metrics_val['PR_AUC']:.3f} | "
        f"BalAcc={metrics_val['BalancedAcc']:.3f}"
    )

    # ----- EARLY STOPPING (val loss uniquement) -----
    if va_loss < best_val - 1e-4:
        best_val = va_loss
        wait = 0
        torch.save(model.state_dict(), BEST_PATH)
        print("  ✅ Best model saved")
    else:
        wait += 1
        print(f"  ⏳ No improvement ({wait}/{patience})")
        if wait >= patience:
            print("  🛑 Early stopping triggered")
            break

# Load best
model.load_state_dict(torch.load(BEST_PATH, map_location=device))
print("Loaded best model from:", BEST_PATH)

# ------------------------
# 9) Plot train/val loss curves
# ------------------------
plt.figure(figsize=(7,5))
plt.plot(range(1, len(train_losses)+1), train_losses, marker="o", label="Train loss")
plt.plot(range(1, len(val_losses)+1), val_losses, marker="o", label="Val loss")
plt.xlabel("Epoch")
plt.ylabel("BCEWithLogitsLoss")
plt.title("Training vs Validation Loss (Early Stopping)")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.show()

from sklearn.metrics import precision_recall_curve

def find_best_threshold(y_true, p):
    prec, rec, thr = precision_recall_curve(y_true, p)
    f1 = 2 * prec * rec / (prec + rec + 1e-8)
    idx = np.argmax(f1)
    return thr[idx], f1[idx]

best_thr, best_f1 = find_best_threshold(y_val, p_val)
print("Best threshold:", best_thr, "Best F1:", best_f1)

# ------------------------
# 10) Final evaluation (VAL + TEST)
#     Report metrics robust for imbalance + confusion matrix
# ------------------------
def evaluate_split(name, loader, thr=0.314):
    y, p = predict_proba(loader)
    metrics, cm = compute_binary_metrics(y, p, thr=thr)
    metrics["Split"] = name
    metrics["Loss"] = float(eval_loss(loader))
    return metrics, cm, y, p

m_val, cm_val, yv, pv = evaluate_split("Validation", val_loader, thr=0.314)
m_test, cm_test, yt, pt = evaluate_split("Test", test_loader, thr=0.314)

results = pd.DataFrame([m_val, m_test])[
    ["Split","Loss","AUC","PR_AUC","BalancedAcc","Sensitivity","Specificity","Precision","Recall","F1","MCC","TN","FP","FN","TP"]
].round(4)

print(results)



# ------------------------
# 11) Confusion matrices (normalized)
# ------------------------
def plot_cm(cm, title):
    cm_norm = cm.astype(float) / cm.sum(axis=1, keepdims=True).clip(min=1)
    fig, ax = plt.subplots(figsize=(6,6))
    im = ax.imshow(cm_norm, vmin=0, vmax=1, cmap="Blues")
    ax.set_xticks([0,1]); ax.set_yticks([0,1])
    ax.set_xticklabels(["No erosion","Erosion"])
    ax.set_yticklabels(["No erosion","Erosion"])
    ax.set_xlabel("Predicted"); ax.set_ylabel("True")
    ax.set_title(title)
    for i in range(2):
        for j in range(2):
            ax.text(j, i, f"{cm_norm[i,j]:.2f}",
                    ha="center", va="center",
                    color="white" if cm_norm[i,j] > 0.5 else "black", fontsize=14)
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    plt.tight_layout()
    plt.show()

plot_cm(cm_val,  "Normalized Confusion Matrix — Validation")
plot_cm(cm_test, "Normalized Confusion Matrix — Test")



# 12) ROC + PR curves (VAL & TEST)
# ------------------------
def plot_roc_pr(y, p, title_prefix):
    # ROC
    if len(np.unique(y)) == 2:
        fpr, tpr, _ = roc_curve(y, p)
        auc_ = roc_auc_score(y, p)
        plt.figure(figsize=(6,6))
        plt.plot(fpr, tpr, label=f"AUC={auc_:.3f}")
        plt.plot([0,1],[0,1],"k--",alpha=0.4)
        plt.xlabel("FPR (1 - Specificity)")
        plt.ylabel("TPR (Sensitivity)")
        plt.title(f"{title_prefix} — ROC")
        plt.legend(loc="lower right")
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.show()

        # PR
        prec, rec, _ = precision_recall_curve(y, p)
        ap = average_precision_score(y, p)
        plt.figure(figsize=(6,6))
        plt.plot(rec, prec, label=f"PR-AUC={ap:.3f}")
        plt.xlabel("Recall")
        plt.ylabel("Precision")
        plt.title(f"{title_prefix} — Precision-Recall")
        plt.legend(loc="lower left")
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.show()
    else:
        print(f"{title_prefix}: ROC/PR skipped (single-class labels).")

plot_roc_pr(yv, pv, "Validation")
plot_roc_pr(yt, pt, "Test")

# ------------------------
# 13) Show example predictions on TEST (qualitative generalization check)
# ------------------------
@torch.no_grad()
def show_test_predictions(df_test, n=10, thr=0.314):
    model.eval()
    idxs = np.random.choice(len(df_test), size=min(n, len(df_test)), replace=False)
    plt.figure(figsize=(16, 6))
    for i, idx in enumerate(idxs, 1):
        r = df_test.iloc[idx]
        img = Image.open(r["image_path"]).convert("L")
        x = EROBoneDataset(df_test.iloc[[idx]], augment=False, mean=train_mean, std=train_std)[0][0].unsqueeze(0).to(device)
        logit = model(x).item()
        p = 1 / (1 + np.exp(-logit))
        y_true = int(r["ero_bin"])
        y_hat = int(p >= thr)

        plt.subplot(2, (len(idxs)+1)//2, i)
        plt.imshow(img, cmap="gray")
        plt.axis("off")
        plt.title(f"{r['bone']} | true={y_true} pred={y_hat} p={p:.2f}", fontsize=10)
    plt.tight_layout()
    plt.show()

show_test_predictions(df_test, n=10, thr=0.314)    