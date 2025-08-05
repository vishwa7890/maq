/**
 * Tracks user interactions with quotes and sends them to the server.
 * Automatically detects various types of interactions:
 * - Clicks on download/export buttons
 * - Text selection (indicates reading/interest)
 * - Time spent viewing (engagement)
 * - Copy/paste actions
 */

class InteractionTracker {
    constructor() {
        this.currentQuoteId = null;
        this.quoteElement = null;
        this.startTime = null;
        this.interactionTimeout = null;
        this.selectionTimeout = null;
        this.debounceTime = 1000; // ms to wait before sending interaction
        
        // Bind event handlers
        this.handleClick = this.handleClick.bind(this);
        this.handleSelection = this.debounce(this.handleSelection.bind(this), 500);
        this.handleCopy = this.handleCopy.bind(this);
        this.handleVisibilityChange = this.handleVisibilityChange.bind(this);
        
        this.initialize();
    }
    
    initialize() {
        // Set up mutation observer to detect new quote elements
        this.observer = new MutationObserver((mutations) => {
            this.attachQuoteListeners();
        });
        
        // Start observing the document with the configured parameters
        this.observer.observe(document.body, { 
            childList: true, 
            subtree: true 
        });
        
        // Set up global event listeners
        document.addEventListener('selectionchange', this.handleSelection);
        document.addEventListener('copy', this.handleCopy);
        document.addEventListener('visibilitychange', this.handleVisibilityChange);
        
        // Initial attachment of listeners
        this.attachQuoteListeners();
    }
    
    attachQuoteListeners() {
        // Find all quote elements and attach listeners
        const quoteElements = document.querySelectorAll('[data-quote-id]');
        
        quoteElements.forEach(element => {
            if (!element.dataset.hasListeners) {
                element.addEventListener('click', this.handleClick);
                element.dataset.hasListeners = 'true';
            }
        });
    }
    
    setCurrentQuote(quoteId, element) {
        if (this.currentQuoteId !== quoteId) {
            // If we were tracking a different quote, send a view end event
            if (this.currentQuoteId) {
                this.sendInteraction('view_end', {
                    duration: Date.now() - this.startTime
                });
            }
            
            // Start tracking the new quote
            this.currentQuoteId = quoteId;
            this.quoteElement = element;
            this.startTime = Date.now();
            
            // Send view start event
            this.sendInteraction('view_start');
        }
    }
    
    handleClick(event) {
        // Find the nearest parent with data-quote-id
        const quoteElement = event.target.closest('[data-quote-id]');
        if (!quoteElement) return;
        
        const quoteId = quoteElement.dataset.quoteId;
        this.setCurrentQuote(quoteId, quoteElement);
        
        // Check for specific interaction types based on the clicked element
        if (event.target.matches('a[download], button.download, .download-btn')) {
            this.sendInteraction('download', {
                target: event.target.tagName,
                href: event.target.href || ''
            });
        } else if (event.target.matches('button, a, input[type="button"], input[type="submit"]')) {
            this.sendInteraction('button_click', {
                buttonText: event.target.innerText.trim(),
                id: event.target.id,
                className: event.target.className
            });
        } else {
            // Generic click interaction
            this.sendInteraction('click', {
                target: event.target.tagName,
                id: event.target.id,
                className: event.target.className
            });
        }
    }
    
    handleSelection() {
        const selection = window.getSelection();
        if (!selection.toString().trim() || !this.currentQuoteId) return;
        
        // Clear any pending selection events
        if (this.selectionTimeout) {
            clearTimeout(this.selectionTimeout);
        }
        
        // Debounce the selection event
        this.selectionTimeout = setTimeout(() => {
            const selectedText = selection.toString().trim();
            if (selectedText) {
                this.sendInteraction('text_selection', {
                    textLength: selectedText.length,
                    preview: selectedText.length > 100 
                        ? selectedText.substring(0, 100) + '...' 
                        : selectedText
                });
            }
        }, 300);
    }
    
    handleCopy(event) {
        if (!this.currentQuoteId) return;
        
        const selection = window.getSelection();
        if (selection.toString().trim()) {
            this.sendInteraction('copy', {
                textLength: selection.toString().length
            });
        }
    }
    
    handleVisibilityChange() {
        if (document.visibilityState === 'hidden' && this.currentQuoteId) {
            // Send view end event when user navigates away
            this.sendInteraction('view_end', {
                duration: Date.now() - this.startTime,
                reason: 'page_hidden'
            });
        } else if (document.visibilityState === 'visible' && this.currentQuoteId) {
            // Restart the timer if user comes back
            this.startTime = Date.now();
            this.sendInteraction('view_start', {
                return_visit: true
            });
        }
    }
    
    sendInteraction(interactionType, metadata = {}) {
        if (!this.currentQuoteId) return;
        
        // Add timestamp and additional context
        const interaction = {
            quote_id: this.currentQuoteId,
            interaction_type: interactionType,
            timestamp: new Date().toISOString(),
            metadata: {
                ...metadata,
                url: window.location.href,
                user_agent: navigator.userAgent,
                viewport: {
                    width: window.innerWidth,
                    height: window.innerHeight
                }
            }
        };
        
        // Send to server
        fetch('/api/track_interaction', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(interaction),
            keepalive: true // Ensure the request is sent even if the page is unloaded
        }).catch(error => {
            console.error('Error tracking interaction:', error);
        });
        
        console.log('Interaction tracked:', interaction);
    }
    
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
}

// Initialize the tracker when the DOM is fully loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.quoteTracker = new InteractionTracker();
    });
} else {
    window.quoteTracker = new InteractionTracker();
}

// Export for module usage if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = InteractionTracker;
}
