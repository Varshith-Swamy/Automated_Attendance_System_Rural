# System Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      CLIENT LAYER                        │
│  ┌──────────────────────────────────────────────────┐   │
│  │              React Frontend (Vite)                │   │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌───────┐ │   │
│  │  │Login │ │Dash  │ │Regis │ │Camera│ │Reports│ │   │
│  │  │      │ │board │ │ter   │ │      │ │       │ │   │
│  │  └──────┘ └──────┘ └──────┘ └──────┘ └───────┘ │   │
│  └──────────────────┬───────────────────────────────┘   │
│                     │ HTTP/REST (JSON)                    │
└─────────────────────┼───────────────────────────────────┘
                      │
┌─────────────────────┼───────────────────────────────────┐
│                     ▼  API LAYER                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │              Flask Backend                        │   │
│  │                                                   │   │
│  │  ┌─────────┐  ┌───────────┐  ┌──────────────┐   │   │
│  │  │ Auth    │  │ Student   │  │ Attendance   │   │   │
│  │  │ Routes  │  │ Routes    │  │ Routes       │   │   │
│  │  └────┬────┘  └─────┬─────┘  └──────┬───────┘   │   │
│  │       │             │               │             │   │
│  │  ┌────▼─────────────▼───────────────▼──────────┐ │   │
│  │  │           Service Layer                      │ │   │
│  │  │                                              │ │   │
│  │  │  ┌──────────────┐  ┌─────────────────────┐  │ │   │
│  │  │  │ Face         │  │ Report Generator    │  │ │   │
│  │  │  │ Recognition  │  │                     │  │ │   │
│  │  │  │ ┌──────────┐ │  └─────────────────────┘  │ │   │
│  │  │  │ │ Detector │ │                            │ │   │
│  │  │  │ │ Embedder │ │  ┌─────────────────────┐  │ │   │
│  │  │  │ │ Matcher  │ │  │ Liveness Detector   │  │ │   │
│  │  │  │ │ Liveness │ │  │ • Texture analysis  │  │ │   │
│  │  │  │ └──────────┘ │  │ • Skin color check  │  │ │   │
│  │  │  └──────────────┘  │ • Multi-frame valid  │  │ │   │
│  │  │                    └─────────────────────┘  │ │   │
│  │  └─────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────┘   │
│                     │                                    │
└─────────────────────┼────────────────────────────────────┘
                      │
┌─────────────────────┼────────────────────────────────────┐
│                     ▼  DATA LAYER                        │
│  ┌──────────────────────────────────────────────────┐   │
│  │              SQLite Database                      │   │
│  │                                                   │   │
│  │  ┌───────┐ ┌──────────┐ ┌────────────────────┐  │   │
│  │  │ users │ │ students │ │ face_embeddings    │  │   │
│  │  └───────┘ └──────────┘ └────────────────────┘  │   │
│  │  ┌───────────┐ ┌──────────┐ ┌────────────────┐  │   │
│  │  │attendance │ │audit_logs│ │ sync_queue     │  │   │
│  │  └───────────┘ └──────────┘ └────────────────┘  │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Data Flow: Face-Based Attendance

```
1. Teacher opens camera on Live Attendance page
2. React captures webcam frame as base64 JPEG
3. POST /api/attendance/mark { image: "base64..." }
4. Flask receives image, decodes to numpy array
5. Face Detection:
   - OpenCV DNN detector (or Haar cascade fallback)
   - Returns bounding boxes for all faces
6. Liveness Check:
   - Texture analysis (Laplacian variance)
   - Skin color distribution (HSV)
   - Glare detection
7. Embedding Generation:
   - Extract face region, resize to 128x128
   - Generate 128-d feature vector (LBP histogram or DNN)
   - Normalize to unit vector
8. Matching:
   - Load all stored embeddings from SQLite
   - Compute cosine similarity against each
   - Best match above threshold (0.6) = recognized
9. Attendance Record:
   - Check no duplicate for today
   - Insert row in attendance table
   - Add to sync_queue
10. Response → React shows recognition overlay
```

## Offline-First Architecture

The system is designed to work without internet for all core operations:

1. **Local First**: SQLite database stores everything locally
2. **Sync Queue**: Every write operation (attendance, registration) is queued
3. **Batch Sync**: When internet is available, admin triggers sync
4. **Conflict Resolution**: Server-side timestamp comparison
5. **Retry Logic**: Failed syncs are retried with exponential backoff

## Component Responsibilities

| Component | Responsibility |
|-----------|---------------|
| **React Frontend** | UI rendering, webcam access, API calls |
| **Flask API** | Request validation, business logic, auth |
| **Face Detection** | Locate faces in images (OpenCV) |
| **Face Recognition** | Generate & compare 128-d embeddings |
| **Liveness Detector** | Prevent photo/video spoofing |
| **Report Generator** | Compute attendance statistics |
| **SQLite** | Persistent local storage |
| **Sync Queue** | Buffer operations for cloud sync |

## Why This Architecture?

| Decision | Rationale |
|----------|-----------|
| **SQLite over PostgreSQL** | Zero install, runs anywhere, no server needed |
| **Embeddings over images** | 512 bytes vs. megabytes, faster matching |
| **Cosine similarity** | O(1) comparison, well-suited for normalized vectors |
| **Haar cascade fallback** | Works when DNN model files aren't available |
| **Offline-first** | Rural schools can't depend on internet |
| **Flask over Django** | Lighter, faster startup, less memory |
| **Vite over CRA** | Faster builds, smaller bundles, modern tooling |
