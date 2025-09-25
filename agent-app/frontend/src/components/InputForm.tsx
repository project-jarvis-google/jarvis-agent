import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Loader2, Send,Paperclip, X } from "lucide-react";
import { Badge } from "@/components/ui/badge"; 


interface InputFormProps {
  onSubmit: (query: string, files: File[]) => void; // Update onSubmit signature
  isLoading: boolean;
  context?: 'homepage' | 'chat'; // Add new context prop
}

export function InputForm({ onSubmit, isLoading, context = 'homepage' }: InputFormProps) {
  const [inputValue, setInputValue] = useState("");
  const [files, setFiles] = useState<File[]>([]); 
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null); 


  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
      if (isLoading) return;
    if (inputValue.trim() || files.length > 0) {
     onSubmit(inputValue.trim(), files);
      setInputValue("");
      setFiles([]); // Clear files on submit
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

    const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles(prevFiles => [...prevFiles, ...Array.from(e.target.files!)]);
    }
    setTimeout(() => {
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }, 0);
  };


     const handleRemoveFile = (indexToRemove: number) => {
    setFiles(prevFiles => prevFiles.filter((_, index) => index !== indexToRemove));
  };


  const placeholderText =
    context === 'chat'
      ? "Respond to the Agent, refine the plan, or type 'Looks good'..."
      : "Ask me anything... e.g., Get your presales and delivery done for App Mod, App Dev and Apigee";

  return (
     <>
      {/* File Preview Area */}
      {files.length > 0 && (
        <div className="mb-2 flex flex-wrap gap-2">
          {files.map((file, index) => (
            <Badge
              key={index}
              variant="secondary"
              className="flex items-center gap-1.5"
            >
              <span>{file.name}</span>
              <button
                type="button"
                onClick={() => handleRemoveFile(index)}
                className="rounded-full hover:bg-neutral-500/20"
                aria-label={`Remove ${file.name}`}
              >
                <X className="h-3 w-3" />
              </button>
            </Badge>
          ))}
        </div>
      )}
      <form onSubmit={handleSubmit} className="flex flex-col gap-2">
        <div className="flex items-end space-x-2">
          {/* Hidden File Input */}
          <input
            type="file"
            multiple // Allow multiple files
            ref={fileInputRef}
            onChange={handleFileChange}
            className="hidden"
            accept="image/*,application/pdf,text/*,.csv" // Allowed file types
          />
          
          {/* Upload Button */}
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={handleUploadClick}
            disabled={isLoading}
            className="shrink-0"
          >
            <Paperclip className="h-4 w-4" />
          </Button>

          <Textarea
            ref={textareaRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholderText}
            rows={1}
            className="flex-1 resize-none pr-10 min-h-[40px]"
          />
          <Button
            type="submit"
            size="icon"
            className="shrink-0"
            // Update disabled logic
            disabled={isLoading || (!inputValue.trim() && files.length === 0)}
          >
            {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          </Button>
        </div>
      </form>
    </>
  );
}