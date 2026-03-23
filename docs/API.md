# API Documentation

## Base URL
```
http://localhost:5000/api
```

## Authentication
All protected endpoints require a JWT token in the `Authorization` header:
```
Authorization: Bearer <token>
```

---

## Auth Endpoints

### POST `/auth/login`
Login and receive JWT token.

**Request:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response (200):**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": 1,
    "username": "admin",
    "full_name": "System Administrator",
    "role": "admin",
    "email": "admin@school.local"
  },
  "message": "Login successful"
}
```

**Errors:** `400` (missing fields), `401` (invalid credentials), `403` (deactivated)

### GET `/auth/me`
Get current authenticated user. **Auth: Token required**

### POST `/auth/change-password`
Change password. **Auth: Token required**

**Request:** `{ "old_password": "...", "new_password": "..." }`

---

## Student Endpoints

### POST `/students/register`
Register a new student with optional face samples. **Auth: Teacher or Admin**

**Request:**
```json
{
  "student_id": "STU-2024-0001",
  "name": "Aarav Sharma",
  "class_id": 1,
  "section": "A",
  "guardian_name": "Ramesh Sharma",
  "guardian_phone": "9876543210",
  "gender": "male",
  "face_images": ["base64_encoded_image_1", "base64_encoded_image_2"]
}
```

**Response (201):**
```json
{
  "message": "Student registered successfully",
  "student": { "id": 1, "student_id": "STU-2024-0001", "name": "Aarav Sharma", ... },
  "embeddings_saved": 2
}
```

**Errors:** `400` (missing fields, invalid class), `409` (duplicate student_id)

### GET `/students?class_id=1&search=aarav&page=1&per_page=20`
List students with optional filters. **Auth: Token required**

### GET `/students/<id>`
Get student details. **Auth: Token required**

### PUT `/students/<id>`
Update student info. **Auth: Teacher or Admin**

### POST `/students/<id>/add-faces`
Add more face samples. **Auth: Teacher or Admin**

**Request:** `{ "face_images": ["base64_1", "base64_2"] }`

### GET `/students/classes`
List all classes. **Auth: Token required**

---

## Attendance Endpoints

### POST `/attendance/recognize`
Detect and identify faces without marking attendance. **Auth: Teacher or Admin**

**Request:** `{ "image": "base64_encoded_image" }`

**Response (200):**
```json
{
  "recognized": true,
  "faces": [
    {
      "recognized": true,
      "confidence": 0.8754,
      "bbox": [120, 80, 200, 250],
      "student": { "id": 1, "student_id": "STU-2024-0001", "name": "Aarav Sharma" }
    }
  ]
}
```

### POST `/attendance/mark`
Mark attendance via face recognition or manually. **Auth: Teacher or Admin**

**Face-based:**
```json
{ "image": "base64_encoded_image", "class_id": 1 }
```

**Manual:**
```json
{ "student_db_id": 5, "status": "present", "class_id": 1 }
```

**Response (201):**
```json
{
  "message": "Processed 1 face(s)",
  "results": [
    {
      "recognized": true,
      "student": { ... },
      "message": "Attendance marked",
      "confidence": 0.89
    }
  ]
}
```

### GET `/attendance/daily?date=2024-01-15&class_id=1`
Get daily attendance. **Auth: Token required**

### PUT `/attendance/<id>`
Admin correction. **Auth: Admin only**

**Request:** `{ "status": "late", "time_in": "09:15:00" }`

---

## Report Endpoints

### GET `/reports/student/<id>?month=2024-01`
Student attendance report with summary.

### GET `/reports/class/<id>?month=2024-01`
Class-level attendance report.

### GET `/reports/export?date=2024-01-15&class_id=1&format=csv`
Download attendance as CSV file.

### GET `/reports/monthly-summary?month=2024-01&class_id=1`
Monthly attendance breakdown by date.

---

## Dashboard Endpoints

### GET `/dashboard/summary`
Dashboard overview with stats, weekly trend, class summary, and recent activity. **Auth: Token required**

---

## Sync Endpoints

### GET `/sync/status`
Get sync queue status (pending, synced, failed counts). **Auth: Token required**

### POST `/sync/upload`
Trigger sync of pending items to cloud. **Auth: Admin only**

### POST `/sync/retry`
Retry failed sync items. **Auth: Admin only**

### GET `/sync/logs?page=1&per_page=50&action=login`
Get paginated audit logs. **Auth: Admin only**

---

## Status Codes
| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad request / validation error |
| 401 | Unauthorized (missing/invalid token) |
| 403 | Forbidden (insufficient role) |
| 404 | Not found |
| 409 | Conflict (duplicate) |
| 500 | Server error |
