// Simple JavaScript for Vidarshov Gård Recording App

class SessionsApp {
    constructor() {
        this.apiBase = '/api/v1';
        this.init();
    }

    init() {
        // Initialize the app based on current page
        const path = window.location.pathname;

        if (path === '/sessions') {
            this.initSessionsPage();
        } else if (path.startsWith('/sessions/')) {
            this.initSessionDetailPage();
        }
    }

    // Sessions listing page
    initSessionsPage() {
        this.loadSessions();
        this.initSearch();
    }

    async loadSessions(searchTerm = '') {
        const container = document.getElementById('sessions-container');
        if (!container) return;

        try {
            this.showLoading(container);

            const url = searchTerm
                ? `${this.apiBase}/sessions/search/${encodeURIComponent(searchTerm)}`
                : `${this.apiBase}/sessions/`;

            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const sessions = await response.json();
            this.renderSessions(sessions, container);

        } catch (error) {
            console.error('Error loading sessions:', error);
            this.showError(container, `Failed to load sessions: ${error.message}`);
        }
    }

    renderSessions(sessions, container) {
        if (sessions.length === 0) {
            container.innerHTML = '<p class="loading">No sessions found.</p>';
            return;
        }

        const sessionsList = sessions.map(session => `
            <div class="session-item">
                <div class="session-filename">
                    <a href="/sessions/${session.id}">${session.filename}</a>
                </div>
                <div class="session-meta">
                    Created: ${this.formatDate(session.created_at)} |
                    Status: <span class="session-status status-${session.processing_status}">${session.processing_status}</span>
                </div>
                ${session.transcript_preview ? `
                    <div class="session-preview">
                        ${session.transcript_preview}
                    </div>
                ` : ''}
            </div>
        `).join('');

        container.innerHTML = `
            <div class="session-list">
                ${sessionsList}
            </div>
        `;
    }

    initSearch() {
        const searchBox = document.getElementById('search-box');
        if (!searchBox) return;

        let searchTimeout;
        searchBox.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.loadSessions(e.target.value.trim());
            }, 300);
        });
    }

    // Session detail page
    initSessionDetailPage() {
        const sessionId = this.getSessionIdFromUrl();
        if (sessionId) {
            this.loadSessionDetail(sessionId);
        }
    }

    getSessionIdFromUrl() {
        const parts = window.location.pathname.split('/');
        return parts[parts.length - 1];
    }

    async loadSessionDetail(sessionId) {
        const container = document.getElementById('session-detail-container');
        if (!container) return;

        try {
            this.showLoading(container);

            const response = await fetch(`${this.apiBase}/sessions/${sessionId}`);
            if (!response.ok) {
                if (response.status === 404) {
                    throw new Error('Session not found');
                }
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const session = await response.json();
            this.renderSessionDetail(session, container);

        } catch (error) {
            console.error('Error loading session detail:', error);
            this.showError(container, `Failed to load session: ${error.message}`);
        }
    }

    renderSessionDetail(session, container) {
        const transcript = session.transcript;

        let transcriptHtml = '';
        if (transcript) {
            if (transcript.segments && transcript.segments.length > 0) {
                transcriptHtml = transcript.segments.map(segment => `
                    <div class="segment">
                        <div class="segment-time">
                            ${this.formatTime(segment.start_time)} - ${this.formatTime(segment.end_time)}
                        </div>
                        <div class="segment-text">${segment.text}</div>
                    </div>
                `).join('');
            } else if (transcript.full_text) {
                transcriptHtml = `<div class="transcript-text">${transcript.full_text}</div>`;
            } else {
                transcriptHtml = '<p>No transcript content available.</p>';
            }
        } else {
            transcriptHtml = '<p>This session has not been transcribed yet.</p>';
        }

        container.innerHTML = `
            <div class="session-detail">
                <div class="detail-section">
                    <h2>${session.filename}</h2>
                    <div class="session-meta">
                        Created: ${this.formatDate(session.created_at)} |
                        Status: <span class="session-status status-${session.processing_status}">${session.processing_status}</span>
                    </div>
                </div>

                ${transcript ? `
                    <div class="detail-section">
                        <h3>Transcript</h3>
                        <div class="session-meta">
                            Language: ${transcript.language || 'Unknown'} |
                            Model: ${transcript.model_version || 'Unknown'} |
                            Processing time: ${transcript.processing_duration_ms || 0}ms
                        </div>
                        ${transcriptHtml}
                    </div>
                ` : `
                    <div class="detail-section">
                        <h3>Transcript</h3>
                        <p>This session has not been transcribed yet.</p>
                        <a href="#" class="btn" onclick="app.requestTranscription('${session.id}', '${session.filename}')">
                            Request Transcription
                        </a>
                    </div>
                `}

                <div class="detail-section">
                    <a href="/sessions" class="btn btn-secondary">← Back to Sessions</a>
                </div>
            </div>
        `;
    }

    async requestTranscription(sessionId, filename) {
        try {
            // Extract just the filename without extension and add .wav
            const baseName = filename.replace(/\.[^/.]+$/, "");
            const wavFilename = baseName + '.wav';

            const response = await fetch(`${this.apiBase}/transcription/transcribe/${wavFilename}`, {
                method: 'POST'
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            if (result.success) {
                alert('Transcription completed successfully!');
                // Reload the page to show the new transcript
                window.location.reload();
            } else {
                throw new Error(result.error_message || 'Transcription failed');
            }

        } catch (error) {
            console.error('Error requesting transcription:', error);
            alert(`Failed to transcribe: ${error.message}`);
        }
    }

    // Utility functions
    showLoading(container) {
        container.innerHTML = '<div class="loading">Loading...</div>';
    }

    showError(container, message) {
        container.innerHTML = `<div class="error">${message}</div>`;
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    }

    formatTime(seconds) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = Math.floor(seconds % 60);
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    }
}

// Initialize the app when the page loads
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new SessionsApp();
});