import React, { useState } from "react";
import {
  Drawer,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  CssBaseline,
  Box,
  Typography,
  IconButton,
  Button,
  ListSubheader,
  Divider,
  AppBar as MuiAppBar,
  Toolbar,
  Stack,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import { Link, useNavigate } from "react-router-dom"; // 1. Import useNavigate
import { useChatContext } from "../contexts/ChatContext";
import MenuIcon from "@mui/icons-material/Menu";
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import AddIcon from "@mui/icons-material/Add";
import SmartToyOutlinedIcon from '@mui/icons-material/SmartToyOutlined';
import LightbulbOutlinedIcon from '@mui/icons-material/LightbulbOutlined';
import BugReportOutlinedIcon from '@mui/icons-material/BugReportOutlined';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';

const drawerWidth = 260;

const Main = styled("main", { shouldForwardProp: (prop) => prop !== "open" })<{ open?: boolean; }>(({ theme, open }) => ({ flexGrow: 1, padding: theme.spacing(3), transition: theme.transitions.create("margin", { easing: theme.transitions.easing.sharp, duration: theme.transitions.duration.leavingScreen, }), marginLeft: `-${drawerWidth}px`, ...(open && { transition: theme.transitions.create("margin", { easing: theme.transitions.easing.easeOut, duration: theme.transitions.duration.enteringScreen, }), marginLeft: 0, }), }));
const AppBar = styled(MuiAppBar, { shouldForwardProp: (prop) => prop !== "open", })<{ open?: boolean }>(({ theme, open }) => ({ transition: theme.transitions.create(["margin", "width"], { easing: theme.transitions.easing.sharp, duration: theme.transitions.duration.leavingScreen, }), ...(open && { width: `calc(100% - ${drawerWidth}px)`, marginLeft: `${drawerWidth}px`, transition: theme.transitions.create(["margin", "width"], { easing: theme.transitions.easing.easeOut, duration: theme.transitions.duration.enteringScreen, }), }), }));
const DrawerHeader = styled("div")(({ theme }) => ({ display: "flex", alignItems: "center", padding: theme.spacing(0, 1), ...theme.mixins.toolbar, justifyContent: "space-between", }));


const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [open, setOpen] = useState(true);
  const { handleCancel, clearChat, messages } = useChatContext(); 
  const navigate = useNavigate(); 
  const handleDrawerOpen = () => setOpen(true);
  const handleDrawerClose = () => setOpen(false);

  const handleClearChat = () => {
    clearChat(); 
    navigate('/'); 
  };

  return (
    <Box sx={{ display: "flex", height: "100vh" }}>
      <CssBaseline />
      
      <AppBar position="fixed" open={open} sx={{ backgroundColor: 'white', color: 'black', boxShadow: 'none', borderBottom: '1px solid #ddd' }}>
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            onClick={handleDrawerOpen}
            edge="start"
            sx={{ mr: 2, ...(open && { display: "none" }) }}
          >
            <MenuIcon />
          </IconButton>
        </Toolbar>
      </AppBar>

      <Drawer
        sx={{ width: drawerWidth, flexShrink: 0, "& .MuiDrawer-paper": { width: drawerWidth, boxSizing: "border-box", backgroundColor: "#f9f9f9", borderRight: 'none' } }}
        variant="persistent"
        anchor="left"
        open={open}
      >
        <DrawerHeader>
            <Link to="/" style={{ textDecoration: 'none', color: 'inherit' }}>
                <Typography variant="h6" sx={{ fontWeight: "bold", pl: 1 }}>
                    HeyBud
                </Typography>
            </Link>
            <IconButton onClick={handleDrawerClose}>
                <ChevronLeftIcon />
            </IconButton>
        </DrawerHeader>

        
           <Box sx={{ px: 2, mb: 2 }}>
            <Stack spacing={1}>
                <Button onClick={handleCancel} variant="outlined" startIcon={<AddIcon />} fullWidth sx={{ justifyContent: 'flex-start', textTransform: 'none', color: 'black', borderColor: '#ddd', '&:hover': { borderColor: '#ccc', backgroundColor: '#f0f0f0' } }}>
                    Start new chat
                </Button>
                {messages.length > 0 && (
                    <Button onClick={handleClearChat} variant="outlined" color="error" startIcon={<DeleteOutlineIcon />} fullWidth sx={{ justifyContent: 'flex-start', textTransform: 'none' }}>
                        Clear Chat
                    </Button>
                )}
            </Stack>
        </Box>

        <List subheader={<ListSubheader sx={{ bgcolor: 'transparent' }}>Agents</ListSubheader>}>
          <ListItemButton selected>
            <ListItemIcon sx={{ minWidth: 40 }}><SmartToyOutlinedIcon /></ListItemIcon>
            <ListItemText primary="Dex Agent" />
          </ListItemButton>
        </List>

        <Box sx={{ flexGrow: 1 }} /> 
        <Divider />
        <List>
            <ListItemButton><ListItemIcon><LightbulbOutlinedIcon /></ListItemIcon><ListItemText primary="Feature Request" /></ListItemButton>
            <ListItemButton><ListItemIcon><BugReportOutlinedIcon /></ListItemIcon><ListItemText primary="Bug Report" /></ListItemButton>
        </List>
      </Drawer>

      <Main open={open}>
        <DrawerHeader />
        {children}
      </Main>
    </Box>
  );
};

export default Layout;