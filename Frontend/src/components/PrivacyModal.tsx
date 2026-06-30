import { X } from 'lucide-react';

interface PrivacyModalProps {
  onClose: () => void;
}

export function PrivacyModal({ onClose }: PrivacyModalProps) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div className="bg-white rounded-2xl p-8 shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="flex items-start justify-between mb-6">
          <h2 className="text-xl font-bold text-gray-900">Privacy Policy</h2>
          <button
            onClick={onClose}
            aria-label="Close privacy policy"
            className="w-8 h-8 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-all flex-shrink-0"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="space-y-5 text-sm">
          <section>
            <h3 className="font-semibold text-gray-900 mb-1">What we collect</h3>
            <p className="text-gray-600 leading-relaxed">
              Nothing. We collect no personal data, require no accounts, and run no analytics.
            </p>
          </section>

          <section>
            <h3 className="font-semibold text-gray-900 mb-1">localStorage</h3>
            <p className="text-gray-600 leading-relaxed">
              We store one key (<code className="bg-gray-100 px-1 rounded text-xs">lotto_gdpr_dismissed</code>) in your browser's localStorage to remember that you've seen this notice. No data leaves your device.
            </p>
          </section>

          <section>
            <h3 className="font-semibold text-gray-900 mb-1">Third-party services</h3>
            <p className="text-gray-600 leading-relaxed">
              None. We use no Google Analytics, no ad networks, and no tracking pixels. All number generation runs entirely in your browser.
            </p>
          </section>

          <section>
            <h3 className="font-semibold text-gray-900 mb-1">Lottery data</h3>
            <p className="text-gray-600 leading-relaxed">
              Historical NZ Lotto draw results are loaded from our own server as public data. No personal information is sent with these requests.
            </p>
          </section>

          <section>
            <h3 className="font-semibold text-gray-900 mb-1">Your rights (GDPR)</h3>
            <p className="text-gray-600 leading-relaxed">
              Under GDPR you have the right to access, rectify, and erase any personal data we hold. Since we hold none, there is nothing to request. For questions, contact:{' '}
              <a href="mailto:jom.nacorda@gmail.com" className="text-highlight-blue underline underline-offset-2">
                jom.nacorda@gmail.com
              </a>
            </p>
          </section>

          <section>
            <h3 className="font-semibold text-gray-900 mb-1">Updates</h3>
            <p className="text-gray-600 leading-relaxed">
              This policy may be updated as the site evolves. Last reviewed: June 2026.
            </p>
          </section>
        </div>

        <button
          onClick={onClose}
          className="mt-8 w-full py-3 rounded-xl bg-base text-white font-semibold hover:bg-base/90 active:scale-[0.98] transition-all"
        >
          Close
        </button>
      </div>
    </div>
  );
}
