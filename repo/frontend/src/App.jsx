import React, { useState } from 'react';
import { Routes, Route, Link } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Box,
  IconButton,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Map as MapIcon,
  Hearing as HearingIcon,
  Description as ReportIcon,
  Mic as MicIcon,
  Dashboard as DashboardIcon,
} from '@mui/icons-material';

import NoiseMap from './pages/NoiseMap';
import Hearings from './pages/Hearings';
import Reports from './pages/Reports';
import Dashboard from './pages/Dashboard';
import HearingDetail from './pages/HearingDetail';
import ReportDetail from './pages/ReportDetail';

const drawerWidth = 240;

function App() {
  const [mobileOpen, setMobileOpen] = useState(false);

  const menuItems = [
    { text: '概览', icon: <DashboardIcon />, path: '/' },
    { text: '噪声地图', icon: <MapIcon />, path: '/noise-map' },
    { text: '听证会', icon: <HearingIcon />, path: '/hearings' },
    { text: '报告', icon: <ReportIcon />, path: '/reports' },
  ];

  const drawer = (
    <div>
      <Toolbar />
      <List>
        {menuItems.map((item) => (
          <ListItem
            button
            component={Link}
            to={item.path}
            key={item.text}
            onClick={() => setMobileOpen(false)}
          >
            <ListItemIcon>{item.icon}</ListItemIcon>
            <ListItemText primary={item.text} />
          </ListItem>
        ))}
      </List>
    </div>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
        <Toolbar>
          <IconButton
            color="inherit"
            edge="start"
            onClick={() => setMobileOpen(!mobileOpen)}
            sx={{ mr: 2, display: { sm: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <MicIcon sx={{ mr: 2 }} />
          <Typography variant="h6" noWrap component="div">
            智慧城市噪声听证会系统
          </Typography>
        </Toolbar>
      </AppBar>

      <Box
        component="nav"
        sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
      >
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={() => setMobileOpen(false)}
          ModalProps={{ keepMounted: true }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: drawerWidth,
            },
          }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: drawerWidth,
            },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          mt: 8,
        }}
      >
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/noise-map" element={<NoiseMap />} />
          <Route path="/hearings" element={<Hearings />} />
          <Route path="/hearings/:id" element={<HearingDetail />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/reports/:id" element={<ReportDetail />} />
        </Routes>
      </Box>
    </Box>
  );
}

export default App;
