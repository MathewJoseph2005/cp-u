# CropSight Project Setup Guide

This guide will help you set up both the frontend and backend for the CropSight project.

## Project Overview

CropSight is a full-stack web application with:
- **Frontend**: React + Vite + Tailwind CSS with map functionality (Leaflet)
- **Backend**: Django REST Framework with image analysis capabilities
- **Database**: SQLite (development) with Supabase integration for storage/data management

---

## Prerequisites

Before starting, ensure you have the following installed:

- **Python 3.10+** - [Download Python](https://www.python.org/)
- **Node.js 18+** - [Download Node.js](https://nodejs.org/)
- **Git** - [Download Git](https://git-scm.com/)
- **Supabase Account** - [Create Free Account](https://supabase.com/)

Verify installations:
```bash
python --version
node --version
npm --version
```

---

## Environment Variables Setup

### 1. Backend Environment Variables

Create a `.env` file in the project root:

```bash
# Django Settings
DJANGO_SECRET_KEY=your-super-secret-key-here
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Supabase (Optional for analytics)
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-service-key
```

**How to get Supabase credentials:**
1. Go to [Supabase](https://supabase.com/)
2. Create a new project
3. Navigate to **Settings > API**
4. Copy your **Project URL** and **Service Role Key** (or anon key for frontend)

### 2. Frontend Environment Variables

Create a `.env.local` file in the project root:

```env
VITE_SUPABASE_URL=your-supabase-url
VITE_SUPABASE_KEY=your-supabase-anon-key
```

---

## Backend Setup (Django)

### Step 1: Create Python Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

### Step 2: Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Database Migrations

```bash
# Apply migrations
python manage.py migrate

# Create superuser for admin access
python manage.py createsuperuser
```

You'll be prompted to enter:
- Username
- Email
- Password (enter twice to confirm)

### Step 4: Collect Static Files (Production Only)

```bash
python manage.py collectstatic --noinput
```

### Step 5: Run Development Server

```bash
python manage.py runserver
```

The backend will be available at `http://localhost:8000`

- Admin panel: `http://localhost:8000/admin`
- API: `http://localhost:8000/api/`

---

## Frontend Setup (React + Vite)

### Step 1: Install Dependencies

```bash
# Make sure you're in the project root
npm install
```

### Step 2: Run Development Server

```bash
npm run dev
```

The frontend will typically run at `http://localhost:5173`

### Build for Production

```bash
npm run build
```

Build files will be generated in the `dist/` folder.

---

## Running Both Services (Recommended Development Setup)

For local development, you'll want both services running simultaneously:

### Option 1: Use Two Terminal Windows

**Terminal 1 - Backend:**
```bash
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux
python manage.py runserver
```

**Terminal 2 - Frontend:**
```bash
npm run dev
```

### Option 2: Use VS Code Terminal Split

1. Open VS Code
2. Press `Ctrl + ~` to open terminal
3. Click the split terminal icon
4. Run backend in one terminal, frontend in the other

---

## Project Structure

```
cp-u/
├── cropsight_backend/          # Django configuration
│   ├── settings.py             # Django settings
│   ├── urls.py                 # URL routing
│   ├── wsgi.py                 # WSGI application
│   └── asgi.py                 # ASGI application
├── analyzer/                   # Django app for image analysis
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   ├── services.py
│   └── urls.py
├── src/                        # React frontend
│   ├── components/             # React components
│   │   └── FarmMap.jsx        # Map visualization
│   ├── pages/                  # Page components
│   │   └── Dashboard.jsx
│   ├── lib/
│   │   └── supabase.js        # Supabase client
│   ├── App.jsx
│   ├── main.jsx
│   └── index.css
├── .venv/                      # Python virtual environment
├── requirements.txt            # Python dependencies
├── package.json                # Node.js dependencies
├── vite.config.js              # Vite configuration
├── tailwind.config.js          # Tailwind CSS configuration
├── pyrightconfig.json          # Pyright configuration
├── manage.py                   # Django management script
└── db.sqlite3                  # SQLite database (created after migration)
```

---

## Key Commands Reference

### Django Commands

```bash
# Create new migration
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Run development server
python manage.py runserver

# Create superuser
python manage.py createsuperuser

# Access Django shell
python manage.py shell

# Collect static files (production)
python manage.py collectstatic
```

### React Commands

```bash
# Install dependencies
npm install

# Development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Install new package
npm install package-name
```

---

## API Endpoints

The API is available at `http://localhost:8000/api/` once the backend is running.

Check [analyzer/urls.py](analyzer/urls.py) for available endpoints.

---

## Troubleshooting

### Issue: Virtual Environment Not Activating

**Solution:**
```bash
# Windows: Try using forward slashes
source .venv/Scripts/activate

# Or run PowerShell as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Issue: Port 8000 Already in Use

**Solution:**
```bash
# Run on a different port
python manage.py runserver 8001
```

### Issue: Module Not Found Errors in Python

**Solution:**
```bash
# Ensure virtual environment is activated, then reinstall
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

### Issue: VITE_SUPABASE Missing Error

**Solution:**
1. Create `.env.local` in project root
2. Add Supabase credentials (see Environment Variables Setup above)
3. Restart the dev server

### Issue: Database Errors

**Solution:**
```bash
# Reset database (deletes all data)
rm db.sqlite3  # Windows: del db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

---

## Production Deployment Checklist

Before deploying to production:

- [ ] Update `DJANGO_DEBUG=False` in environment
- [ ] Set a strong `DJANGO_SECRET_KEY`
- [ ] Configure proper `DJANGO_ALLOWED_HOSTS`
- [ ] Run `npm run build` to build frontend
- [ ] Serve frontend static files via web server (Nginx, Apache, etc.)
- [ ] Use a production database (PostgreSQL recommended over SQLite)
- [ ] Enable HTTPS/SSL
- [ ] Set up proper logging and monitoring
- [ ] Configure CORS settings in Django if needed

---

## Additional Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [React Documentation](https://react.dev/)
- [Vite Guide](https://vitejs.dev/)
- [Tailwind CSS Docs](https://tailwindcss.com/docs)
- [Leaflet.js](https://leafletjs.com/)
- [Supabase Docs](https://supabase.com/docs)

---

**Last Updated:** March 2026

For questions or issues, please refer to the project documentation or open an issue in the repository.
