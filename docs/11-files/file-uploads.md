# File Uploads

## 1. What Is It?

File upload handling is the process of receiving files from clients, validating them, and storing them securely. In DevFlow, users upload attachments to tasks — documents, images, screenshots, and other files relevant to their work.

---

## 2. Why Does It Matter?

File uploads introduce unique challenges:
- **Security** — Malicious files (malware, scripts disguised as images)
- **Storage** — Files can be large; they shouldn't be stored in the database
- **Validation** — Size limits, file type restrictions
- **Performance** — Large uploads consume server resources
- **Access control** — Only authorized users should access uploaded files

---

## 5. How Does It Work?

### Upload Flow

```
1. Client sends file via multipart/form-data
2. Server validates:
   a. File size (< 10MB)
   b. File type (whitelist of allowed MIME types)
   c. File content (magic bytes, not just extension)
3. Server generates a unique filename (UUID-based)
4. Server uploads file to object storage (S3/MinIO)
5. Server creates Attachment record in database with:
   - Original filename
   - Storage path/key
   - File size
   - MIME type
   - Uploaded by (user ID)
   - Associated task ID
6. Server returns attachment metadata (NOT the file URL)
```

### Download Flow

```
1. Client requests GET /attachments/{id}/download
2. Server checks authorization (user has access to the task)
3. Server generates a pre-signed URL (temporary, expires in 15 min)
4. Server returns the pre-signed URL (or redirects to it)
```

### Object Storage (S3/MinIO)

Store files in object storage, not the filesystem:
- **MinIO** for local development (S3-compatible, runs in Docker)
- **AWS S3** for production

Organize files with a path convention:
```
{org_id}/{project_id}/{task_id}/{uuid}-{sanitized_filename}
```

---

## 6. How Does It Fit Into DevFlow?

### Attachment Model
```
Attachment:
  id: UUID
  task_id: UUID (FK)
  uploader_id: UUID (FK)
  original_filename: str
  storage_key: str
  file_size: int (bytes)
  mime_type: str
  created_at: datetime
```

### API Endpoints
- `POST /tasks/{id}/attachments` — Upload file (multipart/form-data)
- `GET /tasks/{id}/attachments` — List attachments for a task
- `GET /attachments/{id}/download` — Get download URL
- `DELETE /attachments/{id}` — Delete attachment

### Allowed File Types
```
Images:    image/jpeg, image/png, image/gif, image/webp
Documents: application/pdf, text/plain, text/markdown
Archives:  application/zip
Spreadsheets: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
```

### Max File Size: 10MB per file

---

## 7. Common Mistakes

### Trusting the File Extension
A `.jpg` file might actually be an executable. Validate MIME type by reading magic bytes (file header), not the extension.

### Storing Files in the Database
BLOBs in PostgreSQL work for small files but don't scale. Use object storage.

### Using User-Provided Filenames
File names can contain path traversal attacks (`../../etc/passwd`). Always generate your own storage keys.

### Not Setting Upload Size Limits
Without limits, a single upload can exhaust server memory and disk.

---

## What I Should Be Able to Do Afterward

- [ ] Handle file uploads with FastAPI's UploadFile
- [ ] Validate file type, size, and content
- [ ] Store files in S3/MinIO
- [ ] Generate pre-signed download URLs
- [ ] Implement access control for file downloads
- [ ] Sanitize filenames and generate storage keys
