# 📚 Smart Lab

A dynamic, full-stack study notes platform built with **Flask**. Smart Lab lets students register, log in, upload PDF study materials, browse the shared notes library, view PDFs inline, and download them — all with secure authentication and CSRF protection.

---

## ✨ Features

- 🔐 **User Authentication** — Register and log in with hashed passwords (Werkzeug security)
- 📄 **PDF Upload** — Upload study notes as PDF files (up to 16 MB)
- 📚 **Notes Library** — Browse all uploaded notes sorted by newest first
- 👁️ **Inline Viewer** — View PDFs directly in the browser
- ⬇️ **Download** — Download any note with its original filename
- 🛡️ **CSRF Protection** — All forms are protected via Flask-WTF tokens
- 🗃️ **SQLite Database** — Lightweight, file-based database (no setup needed)
- 🔒 **Secure File Storage** — Files are saved with UUID-prefixed names on disk

---

## 🗂️ Project Structure

```
firstweb dynamic/
├── app.py                  # Flask application, routes, and WTForms
├── models.py               # SQLAlchemy models (User, Note, UploadedFile)
├── requirements.txt        # Python dependencies
├── smartlab.db             # SQLite database (auto-created on first run)
├── index.html              # (Legacy) original static landing page
├── style.css               # (Legacy) original static styles
├── templates/              # Jinja2 HTML templates
│   ├── base.html           # Shared base layout
│   ├── index.html          # Landing / home page
│   ├── register.html       # Registration form
│   ├── login.html          # Login form
│   ├── notes.html          # Notes library listing
│   ├── upload.html         # PDF upload form
│   └── view.html           # Inline PDF viewer
└── static/
    ├── css/                # Stylesheets
    ├── images/             # Static image assets
    └── uploads/            # Uploaded PDFs (auto-created on first run)
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend Framework | [Flask](https://flask.palletsprojects.com/) >= 3.0 |
| ORM / Database | [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/) + SQLite |
| Authentication | [Flask-Login](https://flask-login.readthedocs.io/) |
| Forms & CSRF | [Flask-WTF](https://flask-wtf.readthedocs.io/) + WTForms |
| Password Hashing | [Werkzeug Security](https://werkzeug.palletsprojects.com/) |
| Email Validation | [email-validator](https://pypi.org/project/email-validator/) |
| Templating | Jinja2 (bundled with Flask) |

---

## ⚙️ Installation & Setup

### 1. Clone / Open the Project

```bash
cd "firstweb dynamic"
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it:

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

The app will start in debug mode at **http://127.0.0.1:5000**.

> The SQLite database (`smartlab.db`) and `static/uploads/` folder are created automatically on first run.

---

## 🔑 Environment Variables

| Variable | Default | Description |
|---|---|---|
| `SMARTLAB_SECRET_KEY` | `dev-change-me-in-production` | Flask secret key for sessions & CSRF |

> **Always set a strong `SMARTLAB_SECRET_KEY` in production!**

```powershell
# PowerShell example
$env:SMARTLAB_SECRET_KEY = "your-very-strong-random-secret"
python app.py
```

---

## 🗺️ Routes

| Method | URL | Auth Required | Description |
|---|---|---|---|
| `GET` | `/` | No | Landing / home page |
| `GET/POST` | `/register` | No | Create a new account |
| `GET/POST` | `/login` | No | Log in to an account |
| `GET` | `/logout` | Yes | Log out the current user |
| `GET/POST` | `/upload` | Yes | Upload a PDF note |
| `GET` | `/notes` | No | Browse all notes |
| `GET` | `/notes/<id>` | No | View a single note (inline PDF) |
| `GET` | `/notes/<id>/download` | No | Download the note PDF |

---

## 🗄️ Database Models

### `User`
| Column | Type | Description |
|---|---|---|
| `id` | Integer PK | Auto-incremented user ID |
| `username` | String (80) | Unique username |
| `email` | String (120) | Unique email address |
| `password_hash` | String (256) | Werkzeug-hashed password |

### `UploadedFile`
| Column | Type | Description |
|---|---|---|
| `id` | Integer PK | Auto-incremented file ID |
| `stored_filename` | String (255) | UUID-prefixed name on disk |
| `original_filename` | String (255) | Original upload filename |
| `upload_date` | DateTime | UTC timestamp of upload |
| `user_id` | FK -> users | Uploader's user ID |

### `Note`
| Column | Type | Description |
|---|---|---|
| `id` | Integer PK | Auto-incremented note ID |
| `title` | String (200) | Note title |
| `subject` | String (120) | Subject / course name |
| `upload_date` | DateTime | UTC timestamp of upload |
| `uploaded_by_id` | FK -> users | Author's user ID |
| `file_id` | FK -> uploaded_files | Linked PDF file record |

---

## 📋 Usage Walkthrough

1. **Register** — Go to `/register` and create an account.
2. **Log In** — Go to `/login` and authenticate.
3. **Upload a Note** — Navigate to `/upload`, fill in the title, subject, and choose a PDF file.
4. **Browse Notes** — Visit `/notes` to see all uploaded study materials.
5. **Read or Download** — Click on a note to view it inline, or use the download button to save it.

---

## 🔒 Security Notes

- Passwords are **never stored in plain text** — Werkzeug's `generate_password_hash` / `check_password_hash` are used.
- All forms include **CSRF tokens** via Flask-WTF.
- Uploaded filenames are sanitised with `werkzeug.utils.secure_filename` and stored with a **UUID prefix** to prevent conflicts and path-traversal attacks.
- Only **PDF files** are accepted (validated by extension on both client and server).
- Open-redirect protection is applied on the `next` query parameter after login.

---

## 📦 Dependencies

```
Flask>=3.0.0
Flask-SQLAlchemy>=3.1.0
Flask-Login>=0.6.3
Flask-WTF>=1.2.0
WTForms>=3.1.0
Werkzeug>=3.0.0
email-validator>=2.0.0
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "Add your feature"`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a pull request

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
