import React from 'react';
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Avatar,
  Menu,
  MenuItem,
  Divider,
  Box,
  Tooltip,
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import {
  Dashboard,
  People,
  CheckCircle,
  Assessment,
  Settings,
  AccountCircle,
  Logout,
  School,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import './Navigation.css';

const drawerWidth = 280;

const navigationItems = [
  { text: 'Dashboard', icon: Dashboard, path: '/dashboard', roles: ['admin', 'teacher', 'principal'] },
  { text: 'Students', icon: People, path: '/students', roles: ['admin', 'teacher', 'principal'] },
  { text: 'Attendance', icon: CheckCircle, path: '/attendance', roles: ['admin', 'teacher', 'principal'] },
  { text: 'Reports', icon: Assessment, path: '/reports', roles: ['admin', 'teacher', 'principal'] },
  { text: 'Settings', icon: Settings, path: '/settings', roles: ['admin'] },
  { text: 'Add Teacher', icon: People, path: '/admin/add-teacher', roles: ['admin'] },
];

function Navigation({ currentUser, onLogout }) {
  const navigate = useNavigate();
  const location = useLocation();
  const [anchorEl, setAnchorEl] = React.useState(null);
  const [collapsed, setCollapsed] = React.useState(false);
  const [hovered, setHovered] = React.useState(false);

  React.useEffect(() => {
    const handleResize = () => {
      setCollapsed(window.innerWidth < 900);
    };
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const handleUserMenuOpen = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleUserMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    handleUserMenuClose();
    onLogout();
  };

  const filteredNavigationItems = navigationItems.filter(item => 
    item.roles.includes(currentUser?.role)
  );

  return (
    <>
      {/* App Bar */}
      <AppBar
        position="fixed"
        elevation={0}
        sx={{
          zIndex: (theme) => theme.zIndex.drawer + 1,
          background: 'linear-gradient(90deg, rgb(99,102,209) 0%, rgb(140,113,199) 100%)',
          color: 'var(--mint-text)'
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            edge="start"
            onClick={() => setCollapsed((c) => !c)}
            sx={{ mr: 1, display: { xs: 'inline-flex', md: 'inline-flex' } }}
            aria-label={collapsed ? 'Expand navigation' : 'Collapse navigation'}
          >
            <MenuIcon />
          </IconButton>
          <School sx={{ mr: 2, color: 'var(--mint)' }} />
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1, fontWeight: 700 }}>
            Automated Attendance System
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Typography variant="body2" sx={{ mr: 2, display: { xs: 'none', sm: 'block' }, color: 'var(--mint-text)' }}>
              Welcome, {currentUser?.full_name}
            </Typography>
            <IconButton
              size="large"
              edge="end"
              aria-label="account of current user"
              aria-controls={anchorEl ? 'user-menu' : undefined}
              aria-haspopup="true"
              onClick={handleUserMenuOpen}
              sx={{ color: 'var(--mint)', cursor: 'pointer' }}
              className={anchorEl ? 'avatar-open' : 'avatar-btn'}
            >
              <Avatar sx={{ width: 32, height: 32, bgcolor: 'var(--mint)', color: 'var(--mint-text-invert)' }}>
                {currentUser?.full_name?.charAt(0) || 'U'}
              </Avatar>
            </IconButton>
          </Box>
        </Toolbar>
      </AppBar>

      {/* User Menu */}
      <Menu
        id="user-menu"
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleUserMenuClose}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'right',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'right',
        }}
        // ensure menu is rendered at the document body level so it isn't clipped by parent stacking contexts
        disablePortal={false}
        PaperProps={{ sx: { zIndex: 3000, transition: 'transform 180ms cubic-bezier(.2,.8,.2,1), opacity 180ms', transformOrigin: 'top right', background: 'var(--surface)', color: 'var(--ink)', minWidth: 180 } }}
        elevation={8}
      >
        <MenuItem onClick={handleUserMenuClose}>
          <ListItemIcon>
            <AccountCircle fontSize="small" />
          </ListItemIcon>
          Profile
        </MenuItem>
        <Divider />
        <MenuItem onClick={handleLogout}>
          <ListItemIcon>
            <Logout fontSize="small" />
          </ListItemIcon>
          Logout
        </MenuItem>
      </Menu>

      {/* Sidebar Drawer */}
      <Drawer
        variant="permanent"
        className="nav-drawer"
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
        sx={{
          width: (collapsed && !hovered) ? 72 : drawerWidth,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: (collapsed && !hovered) ? 72 : drawerWidth,
            boxSizing: 'border-box',
            background: 'var(--mint-sidebar-bg)',
            borderRight: '1px solid var(--mint-border)',
            transition: 'width 200ms ease',
            position: 'fixed',
            top: '64px',
            height: 'calc(100vh - 64px)'
          },
        }}
      >
        <Toolbar />
        <Box sx={{ overflow: 'auto', height: '100%', position: 'relative' }}>
          <List>
            {filteredNavigationItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <ListItem key={item.text} disablePadding>
                  <Tooltip title={item.text} placement="right" arrow>
                    <ListItemButton
                      onClick={() => navigate(item.path)}
                      className={isActive ? 'active-nav-item' : 'nav-item'}
                      aria-current={isActive ? 'page' : undefined}
                      tabIndex={0}
                      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') navigate(item.path); }}
                      sx={{
                        minHeight: 48,
                        px: 2.5,
                        borderRadius: 'var(--radius)',
                        margin: collapsed ? '6px 6px' : '6px 10px',
                        background: isActive ? 'var(--mint-gradient)' : 'transparent',
                        color: isActive ? 'var(--mint-text-invert)' : 'inherit',
                        fontWeight: isActive ? 600 : 400,
                        boxShadow: isActive ? '0 2px 12px rgba(103,125,233,0.12)' : 'none',
                        transition: 'transform 160ms ease, box-shadow 160ms ease, background 160ms ease',
                        '&:hover': { transform: 'translateY(-2px) scale(1.01)' },
                        '&:focus': { outline: 'none', boxShadow: '0 0 0 4px rgba(99,102,209,0.08)' },
                      }}
                    >
                      <ListItemIcon
                        sx={{
                          minWidth: 0,
                          mr: 3,
                          justifyContent: 'center',
                          color: isActive ? 'var(--mint)' : 'inherit',
                        }}
                      >
                        <Icon />
                      </ListItemIcon>
                      <ListItemText 
                        primary={item.text}
                        sx={{
                          display: collapsed ? 'none' : 'block',
                          '& .MuiListItemText-primary': {
                            fontWeight: isActive ? 700 : 400,
                            color: isActive ? 'var(--mint-text-invert)' : 'inherit',
                            transition: 'color 160ms ease',
                          },
                        }}
                      />
                    </ListItemButton>
                  </Tooltip>
                </ListItem>
              );
            })}
          </List>
          {/* User Info at Bottom */}
          <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, padding: 16 }}>
                <div className="card" style={{ display: 'flex', alignItems: 'center', gap: 12, background: 'linear-gradient(90deg, rgb(99,102,209) 0%, rgb(140,113,199) 100%)', boxShadow: 'var(--shadow)', borderRadius: 'var(--radius)' }}>
              <Avatar sx={{ width: 40, height: 40, bgcolor: 'var(--mint)', color: 'var(--mint-text-invert)' }}>
                {currentUser?.full_name?.charAt(0) || 'U'}
              </Avatar>
              <div>
                <Typography variant="subtitle2" sx={{ fontWeight: 700, color: 'var(--mint-text)' }}>
                  {currentUser?.full_name}
                </Typography>
                <Typography variant="caption" sx={{ color: 'var(--mint-text)' }}>
                  {currentUser?.role?.charAt(0).toUpperCase() + currentUser?.role?.slice(1)}
                </Typography>
              </div>
            </div>
          </div>
        </Box>
      </Drawer>
    </>
  );
}

export default Navigation;