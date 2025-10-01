import React from "react";
import { Box, Typography, Grid, Paper } from "@mui/material";
import AutoAwesomeOutlinedIcon from '@mui/icons-material/AutoAwesomeOutlined';
import { InputForm } from "./InputForm"; 

interface WelcomeScreenProps {
  handleSubmit: (query: string, files: File[]) => void;
  isLoading: boolean;
}

const suggestionPrompts = [
  "List the active projects that are showing RED status.", "List the Active projects with no RAG status.", "How many projects are currently showing Active Status in JAPAC?", "List the Active Projects assigned to <LDAP id>", "How many Active projects are there with Infra & Migration?", "List the projects that got completed in last 1 month.", "List the projects with GSD planned end date approaching.", "What is the Cost Score of <Project Name> ?",
];

export function WelcomeScreen({ handleSubmit, isLoading }: WelcomeScreenProps) {
  const handleSuggestionClick = (prompt: string) => {
    if (!isLoading) handleSubmit(prompt, []);
  };

  return (
    <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "space-between", height: "100%", textAlign: "center", p: 2 }}>
      <Box sx={{ flexGrow: 0.5 }} />
      <Box>
        <AutoAwesomeOutlinedIcon sx={{ fontSize: 48, color: "#1976d2" }} />
        <Typography variant="h4" component="h1" sx={{ fontWeight: "bold", mt: 2 }}>Jarvis Agent</Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mt: 1 }}>Explore your projects and gain rich insights through the power of AI.</Typography>
      </Box>
      <Grid container spacing={2} sx={{ maxWidth: "900px", my: 4 }}>
        {suggestionPrompts.map((prompt) => (
          <Grid xs={12} sm={6} md={3} key={prompt}>
            <Paper variant="outlined" onClick={() => handleSuggestionClick(prompt)} sx={{ p: 2, height: "100%", cursor: "pointer", borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', "&:hover": { backgroundColor: "action.hover", borderColor: 'primary.main' }}}>
              <Typography variant="body2">{prompt}</Typography>
            </Paper>
          </Grid>
        ))}
      </Grid>
      <Box sx={{ flexGrow: 1 }} />
      <Box sx={{ width: "100%", maxWidth: "700px" }}>
        <InputForm onSubmit={handleSubmit} isLoading={isLoading} context="homepage" />
        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: "block" }}>Generative AI may display inaccurate information, so double-check its responses.</Typography>
      </Box>
      {/* <Typography variant="body2" color="text.secondary" sx={{ mt: 3 }}>Powered by Gemini</Typography> */}
    </Box>
  );
}