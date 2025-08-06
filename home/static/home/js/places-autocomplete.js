/**
 * Google Places Autocomplete for Trip Django
 * Real-time destination suggestions using Google Places API
 */

class PlacesAutocomplete {
    constructor(inputElement, suggestionsContainer) {
        this.input = inputElement;
        this.suggestionsContainer = suggestionsContainer;
        this.suggestions = [];
        this.selectedIndex = -1;
        this.debounceTimer = null;
        
        this.init();
    }
    
    init() {
        // Create suggestions container if it doesn't exist
        if (!this.suggestionsContainer) {
            this.suggestionsContainer = document.createElement('div');
            this.suggestionsContainer.className = 'places-suggestions';
            this.input.parentNode.appendChild(this.suggestionsContainer);
        }
        
        // Add event listeners
        this.input.addEventListener('input', this.handleInput.bind(this));
        this.input.addEventListener('keydown', this.handleKeydown.bind(this));
        this.input.addEventListener('blur', this.handleBlur.bind(this));
        this.input.addEventListener('focus', this.handleFocus.bind(this));
        
        // Add styles
        this.addStyles();
    }
    
    addStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .places-suggestions {
                position: absolute;
                top: 100%;
                left: 0;
                right: 0;
                background: white;
                border: 1px solid #ddd;
                border-top: none;
                border-radius: 0 0 8px 8px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
                max-height: 300px;
                overflow-y: auto;
                z-index: 1000;
                display: none;
            }
            
            .places-suggestions.show {
                display: block;
            }
            
            .suggestion-item {
                padding: 12px 16px;
                cursor: pointer;
                border-bottom: 1px solid #f0f0f0;
                transition: background-color 0.2s ease;
            }
            
            .suggestion-item:hover,
            .suggestion-item.selected {
                background-color: #f8f9fa;
            }
            
            .suggestion-item:last-child {
                border-bottom: none;
            }
            
            .suggestion-main {
                font-weight: 500;
                color: #333;
                margin-bottom: 2px;
            }
            
            .suggestion-secondary {
                font-size: 13px;
                color: #666;
            }
            
            .suggestion-loading {
                padding: 12px 16px;
                text-align: center;
                color: #666;
                font-style: italic;
            }
            
            .suggestion-error {
                padding: 12px 16px;
                color: #dc3545;
                font-size: 13px;
            }
            
            .places-input-container {
                position: relative;
            }
        `;
        document.head.appendChild(style);
        
        // Wrap input in container for positioning
        if (!this.input.parentNode.classList.contains('places-input-container')) {
            const container = document.createElement('div');
            container.className = 'places-input-container';
            this.input.parentNode.insertBefore(container, this.input);
            container.appendChild(this.input);
            container.appendChild(this.suggestionsContainer);
        }
    }
    
    handleInput(event) {
        const query = event.target.value.trim();
        
        // Clear previous timer
        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
        }
        
        // Debounce the API call
        this.debounceTimer = setTimeout(() => {
            if (query.length >= 2) {
                this.fetchSuggestions(query);
            } else {
                this.hideSuggestions();
            }
        }, 300);
    }
    
    handleKeydown(event) {
        if (!this.suggestionsContainer.classList.contains('show')) {
            return;
        }
        
        switch (event.key) {
            case 'ArrowDown':
                event.preventDefault();
                this.selectedIndex = Math.min(this.selectedIndex + 1, this.suggestions.length - 1);
                this.updateSelection();
                break;
                
            case 'ArrowUp':
                event.preventDefault();
                this.selectedIndex = Math.max(this.selectedIndex - 1, -1);
                this.updateSelection();
                break;
                
            case 'Enter':
                event.preventDefault();
                if (this.selectedIndex >= 0) {
                    this.selectSuggestion(this.suggestions[this.selectedIndex]);
                }
                break;
                
            case 'Escape':
                this.hideSuggestions();
                break;
        }
    }
    
    handleBlur(event) {
        // Delay hiding to allow clicking on suggestions
        setTimeout(() => {
            this.hideSuggestions();
        }, 150);
    }
    
    handleFocus(event) {
        const query = event.target.value.trim();
        if (query.length >= 2 && this.suggestions.length > 0) {
            this.showSuggestions();
        }
    }
    
    async fetchSuggestions(query) {
        try {
            this.showLoading();
            
            const response = await fetch(`/api/places-autocomplete/?query=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            if (data.error) {
                this.showError(data.error);
                return;
            }
            
            this.suggestions = data.suggestions || [];
            this.selectedIndex = -1;
            this.renderSuggestions();
            
        } catch (error) {
            console.error('Error fetching suggestions:', error);
            this.showError('Failed to fetch suggestions. Please try again.');
        }
    }
    
    showLoading() {
        this.suggestionsContainer.innerHTML = '<div class="suggestion-loading">🔍 Searching...</div>';
        this.suggestionsContainer.classList.add('show');
    }
    
    showError(message) {
        this.suggestionsContainer.innerHTML = `<div class="suggestion-error">⚠️ ${message}</div>`;
        this.suggestionsContainer.classList.add('show');
    }
    
    renderSuggestions() {
        if (this.suggestions.length === 0) {
            this.suggestionsContainer.innerHTML = '<div class="suggestion-loading">No suggestions found</div>';
            this.suggestionsContainer.classList.add('show');
            return;
        }
        
        const html = this.suggestions.map((suggestion, index) => `
            <div class="suggestion-item" data-index="${index}">
                <div class="suggestion-main">${suggestion.main_text}</div>
                ${suggestion.secondary_text ? `<div class="suggestion-secondary">${suggestion.secondary_text}</div>` : ''}
            </div>
        `).join('');
        
        this.suggestionsContainer.innerHTML = html;
        this.suggestionsContainer.classList.add('show');
        
        // Add click listeners
        this.suggestionsContainer.querySelectorAll('.suggestion-item').forEach((item, index) => {
            item.addEventListener('click', () => {
                this.selectSuggestion(this.suggestions[index]);
            });
        });
    }
    
    updateSelection() {
        this.suggestionsContainer.querySelectorAll('.suggestion-item').forEach((item, index) => {
            item.classList.toggle('selected', index === this.selectedIndex);
        });
    }
    
    selectSuggestion(suggestion) {
        this.input.value = suggestion.description;
        this.input.dataset.placeId = suggestion.place_id;
        this.hideSuggestions();
        
        // Trigger change event
        const event = new Event('change', { bubbles: true });
        this.input.dispatchEvent(event);
        
        // Custom event for additional handling
        const customEvent = new CustomEvent('placeSelected', {
            detail: suggestion,
            bubbles: true
        });
        this.input.dispatchEvent(customEvent);
    }
    
    showSuggestions() {
        this.suggestionsContainer.classList.add('show');
    }
    
    hideSuggestions() {
        this.suggestionsContainer.classList.remove('show');
        this.selectedIndex = -1;
    }
}

// Auto-initialize for elements with data-places-autocomplete attribute
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('[data-places-autocomplete]').forEach(input => {
        new PlacesAutocomplete(input);
    });
});

// Export for manual initialization
window.PlacesAutocomplete = PlacesAutocomplete;
