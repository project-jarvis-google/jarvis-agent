import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useChatContext } from '../contexts/ChatContext';
import { WelcomeScreen } from '../components/WelcomeScreen';

const Home: React.FC = () => {
  const navigate = useNavigate();
  const { handleSubmit, isLoading } = useChatContext();

  const handleInitialSubmit = (query: string, files: File[]) => {
    navigate('/chat');
    
    handleSubmit(query, files);
  };

  return (
    <WelcomeScreen
      handleSubmit={handleInitialSubmit}
      isLoading={isLoading}
    />
  );
};

export default Home;