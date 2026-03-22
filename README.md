# RheumaAssist

**RheumaAssist** is a local-first clinical prototype for **AI-assisted early radiographic assessment in rheumatology workflows**.

This project is a practical software continuation of the research work:

**“Automated Early Detection of Rheumatoid Arthritis Using Neural Networks”**

The application was designed to translate the core logic of the research into a usable clinical workflow, centered on:
- patient registration,
- wrist image analysis,
- AI-assisted erosion prediction,
- clinician review and validation,
- and longitudinal follow-up over time.

---

## 1. Project purpose

RheumaAssist was created to support clinicians in the **early radiographic assessment of rheumatoid arthritis (RA)**, especially in settings where specialized expertise and advanced infrastructure may be limited.

The current MVP focuses on a **local-first workflow**:
- it runs locally on a Windows laptop,
- uses a **FastAPI + SQLite + PyTorch CPU-only backend**,
- uses a **Next.js frontend**,
- and is intentionally designed as an **assistive system**, not an autonomous diagnostic tool.

### Important clinical scope

RheumaAssist does **not** independently diagnose rheumatoid arthritis.

The application follows this logic:

**AI result → clinician review → final clinical interpretation**

The AI component provides an assistive output that must always be reviewed by a licensed clinician.

---

## 2. Research origin of the project

This software prototype is the implementation-oriented continuation of the thesis work:

**Automated Early Detection of Rheumatoid Arthritis Using Neural Networks**

The underlying research focused on automated analysis of wrist radiographs for rheumatoid arthritis, using neural networks and image-based prediction pipelines. RheumaAssist extends this work into a practical local application that allows:
- patient-centered workflow organization,
- ROI-based inference,
- clinician review capture,
- and longitudinal comparison of analyses.

In other words, this repository is not just a web app: it is the first operational prototype derived from the research pipeline.

---

## 3. Current MVP scope

The current MVP supports the following workflows:

### Authentication
- local login
- protected application workspace
- logout

### Patient registry
- patient list
- patient search
- pagination
- patient creation
- patient detail page

### AI analysis workflows
- **ROI direct workflow**
  - upload a pre-extracted wrist ROI image
  - run AI inference directly

- **Full radiograph + manual ROI workflow**
  - upload a full radiograph image
  - manually draw a ROI in the UI
  - automatically crop and send the ROI for inference

### Analysis result page
- probability score
- threshold
- predicted class
- patient and exam metadata
- ROI image preview

### Clinician review
- save review as **draft**
- finalize review
- store decision and free-text note
- reload saved review automatically

### Longitudinal follow-up
- patient analysis history
- review status visible in history
- comparison between two analyses of the same patient

### Dashboard
- total patients
- total analyses
- total final reviews
- total draft reviews
- recent analyses overview

---

## 4. Tech stack

### Frontend
- **Next.js**
- **TypeScript**
- **Tailwind CSS**

### Backend
- **FastAPI**
- **SQLAlchemy**
- **SQLite**
- **PyTorch (CPU-only)**

### Local development environment
- Windows
- VS Code
- PowerShell

---

## 5. Repository structure

```text
rheumaassist/
│
├── backend/                 # FastAPI backend
├── frontend/                # Next.js frontend
├── model_artifacts/         # Local PyTorch model files
├── uploads/                 # Local uploaded images
├── start-dev.ps1            # Dev launcher for backend + frontend
└── README.md