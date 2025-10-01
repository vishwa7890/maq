import Link from 'next/link';

export function Footer() {
  return (
    <footer className="border-t py-8 text-center text-sm text-gray-500 bg-white/50">
      <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 bg-gradient-to-r from-blue-600 to-purple-600 rounded flex items-center justify-center">
            <span className="text-white font-bold text-xs">V</span>
          </div>
          <span className="font-semibold">VilaiMathi AI</span>
        </div>
        
        <div className="flex flex-wrap justify-center gap-4 md:gap-6">
          <Link 
            href="#pricing" 
            className="text-gray-600 hover:text-gray-900 transition-colors"
          >
            Pricing
          </Link>
          <Link 
            href="#features" 
            className="text-gray-600 hover:text-gray-900 transition-colors"
          >
            Features
          </Link>
          <a 
            href="mailto:vilaimathiai@gmail.com"
            className="text-gray-600 hover:text-gray-900 transition-colors"
          >
            Contact
          </a>
          <Link 
            href="/auth" 
            className="text-blue-600 hover:text-blue-700 font-medium"
          >
            Get Started
          </Link>
        </div>
      </div>
      
      <div className="mt-6 text-xs text-gray-400 space-y-1">
        <p>© {new Date().getFullYear()} VilaiMathi AI.</p>
        <p>All rights are reserved under MindApt, Promptelligence, LevelUp and BehindBrainz.ai</p>
      </div>
    </footer>
  );
}
