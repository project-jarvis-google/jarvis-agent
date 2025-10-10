import React, { useRef, useEffect } from "react";
import {
  Box,
  Paper,
  Stack,
  Avatar,
  Typography,
  Chip,
  CircularProgress,
} from "@mui/material";
import { useTypingEffect } from "../hooks/useTypingEffect";
import { InputForm } from "./InputForm";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import PersonOutlineOutlinedIcon from "@mui/icons-material/PersonOutlineOutlined";
import InsertDriveFileOutlinedIcon from "@mui/icons-material/InsertDriveFileOutlined";
import logo from "../assets/spark-final.png";

interface DisplayFile {
  name: string;
  type: string;
  url: string;
}
export interface Message {
  type: "human" | "ai";
  content: string;
  id: string;
  files?: DisplayFile[];
}
interface ChatMessagesViewProps {
  messages: Message[];
  isLoading: boolean;
  onSubmit: (query: string, files: File[]) => void;
}

const AIMessageBubble: React.FC<{ message: Message }> = ({ message }) => {
  const typedContent = useTypingEffect(message.content, 20);

  return (
    <Stack
      key={message.id}
      direction="row"
      spacing={2}
      sx={{ justifyContent: "flex-start", alignItems: "flex-start" }}
    >
      <Avatar sx={{ bgcolor: "primary.main", p: 0.5 }}>
        <Box
          component="img"
          src={logo}
          sx={{ height: "100%", width: "100%" }}
        />
      </Avatar>
      <Box sx={{ maxWidth: "80%" }}>
        <Typography sx={{ fontWeight: "bold", mb: 0.5 }}>
          SPARC
        </Typography>
        <Paper
          elevation={0}
          sx={{
            p: 2,
            bgcolor: "action.hover",
            color: "text.primary",
            borderRadius: "20px",
            position: "relative",
          }}
        >
          <Typography component="div" sx={{ "& p": { margin: 0 } }}>
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                   code(props) {
                  const { children, className, node, ref, ...rest } = props;
                  const match = /language-(\w+)/.exec(className || '');
                  return match ? (
                    <SyntaxHighlighter
                      {...rest}
                      PreTag="div"
                      language={match[1]}
                      style={vscDarkPlus}
                    >
                      {String(children).replace(/\n$/, '')}
                    </SyntaxHighlighter>
                  ) : (
                    <code
                      className={className}
                      {...props}
                      style={{
                        backgroundColor: "rgba(255, 255, 255, 0.1)",
                        padding: "2px 4px",
                        borderRadius: "4px",
                      }}
                    >
                      {children}
                    </code>
                  );
                },
              }}
            >
              {typedContent}
            </ReactMarkdown>
          </Typography>
        </Paper>
      </Box>
    </Stack>
  );
};

export function ChatMessagesView({
  messages,
  isLoading,
  onSubmit,
}: ChatMessagesViewProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  return (
    <Stack sx={{ height: "100%", width: "100%" }}>
      <Box
        sx={{
          flexGrow: 1,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          overflowY: "auto",
        }}
      >
        <Box ref={scrollRef} sx={{ width: "100%", maxWidth: "900px", p: 3 }}>
          <Stack spacing={4}>
            {messages.map((message) => {
              if (message.type === "ai") {
                return message.content ? (
                  <AIMessageBubble key={message.id} message={message} />
                ) : null;
              }
              return (
                <Stack
                  key={message.id}
                  direction="row"
                  spacing={2}
                  sx={{ justifyContent: "flex-end", alignItems: "flex-start" }}
                >
                  <Box sx={{ maxWidth: "80%" }}>
                    {(message.content ||
                      (message.files && message.files.length > 0)) && (
                      <>
                        <Typography sx={{ fontWeight: "bold", mb: 0.5 }}>
                          You
                        </Typography>
                        <Paper
                          elevation={0}
                          sx={{
                            p: 2,
                            bgcolor: "action.selected",
                            color: "text.primary",
                            borderRadius: "20px",
                            position: "relative",
                          }}
                        >
                          {message.files && message.files.length > 0 && (
                            <Stack
                              spacing={1}
                              sx={{ mb: message.content ? 1.5 : 0 }}
                            >
                              {message.files.map((file, index) => (
                                <Paper
                                  key={index}
                                  variant="outlined"
                                  sx={{
                                    p: 1,
                                    borderRadius: "12px",
                                    bgcolor: "background.default",
                                  }}
                                >
                                  {file.type.startsWith("image/") ? (
                                    <Box
                                      component="img"
                                      src={file.url}
                                      alt={file.name}
                                      sx={{
                                        maxWidth: "100%",
                                        maxHeight: "200px",
                                        borderRadius: "8px",
                                        objectFit: "contain",
                                      }}
                                    />
                                  ) : (
                                    <Chip
                                      icon={<InsertDriveFileOutlinedIcon />}
                                      label={file.name}
                                      variant="outlined"
                                      sx={{
                                        height: "auto",
                                        "& .MuiChip-label": { p: 1 },
                                      }}
                                    />
                                  )}
                                </Paper>
                              ))}
                            </Stack>
                          )}

                          {message.content && (
                            <Typography
                              component="div"
                              sx={{ "& p": { margin: 0 } }}
                            >
                              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                {message.content}
                              </ReactMarkdown>
                            </Typography>
                          )}
                        </Paper>
                      </>
                    )}
                  </Box>
                  <Avatar>
                    <PersonOutlineOutlinedIcon />
                  </Avatar>
                </Stack>
              );
            })}
            {isLoading && (
              <Stack
                direction="row"
                spacing={2}
                sx={{ justifyContent: "flex-start", alignItems: "center" }}
              >
                <Avatar sx={{ bgcolor: "primary.main", p: 0.5 }}>
                  <Box
                    component="img"
                    src={logo}
                    sx={{ height: "100%", width: "100%" }}
                  />
                </Avatar>
                 <Typography sx={{ fontWeight: "bold", mr: 2 }}>
                  SPARC is thinking...
                </Typography>
                <CircularProgress size={24} />
              </Stack>
            )}
          </Stack>
        </Box>
      </Box>
      <Box
        sx={{
          p: 2,
          bgcolor: "background.default",
          display: "flex",
          justifyContent: "center",
        }}
      >
        <Box sx={{ width: "100%", maxWidth: "900px" }}>
          <InputForm onSubmit={onSubmit} isLoading={isLoading} context="chat" />
        </Box>
      </Box>
    </Stack>
  );
}
