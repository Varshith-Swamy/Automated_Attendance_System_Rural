# Deployment Guide

## Option 1: Local Development (Quickstart)

### Prerequisites
- Python 3.9+ 
- Node.js 18+
- USB Webcam

### Steps

```bash
# 1. Clone
git clone <repo-url>
cd Automated_Attendance_System_Rural

# 2. Backend
cd backend
pip install -r requirements.txt
python seed_data.py       # Generate 55 test students + 30 days attendance
python run.py             # Starts on http://localhost:5000

# 3. Frontend (new terminal)
cd frontend
npm install
npm run dev               # Starts on http://localhost:5173
```

Login: `admin` / `admin123` or `teacher1` / `teacher123`

---

## Option 2: Production Deployment (Single Machine)

### Build Frontend
```bash
cd frontend
npm run build            # Creates dist/ folder
```

### Serve with Gunicorn
```bash
cd backend
pip install gunicorn
gunicorn run:app -w 2 -b 0.0.0.0:5000
```

### Serve Frontend via Nginx
```nginx
server {
    listen 80;
    server_name attendance.school.local;

    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Option 3: Raspberry Pi Deployment

### Hardware Requirements
- Raspberry Pi 4 (2GB+ RAM recommended)
- USB Webcam (720p sufficient)
- MicroSD card (16GB+)
- Power supply

### Setup
```bash
# Install system dependencies
sudo apt update
sudo apt install python3-pip python3-venv nodejs npm

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python packages (headless OpenCV — no GUI required)
pip install -r backend/requirements.txt

# Run backend
cd backend && python run.py &

# Build and serve frontend
cd frontend && npm install && npm run build
# Serve dist/ with nginx or python http server
```

### Performance Tips for Pi
- Use 1 gunicorn worker: `gunicorn run:app -w 1`
- Set `FACE_RECOGNITION_THRESHOLD=0.65` for faster matching
- Limit webcam resolution to 480p
- Use Haar cascade detector (lighter than DNN)

---

## Option 4: Cloud Sync (Optional)

For multi-school deployments, configure cloud sync:

1. Set up PostgreSQL on cloud server
2. Update `SQLALCHEMY_DATABASE_URI` in production config
3. Each local instance syncs via `/api/sync/upload`
4. Central dashboard aggregates data from all schools

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_ENV` | `development` | `development`, `production`, `testing` |
| `SECRET_KEY` | (built-in) | Flask secret key |
| `JWT_SECRET_KEY` | (built-in) | JWT signing key |
| `DATABASE_URL` | `sqlite:///data/attendance.db` | Database connection string |
| `PORT` | `5000` | Backend port |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Camera not found | Check USB connection, ensure browser has camera permissions |
| Slow recognition | Reduce webcam resolution, use Haar cascade |
| Module import errors | Reinstall `requirements.txt`, check Python version |
| Database locked | Restart Flask server, check no other process is using the DB |
| CORS errors | Ensure Flask-CORS is enabled, check proxy config in Vite |
