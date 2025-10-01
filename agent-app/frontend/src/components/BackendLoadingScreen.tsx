export const BackendLoadingScreen = () => (
  <div className="flex-1 flex flex-col items-center justify-center p-4 overflow-hidden relative">
    <div className="w-full max-w-2xl z-10 bg-card/50 backdrop-blur-md p-8 rounded-2xl border shadow-2xl">
      <div className="text-center space-y-6">
        <h1 className="text-4xl font-bold">✨ Jarvis Agent 🚀</h1>
        <div className="flex flex-col items-center space-y-4">
          <div className="relative">
            <div className="w-16 h-16 border-4 border-t-primary rounded-full animate-spin"></div>
            <div
              className="absolute inset-0 w-16 h-16 border-4 border-transparent border-r-accent rounded-full animate-spin"
              style={{ animationDirection: "reverse", animationDuration: "1.5s" }}
            />
          </div>
          <p className="text-xl text-muted-foreground">Waiting for backend to be ready...</p>
          <p className="text-sm text-muted-foreground">This may take a moment</p>
        </div>
      </div>
    </div>
  </div>
);
