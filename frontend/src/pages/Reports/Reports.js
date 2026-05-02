import { Assessment, BarChart, Download, Timeline } from '@mui/icons-material';
import {
    Alert,
    Box,
    Button,
    Card,
    CardContent,
    Chip,
    Container,
    Grid,
    TextField,
    Typography
} from '@mui/material';
import { useEffect, useState } from 'react';
import { toast } from 'react-toastify';
import { Bar, CartesianGrid, Legend, Line, BarChart as ReBarChart, LineChart as ReLineChart, Tooltip as ReTooltip, ResponsiveContainer, XAxis, YAxis } from 'recharts';
import { apiService } from '../../services/apiService';

function Reports() {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [summary, setSummary] = useState([]);
  const [students, setStudents] = useState([]);
  const [classes, setClasses] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const loadReports = async () => {
    setLoading(true);
    setError('');
    try {
      const filters = {};
      if (startDate) filters.start_date = startDate;
      if (endDate) filters.end_date = endDate;

      const summaryResp = await apiService.getReportsSummary(filters);
      const studentResp = await apiService.getStudentAnalytics(filters);
      const classResp = await apiService.getClassAnalytics(filters);

      setSummary(summaryResp.summary || []);
      setStudents(studentResp.students || []);
      setClasses(classResp.classes || []);
    } catch (err) {
      setError(err.message || 'Failed to load reports');
      toast.error(err.message || 'Failed to load reports');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format) => {
    try {
      const filters = {};
      if (startDate) filters.start_date = startDate;
      if (endDate) filters.end_date = endDate;

      const blob = await apiService.exportAttendanceReport(format, filters);
      const url = window.URL.createObjectURL(new Blob([blob]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `attendance_report.${format === 'excel' ? 'xlsx' : 'pdf'}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      toast.error(err.message || 'Export failed');
    }
  };

  useEffect(() => {
    loadReports();
  }, []);

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <div className="page-header">
        <Typography variant="h4" className="page-title">
          Reports & Analytics
        </Typography>
        <Typography variant="body1" className="page-subtitle">
          Comprehensive attendance reports and Power BI integration
        </Typography>
      </div>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                label="Start Date"
                type="date"
                InputLabelProps={{ shrink: true }}
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                label="End Date"
                type="date"
                InputLabelProps={{ shrink: true }}
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
            </Grid>
            <Grid item xs={12} md={6} sx={{ display: 'flex', gap: 2, justifyContent: { xs: 'flex-start', md: 'flex-end' } }}>
              <Button variant="outlined" onClick={loadReports} disabled={loading}>
                Refresh
              </Button>
              <Button variant="contained" startIcon={<Download />} onClick={() => handleExport('excel')} disabled={loading}>
                Export Excel
              </Button>
              <Button variant="outlined" startIcon={<Download />} onClick={() => handleExport('pdf')} disabled={loading}>
                Export PDF
              </Button>
            </Grid>
          </Grid>
          {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
        </CardContent>
      </Card>


      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Daily, Weekly, and Monthly Summary
          </Typography>
          {summary.length === 0 ? (
            <Alert severity="info">No summary data available for the selected range.</Alert>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <ReLineChart data={summary} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <ReTooltip />
                <Legend />
                <Line type="monotone" dataKey="present" stroke="#4caf50" name="Present" />
                <Line type="monotone" dataKey="absent" stroke="#f44336" name="Absent" />
                <Line type="monotone" dataKey="late" stroke="#ff9800" name="Late" />
              </ReLineChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>

      <Grid container spacing={3} sx={{ mt: 1 }}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Student-wise Attendance Analytics
              </Typography>
              {students.length === 0 ? (
                <Alert severity="info">No student analytics found.</Alert>
              ) : (
                <ResponsiveContainer width="100%" height={300}>
                  <ReBarChart data={students} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="student_name" />
                    <YAxis />
                    <ReTooltip />
                    <Legend />
                    <Bar dataKey="present" fill="#4caf50" name="Present" />
                    <Bar dataKey="total" fill="#1976d2" name="Total" />
                  </ReBarChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Class and Section Performance
              </Typography>
              {classes.length === 0 ? (
                <Alert severity="info">No class analytics found.</Alert>
              ) : (
                <ResponsiveContainer width="100%" height={300}>
                  <ReBarChart data={classes} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="class_name" />
                    <YAxis />
                    <ReTooltip />
                    <Legend />
                    <Bar dataKey="present" fill="#4caf50" name="Present" />
                    <Bar dataKey="absent" fill="#f44336" name="Absent" />
                    <Bar dataKey="total" fill="#1976d2" name="Total" />
                  </ReBarChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
}

export default Reports;