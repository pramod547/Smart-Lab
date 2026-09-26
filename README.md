# 📚 Smart Lab

A secure, modular, full-stack study notes sharing platform built with **Flask** and **SQLAlchemy**. Smart Lab lets students register, log in, upload PDF study materials, search/filter notes, view PDFs inline in browser, and download them with secure session management, magic-byte validation, and CSRF protection.

---

## ✨ Features

- 🔐 **User Authentication** — Register and log in securely with salted password hashing (Werkzeug security)
- 📄 **Secure PDF Upload** — Magic-byte (`%PDF-`) verification and extension check (max 16 MB)
- 🔍 **Search & Filter** — Instant search across titles and subjects in the library
- 📚 **Notes Library** — Browse notes sorted chronologically (newest first)
- 👁️ **Inline PDF Viewer** — View documents directly inside browser with native PDF rendering
- ⬇️ **Safe Downloads** — Download study materials with their original filenames
- 🛡️ **Comprehensive Security** — CSRF tokens on all forms, HTTP-only cookies, SameSite cookies, clickjacking protection (`X-Frame-Options: SAMEORIGIN`), MIME-sniffing protection (`nosniff`), and strict open-redirect validation
- 🗃️ **SQLite Database** — File-based database with automatic table creation
- 🚫 **Graceful Error Handling** — Custom error pages for 404 (Not Found), 413 (File Size Exceeded), and 500 (Internal Error)

---

## 🗂️ Project Structure

```
firstweb dynamic/
├── app.py                  # Application factory, server entry point, and error handlers
├── config.py               # Environment configuration (Dev, Prod, Security tokens)
├── routes.py               # View controllers, security helpers, and routes
├── forms.py                # WTForms definitions with validators and CSRF
├── models.py               # SQLAlchemy database models (User, Note, UploadedFile)
├── requirements.txt        # Python dependencies
├── smartlab.db             # SQLite database
├── .gitignore              # Git ignore rules for venvs, pycache, uploads, and secrets
├── templates/              # Jinja2 HTML templates
│   ├── base.html           # Base layout with navbar, dark mode toggle, and footer
│   ├── index.html          # Landing / home page
│   ├── register.html       # Registration form
│   ├── login.html          # Login form
│   ├── notes.html          # Notes library with search bar & cards
│   ├── upload.html         # PDF upload form
│   ├── view.html           # Inline PDF viewer
│   ├── 404.html            # Page Not Found error page
│   ├── 413.html            # File size limit exceeded page
│   └── 500.html            # Server error page
└── static/
    ├── css/
    │   └── style.css       # Custom stylesheets & dark mode support
    ├── images/             # Static image assets
    └── uploads/            # Securely stored PDF notes
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend Framework | [Flask](https://flask.palletsprojects.com/) ≥ 3.0 |
| ORM / Database | [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/) + SQLite |
| Authentication | [Flask-Login](https://flask-login.readthedocs.io/) |
| Forms & CSRF | [Flask-WTF](https://flask-wtf.readthedocs.io/) + WTForms |
| Password Hashing | [Werkzeug Security](https://werkzeug.palletsprojects.com/) |
| Email Validation | [email-validator](https://pypi.org/project/email-validator/) |
| UI Framework | [Bootstrap 5](https://getbootstrap.com/) + Bootstrap Icons |
| Templating | Jinja2 |

---

## ⚙️ Installation & Setup

### 1. Open the Project Directory

```bash
cd "firstweb dynamic"
```

### 2. Activate Virtual Environment

- **Windows (PowerShell):**
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
- **Windows (CMD):**
  ```cmd
  .venv\Scripts\activate.bat
  ```
- **macOS / Linux:**
  ```bash
  source .venv/bin/activate
  ```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Application

```bash
python app.py
```

The application will start in development mode at **http://127.0.0.1:5000**.

---

## 🔑 Environment Variables

| Variable | Default | Description |
|---|---|---|
| `SMARTLAB_SECRET_KEY` | `dev-change-me-in-production` | Secret key for sessions & CSRF protection |
| `FLASK_ENV` | `development` | Environment mode (`development` or `production`) |
| `DATABASE_URL` | `sqlite:///smartlab.db` | Database connection URI |

> ⚠️ In production, set a strong random secret key:
> ```powershell
> $env:SMARTLAB_SECRET_KEY = "your-strong-random-key"
> $env:FLASK_ENV = "production"
> python app.py
> ```

---

## 🗺️ Routes & Endpoints

| Method | URL | Auth Required | Description |
|---|---|---|---|
| `GET` | `/` | No | Landing / home page |
| `GET/POST` | `/register` | No | Register a new account |
| `GET/POST` | `/login` | No | User authentication |
| `GET` | `/logout` | ✅ Yes | End current user session |
| `GET/POST` | `/upload` | ✅ Yes | Upload study note (PDF) |
| `GET` | `/notes` | No | Browse & search library |
| `GET` | `/notes/<id>` | No | View note page |
| `GET` | `/notes/<id>/pdf` | No | Stream inline PDF preview |
| `GET` | `/notes/<id>/download` | No | Download note with original filename |

---

## 🗄️ Database Models

### `User`
| Column | Type | Description |
|---|---|---|
| `id` | Integer PK | Primary key |
| `username` | String (80) | Unique username |
| `email` | String (120) | Unique email address |
| `password_hash` | String (256) | Salted password hash |
| `role` | String (20) | Role (`user` or `admin`) |

### `UploadedFile`
| Column | Type | Description |
|---|---|---|
| `id` | Integer PK | Primary key |
| `stored_filename` | String (255) | UUID-prefixed filename on disk |
| `original_filename` | String (255) | User's original upload filename |
| `upload_date` | DateTime | UTC timestamp |
| `user_id` | FK → users.id | Uploader user ID (Cascade delete) |

### `Note`
| Column | Type | Description |
|---|---|---|
| `id` | Integer PK | Primary key |
| `title` | String (200) | Note title |
| `subject` | String (120) | Subject / Course |
| `upload_date` | DateTime | UTC timestamp |
| `uploaded_by_id` | FK → users.id | Author user ID |
| `file_id` | FK → uploaded_files.id | Linked file ID (Cascade delete) |

---

## 🔒 Security Hardening

1. **Magic-Byte Header Validation**: Uploaded files must match `%PDF-` signature to prevent disguised executables or malicious script execution.
2. **Safe Redirection**: Validates redirect URLs against open redirect vulnerabilities on login.
3. **Session Cookie Security**: `HttpOnly` and `SameSite=Lax` enabled by default.
4. **Clickjacking & Sniffing Protection**: Sends `X-Frame-Options: SAMEORIGIN` and `X-Content-Type-Options: nosniff`.
5. **Sanitized Storage**: `werkzeug.utils.secure_filename` combined with random UUID prevents filesystem path traversal and name collisions.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
