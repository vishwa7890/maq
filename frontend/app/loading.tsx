'use client'

export default function Loading() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-purple-900">
      <div className="relative">
        {/* Glow effect background */}
        <div className="absolute inset-0 blur-3xl opacity-50">
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-cyan-500 rounded-full animate-pulse" />
          <div
            className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-48 h-48 bg-purple-600 rounded-full animate-pulse"
            style={{ animationDelay: '0.5s' }}
          />
        </div>

        {/* VL Logo Container */}
        <div className="relative">
          <svg width="200" height="200" viewBox="0 0 200 200" className="drop-shadow-2xl">
            {/* Circuit pattern background */}
            <defs>
              <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style={{ stopColor: '#06b6d4', stopOpacity: 1 }}>
                  <animate attributeName="stop-color" values="#06b6d4;#3b82f6;#8b5cf6;#06b6d4" dur="3s" repeatCount="indefinite" />
                </stop>
                <stop offset="100%" style={{ stopColor: '#8b5cf6', stopOpacity: 1 }}>
                  <animate attributeName="stop-color" values="#8b5cf6;#06b6d4;#3b82f6;#8b5cf6" dur="3s" repeatCount="indefinite" />
                </stop>
              </linearGradient>

              <filter id="glow">
                <feGaussianBlur stdDeviation="4" result="coloredBlur" />
                <feMerge>
                  <feMergeNode in="coloredBlur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>

            {/* V Letter */}
            <g className="animate-[fadeIn_1s_ease-in-out]">
              <path
                d="M 40 50 L 70 130 L 100 50"
                stroke="url(#grad1)"
                strokeWidth="8"
                fill="none"
                strokeLinecap="round"
                strokeLinejoin="round"
                filter="url(#glow)"
                className="animate-[draw_2s_ease-in-out_infinite]"
                strokeDasharray="200"
                strokeDashoffset="0"
              >
                <animate attributeName="stroke-dashoffset" values="200;0;200" dur="3s" repeatCount="indefinite" />
              </path>

              {/* Circuit details on V */}
              <circle cx="55" cy="75" r="3" fill="#06b6d4" className="animate-pulse">
                <animate attributeName="opacity" values="0.3;1;0.3" dur="2s" repeatCount="indefinite" />
              </circle>
              <circle cx="85" cy="75" r="3" fill="#8b5cf6" className="animate-pulse" style={{ animationDelay: '0.5s' }}>
                <animate attributeName="opacity" values="0.3;1;0.3" dur="2s" repeatCount="indefinite" begin="0.5s" />
              </circle>
            </g>

            {/* L Letter */}
            <g className="animate-[fadeIn_1.5s_ease-in-out]">
              <path
                d="M 120 50 L 120 130 L 170 130"
                stroke="url(#grad1)"
                strokeWidth="8"
                fill="none"
                strokeLinecap="round"
                strokeLinejoin="round"
                filter="url(#glow)"
                className="animate-[draw_2s_ease-in-out_infinite]"
                strokeDasharray="200"
                strokeDashoffset="0"
              >
                <animate attributeName="stroke-dashoffset" values="200;0;200" dur="3s" repeatCount="indefinite" begin="0.3s" />
              </path>

              {/* Circuit details on L */}
              <circle cx="120" cy="90" r="3" fill="#3b82f6" className="animate-pulse" style={{ animationDelay: '1s' }}>
                <animate attributeName="opacity" values="0.3;1;0.3" dur="2s" repeatCount="indefinite" begin="1s" />
              </circle>
              <circle cx="145" cy="130" r="3" fill="#06b6d4" className="animate-pulse" style={{ animationDelay: '1.5s' }}>
                <animate attributeName="opacity" values="0.3;1;0.3" dur="2s" repeatCount="indefinite" begin="1.5s" />
              </circle>
            </g>

            {/* Orbiting particles */}
            <circle r="4" fill="#06b6d4" filter="url(#glow)">
              <animateMotion dur="4s" repeatCount="indefinite" path="M 100 100 m -60, 0 a 60,60 0 1,0 120,0 a 60,60 0 1,0 -120,0" />
            </circle>
            <circle r="3" fill="#8b5cf6" filter="url(#glow)">
              <animateMotion
                dur="3s"
                repeatCount="indefinite"
                path="M 100 100 m -60, 0 a 60,60 0 1,0 120,0 a 60,60 0 1,0 -120,0"
                begin="0.5s"
              />
            </circle>
            <circle r="3" fill="#3b82f6" filter="url(#glow)">
              <animateMotion
                dur="5s"
                repeatCount="indefinite"
                path="M 100 100 m -60, 0 a 60,60 0 1,0 120,0 a 60,60 0 1,0 -120,0"
                begin="1s"
              />
            </circle>
          </svg>

          {/* Loading text */}
          <div className="absolute -bottom-16 left-1/2 -translate-x-1/2 text-center">
            <div className="text-cyan-400 text-xl font-bold tracking-wider animate-pulse">
              AI Processing
            </div>
            <div className="flex justify-center gap-1 mt-2">
              <div className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" />
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
              <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }} />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
