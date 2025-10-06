import React from "react";
import { Box, Typography, Grid, Paper } from "@mui/material";
import { InputForm } from "./InputForm";
import logo from "../assets/logo.png";

interface WelcomeScreenProps {
  handleSubmit: (query: string, files: File[]) => void;
  isLoading: boolean;
}

const suggestionPrompts = [
  "Generate a conceptual architecture for a new mobile banking app.",
  "Recommend a cloud migration strategy for a legacy Java monolith.",
  "Analyze our application portfolio and identify the best candidates for modernization.",
  "Create a sample Statement of Work (SOW) for a 3-month Apigee implementation.",
  "Generate unit tests for this Spring Boot controller I've uploaded.",
  "Scaffold a new microservice using Python and Flask with a CI/CD pipeline.",
];

export function WelcomeScreen({ handleSubmit, isLoading }: WelcomeScreenProps) {
  const handleSuggestionClick = (prompt: string) => {
    if (!isLoading) {
      handleSubmit(prompt, []);
    }
  };

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        height: "100%",
        textAlign: "center",
        p: 2,
      }}
    >
      <Box sx={{ mb: 4 }}>
        <Box
          component="img"
          src={logo}
          alt="Jarvis Agent Logo"
          sx={{ height: 150, mb: 3 }}
        />
        <Typography
          variant="h3"
          component="h1"
          sx={{ fontWeight: "bold", mb: 1 }}
        >
          Jarvis Agent
        </Typography>
        <Typography variant="h6" color="text.secondary">
          Explore your projects and gain rich insights through the power of AI.
        </Typography>
      </Box>

      <Grid
        container
        spacing={2}
        sx={{ maxWidth: "900px", justifyContent: "center" }}
      >
        {suggestionPrompts.map((prompt) => (
          <Grid item xs={12} sm={6} key={prompt}>
            <Paper
              variant="outlined"
              onClick={() => handleSuggestionClick(prompt)}
              sx={{
                p: 2,
                height: "100%",
                cursor: "pointer",
                borderRadius: "16px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                borderColor: "rgba(255, 255, 255, 0.23)",
                transition: "background-color 0.3s, border-color 0.3s",
                "&:hover": {
                  backgroundColor: "action.hover",
                  borderColor: "primary.main",
                },
              }}
            >
              <Typography variant="body2" color="text.secondary">
                {prompt}
              </Typography>
            </Paper>
          </Grid>
        ))}
      </Grid>

      <Box sx={{ flexGrow: 1 }} />

      <Box sx={{ width: "100%", maxWidth: "700px", mt: 4 }}>
        <InputForm
          onSubmit={handleSubmit}
          isLoading={isLoading}
          context="homepage"
        />
        <Typography
          variant="caption"
          color="text.secondary"
          sx={{ mt: 1, display: "block" }}
        >
          Generative AI may display inaccurate information, so double-check its
          responses.
        </Typography>
      </Box>
    </Box>
  );
}
