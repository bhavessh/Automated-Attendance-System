Deployment (Free-tier) — Quick Guide

Overview
- Frontend: Vercel (free)
- Backend: Render (free Web Service using `backend/Dockerfile`)
- Database: MongoDB Atlas (free tier)

Steps — high level
1) Push this repo to GitHub (if not already):

   cd "d:/CODE/CM/Automated-Attendance-System-main/Automated-Attendance-System-main"
   git init
   git add -A
   git commit -m "Initial commit for deployment"
   git remote add origin https://github.com/<your-username>/Automated-Attendance-System.git
   git push -u origin main

2) Create a MongoDB Atlas free cluster and get a connection string:
   - Create cluster, create database user with password, allow IP access (0.0.0.0/0 for quick dev).
   - Copy the connection string and replace `<password>` and `<dbname>`.
   - Example env var: `MONGODB_URI=mongodb+srv://user:PASS@cluster0.abcd.mongodb.net/attendance?retryWrites=true&w=majority`

3) Deploy backend to Render (recommended) — using Dockerfile in `backend/`:
   - Create a Render account, "New" → "Web Service" → connect your GitHub repo.
   - Select the `backend` folder as the root for the service and choose "Docker" (Render detects Dockerfile).
   - In Render service settings add Environment Variables:
     - `MONGODB_URI` = (Atlas connection string)
     - `JWT_SECRET_KEY` = (random secret)
     - `FLASK_ENV` = production
   - Choose free plan and deploy. Note the service URL (e.g. `https://attendance-backend.onrender.com`).

4) Deploy frontend to Vercel:
   - Create a Vercel account and "Import Project" → choose this repo.
   - In the import UI set the root to `/frontend` (monorepo) or deploy only the `frontend` path.
   - Set Build Command: `npm run build` and Output Directory: `build`.
   - Add an Environment Variable: `REACT_APP_API_BASE_URL=https://<your-backend>/api`.
   - Deploy. Vercel will give you a URL like `https://attendance-frontend.vercel.app`.

5) Post-deploy (optional):
   - If you have existing SQLite data and want it migrated to Atlas, run the migration script locally with `MONGODB_URI` set and follow `backend/scripts/migrate_sqlite_to_mongo.py` usage.
   - Confirm login at `https://<frontend-url>/login`.

Notes & caveats
- The face-recognition features depend on native libs (OpenCV, dlib). Free platform containers may not include these binaries. For face features in production consider a paid VM or a separate specialized service.
- Keep secrets out of the repo. Use provider env variables (Render/Vercel/Atlas UI).

If you want, I can add `render.yaml` and a short `vercel.json` to the repo and create a GitHub Action to automate backend deploys — say "yes add configs" and I will add them and show the exact steps to finish deploy.
