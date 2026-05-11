import React, { useState, useEffect, useCallback } from 'react';

import {
    Box,
    Button,
    Chip,
    CircularProgress,
    Container,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    FormControl,
    InputLabel,
    Select,
    Typography,
    Grid,
    TextField,
    IconButton,
    Paper,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    MenuItem
} from '@mui/material';

import { toast } from 'react-toastify';
import CameraCapture from '../../components/CameraCapture/CameraCapture';
import InputAdornment from '@mui/material/InputAdornment';

import { Add as AddIcon, Delete as DeleteIcon, Edit as EditIcon, Person as PersonIcon, School as SchoolIcon, Search as SearchIcon } from '@mui/icons-material';

import { studentService } from '../../services/studentService';
import { apiService } from '../../services/apiService';

const Students = () => {
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [confirmDeleteOpen, setConfirmDeleteOpen] = useState(false);
  const [studentToDelete, setStudentToDelete] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [classFilter, setClassFilter] = useState('');
  const [sectionFilter, setSectionFilter] = useState('');
  const [formData, setFormData] = useState({
    roll_number: '',
    admission_number: '',
    full_name: '',
    class_name: '',
    section: '',
    date_of_birth: '',
    parent_contact: '',
    parent_email: '',
    address: ''
  });
  const [formErrors, setFormErrors] = useState({});
  const [selectedPhoto, setSelectedPhoto] = useState(null);
  const [photoPreview, setPhotoPreview] = useState(null);
  const [uploadingPhoto, setUploadingPhoto] = useState(false);
  const [showCamera, setShowCamera] = useState(false);
  const [availableClasses, setAvailableClasses] = useState([]);
  const [editingStudent, setEditingStudent] = useState(null);
  const [openDialog, setOpenDialog] = useState(false);

  const fetchStudents = useCallback(async () => {
    setLoading(true);
    try {
      const filters = {};
      if (searchTerm) filters.search = searchTerm;
      if (classFilter) filters.class = classFilter;
      if (sectionFilter) filters.section = sectionFilter;

      const result = await studentService.getAllStudents(filters);
      if (result.success) {
        setStudents(result.data.students || []);
      } else {
        toast.error(result.error);
        setStudents([]);
      }
    } catch (error) {
      toast.error('Failed to fetch students');
      setStudents([]);
    } finally {
      setLoading(false);
    }
  }, [searchTerm, classFilter, sectionFilter]);

  useEffect(() => {
    fetchStudents();
    const fetchClasses = async () => {
      try {
        const data = await apiService.getClassList();
        setAvailableClasses(data.classes || []);
      } catch (err) {
        console.error('Failed to fetch classes', err);
      }
    };
    fetchClasses();
  }, [fetchStudents]);

  

  const handleOpenDialog = (student = null) => {
    if (student) {
      setEditingStudent(student);
      setFormData({
        roll_number: student.roll_number || '',
        admission_number: student.admission_number || '',
        full_name: student.full_name || '',
        class_name: student.class_name || '',
        section: student.section || '',
        date_of_birth: student.date_of_birth || '',
        parent_contact: student.parent_contact || '',
        parent_email: student.parent_email || '',
        address: student.address || ''
      });
    } else {
      setEditingStudent(null);
      setFormData({
        roll_number: '',
        admission_number: '',
        full_name: '',
        class_name: '',
        section: '',
        date_of_birth: '',
        parent_contact: '',
        parent_email: '',
        address: ''
      });
    }
    setFormErrors({});
    setSelectedPhoto(null);
    setPhotoPreview(null);
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingStudent(null);
    setSelectedPhoto(null);
    setPhotoPreview(null);
    setFormErrors({});
    setFormData({
      roll_number: '',
      admission_number: '',
      full_name: '',
      class_name: '',
      section: '',
      date_of_birth: '',
      parent_contact: '',
      parent_email: '',
      address: ''
    });
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // Clear field-level error on change
    setFormErrors(prev => ({
      ...prev,
      [name]: ''
    }));
  };

  const handlePhotoChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) { // 5MB limit
        toast.error('Photo size must be less than 5MB');
        return;
      }
      if (!file.type.startsWith('image/')) {
        toast.error('Please select a valid image file');
        return;
      }
      setSelectedPhoto(file);
      // Create preview
      const reader = new FileReader();
      reader.onload = (e) => {
        setPhotoPreview(e.target.result);
      };
      reader.readAsDataURL(file);
    }
  };

  // Handle photo from camera capture (base64 string)
  const handleCameraPhoto = (photoDataUrl) => {
    // Convert base64 to Blob for upload
    function dataURLtoFile(dataurl, filename) {
      const arr = dataurl.split(','), mime = arr[0].match(/:(.*?);/)[1], bstr = atob(arr[1]), n = bstr.length, u8arr = new Uint8Array(n);
      for (let i = 0; i < n; i++) u8arr[i] = bstr.charCodeAt(i);
      return new File([u8arr], filename, { type: mime });
    }
    const file = dataURLtoFile(photoDataUrl, 'captured_photo.jpg');
    setSelectedPhoto(file);
    setPhotoPreview(photoDataUrl);
    setShowCamera(false);
  };

  const handleRemovePhoto = () => {
    setSelectedPhoto(null);
    setPhotoPreview(null);
  };

  const handleSubmit = async () => {
    try {
      // Validate required fields inline
      const requiredFields = ['roll_number', 'admission_number', 'full_name', 'class_name', 'section'];
      const newErrors = {};
      requiredFields.forEach((f) => {
        if (!formData[f]) newErrors[f] = 'This field is required';
      });
      if (Object.keys(newErrors).length > 0) {
        setFormErrors(newErrors);
        return;
      }

      // Create or update student
      const result = editingStudent
        ? await studentService.updateStudent(editingStudent.id, formData)
        : await studentService.createStudent(formData);

      if (result.success) {
        const savedStudent = result.data.student;

        // If photo is selected, upload it
        if (selectedPhoto) {
          setUploadingPhoto(true);
          const photoResult = await studentService.uploadStudentPhoto(savedStudent.id, selectedPhoto);

          if (photoResult.success) {
            toast.success(`${editingStudent ? 'Student updated' : 'Student added'} with photo successfully!`);
          } else {
            toast.warning(`${editingStudent ? 'Student updated' : 'Student added'} but photo upload failed: ${photoResult.error}`);
          }
          setUploadingPhoto(false);
        } else {
          toast.success(`Student ${editingStudent ? 'updated' : 'added'} successfully!`);
        }

        handleCloseDialog();
        fetchStudents();
      } else {
        // Map specific backend errors to fields
        const errMsg = (result.error || '').toLowerCase();
        const fieldErrors = {};
        if (errMsg.includes('admission') && errMsg.includes('exists')) {
          fieldErrors.admission_number = 'Admission number must be unique';
        }
        if (errMsg.includes('roll') && errMsg.includes('class') && errMsg.includes('section')) {
          fieldErrors.roll_number = 'Roll number must be unique within class and section';
        }
        if (Object.keys(fieldErrors).length > 0) {
          setFormErrors(fieldErrors);
        } else {
          toast.error(result.error);
        }
      }
    } catch (error) {
      toast.error('Failed to save student');
      setUploadingPhoto(false);
    }
  };

  const getUniqueClasses = () => {
    const classes = [...new Set(students.map(student => student.class_name))];
    return classes.filter(cls => cls);
  };

  const getUniqueSections = () => {
    const sections = [...new Set(students.map(student => student.section))];
    return sections.filter(section => section);
  };

  const handleConfirmDelete = async () => {
    if (!studentToDelete) return;

    // Optimistic UI: remove immediately
    const prevStudents = students;
    setStudents((cur) => cur.filter((s) => s.id !== studentToDelete.id));

    try {
      const res = await studentService.deleteStudent(studentToDelete.id);
      if (res.success) {
        toast.success('Student deleted');
      } else {
        // rollback
        setStudents(prevStudents);
        toast.error(res.error || 'Failed to delete student');
      }
    } catch (e) {
      setStudents(prevStudents);
      toast.error('Failed to delete student');
    } finally {
      setConfirmDeleteOpen(false);
      setStudentToDelete(null);
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <div className="page-header">
        <Typography variant="h4" className="page-title" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <SchoolIcon /> Students Management
        </Typography>
        <Typography variant="body1" className="page-subtitle">
          Manage student records and information
        </Typography>
      </div>

      {/* Controls */}
      <div className="card" style={{ marginBottom: 32 }}>
        <Grid container spacing={3} alignItems="center">
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              placeholder="Search students..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
                className: 'input'
              }}
            />
          </Grid>
          <Grid item xs={12} md={2}>
            <FormControl fullWidth>
              <InputLabel>Class</InputLabel>
              <Select
                value={classFilter}
                onChange={(e) => setClassFilter(e.target.value)}
                label="Class"
                className="input"
              >
                <MenuItem value="">All Classes</MenuItem>
                {getUniqueClasses().map((cls) => (
                  <MenuItem key={cls} value={cls}>{cls}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={2}>
            <FormControl fullWidth>
              <InputLabel>Section</InputLabel>
              <Select
                value={sectionFilter}
                onChange={(e) => setSectionFilter(e.target.value)}
                label="Section"
                className="input"
              >
                <MenuItem value="">All Sections</MenuItem>
                {getUniqueSections().map((section) => (
                  <MenuItem key={section} value={section}>{section}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={4} sx={{ textAlign: 'right' }}>
            <button
              className="button-primary"
              style={{ minWidth: 140 }}
              onClick={() => handleOpenDialog()}
            >
              <AddIcon style={{ verticalAlign: 'middle', marginRight: 8 }} /> Add Student
            </button>
          </Grid>
        </Grid>
      </div>

      {/* Students Table */}
      {/* Students Table */}
      <>
        <div className="card" style={{ borderRadius: 28, overflow: 'hidden' }}>
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
              <CircularProgress />
            </Box>
          ) : students.length === 0 ? (
            <Box sx={{ textAlign: 'center', p: 4 }}>
              <PersonIcon sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" color="text.secondary">
                No students found
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {searchTerm || classFilter || sectionFilter 
                  ? 'Try adjusting your search filters'
                  : 'Get started by adding your first student'
                }
              </Typography>
              <button 
                className="button-primary"
                style={{ minWidth: 140 }}
                onClick={() => handleOpenDialog()}
              >
                <AddIcon style={{ verticalAlign: 'middle', marginRight: 8 }} /> Add Student
              </button>
            </Box>
          ) : (
            <TableContainer component={Paper} elevation={0} >
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Roll Number</TableCell>
                    <TableCell>Name</TableCell>
                    <TableCell>Class</TableCell>
                    <TableCell>Section</TableCell>
                    <TableCell>Parent Contact</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell align="center">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {students.map((student) => (
                    <TableRow key={student.id} hover>
                      <TableCell>
                        <Typography variant="body2" fontWeight="medium">
                          {student.roll_number}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" fontWeight="medium">
                          {student.full_name}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {student.admission_number}
                        </Typography>
                      </TableCell>
                      <TableCell>{student.class_name}</TableCell>
                      <TableCell>{student.section}</TableCell>
                      <TableCell>{student.parent_contact}</TableCell>
                      <TableCell>
                        <Chip
                          label={student.is_active ? 'Active' : 'Inactive'}
                          color={student.is_active ? 'success' : 'default'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell align="center">
                        <IconButton
                          size="small"
                          onClick={() => handleOpenDialog(student)}
                          color="primary"
                        >
                          <EditIcon />
                        </IconButton>
                        <IconButton
                          size="small"
                          onClick={() => {
                            setStudentToDelete(student);
                            setConfirmDeleteOpen(true);
                          }}
                          color="error"
                          sx={{ ml: 1 }}
                        >
                          <DeleteIcon />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </div>
      </>

      {/* Add/Edit Student Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingStudent ? 'Edit Student' : 'Add New Student'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Grid container spacing={3}>
              {/* Photo Upload/Capture Section */}
              <Grid item xs={12}>
                <Box sx={{ textAlign: 'center', mb: 2 }}>
                  <Typography variant="h6" gutterBottom>
                    Student Photo for Face Recognition
                  </Typography>
                  {photoPreview ? (
                    <Box sx={{ position: 'relative', display: 'inline-block' }}>
                      <img
                        src={photoPreview}
                        alt="Student preview"
                        style={{
                          width: 120,
                          height: 120,
                          objectFit: 'cover',
                          borderRadius: '50%',
                          border: '3px solid #1976d2'
                        }}
                      />
                      <IconButton
                        sx={{
                          position: 'absolute',
                          top: -5,
                          right: -5,
                          bgcolor: 'error.main',
                          color: 'white',
                          '&:hover': { bgcolor: 'error.dark' }
                        }}
                        size="small"
                        onClick={handleRemovePhoto}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Box>
                  ) : (
                    <Box
                      sx={{
                        width: 120,
                        height: 120,
                        borderRadius: '50%',
                        border: '2px dashed #ccc',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        mx: 'auto',
                        mb: 2,
                        cursor: 'pointer',
                        '&:hover': { borderColor: '#1976d2' }
                      }}
                      component="label"
                    >
                      <PersonIcon sx={{ fontSize: 40, color: 'text.secondary' }} />
                      <input
                        type="file"
                        accept="image/*"
                        onChange={handlePhotoChange}
                        style={{ display: 'none' }}
                      />
                    </Box>
                  )}
                  <Button
                    variant="outlined"
                    component="label"
                    size="small"
                    sx={{ mb: 1, mr: 1 }}
                  >
                    {photoPreview ? 'Change Photo' : 'Upload Photo'}
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handlePhotoChange}
                      style={{ display: 'none' }}
                    />
                  </Button>
                  <Button
                    variant="contained"
                    size="small"
                    sx={{ mb: 1 }}
                    onClick={() => setShowCamera(true)}
                  >
                    {photoPreview ? 'Retake with Camera' : 'Capture with Camera'}
                  </Button>
                  <Typography variant="caption" display="block" color="text.secondary">
                    Upload or capture a clear photo for facial recognition. JPG, PNG up to 5MB.
                  </Typography>
                </Box>
                {/* Camera Dialog */}
                <Dialog open={showCamera} onClose={() => setShowCamera(false)} maxWidth="md" fullWidth>
                  <DialogTitle>Capture Photo with Camera</DialogTitle>
                  <DialogContent>
                    <CameraCapture onPhotoCapture={handleCameraPhoto} onClose={() => setShowCamera(false)} />
                  </DialogContent>
                  <DialogActions>
                    <Button onClick={() => setShowCamera(false)}>Cancel</Button>
                  </DialogActions>
                </Dialog>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Roll Number *"
                  name="roll_number"
                  value={formData.roll_number}
                  onChange={handleInputChange}
                  required
                  error={Boolean(formErrors.roll_number)}
                  helperText={formErrors.roll_number}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Admission Number *"
                  name="admission_number"
                  value={formData.admission_number}
                  onChange={handleInputChange}
                  required
                  error={Boolean(formErrors.admission_number)}
                  helperText={formErrors.admission_number}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Full Name *"
                  name="full_name"
                  value={formData.full_name}
                  onChange={handleInputChange}
                  required
                  error={Boolean(formErrors.full_name)}
                  helperText={formErrors.full_name}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth required error={Boolean(formErrors.class_name)}>
                  <InputLabel>Class</InputLabel>
                  <Select
                    name="class_name"
                    value={formData.class_name}
                    label="Class"
                    onChange={(e) => {
                      handleInputChange(e);
                      // Clear section when class changes
                      setFormData(prev => ({ ...prev, section: '' }));
                    }}
                  >
                    {[...new Set(availableClasses.map(c => c.name))].map(name => (
                      <MenuItem key={name} value={name}>{name}</MenuItem>
                    ))}
                  </Select>
                  {formErrors.class_name && <Typography variant="caption" color="error">{formErrors.class_name}</Typography>}
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth required error={Boolean(formErrors.section)}>
                  <InputLabel>Section</InputLabel>
                  <Select
                    name="section"
                    value={formData.section}
                    label="Section"
                    onChange={handleInputChange}
                    disabled={!formData.class_name}
                  >
                    {availableClasses.filter(c => c.name === formData.class_name).map(c => (
                      <MenuItem key={c.section} value={c.section}>{c.section}</MenuItem>
                    ))}
                  </Select>
                  {formErrors.section && <Typography variant="caption" color="error">{formErrors.section}</Typography>}
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Date of Birth"
                  name="date_of_birth"
                  type="date"
                  value={formData.date_of_birth}
                  onChange={handleInputChange}
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Parent Contact"
                  name="parent_contact"
                  value={formData.parent_contact}
                  onChange={handleInputChange}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Parent Email"
                  name="parent_email"
                  type="email"
                  value={formData.parent_email}
                  onChange={handleInputChange}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Address"
                  name="address"
                  multiline
                  rows={3}
                  value={formData.address}
                  onChange={handleInputChange}
                />
              </Grid>
            </Grid>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog} disabled={uploadingPhoto}>
            Cancel
          </Button>
          <Button 
            onClick={handleSubmit} 
            variant="contained"
            disabled={uploadingPhoto}
            startIcon={uploadingPhoto ? <CircularProgress size={20} /> : null}
          >
            {uploadingPhoto ? 'Uploading...' : (editingStudent ? 'Update' : 'Add')} Student
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={confirmDeleteOpen} onClose={() => setConfirmDeleteOpen(false)}>
        <DialogTitle>Delete Student</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete
            {studentToDelete ? ` "${studentToDelete.full_name}" (${studentToDelete.admission_number})` : ''}?
            This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmDeleteOpen(false)}>Cancel</Button>
          <Button color="error" variant="contained" onClick={handleConfirmDelete}>
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}

export default Students;