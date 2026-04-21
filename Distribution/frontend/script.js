/**
 * LexiMind Frontend Script
 * handling user input, calling backend api and rendering markdown results
 */

(function() {
    'use strict';

    // DOM elements
    const modelSelect = document.getElementById('model-select');
    const commandInput = document.getElementById('command-input');
    const submitBtn = document.getElementById('submit-btn');
    const loadingIndicator = document.getElementById('loading-indicator');
    const resultContainer = document.getElementById('result-container');
    const errorMessageDiv = document.getElementById('error-message');

    // Default text is "Submit", but we store it in case we want to change it later
    const SUBMIT_DEFAULT_TEXT = submitBtn.textContent;

    // Status management
    let isRequesting = false;

    // Initializing configurations for marked.js if it's available
    if (typeof marked !== 'undefined') {
        marked.setOptions({
            breaks: true,      // Supporting GFM line breaks
            gfm: true,         // Enabling GitHub Flavored Markdown
        });
    }

    /**
     * Flashing error message in the UI
     */
    function showError(message) {
        errorMessageDiv.style.display = 'block';
        errorMessageDiv.textContent = message;
        resultContainer.innerHTML = '<p><em>Your answer will appear here.</em></p>';
    }

    /**
     * Getting rid of error message and resetting the container
     */
    function clearError() {
        errorMessageDiv.style.display = 'none';
        errorMessageDiv.textContent = '';
    }

    /**
     * Setting loading state: toggle button text and disable button
     */
    function setLoading(loading) {
        isRequesting = loading;
        submitBtn.disabled = loading;
        
        if (loading) {
            submitBtn.textContent = 'Processing...';
            if (loadingIndicator) {
                loadingIndicator.style.display = 'none';
            }
        } else {
            submitBtn.textContent = SUBMIT_DEFAULT_TEXT;
            if (loadingIndicator) {
                loadingIndicator.style.display = 'none';
            }
        }
    }

    /**
     * Rendering md result
     */
    function renderResult(markdownText) {
        if (typeof marked === 'undefined') {
            resultContainer.innerHTML = `<pre>${escapeHtml(markdownText)}</pre>`;
            return;
        }
        try {
            const html = marked.parse(markdownText);
            resultContainer.innerHTML = html;
        } catch (e) {
            console.error('Markdown parsing error:', e);
            resultContainer.innerHTML = `<pre>${escapeHtml(markdownText)}</pre>`;
        }
    }

    /**
     * Simple HTML escaping function (for fallback display)
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Handling submit action
     */
    async function handleSubmit() {
        if (isRequesting) return;

        const userInput = commandInput.value.trim();
        if (!userInput) {
            showError('Please enter a command.');
            return;
        }

        // Empty the input field
        commandInput.value = '';

        const selectedModel = modelSelect.value;
        const payload = {
            input: userInput,
            model: selectedModel
        };

        clearError();
        setLoading(true);

        try {
            const response = await fetch('/api/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (!response.ok) {
                showError(data.error || `Request failed (${response.status})`);
                return;
            }

            if (data.result) {
                renderResult(data.result);
            } else {
                showError('Empty response from server.');
            }
        } catch (error) {
            console.error('Fetch error:', error);
            showError('Network error. Please try again.');
        } finally {
            setLoading(false);
        }
    }

    /**
     * Binding event listeners
     */
    function bindEvents() {
        submitBtn.addEventListener('click', handleSubmit);

        commandInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                if (e.shiftKey) {
                    return;
                } else {
                    e.preventDefault();
                    handleSubmit();
                }
            }
        });
    }

    // Initialize the app
    bindEvents();
    commandInput.focus();
})();