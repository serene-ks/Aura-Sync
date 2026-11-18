# Aura-Sync

**An AI-powered Job Matching Platform connecting students with relevant career opportunities and helping recruiters discover suitable candidates.**

## 🌐 Live Deployment

| Component | Platform | Live URL |
|---|---|---|
| Frontend | Vercel | https://aura-sync-rho.vercel.app/ |
| Backend API | Render | https://aura-sync-14dn.onrender.com/ |
| Backend Health Check | Render | https://aura-sync-14dn.onrender.com/hello |

## 📌 Project Overview

Aura-Sync is a job-matching platform designed to bridge the gap between students seeking employment opportunities and recruiters searching for suitable candidates.

The platform provides student profiles, job listings, application tracking, and recruiter-side candidate management through a centralized application.

## ✨ Key Features

- **Student Profiles:** Create and manage student information and professional details.
- **Job Listings:** Explore available job opportunities.
- **Recruiter Dashboard:** Manage job postings and access candidate information.
- **Candidate Management:** View student profiles and identify potential candidates.
- **Application Tracker:** Track and manage job application progress.
- **Authentication:** Supabase-powered authentication and database integration.
- **Backend API:** Flask-based backend supporting application operations.

## 🛠️ Technology Stack

### Frontend
- React.js
- Vite
- JavaScript
- Tailwind CSS
- React Router
- Lucide React

### Backend
- Python
- Flask
- Flask-CORS
- Gunicorn
- HTTPX

### Database & Authentication
- Supabase
- PostgreSQL
- Supabase Authentication

### Deployment
- Vercel — Frontend hosting
- Render — Backend hosting
- GitHub — Version control and source code management

## 🏗️ Project Structure

```text
Aura-Sync/
│
├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── lib/
│   │   └── store.jsx
│   │   └── app.jsx
│   ├── public/
│   ├── package.json
│   └── index.html
│
├── job_matching_backend/
│   ├── routes/
│   ├── app.py
│   ├── auth.py
│   ├── supabase_client.py
│   ├── requirements.txt
│   └── .env.example
│
├── .gitignore
└── README.md
```

## ⚙️ Local Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/serene-ks/Aura-Sync.git
cd Aura-Sync
```

### 2. Frontend Setup

```bash
cd app
npm install
```

Create a `.env` file inside the `app` directory:

```env
VITE_API_URL=http://127.0.0.1:5000
VITE_SUPABASE_URL=your_supabase_project_url
VITE_SUPABASE_ANON_KEY=your_supabase_publishable_or_anon_key
```

Start the frontend:

```bash
npm run dev
```

### 3. Backend Setup

Open another terminal:

```bash
cd job_matching_backend
```

Create and activate a Python virtual environment:

```bash
python -m venv venv
```

Windows:

```powershell
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file inside `job_matching_backend`:

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_server_key
```

Run the Flask application:

```bash
flask --app app run --debug
```

The backend should be available at:

```text
http://127.0.0.1:5000
```

## 🔗 API & Deployment Configuration

The deployed frontend communicates with the backend through the following environment variable:

```env
VITE_API_URL=https://aura-sync-14dn.onrender.com
```

The backend uses the Supabase environment variables:

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_server_key
```

The frontend uses `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` for its Supabase client.

## 🔐 Environment Variables & Security

- Never commit `.env` files containing credentials.
- Keep Supabase service-role or secret keys exclusively on the backend.
- Only use the Supabase publishable/anon key in the frontend.
- Configure environment variables through the respective deployment dashboards.

## 🚀 Deployment

- **Frontend:** Deployed through Vercel using the Vite build configuration.
- **Backend:** Deployed through Render using Gunicorn.
- **Database:** Supabase provides database and authentication services.

## 👩‍💻 Repository

GitHub: https://github.com/serene-ks/Aura-Sync

---

**Aura-Sync — Connecting Skills, Opportunities, and Careers.**
