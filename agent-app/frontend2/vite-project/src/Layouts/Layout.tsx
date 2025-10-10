import React, { useState, useContext } from "react";
import { useTheme } from '@mui/material/styles';
import {
  Drawer, List, ListItemButton, ListItemIcon, ListItemText, CssBaseline, Box, IconButton, Button, ListSubheader, Divider, AppBar as MuiAppBar, Toolbar, Stack
} from "@mui/material";
import { styled } from "@mui/material/styles";
import { Link, Outlet, useNavigate } from "react-router-dom";
import { useChatContext } from "../contexts/ChatContext";
import { ColorModeContext } from "../App";
import MenuIcon from "@mui/icons-material/Menu";
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import AddIcon from "@mui/icons-material/Add";
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import SmartToyOutlinedIcon from '@mui/icons-material/SmartToyOutlined';
import LightbulbOutlinedIcon from '@mui/icons-material/LightbulbOutlined';
import BugReportOutlinedIcon from '@mui/icons-material/BugReportOutlined';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';
import logo from '../assets/spark-final.png';
const drawerWidth = 260;

const Main = styled("main", { shouldForwardProp: (prop) => prop !== "open" })<{ open?: boolean; }>(({ theme, open }) => ({
  flexGrow: 1,
  padding: theme.spacing(3),
  transition: theme.transitions.create("margin", {
    easing: theme.transitions.easing.sharp,
    duration: theme.transitions.duration.leavingScreen,
  }),
  marginLeft: `-${drawerWidth}px`,
  display: 'flex',
  flexDirection: 'column',
  height: 'calc(100vh - 64px)',
  ...(open && {
    transition: theme.transitions.create("margin", {
      easing: theme.transitions.easing.easeOut,
      duration: theme.transitions.duration.enteringScreen,
    }),
    marginLeft: 0,
  }),
}));
const AppBar = styled(MuiAppBar, { shouldForwardProp: (prop) => prop !== "open", })<{ open?: boolean }>(({ theme, open }) => ({
  transition: theme.transitions.create(["margin", "width"], {
    easing: theme.transitions.easing.sharp,
    duration: theme.transitions.duration.leavingScreen,
  }),
  ...(open && {
    width: `calc(100% - ${drawerWidth}px)`,
    marginLeft: `${drawerWidth}px`,
    transition: theme.transitions.create(["margin", "width"], {
      easing: theme.transitions.easing.easeOut,
      duration: theme.transitions.duration.enteringScreen,
    }),
  }),
}));
const DrawerHeader = styled("div")(({ theme }) => ({
  display: "flex",
  alignItems: "center",
  padding: theme.spacing(0, 1),
  ...theme.mixins.toolbar,
  justifyContent: "space-between",
}));

const agentList = [
    { name: "SPARC", icon: <SmartToyOutlinedIcon /> },
];

const Layout: React.FC = () => {
  const [open, setOpen] = useState(true);
  const { handleCancel, clearChat, messages } = useChatContext();
  const navigate = useNavigate();
  const theme = useTheme();
  const colorMode = useContext(ColorModeContext);

  const handleDrawerOpen = () => setOpen(true);
  const handleDrawerClose = () => setOpen(false);

  const handleClearChat = () => {
    clearChat();
    navigate("/");
  };

  return (
    <Box sx={{ display: "flex", height: "100vh" }}>
      <CssBaseline />

      <AppBar
        position="fixed"
        open={open}
        sx={{
          boxShadow: "none",
          borderBottom: "1px solid",
          borderColor: "divider",
        }}
      >
        <Toolbar sx={{ justifyContent: 'space-between' }}>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            onClick={handleDrawerOpen}
            edge="start"
            sx={{ mr: 2, ...(open && { display: "none" }) }}
          >
            <MenuIcon />
          </IconButton>
          <IconButton sx={{ ml: 1 }} onClick={colorMode.toggleColorMode} color="inherit">
            {theme.palette.mode === 'dark' ? <Brightness7Icon /> : <Brightness4Icon />}
          </IconButton>
        </Toolbar>
      </AppBar>

      <Drawer
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          "& .MuiDrawer-paper": {
            width: drawerWidth,
            boxSizing: "border-box",
            borderRight: "none",
          },
        }}
        variant="persistent"
        anchor="left"
        open={open}
      >
        <DrawerHeader>
          <Link to="/" style={{ textDecoration: "none", color: "inherit" }}>
            <Box
              component="img"
              src={logo}
              alt="SPARC logo"
              sx={{ height: 40, pl: 1 }}
            />
          </Link>
          <IconButton onClick={handleDrawerClose}>
            <ChevronLeftIcon />
          </IconButton>
        </DrawerHeader>

        <Box sx={{ px: 2, mb: 2 }}>
          <Stack spacing={1}>
            <Button
              onClick={handleCancel}
              variant="outlined"
              startIcon={<AddIcon />}
              fullWidth
              sx={{
                justifyContent: "flex-start",
                textTransform: "none",
              }}
            >
              Start new chat
            </Button>
            {messages.length > 0 && (
              <Button
                onClick={handleClearChat}
                variant="outlined"
                color="error"
                startIcon={<DeleteOutlineIcon />}
                fullWidth
                sx={{ justifyContent: "flex-start", textTransform: "none" }}
              >
                Clear Chat
              </Button>
            )}
          </Stack>
        </Box>

        <List
          subheader={
            <ListSubheader sx={{ bgcolor: "transparent" }}>
              Agents
            </ListSubheader>
          }
        >
          {agentList.map((agent) => (
            <ListItemButton key={agent.name} selected={agent.name === "Jarvis"}>
              <ListItemIcon sx={{ minWidth: 40 }}>
                {agent.icon}
              </ListItemIcon>
              <ListItemText primary={agent.name} />
            </ListItemButton>
          ))}
        </List>

        <Box sx={{ flexGrow: 1 }} />
        <Divider />
        <List>
          <ListItemButton>
            <ListItemIcon>
              <LightbulbOutlinedIcon />
            </ListItemIcon>
            <ListItemText primary="Feature Request" />
          </ListItemButton>
          <ListItemButton>
            <ListItemIcon>
              <BugReportOutlinedIcon />
            </ListItemIcon>
            <ListItemText primary="Bug Report" />
          </ListItemButton>
        </List>
      </Drawer>

      <Main open={open}>
        <DrawerHeader />
        <Outlet />
      </Main>
    </Box>
  );
};

export default Layout;