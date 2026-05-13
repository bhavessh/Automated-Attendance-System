import {
  CheckCircle,
  People,
  School,
  TrendingUp,
} from '@mui/icons-material';
import {
  Alert,
  Box,
  Card,
  CardContent,
  CircularProgress,
  Container,
  Divider,
  FormControl,
  Grid,
  InputLabel,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  MenuItem,
  Select,
  Typography,
} from '@mui/material';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { toast } from 'react-toastify';
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { apiService } from '../../services/apiService';

function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const pollRef = useRef(null);
  const studentsLoadedRef = useRef(false);
  const [students, setStudents] = useState([]);
  const [classFilter, setClassFilter] = useState('');
  const [sectionFilter, setSectionFilter] = useState('');

  const loadDashboardData = useCallback(async () => {
    try {
      if (!stats) setLoading(true);
      const filters = {};
      if (classFilter) filters.class = classFilter;
      if (sectionFilter) filters.section = sectionFilter;
      const response = await apiService.getAttendanceStatistics(filters);
      setStats(response.statistics);
      setError('');
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      setError('Failed to load dashboard data');
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  }, [classFilter, sectionFilter, stats]);

  useEffect(() => {
    // Load options and initial stats
    if (!studentsLoadedRef.current) {
      studentsLoadedRef.current = true;
      loadClassSectionOptions();
    }
    loadDashboardData();

    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = setInterval(loadDashboardData, 30000);

    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [loadDashboardData]);

  

  const loadClassSectionOptions = async () => {
    try {
      const data = await apiService.getStudents();
      setStudents(data.students || []);
    } catch (e) {
      console.warn('Failed to load student list for filters');
    }
  };

  const availableClasses = useMemo(() => {
    const setC = new Set();
    (students || []).forEach((s) => s.class_name && setC.add(s.class_name));
    return Array.from(setC);
  }, [students]);

  const availableSections = useMemo(() => {
    const setS = new Set();
    (students || [])
      .filter((s) => (classFilter ? s.class_name === classFilter : true))
      .forEach((s) => s.section && setS.add(s.section));
    return Array.from(setS);
  }, [students, classFilter]);

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress size={60} />
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Alert severity="error">{error}</Alert>
      </Container>
    );
  }

  const statCards = [
    {
      title: 'Total Students',
      value: stats?.totalStudents || 0,
      icon: People,
      color: '#1976d2',
      bgColor: 'rgba(25, 118, 210, 0.1)',
    },
    {
      title: 'Present Today',
      value: stats?.presentToday || 0,
      icon: CheckCircle,
      color: '#4caf50',
      bgColor: 'rgba(76, 175, 80, 0.1)',
    },
    {
      title: 'Attendance Rate',
      value: `${stats?.attendanceRate || 0}%`,
      icon: TrendingUp,
      color: '#ff9800',
      bgColor: 'rgba(255, 152, 0, 0.1)',
    },
    {
      title: 'Alerts',
      value: stats?.alertsCount || 0,
      icon: School,
      color: '#f44336',
      bgColor: 'rgba(244, 67, 54, 0.1)',
    },
  ];

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <div className="page-header">
        <Typography variant="h4" className="page-title">
          Dashboard
        </Typography>
        <Typography variant="body1" className="page-subtitle">
          Welcome to the Automated Attendance System
        </Typography>
      </div>

      <div className="card" style={{ marginBottom: 32 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth>
              <InputLabel>Class</InputLabel>
              <Select
                value={classFilter}
                label="Class"
                onChange={(e) => {
                  setClassFilter(e.target.value);
                  if (e.target.value === '' || !availableSections.includes(sectionFilter)) {
                    setSectionFilter('');
                  }
                }}
                className="input"
              >
                <MenuItem value="">All Classes</MenuItem>
                {availableClasses.map((c) => (
                  <MenuItem key={c} value={c}>{c}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth>
              <InputLabel>Section</InputLabel>
              <Select
                value={sectionFilter}
                label="Section"
                onChange={(e) => setSectionFilter(e.target.value)}
                className="input"
              >
                <MenuItem value="">All Sections</MenuItem>
                {availableSections.map((s) => (
                  <MenuItem key={s} value={s}>{s}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </div>

      {/* Attendance Trend Chart */}
      <div className="card" style={{ marginBottom: 40 }}>
        <Typography variant="h6" gutterBottom>
          Attendance Trend
        </Typography>
        {stats?.trend && stats.trend.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={stats.trend} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="present" stroke="#4caf50" name="Present" />
              <Line type="monotone" dataKey="absent" stroke="#f44336" name="Absent" />
              <Line type="monotone" dataKey="late" stroke="#ff9800" name="Late" />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <Typography variant="body2" color="textSecondary">No trend data available.</Typography>
        )}
      </div>
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {statCards.map((card, index) => {
          const Icon = card.icon;
          return (
            <Grid item xs={12} sm={6} md={3} key={index}>
              <Card
                sx={{
                  height: '100%',
                  background: card.bgColor,
                  transition: 'transform 0.2s ease-in-out',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                  },
                }}
              >
                <CardContent>
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                    }}
                  >
                    <Box>
                      <Typography
                        variant="h3"
                        sx={{
                          fontWeight: 700,
                          color: card.color,
                          mb: 1,
                        }}
                      >
                        {card.value}
                      </Typography>
                      <Typography
                        variant="body2"
                        sx={{
                          color: 'text.secondary',
                          fontWeight: 500,
                        }}
                      >
                        {card.title}
                      </Typography>
                    </Box>
                    <Icon
                      sx={{
                        fontSize: 48,
                        color: card.color,
                        opacity: 0.8,
                      }}
                    />
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          );
        })}
      </Grid>

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Actions
              </Typography>
              <Box sx={{ p: 3 }}>
                <Typography variant="body1" color="textSecondary">
                  Use the navigation menu to access different features:
                </Typography>
                <List sx={{ mt: 2 }}>
                  <ListItem>
                    <ListItemIcon><People color="primary" /></ListItemIcon>
                    <ListItemText
                      primary="Students"
                      secondary="Manage student records and register faces"
                    />
                  </ListItem>
                  <Divider component="li" />
                  <ListItem>
                    <ListItemIcon><CheckCircle color="success" /></ListItemIcon>
                    <ListItemText
                      primary="Attendance"
                      secondary="Mark attendance using facial recognition"
                    />
                  </ListItem>
                  <Divider component="li" />
                  <ListItem>
                    <ListItemIcon><TrendingUp color="warning" /></ListItemIcon>
                    <ListItemText
                      primary="Reports"
                      secondary="View attendance reports and analytics"
                    />
                  </ListItem>
                  <Divider component="li" />
                  <ListItem>
                    <ListItemIcon><School color="error" /></ListItemIcon>
                    <ListItemText
                      primary="Settings"
                      secondary="Configure system settings (Admin only)"
                    />
                  </ListItem>
                </List>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Status
              </Typography>
              <Box sx={{ p: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Box
                    sx={{
                      width: 12,
                      height: 12,
                      borderRadius: '50%',
                      bgcolor: '#4caf50',
                      mr: 2,
                    }}
                  />
                  <Typography variant="body2">
                    Face Recognition: <strong>Active</strong>
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Box
                    sx={{
                      width: 12,
                      height: 12,
                      borderRadius: '50%',
                      bgcolor: '#4caf50',
                      mr: 2,
                    }}
                  />
                  <Typography variant="body2">
                    Database: <strong>Connected</strong>
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Box
                    sx={{
                      width: 12,
                      height: 12,
                      borderRadius: '50%',
                      bgcolor: '#ff9800',
                      mr: 2,
                    }}
                  />
                  <Typography variant="body2">
                    Sync Status: <strong>Offline Mode</strong>
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
}

export default Dashboard;