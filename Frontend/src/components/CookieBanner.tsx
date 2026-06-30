import { useState, useEffect } from 'react';
import { Lock, X } from 'lucide-react';

interface CookieBannerProps {
  onPrivacyClick: () => void;
  onDismiss: () => void;
}

export function CookieBanner({ onPrivacyClick, onDismiss }: CookieBannerProps) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setVisible(true), 100);
    return () => clearTimeout(t);
  }, []);

  const dismiss = () => {
    setVisible(false);
    setTimeout(onDismiss, 300);
  };

  return (
    <div
      className={`fixed bottom-0 left-0 right-0 z-50 bg-white border-t border-gray-200 shadow-[0_-4px_24px_rgba(0,0,0,0.08)] transition-transform duration-300 ease-out ${
        visible ? 'translate-y-0' : 'translate-y-full'
      }`}
    >
      <div className="max-w-6xl mx-auto px-4 py-3 flex items-center gap-4">
        <Lock className="w-4 h-4 text-base flex-shrink-0" />
        <p className="flex-1 text-sm text-gray-600">
          We don't track you. This site uses localStorage only to remember this notice. See our{' '}
          <button
            onClick={onPrivacyClick}
            className="text-highlight-blue underline underline-offset-2 hover:text-highlight-blue/80 transition-colors"
          >
            Privacy Policy
          </button>
          .
        </p>
        <div className="flex items-center gap-2 flex-shrink-0">
          <button
            onClick={dismiss}
            className="px-4 py-2 rounded-lg bg-base text-white text-sm font-semibold hover:bg-base/90 active:scale-95 transition-all"
          >
            Accept &amp; Close
          </button>
          <button
            onClick={dismiss}
            aria-label="Close"
            className="w-8 h-8 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-all"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
