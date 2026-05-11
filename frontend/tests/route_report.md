# Route Capture Report — 2026-05-09

Summary: Playwright captured the main SPA routes by injecting auth before load and performing client-side navigation. Screenshots were saved to the frontend folder. All captured `.main-content` roots were visible.

Routes captured

- **/dashboard** — screenshot: [dashboard.png](dashboard.png)
  - text excerpt: "Dashboard Welcome to the Automated Attendance System ... Total Students 1 Present Today 50% Attendance Rate 1 Alerts"
  - size: 1000 × 1397, display: block, visibility: visible

- **/students** — screenshot: [students.png](students.png)
  - text excerpt: "Students Management Manage student records and information ... Add Student"
  - size: 1000 × 640, display: block, visibility: visible

- **/attendance** — screenshot: [attendance.png](attendance.png)
  - text excerpt: "Attendance Management Mark and track student attendance ... Open Camera for Attendance OR Upload Photo"
  - size: 1000 × 962, display: block, visibility: visible

- **/reports** — screenshot: [reports.png](reports.png)
  - text excerpt: "Reports & Analytics Comprehensive attendance reports and Power BI integration ..."
  - size: 1000 × 1128, display: block, visibility: visible

- **/settings** — screenshot: [settings.png](settings.png)
  - text excerpt: "System Settings Configure system parameters and preferences ..."
  - size: 1000 × 1369, display: block, visibility: visible

- **/admin/add-teacher** — screenshot: [admin_add-teacher.png](admin_add-teacher.png)
  - text excerpt: "Add Teacher Create, assign, and manage teacher accounts ..."
  - size: 1000 × 1105, display: block, visibility: visible

Notes & next steps

- All routes returned visible `.main-content` elements when the app was loaded as an authenticated user (auth injected via `page.addInitScript`).
- If you want these screenshots committed, I can create a git commit for the `tests/*` changes and add the PNGs.
- For CI-friendly checks, I recommend adding a Playwright job that runs headless with the same `addInitScript` and fails on `!root` or zero-sized bounding boxes.

Files produced

- `tests/batch_results.json` — JSON with details (already written)
- `dashboard.png`, `students.png`, `attendance.png`, `reports.png`, `settings.png`, `admin_add-teacher.png`
