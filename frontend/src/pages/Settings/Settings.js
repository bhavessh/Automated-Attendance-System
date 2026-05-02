import { CloudSync, Security, Settings as SettingsIcon, Tune } from '@mui/icons-material';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Container,
  FormControlLabel,
  Grid,
  Switch,
  TextField,
  Typography
} from '@mui/material';
import { useEffect, useState } from 'react';
import { toast } from 'react-toastify';
import { apiService } from '../../services/apiService';

function Settings() {
  const [settings, setSettings] = useState({
    faceRecognition: {
      threshold: 0.6,
      minFaceSize: 80
    },
    users: {
      allowTeacherEdits: false
    },
    powerbi: {
      workspaceId: '',
      datasetId: '',
      enabled: false
    },
    notifications: {
      emailEnabled: false,
      smsEnabled: false
    },
    backup: {
      enabled: false,
      schedule: 'daily'
    }
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const loadSettings = async () => {
    setLoading(true);
    setError('');
    try {
      const resp = await apiService.getSystemSettings();
      setSettings(resp.settings || settings);
    } catch (err) {
      setError(err.message || 'Failed to load settings');
      toast.error(err.message || 'Failed to load settings');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setLoading(true);
    setError('');
    try {
      await apiService.updateSystemSettings(settings);
      toast.success('Settings saved');
    } catch (err) {
      setError(err.message || 'Failed to save settings');
      toast.error(err.message || 'Failed to save settings');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSettings();
  }, []);

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <div className="page-header">
        <Typography variant="h4" className="page-title">
          System Settings
        </Typography>
        <Typography variant="body1" className="page-subtitle">
          Configure system parameters and preferences
        </Typography>
      </div>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Tune sx={{ fontSize: 48, color: 'secondary.main', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                Face Recognition Tuning
              </Typography>
              <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                Configure recognition parameters and accuracy thresholds.
              </Typography>
              <Chip label="Admin" size="small" color="secondary" />
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Security sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                Users & Permissions
              </Typography>
              <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                Manage user accounts, roles, and access control.
              </Typography>
              <Chip label="Admin" size="small" color="primary" />
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <CloudSync sx={{ fontSize: 48, color: 'success.main', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                Integrations & Backup
              </Typography>
              <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                Power BI setup, notifications, and system maintenance.
              </Typography>
              <Chip label="Admin" size="small" color="success" />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <SettingsIcon sx={{ mr: 1, color: 'text.secondary' }} />
            <Typography variant="subtitle1">System Configuration</Typography>
          </Box>
          <Box sx={{ ml: 1 }}>
            <Typography variant="body2" sx={{ mb: 1 }}>• Configure face recognition parameters</Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>• Manage user accounts and permissions</Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>• Set up Power BI integration</Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>• Configure notification settings</Typography>
            <Typography variant="body2">• System backup and maintenance</Typography>
          </Box>
        </CardContent>
      </Card>

      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Configure System Parameters
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>Face Recognition Tuning</Typography>
              <TextField
                fullWidth
                label="Recognition Threshold"
                type="number"
                inputProps={{ step: 0.01, min: 0, max: 1 }}
                value={settings.faceRecognition.threshold}
                onChange={(e) => setSettings((s) => ({
                  ...s,
                  faceRecognition: { ...s.faceRecognition, threshold: Number(e.target.value) }
                }))}
                sx={{ mb: 2 }}
              />
              <TextField
                fullWidth
                label="Min Face Size (px)"
                type="number"
                value={settings.faceRecognition.minFaceSize}
                onChange={(e) => setSettings((s) => ({
                  ...s,
                  faceRecognition: { ...s.faceRecognition, minFaceSize: Number(e.target.value) }
                }))}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>Users & Permissions</Typography>
              <FormControlLabel
                control={(
                  <Switch
                    checked={settings.users.allowTeacherEdits}
                    onChange={(e) => setSettings((s) => ({
                      ...s,
                      users: { ...s.users, allowTeacherEdits: e.target.checked }
                    }))}
                  />
                )}
                label="Allow teachers to edit attendance"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>Power BI Integration</Typography>
              <FormControlLabel
                control={(
                  <Switch
                    checked={settings.powerbi.enabled}
                    onChange={(e) => setSettings((s) => ({
                      ...s,
                      powerbi: { ...s.powerbi, enabled: e.target.checked }
                    }))}
                  />
                )}
                label="Enable Power BI integration"
              />
              <TextField
                fullWidth
                label="Power BI Workspace ID"
                value={settings.powerbi.workspaceId}
                onChange={(e) => setSettings((s) => ({
                  ...s,
                  powerbi: { ...s.powerbi, workspaceId: e.target.value }
                }))}
                sx={{ mt: 2 }}
              />
              <TextField
                fullWidth
                label="Power BI Dataset ID"
                value={settings.powerbi.datasetId}
                onChange={(e) => setSettings((s) => ({
                  ...s,
                  powerbi: { ...s.powerbi, datasetId: e.target.value }
                }))}
                sx={{ mt: 2 }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>Notifications</Typography>
              <FormControlLabel
                control={(
                  <Switch
                    checked={settings.notifications.emailEnabled}
                    onChange={(e) => setSettings((s) => ({
                      ...s,
                      notifications: { ...s.notifications, emailEnabled: e.target.checked }
                    }))}
                  />
                )}
                label="Enable email alerts"
              />
              <FormControlLabel
                control={(
                  <Switch
                    checked={settings.notifications.smsEnabled}
                    onChange={(e) => setSettings((s) => ({
                      ...s,
                      notifications: { ...s.notifications, smsEnabled: e.target.checked }
                    }))}
                  />
                )}
                label="Enable SMS alerts"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>System Backup</Typography>
              <FormControlLabel
                control={(
                  <Switch
                    checked={settings.backup.enabled}
                    onChange={(e) => setSettings((s) => ({
                      ...s,
                      backup: { ...s.backup, enabled: e.target.checked }
                    }))}
                  />
                )}
                label="Enable scheduled backups"
              />
              <TextField
                fullWidth
                label="Backup Schedule"
                value={settings.backup.schedule}
                onChange={(e) => setSettings((s) => ({
                  ...s,
                  backup: { ...s.backup, schedule: e.target.value }
                }))}
              />
            </Grid>
          </Grid>
          <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
            <Button variant="contained" onClick={handleSave} disabled={loading}>
              Save Settings
            </Button>
          </Box>
        </CardContent>
      </Card>
    </Container>
  );
}

export default Settings;