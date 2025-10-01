export const BackendUnavailable = () => (
  <div className="flex-1 flex flex-col items-center justify-center p-4">
    <div className="text-center space-y-4">
      <h2 className="text-2xl font-bold text-destructive">Backend Unavailable</h2>
      <p className="text-muted-foreground">Unable to connect to backend services</p>
      <button
        onClick={() => window.location.reload()}
        className="px-4 py-2 bg-primary text-primary-foreground hover:bg-primary/90 rounded-lg transition-colors"
      >
        Retry
      </button>
    </div>
  </div>
);
