/**
 * Reliable PDF Download using Browser Native Print Functionality
 * This approach is 100% reliable as it uses the browser's built-in print-to-PDF feature
 */

interface Message {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: Date
  quote?: any
}

interface User {
  role: 'normal' | 'premium'
  [key: string]: any
}

// Escape HTML characters to prevent XSS
const escapeHtml = (text: string): string => {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

// Convert markdown tables to HTML tables
const convertMarkdownTablesToHtml = (markdown: string): string => {
  const lines = markdown.split(/\r?\n/)
  let result = ''
  let i = 0

  while (i < lines.length) {
    const line = lines[i]
    const nextLine = lines[i + 1] || ''

    // Check if this is a table header followed by separator
    if (line.trim().startsWith('|') && /\|/.test(line) && /^\s*\|\s*:?[-]+.*\|\s*$/.test(nextLine)) {
      // Parse table
      const headerCells = line.trim().replace(/^\||\|$/g, '').split('|').map(cell => cell.trim())
      i += 2 // Skip separator line

      const bodyRows: string[][] = []
      while (i < lines.length && lines[i].trim().startsWith('|')) {
        const rowCells = lines[i].trim().replace(/^\||\|$/g, '').split('|').map(cell => cell.trim())
        bodyRows.push(rowCells)
        i++
      }

      // Generate HTML table
      result += '<table style="width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 12px;">'
      result += '<thead><tr>'
      headerCells.forEach(cell => {
        result += `<th style="border: 1px solid #e5e7eb; padding: 8px; background: #f9fafb; text-align: left; font-weight: 600;">${escapeHtml(cell)}</th>`
      })
      result += '</tr></thead><tbody>'
      
      bodyRows.forEach(row => {
        result += '<tr>'
        row.forEach(cell => {
          result += `<td style="border: 1px solid #e5e7eb; padding: 8px; vertical-align: top;">${escapeHtml(cell)}</td>`
        })
        result += '</tr>'
      })
      result += '</tbody></table>'
    } else {
      // Regular paragraph
      if (line.trim()) {
        result += `<p style="margin: 8px 0; line-height: 1.5;">${escapeHtml(line)}</p>`
      } else {
        result += '<br>'
      }
      i++
    }
  }

  return result
}

// Generate the printable HTML document
const generatePrintableHtml = (message: Message, user: User): string => {
  const isFreePlan = user.role === 'normal'
  const formattedContent = convertMarkdownTablesToHtml(message.content)
  const timestamp = new Date().toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })

  return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quote Response - ${timestamp}</title>
    <style>
        @page {
            margin: 20mm;
            size: A4;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #1f2937;
            margin: 0;
            padding: 0;
            background: white;
        }
        
        .container {
            max-width: 100%;
            margin: 0 auto;
            position: relative;
        }
        
        .header {
            border-bottom: 2px solid #e5e7eb;
            padding-bottom: 16px;
            margin-bottom: 24px;
        }
        
        .header h1 {
            margin: 0 0 8px 0;
            font-size: 24px;
            font-weight: 700;
            color: #111827;
        }
        
        .header .meta {
            color: #6b7280;
            font-size: 14px;
        }
        
        .content {
            position: relative;
            z-index: 2;
        }
        
        .footer {
            margin-top: 40px;
            padding-top: 16px;
            border-top: 1px solid #e5e7eb;
            font-size: 12px;
            color: #6b7280;
            text-align: center;
        }
        
        /* Watermark for free plan users */
        .watermark {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%) rotate(-45deg);
            font-size: 80px;
            font-weight: 900;
            color: #f3f4f6;
            opacity: 0.1;
            z-index: 1;
            pointer-events: none;
            user-select: none;
        }
        
        /* Table styling */
        table {
            page-break-inside: avoid;
        }
        
        /* Ensure good printing */
        @media print {
            body {
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }
            
            .no-print {
                display: none !important;
            }
        }
        
        /* Better paragraph spacing */
        p {
            margin: 12px 0;
        }
        
        /* Section headers */
        h2, h3, h4 {
            margin: 20px 0 12px 0;
            color: #111827;
        }
        
        /* List styling */
        ul, ol {
            margin: 12px 0;
            padding-left: 24px;
        }
        
        li {
            margin: 4px 0;
        }
    </style>
    <script>
        // Auto-trigger print dialog when page loads
        window.addEventListener('load', function() {
            setTimeout(function() {
                window.print();
            }, 500);
        });
        
        // Close window after printing (optional)
        window.addEventListener('afterprint', function() {
            setTimeout(function() {
                window.close();
            }, 1000);
        });
    </script>
</head>
<body>
    <div class="container">
        ${isFreePlan ? '<div class="watermark">FREE PLAN</div>' : ''}
        
        <div class="header">
            <h1>Business Quote Response</h1>
            <div class="meta">
                Generated on ${timestamp} | VilaiMathi AI Assistant
            </div>
        </div>
        
        <div class="content">
            ${formattedContent}
        </div>
        
        <div class="footer">
            <p>This document was generated by VilaiMathi AI - Professional Business Quotation Assistant</p>
            <p>For more information, visit our website or contact support</p>
        </div>
    </div>
</body>
</html>`
}

// Main function to download message as PDF
export const downloadMessageAsPdf = (message: Message, user: User): void => {
  try {
    const htmlContent = generatePrintableHtml(message, user)
    
    // Try to open in new window for printing
    const printWindow = window.open('', '_blank', 'width=800,height=600')
    
    if (printWindow) {
      printWindow.document.open()
      printWindow.document.write(htmlContent)
      printWindow.document.close()
      
      // Focus the print window
      printWindow.focus()
    } else {
      // Fallback: Download as HTML file if popup is blocked
      const blob = new Blob([htmlContent], { type: 'text/html' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `quote-response-${message.id}-${Date.now()}.html`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
      
      alert('Popup blocked! HTML file downloaded instead. Open it in your browser and use Ctrl+P to print as PDF.')
    }
  } catch (error) {
    console.error('PDF generation failed:', error)
    
    // Ultimate fallback: Copy content to clipboard
    const textContent = message.content
    if (navigator.clipboard) {
      navigator.clipboard.writeText(textContent).then(() => {
        alert('PDF generation failed. Content copied to clipboard instead.')
      }).catch(() => {
        alert('PDF generation failed. Please copy the content manually.')
      })
    } else {
      alert('PDF generation failed. Please copy the content manually.')
    }
  }
}

export default downloadMessageAsPdf
