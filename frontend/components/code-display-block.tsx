'use client';
import { CheckIcon, CopyIcon } from 'lucide-react';
import React from 'react';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';

interface ButtonCodeblockProps {
  code: string;
  lang: string;
}

export default function CodeDisplayBlock({ code, lang }: ButtonCodeblockProps) {
  const [isCopied, setisCopied] = React.useState(false);

  const copyToClipboard = () => {
    navigator.clipboard.writeText(code);
    setisCopied(true);
    toast.success('Code copied to clipboard!');
    setTimeout(() => {
      setisCopied(false);
    }, 1500);
  };

  return (
    <div className="relative flex flex-col   text-start  ">
      <Button onClick={copyToClipboard} variant="ghost" size="icon" className="h-5 w-5 absolute top-2 right-2">
        {isCopied ? (
          <CheckIcon className="w-4 h-4 scale-100 transition-all" />
        ) : (
          <CopyIcon className="w-4 h-4 scale-100 transition-all" />
        )}
      </Button>
      <code className="block overflow-x-auto rounded-md bg-muted p-4 font-mono text-sm" data-language={lang || 'text'}>
        {code}
      </code>
    </div>
  );
}
