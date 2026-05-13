import { AccountCircle, Logout } from '@mui/icons-material';
import { Avatar, IconButton, ListItemIcon, Menu, MenuItem } from '@mui/material';
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { authService } from '../../services/authService';

export default function AccountMenu() {
  const [anchorEl, setAnchorEl] = React.useState(null);
  const open = Boolean(anchorEl);
  const handleOpen = (e) => setAnchorEl(e.currentTarget);
  const handleClose = () => setAnchorEl(null);
  const navigate = useNavigate();

  const handleLogout = () => {
    handleClose();
    try {
      authService.logout();
    } catch (e) {
      // ignore
    }
    // navigate to login and reload to ensure app state resets
    navigate('/login');
    window.location.reload();
  };

  return (
    <>
      <IconButton onClick={handleOpen} sx={{ p: 0.5 }} aria-label="Open account menu">
        <Avatar sx={{ width: 36, height: 36 }}>U</Avatar>
      </IconButton>
      <Menu anchorEl={anchorEl} open={open} onClose={handleClose} PaperProps={{ sx: { minWidth: 180 } }}>
        <MenuItem onClick={handleClose}><ListItemIcon><AccountCircle fontSize="small"/></ListItemIcon>Profile</MenuItem>
        <MenuItem onClick={handleLogout}><ListItemIcon><Logout fontSize="small"/></ListItemIcon>Logout</MenuItem>
      </Menu>
    </>
  );
}
