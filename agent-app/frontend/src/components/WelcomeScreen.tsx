import { Button } from "@/components/ui/button";
import { InputForm } from "@/components/InputForm";
import logo from '@/assets/spark-final.png';
import Card from '@mui/material/Card';
import CardMedia from '@mui/material/CardMedia';

interface WelcomeScreenProps {
  handleSubmit: (query: string, files: File[]) => void; 
  isLoading: boolean;
  onCancel: () => void;
}

export function WelcomeScreen({
  handleSubmit,
  isLoading,
  onCancel,
}: WelcomeScreenProps) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center p-4 overflow-hidden relative">
      <div className="w-full max-w-2xl z-10
                       backdrop-blur-md 
                      p-8 rounded-2xl border border-neutral-700 
                      shadow-2xl shadow-black/60 
                      transition-all duration-300 hover:border-neutral-600">
        
        <div className="text-center space-y-4">
      <Card sx={{ maxWidth: 175, mx: 'auto' }} elevation={8}>
        <CardMedia
          component="img"
          height="120" 
          image={logo}
        />
      </Card>
      <h1 className="text-4xl font-bold text-[#4285F4] flex items-center justify-center gap-3">
        SPARC
      </h1>
      <p className="text-base text-neutral-600 max-w-md mx-auto">
        Your Answer to every question related to App Mod, App Dev and Apigee!
      </p>
    </div>

        <div className="mt-8">
          <InputForm onSubmit={handleSubmit} isLoading={isLoading} context="homepage" />
          {isLoading && (
            <div className="mt-4 flex justify-center">
              <Button
                variant="outline"
                onClick={onCancel}
                className="bg-black text-white hover:bg-black/80" 
              >
                Cancel
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}