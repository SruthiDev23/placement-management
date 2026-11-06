SRUTHI COLLEGE PLACEMENT MANAGEMENT SYSTEM

1. Open MySQL Workbench and make sure MySQL Server is running.
2. Ensure database placement_management has the four tables:
   students, companies, users, applications.
   If not, open database.sql in Workbench and execute it.
3. Open this folder in VS Code.
4. Open app.py and replace YOUR_MYSQL_PASSWORD with your MySQL root password.
5. Open VS Code Terminal (PowerShell) in this project folder.
6. Run:
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   python app.py
7. Open http://127.0.0.1:5000 in Chrome.

FIRST ADMIN LOGIN:
Username: admin
Password: admin123

Change the default admin password and Flask secret key before using this beyond local testing.
Students can register from the login page. Student registration creates both a student
record and a hashed-password login account. Admin can add student records and companies.
Admin can review applications and update their status.

If PowerShell blocks venv activation, run:
Set-ExecutionPolicy -Scope Process Bypass
Then activate again.

For this starter version, admin can add/view students and companies; student accounts
are created using Student Registration. Editing/deleting student/company records and
admin account management are not yet included.
