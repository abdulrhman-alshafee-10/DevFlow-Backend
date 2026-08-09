# Phase 12 — File Uploads and Storage

## Objective

Implement file upload handling for task attachments. Users can upload files to tasks, download them via pre-signed URLs, and manage attachments with proper validation and access control.

---

## Concepts Learned

- Multipart file upload handling
- File validation (type, size, content)
- Object storage (S3/MinIO)
- Pre-signed URLs for secure downloads
- File metadata storage in the database
- Filename sanitization
- File security (scanning, content validation)

**Relevant docs**:
- `11-files/file-uploads.md`

---

## Features After This Phase

- [ ] Upload files to tasks (multipart/form-data)
- [ ] Validate file type (whitelist), size (max 10MB), and content (magic bytes)
- [ ] Store files in MinIO (dev) / S3 (prod)
- [ ] Store metadata in database (Attachment model)
- [ ] Download via pre-signed URLs (expire in 15 min)
- [ ] Delete attachments (with storage cleanup)
- [ ] Authorization checks (project member access only)

---

## Database Changes

### Attachment Model

```
Table: attachments
  id:                UUID (PK)
  task_id:           UUID (FK → tasks, NOT NULL)
  uploader_id:       UUID (FK → users, NOT NULL)
  original_filename: VARCHAR(500) (NOT NULL)
  storage_key:       VARCHAR(1000) (NOT NULL)
  file_size:         INTEGER (NOT NULL) — bytes
  mime_type:         VARCHAR(100) (NOT NULL)
  created_at:        TIMESTAMP WITH TIME ZONE

Indexes:
  - INDEX on task_id
  - INDEX on uploader_id
```

---

## API Endpoints

| Method | Path | Description | Auth | Permission |
|---|---|---|---|---|
| POST | `/api/v1/tasks/{task_id}/attachments` | Upload file | Yes | attachment:upload |
| GET | `/api/v1/tasks/{task_id}/attachments` | List attachments | Yes | attachment:read |
| GET | `/api/v1/attachments/{id}/download` | Get download URL | Yes | attachment:read |
| DELETE | `/api/v1/attachments/{id}` | Delete attachment | Yes | Uploader or ADMIN+ |

---

## Completion Checklist

- [ ] MinIO container added to docker-compose.yml
- [ ] Created storage utility (S3-compatible client)
- [ ] Created Attachment model and migration
- [ ] Created attachment repository and service
- [ ] Created upload endpoint with multipart handling
- [ ] File type validation by content (magic bytes)
- [ ] File size limit enforced (10MB)
- [ ] UUID-based storage keys (no user-controlled paths)
- [ ] Pre-signed URL generation for downloads
- [ ] Storage cleanup on attachment deletion
- [ ] Authorization tests (project member access only)
- [ ] File validation tests (reject invalid types, oversized files)
