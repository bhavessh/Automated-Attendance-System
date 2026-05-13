import {
    Alert,
    Box,
    Button,
    Card,
    CardContent,
    Chip,
    Container,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    Divider,
    FormControl,
    FormControlLabel,
    Grid,
    InputLabel,
    MenuItem,
    Paper,
    Select,
    Switch,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    TextField,
    Typography
} from '@mui/material';
import { useEffect, useState } from 'react';
import { apiService } from '../../services/apiService';
import { authService } from '../../services/authService';

export default function AdminAddTeacher() {
  const [classes, setClasses] = useState([]);
  const [teachers, setTeachers] = useState([]);
  const [form, setForm] = useState({
    username: '',
    email: '',
    password: '',
    full_name: '',
    class_id: ''
  });
  const [assignOpen, setAssignOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [selectedTeacher, setSelectedTeacher] = useState(null);
  const [editForm, setEditForm] = useState({ email: '', full_name: '', password: '', is_active: true, class_id: '' });
  const [addClassOpen, setAddClassOpen] = useState(false);
  const [classForm, setClassForm] = useState({ name: '', section: '', academic_year: '' });
  const [editClassOpen, setEditClassOpen] = useState(false);
  const [selectedClass, setSelectedClass] = useState(null);
  const [editClassForm, setEditClassForm] = useState({ name: '', section: '', academic_year: '' });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadClasses() {
      try {
        const resp = await apiService.getClassList();
        setClasses(resp.classes || resp);
      } catch (err) {
        console.error('Failed to load classes', err);
      }
    }
    async function loadTeachers() {
      try {
        const resp = await apiService.listTeachers();
        setTeachers(resp.teachers || resp);
      } catch (err) {
        console.error('Failed to load teachers', err);
      }
    }
    loadClasses();
    loadTeachers();
  }, []);

  function onChange(e) {
    const { name, value } = e.target;
    setForm((f) => ({ ...f, [name]: value }));
  }

  async function onSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setMessage(null);
    setError(null);

    // Prepare payload
    const payload = {
      username: form.username,
      email: form.email,
      password: form.password,
      full_name: form.full_name,
      class_id: form.class_id ? Number(form.class_id) : undefined
    };

    try {
      const resp = await apiService.createTeacher(payload);
      setMessage(resp.message || 'Teacher created');
      setForm({ username: '', email: '', password: '', full_name: '', class_id: '' });
      // Refresh lists
      const t = await apiService.listTeachers();
      setTeachers(t.teachers || t);
      const c = await apiService.getClassList();
      setClasses(c.classes || c);
    } catch (err) {
      setError(err.message || 'Failed to create teacher');
    } finally {
      setLoading(false);
    }
  }

  // Simple role guard in UI
  const currentUser = authService.getCurrentUser();
  if (!currentUser || currentUser.role !== 'admin') {
    return (
      <Container maxWidth="md" sx={{ mt: 4 }}>
        <Alert severity="warning">You must be an administrator to access this page.</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <div className="page-header">
        <Typography variant="h4" className="page-title">
          Add Teacher
        </Typography>
        <Typography variant="body1" className="page-subtitle">
          Create, assign, and manage teacher accounts
        </Typography>
      </div>

      {message && <Alert severity="success" sx={{ mb: 2 }}>{message}</Alert>}
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Teacher Details
          </Typography>
          <Box component="form" onSubmit={onSubmit}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Username"
                  name="username"
                  value={form.username}
                  onChange={onChange}
                  required
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Email"
                  name="email"
                  value={form.email}
                  onChange={onChange}
                  type="email"
                  required
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Password"
                  name="password"
                  value={form.password}
                  onChange={onChange}
                  type="password"
                  required
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Full name"
                  name="full_name"
                  value={form.full_name}
                  onChange={onChange}
                  required
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Assign to Class (optional)</InputLabel>
                  <Select
                    name="class_id"
                    value={form.class_id}
                    onChange={onChange}
                    label="Assign to Class (optional)"
                  >
                    <MenuItem value="">None</MenuItem>
                    {classes && classes.map((c) => (
                      <MenuItem key={c.id} value={c.id}>{`${c.name} ${c.section} (${c.academic_year})`}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <Box sx={{ display: 'flex', justifyContent: 'flex-end', height: '100%', alignItems: 'center' }}>
                  <Button type="submit" variant="contained" disabled={loading}>
                    {loading ? 'Creating...' : 'Create Teacher'}
                  </Button>
                </Box>
              </Grid>
            </Grid>
          </Box>
        </CardContent>
      </Card>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Typography variant="h6">Classes</Typography>
              <Chip label={`${classes.length} total`} size="small" />
            </Box>
            <Button variant="outlined" size="small" onClick={() => setAddClassOpen(true)}>Add Class</Button>
          </Box>
          <Divider sx={{ my: 2 }} />
          <TableContainer component={Paper} elevation={0}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Class</TableCell>
                  <TableCell>Section</TableCell>
                  <TableCell>Academic Year</TableCell>
                  <TableCell>Assigned Teacher</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {classes && classes.map((c) => (
                  <TableRow key={c.id} hover>
                    <TableCell>{c.name}</TableCell>
                    <TableCell>{c.section}</TableCell>
                    <TableCell>{c.academic_year}</TableCell>
                    <TableCell>{c.teacher_name || 'None'}</TableCell>
                    <TableCell align="right">
                      <Button variant="contained" size="small" sx={{ mr: 1 }} onClick={() => {
                        setSelectedClass(c);
                        setEditClassForm({ name: c.name, section: c.section, academic_year: c.academic_year });
                        setEditClassOpen(true);
                      }}>Edit</Button>
                      <Button color="error" size="small" onClick={async () => {
                        if (!window.confirm('Delete this class?')) return;
                        try {
                          await apiService.deleteClass(c.id);
                          const cc = await apiService.getClassList();
                          setClasses(cc.classes || cc);
                          setMessage('Class deleted');
                        } catch (err) {
                          setError(err.message || 'Failed to delete class');
                        }
                      }}>Delete</Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography variant="h6">Teachers</Typography>
            <Chip label={`${teachers.length} total`} size="small" />
          </Box>
          <Divider sx={{ my: 2 }} />
          <TableContainer component={Paper} elevation={0}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>Username</TableCell>
                  <TableCell>Email</TableCell>
                  <TableCell>Role</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {teachers && teachers.map((t) => (
                  <TableRow key={t.id} hover>
                    <TableCell>{t.full_name}</TableCell>
                    <TableCell>{t.username}</TableCell>
                    <TableCell>{t.email}</TableCell>
                    <TableCell>{t.role}</TableCell>
                    <TableCell align="right">
                      <Button variant="outlined" size="small" onClick={() => {
                        setSelectedTeacher(t);
                        setAssignOpen(true);
                      }}>Assign</Button>
                      <Button variant="contained" size="small" sx={{ ml: 1 }} onClick={() => {
                        setSelectedTeacher(t);
                        setEditForm({ email: t.email, full_name: t.full_name, password: '', is_active: t.is_active, class_id: '' });
                        setEditOpen(true);
                      }}>Edit</Button>
                      <Button color="error" size="small" sx={{ ml: 1 }} onClick={async () => {
                        if (!window.confirm('Delete this teacher? This will unassign their classes.')) return;
                        try {
                          await apiService.deleteTeacher(t.id);
                          const tt = await apiService.listTeachers();
                          setTeachers(tt.teachers || tt);
                          const cc = await apiService.getClassList();
                          setClasses(cc.classes || cc);
                          setMessage('Teacher deleted');
                        } catch (err) {
                          setError(err.message || 'Failed to delete teacher');
                        }
                      }}>Delete</Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Assign Dialog */}
      <Dialog open={assignOpen} onClose={() => setAssignOpen(false)}>
        <DialogTitle>Assign Teacher to Class</DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mt: 1 }}>
            <InputLabel id="assign-class-label">Class</InputLabel>
            <Select
              labelId="assign-class-label"
              value={selectedTeacher?.class_id || ''}
              label="Class"
              onChange={(e) => setSelectedTeacher(s => ({ ...s, class_id: e.target.value }))}
            >
              <MenuItem value="">-- Unassign --</MenuItem>
              {classes.map(c => (
                <MenuItem key={c.id} value={c.id}>{`${c.name} ${c.section} (${c.academic_year})`}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAssignOpen(false)}>Cancel</Button>
          <Button onClick={async () => {
            try {
              await apiService.updateTeacher(selectedTeacher.id, { class_id: selectedTeacher.class_id === '' ? '' : Number(selectedTeacher.class_id) });
              const tt = await apiService.listTeachers();
              setTeachers(tt.teachers || tt);
              const cc = await apiService.getClassList();
              setClasses(cc.classes || cc);
              setMessage('Teacher assignment updated');
              setAssignOpen(false);
            } catch (err) {
              setError(err.message || 'Failed to assign teacher');
            }
          }}>Save</Button>
        </DialogActions>
      </Dialog>

      {/* Edit Dialog */}
      <Dialog open={editOpen} onClose={() => setEditOpen(false)}>
        <DialogTitle>Edit Teacher</DialogTitle>
        <DialogContent>
          <TextField fullWidth label="Full name" sx={{ mt: 1 }} value={editForm.full_name} onChange={(e) => setEditForm(f => ({ ...f, full_name: e.target.value }))} />
          <TextField fullWidth label="Email" sx={{ mt: 1 }} value={editForm.email} onChange={(e) => setEditForm(f => ({ ...f, email: e.target.value }))} />
          <TextField fullWidth label="Password (leave blank to keep)" sx={{ mt: 1 }} type="password" value={editForm.password} onChange={(e) => setEditForm(f => ({ ...f, password: e.target.value }))} />
          <FormControlLabel control={<Switch checked={editForm.is_active} onChange={(e) => setEditForm(f => ({ ...f, is_active: e.target.checked }))} />} label="Active" sx={{ mt: 1 }} />
          <FormControl fullWidth sx={{ mt: 1 }}>
            <InputLabel id="edit-class-label">Assign Class</InputLabel>
            <Select labelId="edit-class-label" value={editForm.class_id} label="Assign Class" onChange={(e) => setEditForm(f => ({ ...f, class_id: e.target.value }))}>
              <MenuItem value="">-- none --</MenuItem>
              {classes.map(c => (
                <MenuItem key={c.id} value={c.id}>{`${c.name} ${c.section} (${c.academic_year})`}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditOpen(false)}>Cancel</Button>
          <Button onClick={async () => {
            try {
              const payload = {
                full_name: editForm.full_name,
                email: editForm.email,
                password: editForm.password || undefined,
                is_active: editForm.is_active,
                class_id: editForm.class_id === '' ? '' : Number(editForm.class_id)
              };
              await apiService.updateTeacher(selectedTeacher.id, payload);
              const tt = await apiService.listTeachers();
              setTeachers(tt.teachers || tt);
              const cc = await apiService.getClassList();
              setClasses(cc.classes || cc);
              setMessage('Teacher updated');
              setEditOpen(false);
            } catch (err) {
              setError(err.message || 'Failed to update teacher');
            }
          }}>Save</Button>
        </DialogActions>
      </Dialog>

      {/* Add Class Dialog */}
      <Dialog open={addClassOpen} onClose={() => setAddClassOpen(false)}>
        <DialogTitle>Add New Class</DialogTitle>
        <DialogContent>
          <TextField fullWidth label="Class Name (e.g. Grade 10)" sx={{ mt: 2 }} value={classForm.name} onChange={(e) => setClassForm(f => ({ ...f, name: e.target.value }))} required />
          <TextField fullWidth label="Section (e.g. A)" sx={{ mt: 2 }} value={classForm.section} onChange={(e) => setClassForm(f => ({ ...f, section: e.target.value }))} required />
          <TextField fullWidth label="Academic Year (e.g. 2023-2024)" sx={{ mt: 2 }} value={classForm.academic_year} onChange={(e) => setClassForm(f => ({ ...f, academic_year: e.target.value }))} required />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddClassOpen(false)}>Cancel</Button>
          <Button onClick={async () => {
            try {
              await apiService.createClass(classForm);
              const cc = await apiService.getClassList();
              setClasses(cc.classes || cc);
              setMessage('Class created');
              setClassForm({ name: '', section: '', academic_year: '' });
              setAddClassOpen(false);
            } catch (err) {
              setError(err.message || 'Failed to create class');
            }
          }} variant="contained">Save</Button>
        </DialogActions>
      </Dialog>

      {/* Edit Class Dialog */}
      <Dialog open={editClassOpen} onClose={() => setEditClassOpen(false)}>
        <DialogTitle>Edit Class</DialogTitle>
        <DialogContent>
          <TextField fullWidth label="Class Name (e.g. Grade 10)" sx={{ mt: 2 }} value={editClassForm.name} onChange={(e) => setEditClassForm(f => ({ ...f, name: e.target.value }))} required />
          <TextField fullWidth label="Section (e.g. A)" sx={{ mt: 2 }} value={editClassForm.section} onChange={(e) => setEditClassForm(f => ({ ...f, section: e.target.value }))} required />
          <TextField fullWidth label="Academic Year (e.g. 2023-2024)" sx={{ mt: 2 }} value={editClassForm.academic_year} onChange={(e) => setEditClassForm(f => ({ ...f, academic_year: e.target.value }))} required />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditClassOpen(false)}>Cancel</Button>
          <Button onClick={async () => {
            try {
              await apiService.updateClass(selectedClass.id, editClassForm);
              const cc = await apiService.getClassList();
              setClasses(cc.classes || cc);
              setMessage('Class updated');
              setEditClassOpen(false);
            } catch (err) {
              setError(err.message || 'Failed to update class');
            }
          }} variant="contained">Save</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}
