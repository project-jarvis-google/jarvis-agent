import React, { useState, useRef, useEffect } from "react";
import { Box, Paper, IconButton, Stack, CircularProgress, Avatar, Typography, Chip } from "@mui/material";
import { InputForm } from "./InputForm";
import ReactMarkdown from "react-markdown";
import remarkGfm from 'remark-gfm'; 
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import SmartToyOutlinedIcon from '@mui/icons-material/SmartToyOutlined';
import PersonOutlineOutlinedIcon from '@mui/icons-material/PersonOutlineOutlined';
import InsertDriveFileOutlinedIcon from '@mui/icons-material/InsertDriveFileOutlined';

interface DisplayFile { name: string; type: string; url: string; }
export interface Message { type: "human" | "ai"; content: string; id: string; files?: DisplayFile[]; }
interface ChatMessagesViewProps { messages: Message[]; isLoading: boolean; onSubmit: (query: string, files: File[]) => void; onCancel: () => void; }


export function ChatMessagesView({ messages, isLoading, onSubmit, onCancel }: ChatMessagesViewProps) {
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);


  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleCopy = async (text: string, messageId: string) => { await navigator.clipboard.writeText(text); setCopiedMessageId(messageId); setTimeout(() => setCopiedMessageId(null), 2000); };

  return (
    <Stack sx={{ height: "100%", width: '100%' }}>
      <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', overflowY: 'auto' }}>
        <Box ref={scrollRef} sx={{ width: '100%', maxWidth: '900px', p: 3 }}>
          <Stack spacing={4}>
            {messages.map((message) => (
              <Stack
                key={message.id}
                direction="row"
                spacing={2}
                sx={{ justifyContent: message.type === 'human' ? 'flex-end' : 'flex-start', alignItems: 'flex-start' }}
              >
                {message.type === 'ai' && <Avatar sx={{ bgcolor: 'primary.main' }}><SmartToyOutlinedIcon /></Avatar>}
                <Box sx={{ maxWidth: '80%' }}>
                  <Typography sx={{ fontWeight: 'bold', mb: 0.5 }}>
                    {message.type === 'human' ? 'You' : 'Jarvis Agent'}
                  </Typography>
                  <Paper
                    elevation={0}
                    sx={{ p: 2, bgcolor: message.type === 'human' ? 'action.selected' : 'action.hover', color: 'text.primary', borderRadius: '20px', position: 'relative' }}
                  >
                    {message.type === 'human' && message.files && message.files.length > 0 && (
                      <Stack spacing={1} sx={{ mb: message.content ? 1.5 : 0 }}>
                        {message.files.map((file, index) => (
                          <Paper key={index} variant="outlined" sx={{ p: 1, borderRadius: '12px' }}>
                            {file.type.startsWith('image/') ? (
                              <Box component="img" src={file.url} alt={file.name} sx={{ maxWidth: '100%', maxHeight: '200px', borderRadius: '8px', objectFit: 'contain' }} />
                            ) : (
                              <Chip icon={<InsertDriveFileOutlinedIcon />} label={file.name} variant="outlined" sx={{ height: 'auto', '& .MuiChip-label': { p: 1 } }} />
                            )}
                          </Paper>
                        ))}
                      </Stack>
                    )}
                    
                    {message.content && (
                      <Typography component="div" sx={{ '& p': { margin: 0 } }}>
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
                      </Typography>
                    )}
                  </Paper>
                </Box>
                 {message.type === 'human' && <Avatar><PersonOutlineOutlinedIcon /></Avatar>}
              </Stack>
            ))}
            {isLoading && messages.length > 0 && messages[messages.length - 1]?.type === 'human' && (
                            <Stack direction="row" spacing={2} sx={{ justifyContent: 'flex-start', alignItems: 'flex-start' }}>
                                <Avatar sx={{ bgcolor: 'primary.main' }}><SmartToyOutlinedIcon /></Avatar>
                                <Box>
                                    <Typography sx={{ fontWeight: 'bold', mb: 0.5 }}>Jarvis Agent</Typography>
                                    <Paper
                                        elevation={0}
                                        sx={{
                                            p: 2,
                                            borderRadius: '20px',
                                            bgcolor: 'action.hover',
                                            display: 'flex', 
                                            alignItems: 'center', 
                                            justifyContent: 'center', 
                                            minHeight: 40, 
                                        }}
                                    >
                                        <CircularProgress size={24} />
                                    </Paper>
                                </Box>
                            </Stack>
                        )}
          </Stack>
        </Box>
      </Box>
      <Box sx={{ p: 2, bgcolor: 'background.default', display: 'flex', justifyContent: 'center' }}>
        <Box sx={{ width: '100%', maxWidth: '900px' }}>
          <InputForm onSubmit={onSubmit} isLoading={isLoading} context="chat" />
        </Box>
      </Box>
    </Stack>
  );
}