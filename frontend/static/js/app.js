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
        let speakerInfoHtml = '';

        if (transcript) {
            // Check if we have speaker-aware segments
            const hasSegments = transcript.segments && transcript.segments.length > 0;
            const hasSpeakerInfo = hasSegments && transcript.segments[0] && transcript.segments[0].speaker_id;

            console.log('Transcript debug:', {
                hasSegments,
                hasSpeakerInfo,
                segmentsLength: transcript.segments ? transcript.segments.length : 0,
                firstSegment: transcript.segments ? transcript.segments[0] : null,
                fullTextLength: transcript.full_text ? transcript.full_text.length : 0
            });

            if (hasSegments && hasSpeakerInfo) {
                // Render as dialogue with speaker attribution
                console.log('Rendering dialogue view');
                transcriptHtml = this.renderDialogue(transcript.segments);

                // Add speaker information if available
                if (transcript.speaker_info && transcript.speaker_info.length > 0) {
                    speakerInfoHtml = this.renderSpeakerInfo(transcript.speaker_info, transcript.has_speakers, transcript.speakers_detected);
                }
            } else if (transcript.full_text) {
                // Fallback to plain text display
                console.log('Rendering plain text view');
                transcriptHtml = `<div class="transcript-text">${this.escapeHtml(transcript.full_text)}</div>`;
            } else {
                console.log('No content available');
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
                            ${transcript.speakers_detected ? ` | Speakers detected: ${transcript.speakers_detected}` : ''}
                        </div>
                        ${speakerInfoHtml}
                        ${transcriptHtml}
                    </div>
                ` : `
                    <div class="detail-section">
                        <h3>Transcript</h3>
                        <p>This session has not been transcribed yet. Choose a transcription method:</p>
                        <div style="display: flex; gap: 1rem; margin-top: 1rem;">
                            <a href="#" class="btn" onclick="app.requestBasicTranscription('${session.id}', '${session.filename}'); return false;">
                                Basic Transcription
                            </a>
                            <a href="#" class="btn" style="background-color: #27ae60;" onclick="app.requestSpeakerAwareTranscription('${session.id}', '${session.filename}'); return false;">
                                Speaker-Aware Transcription
                            </a>
                        </div>
                        <div style="margin-top: 1rem; font-size: 0.9rem; color: #666;">
                            <strong>Basic:</strong> Mono transcription, faster<br>
                            <strong>Speaker-Aware:</strong> Stereo with speaker detection
                        </div>
                    </div>
                `}

                <div class="detail-section">
                    <a href="/sessions" class="btn btn-secondary">← Back to Sessions</a>
                </div>
            </div>
        `;
    }

    async requestBasicTranscription(sessionId, filename) {
        try {
            // Extract just the filename without extension and add .wav
            const baseName = filename.replace(/\.[^/.]+$/, "");
            const wavFilename = baseName + '.wav';

            alert('Starting basic transcription...');

            const response = await fetch(`${this.apiBase}/transcription/transcribe/${wavFilename}`, {
                method: 'POST'
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            if (result.success) {
                alert('Basic transcription completed successfully!');
                // Reload the page to show the new transcript
                window.location.reload();
            } else {
                throw new Error(result.error_message || 'Transcription failed');
            }

        } catch (error) {
            console.error('Error requesting basic transcription:', error);
            alert(`Failed to transcribe: ${error.message}`);
        }
    }

    async requestSpeakerAwareTranscription(sessionId, filename) {
        try {
            // Use the original filename (MP3/M4A/WAV supported)
            alert('Starting speaker-aware transcription...');

            const response = await fetch(`${this.apiBase}/speaker-aware-transcription/transcribe/${filename}`, {
                method: 'POST'
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            if (result.success) {
                const speakerMsg = result.has_speakers
                    ? `Detected ${result.speakers_detected} speakers!`
                    : 'No speaker separation detected.';
                alert(`Speaker-aware transcription completed successfully! ${speakerMsg}`);
                // Reload the page to show the new transcript
                window.location.reload();
            } else {
                throw new Error(result.error_message || 'Transcription failed');
            }

        } catch (error) {
            console.error('Error requesting speaker-aware transcription:', error);
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

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    getSpeakerLabel(speakerId) {
        if (!speakerId || speakerId === 'speaker_unknown') {
            return 'Speaker';
        }
        if (speakerId === 'speaker_1') {
            return 'Speaker 1';
        }
        if (speakerId === 'speaker_2') {
            return 'Speaker 2';
        }
        return speakerId;
    }

    renderSpeakerInfo(speakerInfo, hasSpeakers, speakersDetected) {
        if (!speakerInfo || speakerInfo.length === 0) {
            return '';
        }

        const separationStatus = hasSpeakers === 'true' || hasSpeakers === true
            ? '<span style="color: #27ae60;">✓ Stereo separation detected</span>'
            : '<span style="color: #95a5a6;">○ Mono/mixed audio</span>';

        let speakerCards = speakerInfo.map(speaker => {
            const channelLabel = speaker.channel ? ` (${speaker.channel} channel)` : '';
            const bgColor = speaker.speaker_id === 'speaker_1' ? '#e3f2fd' : speaker.speaker_id === 'speaker_2' ? '#e8f5e9' : '#f5f5f5';
            const borderColor = speaker.speaker_id === 'speaker_1' ? '#3498db' : speaker.speaker_id === 'speaker_2' ? '#27ae60' : '#95a5a6';

            return `
                <div style="background: ${bgColor}; border-left: 4px solid ${borderColor}; padding: 1rem; border-radius: 8px; margin: 0.5rem 0;">
                    <div style="font-weight: 600; margin-bottom: 0.5rem;">
                        ${speaker.label || this.getSpeakerLabel(speaker.speaker_id)}${channelLabel}
                    </div>
                    <div style="font-size: 0.9rem; color: #666;">
                        Voice activity: ${(100 - speaker.silence_percent).toFixed(1)}% |
                        Energy: ${speaker.energy_percent.toFixed(1)}%
                    </div>
                </div>
            `;
        }).join('');

        return `
            <div style="margin: 1rem 0 1.5rem 0; padding: 1rem; background: #f8f9fa; border-radius: 8px;">
                <div style="font-size: 0.95rem; margin-bottom: 0.75rem;">
                    ${separationStatus}
                </div>
                ${speakerCards}
            </div>
        `;
    }

    renderDialogue(segments) {
        // Sort segments by start time
        const sortedSegments = [...segments].sort((a, b) => a.start_time - b.start_time);

        // Group segments into dialogue turns
        const turns = this.groupIntoTurns(sortedSegments);

        // Render dialogue with two columns
        let html = '<div class="dialogue-container">';

        for (const turn of turns) {
            html += '<div class="dialogue-turn">';

            // Left column (Speaker 1)
            if (turn.speaker1) {
                html += `<div class="dialogue-left">${turn.speaker1}</div>`;
            } else {
                html += '<div class="dialogue-left"></div>';
            }

            // Right column (Speaker 2)
            if (turn.speaker2) {
                html += `<div class="dialogue-right">${turn.speaker2}</div>`;
            } else {
                html += '<div class="dialogue-right"></div>';
            }

            html += '</div>';
        }

        html += '</div>';
        return html;
    }

    groupIntoTurns(segments) {
        const turns = [];
        let currentTurn = { speaker1: null, speaker2: null };
        let speaker1Words = [];
        let speaker2Words = [];
        let lastSpeaker = null;

        // Define overlap threshold (in seconds) - segments within this time are considered overlapping
        const overlapThreshold = 0.5;

        for (let i = 0; i < segments.length; i++) {
            const segment = segments[i];
            const speaker = segment.speaker_id;
            const nextSegment = i < segments.length - 1 ? segments[i + 1] : null;

            // Check if next segment overlaps with current
            const hasOverlap = nextSegment &&
                               nextSegment.start_time < segment.end_time + overlapThreshold &&
                               nextSegment.speaker_id !== speaker;

            // Add word to appropriate speaker
            if (speaker === 'speaker_1') {
                speaker1Words.push(segment.text);
            } else if (speaker === 'speaker_2') {
                speaker2Words.push(segment.text);
            }

            // Determine if we should create a new turn
            const shouldCreateTurn =
                // Speaker change without overlap
                (nextSegment && nextSegment.speaker_id !== speaker && !hasOverlap) ||
                // Last segment
                !nextSegment ||
                // Overlapping speech detected (both speakers have content)
                (hasOverlap && speaker1Words.length > 0 && speaker2Words.length > 0);

            if (shouldCreateTurn) {
                // Create current turn with accumulated words
                if (speaker1Words.length > 0) {
                    currentTurn.speaker1 = speaker1Words.join(' ');
                }
                if (speaker2Words.length > 0) {
                    currentTurn.speaker2 = speaker2Words.join(' ');
                }

                // Only add turn if it has content
                if (currentTurn.speaker1 || currentTurn.speaker2) {
                    turns.push(currentTurn);
                }

                // Reset for next turn
                currentTurn = { speaker1: null, speaker2: null };
                speaker1Words = [];
                speaker2Words = [];
            }

            lastSpeaker = speaker;
        }

        return turns;
    }
}

// Initialize the app when the page loads
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new SessionsApp();
});