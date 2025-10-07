import React from "react";
import { Routes, Route } from "react-router-dom"; 
import Home from "./pages/Home";
import Chat from "./pages/Chat";
import Layout from "./Layouts/Layout";
import { useBackendHealth } from "./hooks/useBackendHealth";
import { BackendLoadingScreen } from "./components/BackendLoadingScreen";
import { BackendUnavailable } from "./components/BackendUnavailable";
import { ChatProvider } from "./contexts/ChatContext";

const API_BASE_URL = "http://localhost:8000";

const App: React.FC = () => {
  const { isBackendReady, isCheckingBackend } = useBackendHealth(API_BASE_URL);

  if (isCheckingBackend) return <BackendLoadingScreen />;
  if (!isBackendReady) return <BackendUnavailable />;

  return (
    <ChatProvider apiBaseUrl={API_BASE_URL}>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/chat" element={<Chat />} />
        </Routes>
      </Layout>
    </ChatProvider>
  );
};

export default App;