# student management system  — Routes & Navigation

## How to run
cd /workspace/frontend_runs/518a2500-2dce-48a1-b9d6-2c8b3ca7b4bd/project
npm install --legacy-peer-deps && npm run dev
Then open http://localhost:40361

## Routes

| Route | Page file | Description |
|-------|-----------|-------------|
| / | redirects | Redirects to /students |
| /students | src/pages/StudentList.tsx | Searchable, class-filterable, sortable, paginated student table with delete |
| /students/new | src/pages/StudentForm.tsx | Create a student |
| /students/:id | src/pages/StudentDetail.tsx | Full student profile with edit/delete |
| /students/:id/edit | src/pages/StudentForm.tsx | Edit a student |
| * | src/pages/NotFound.tsx | 404 with Go Home |

## Navigation map
- Root -> StudentList (redirect)
- Sidebar -> StudentList / Add Student form
- StudentList -> StudentDetail (click row / view icon)
- StudentList -> StudentForm (Add Student button, row edit icon)
- StudentDetail -> StudentForm (Edit button)
- StudentDetail -> StudentList (Back button, after delete)
- StudentForm -> StudentDetail (submit) / StudentList or StudentDetail (Cancel)
- Any page -> NotFound (unknown URL)

## Shared components
- Sidebar.tsx — NavLink navigation
- TopBar.tsx — header bar
- StudentTable.tsx — student rows with view/edit/delete actions
- ClassFilter.tsx — class 1–12 select
- FormInput.tsx — labelled input with helper/error text
- ConfirmDialog.tsx — delete confirmation modal

## Design tokens
primary #1976D2, primary-dark #1565C0, secondary #757575, success #4CAF50, danger #F44336, background #FAFAFA, surface #FFFFFF, line #E0E0E0, ink #212121
