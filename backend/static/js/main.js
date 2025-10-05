(function () {
	// Updated: Fixed LLM endpoint calls - Oct 5, 2025
	document.addEventListener('DOMContentLoaded', () => {
		const page = document.body.dataset.page;

		switch (page) {
			case 'vent':
				initVentPage();
				break;
			case 'stress':
				initStressPage();
				break;
			case 'pacing':
				initPacingPage();
				break;
			case 'calendar':
				initCalendarPage();
				break;
			default:
				break;
		}
	});

	// --- Vent page ---
	function initVentPage() {
		const recordButton = document.getElementById('recordButton');
		const stopButton = document.getElementById('stopButton');
		const statusText = document.getElementById('ventStatus');
		const latestTranscription = document.getElementById('latestTranscription');
		const fetchTranscriptions = document.getElementById('fetchTranscriptions');
		const transcriptionList = document.getElementById('transcriptionList');
		const insightsButton = document.getElementById('ventInsights');
		const insightList = document.getElementById('insightList');

		if (!recordButton || !stopButton) {
			return;
		}

		let mediaRecorder = null;
		let audioChunks = [];

		recordButton.addEventListener('click', async () => {
			try {
				const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
				mediaRecorder = new MediaRecorder(stream);
				audioChunks = [];

				mediaRecorder.ondataavailable = (event) => {
					audioChunks.push(event.data);
				};

				mediaRecorder.onstop = handleRecordingStop;

				mediaRecorder.start();
				recordButton.disabled = true;
				stopButton.disabled = false;
				updateStatus('Recording…', 'warning');
				latestTranscription.innerHTML = '<p class="placeholder">Listening… share whatever you need.</p>';
			} catch (error) {
				updateStatus(`Microphone error: ${error.message}`, 'danger');
			}
		});

		stopButton.addEventListener('click', () => {
			if (!mediaRecorder) return;
			mediaRecorder.stop();
			mediaRecorder.stream.getTracks().forEach((track) => track.stop());
			stopButton.disabled = true;
			recordButton.disabled = false;
			updateStatus('Processing transcription…', 'info');
		});

		fetchTranscriptions?.addEventListener('click', () => loadTranscriptions(transcriptionList));
		insightsButton?.addEventListener('click', () => {
			const latestText = latestTranscription?.querySelector('p')?.textContent || '';
			handleInsights('vent', insightList, { latestText });
		});

		// auto-load on entry
		loadTranscriptions(transcriptionList);

		async function handleRecordingStop() {
			if (audioChunks.length === 0) {
				updateStatus('No audio captured, try again.', 'danger');
				return;
			}

			const blob = new Blob(audioChunks, { type: 'audio/webm' });
			const formData = new FormData();
			formData.append('audio', blob, 'vent.webm');

			try {
				// Prefer new namespaced endpoint, but fall back to legacy '/transcribe' if needed
				let response = await fetch('/api/transcribe', { method: 'POST', body: formData });
				if (response.status === 404) {
					response = await fetch('/transcribe', { method: 'POST', body: formData });
				}

				// Safely parse JSON; if server returned HTML (e.g., auth redirect) provide clearer error
				let result;
				const contentType = response.headers.get('content-type') || '';
				if (contentType.includes('application/json')) {
					result = await response.json();
				} else {
					const textSample = (await response.text()).slice(0, 120);
					throw new Error('Unexpected non-JSON response from server: ' + textSample.replace(/</g, '&lt;'));
				}

				if (!response.ok) {
					throw new Error(result.error || 'Unknown error during transcription');
				}

				const timestamp = new Date(result.timestamp).toLocaleString();
				latestTranscription.innerHTML = `
					<h3>Latest reflection</h3>
					<p>${sanitize(result.text)}</p>
					<p class="helper-text">Captured ${timestamp}</p>
				`;

				updateStatus('Transcription saved successfully.', 'success');
				loadTranscriptions(transcriptionList);
			} catch (error) {
				updateStatus(`Transcription failed: ${error.message}`, 'danger');
			}
		}

		function updateStatus(message, tone = 'info') {
			const tones = {
				info: '#a29bfe',
				warning: '#ffb347',
				danger: '#ff6b6b',
				success: '#00cec9',
			};
			statusText.textContent = message;
			statusText.style.color = tones[tone] || tones.info;
		}
	}

	async function loadTranscriptions(container) {
		if (!container) return;
		container.innerHTML = '<p class="placeholder">Loading your reflections…</p>';
		try {
			const response = await fetch('/api/transcriptions');
			const data = await response.json();

			if (!response.ok) {
				throw new Error(data.error || 'Failed to fetch');
			}

			if (!Array.isArray(data) || data.length === 0) {
				container.innerHTML = '<p class="placeholder">No reflections yet. Your first vent will appear here.</p>';
				return;
			}

			container.innerHTML = '';
			data.forEach((item) => {
				const entry = document.createElement('div');
				entry.className = 'entry';
				const timestamp = item.created_at ? new Date(item.created_at).toLocaleString() : 'Unknown time';
				entry.innerHTML = `
					<time>${timestamp}</time>
					<p>${sanitize(item.text || '')}</p>
					<p class="helper-text">Language: ${item.language || 'n/a'}</p>
				`;
				container.appendChild(entry);
			});
		} catch (error) {
			container.innerHTML = `<p class="placeholder">Could not load reflections: ${sanitize(error.message)}</p>`;
		}
	}

	async function handleInsights(topic, listEl, payload = {}) {
		if (!listEl) return;
		const isBareList = listEl.tagName === 'UL';
		if (isBareList) {
			listEl.innerHTML = `<li class="placeholder">Thinking…</li>`;
		} else {
			listEl.innerHTML = '<p class="placeholder">Thinking…</p>';
		}
		try {
			const response = await fetch('/api/insights', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
				},
				body: JSON.stringify({ topic, inputs: payload }),
			});

			// Check if redirected to login (HTML response)
			const contentType = response.headers.get('content-type') || '';
			if (!contentType.includes('application/json')) {
				throw new Error('Please log in to view insights');
			}

			const data = await response.json();
			if (!response.ok) {
				throw new Error(data.error || 'Failed to generate insights');
			}

			if (!Array.isArray(data.suggestions) || data.suggestions.length === 0) {
				if (isBareList) {
					listEl.innerHTML = '<li class="placeholder">No insights available yet.</li>';
				} else {
					listEl.innerHTML = '<p class="placeholder">No insights available yet.</p>';
				}
				return;
			}

			if (isBareList) {
				listEl.innerHTML = '';
				data.suggestions.forEach((suggestion) => {
					const item = document.createElement('li');
					item.textContent = suggestion;
					listEl.appendChild(item);
				});
			} else {
				const list = document.createElement('ul');
				data.suggestions.forEach((suggestion) => {
					const item = document.createElement('li');
					item.textContent = suggestion;
					list.appendChild(item);
				});
				listEl.innerHTML = '';
				listEl.appendChild(list);
			}
		} catch (error) {
			if (isBareList) {
				listEl.innerHTML = `<li class="placeholder">Error fetching insights: ${sanitize(error.message)}</li>`;
			} else {
				listEl.innerHTML = `<p class="placeholder">Error fetching insights: ${sanitize(error.message)}</p>`;
			}
		}
	}

	// --- Stress page ---
	function initStressPage() {
		const stressSlider = document.getElementById('stressLevel');
		const overwhelmSlider = document.getElementById('overwhelmLevel');
		const energySlider = document.getElementById('energyLevel');
		const notesInput = document.getElementById('stressNotes');
		const calculateBtn = document.getElementById('calculateStress');
		const insightsBtn = document.getElementById('stressInsights');
		const scoreDisplay = document.getElementById('stressScore');
		const interpretation = document.getElementById('stressInterpretation');
		const insightList = document.getElementById('stressInsightList');

		if (!stressSlider || !calculateBtn) {
			return;
		}

		calculateBtn.addEventListener('click', () => {
			const stress = Number(stressSlider.value || 0);
			const overwhelm = Number(overwhelmSlider.value || 0);
			const energy = Number(energySlider.value || 0);

			const score = Math.round(((stress + overwhelm + (10 - energy)) / 30) * 100);
			scoreDisplay.textContent = `${score} / 100`;

			if (score < 33) {
				interpretation.textContent = 'Steady! Keep protecting the habits that anchor you.';
			} else if (score < 66) {
				interpretation.textContent = 'Moderate load—consider adding an extra reset or delegating a task.';
			} else {
				interpretation.textContent = 'High strain detected. Prioritize recovery and renegotiate commitments.';
			}
		});

		insightsBtn?.addEventListener('click', () => {
			const payload = {
				stress: Number(stressSlider.value || 0),
				overwhelm: Number(overwhelmSlider.value || 0),
				energy: Number(energySlider.value || 0),
				notes: notesInput?.value || '',
			};
			handleInsights('stress', insightList, payload);
		});
	}

	// --- Pacing advice page ---
	function initPacingPage() {
		const refreshBtn = document.getElementById('adviceRefresh');
		const insightList = document.getElementById('adviceInsightList');
		const focusInput = document.getElementById('planFocusBlock');
		const recoveryInput = document.getElementById('planRecoveryBlock');
		const connectionInput = document.getElementById('planConnectionBlock');
		const notesInput = document.getElementById('planNotes');
		const saveButton = document.getElementById('savePacingPlan');
		const planStatus = document.getElementById('planStatus');

		const storedPlan = JSON.parse(localStorage.getItem('pace-plan') || 'null');
		if (storedPlan) {
			focusInput.value = storedPlan.focus || '';
			recoveryInput.value = storedPlan.recovery || '';
			connectionInput.value = storedPlan.connection || '';
			notesInput.value = storedPlan.notes || '';
			planStatus.textContent = `Draft restored from ${new Date(storedPlan.saved_at).toLocaleString()}.`;
		}

		refreshBtn?.addEventListener('click', () => handleInsights('pacing', insightList));

		saveButton?.addEventListener('click', () => {
			const plan = {
				focus: focusInput.value.trim(),
				recovery: recoveryInput.value.trim(),
				connection: connectionInput.value.trim(),
				notes: notesInput.value.trim(),
				saved_at: new Date().toISOString(),
			};
			localStorage.setItem('pace-plan', JSON.stringify(plan));
			planStatus.textContent = `Draft saved locally at ${new Date(plan.saved_at).toLocaleTimeString()}.`;
		});
	}

	// --- Calendar page ---
	function initCalendarPage() {
		const toggleBtn = document.getElementById('toggleEventForm');
		const eventForm = document.getElementById('addEventForm');
		const cancelBtn = document.getElementById('cancelEventForm');
		const statusEl = document.getElementById('eventStatus');
		const refreshEventsBtn = document.getElementById('refreshEvents');
		const eventList = document.getElementById('eventList');
		const refreshBreaksBtn = document.getElementById('refreshBreaks');
		const breakList = document.getElementById('breakSuggestions');

		if (toggleBtn) {
			toggleBtn.addEventListener('click', () => {
				const hidden = eventForm.hasAttribute('hidden');
				if (hidden) {
					eventForm.removeAttribute('hidden');
				} else {
					eventForm.setAttribute('hidden', 'hidden');
				}
			});
		}

		cancelBtn?.addEventListener('click', () => {
			eventForm?.setAttribute('hidden', 'hidden');
		});

		eventForm?.addEventListener('submit', async (event) => {
			event.preventDefault();
			const summary = document.getElementById('eventSummary').value.trim();
			const description = document.getElementById('eventDescription').value.trim();
			const startOffset = Number(document.getElementById('eventStartOffset').value || 0);
			const duration = Number(document.getElementById('eventDuration').value || 1);

			if (!summary) {
				updateEventStatus('Title is required.', 'danger');
				return;
			}

			try {
				updateEventStatus('Creating event…', 'info');
				const response = await fetch('/api/events/add', {
					method: 'POST',
					headers: {
						'Content-Type': 'application/json',
					},
					body: JSON.stringify({
						summary,
						description,
						hours_from_now: startOffset,
						duration_hours: duration,
					}),
				});

				const data = await response.json();
				if (!response.ok) {
					throw new Error(data.error || 'Unable to create event');
				}

				updateEventStatus('Event scheduled! Refresh to see it below.', 'success');
				eventForm.reset();
				eventForm.setAttribute('hidden', 'hidden');
				refreshEvents();
			} catch (error) {
				updateEventStatus(`Error: ${error.message}`, 'danger');
			}
		});

		refreshEventsBtn?.addEventListener('click', refreshEvents);
		refreshBreaksBtn?.addEventListener('click', () => handleInsights('pacing', breakList));

		async function refreshEvents() {
			if (!eventList) return;
			eventList.innerHTML = '<p class="placeholder">Syncing with Google Calendar…</p>';
			try {
				const response = await fetch('/api/events');
				const data = await response.json();
				if (!response.ok) {
					throw new Error(data.error || 'Failed to refresh events');
				}

				if (!Array.isArray(data) || data.length === 0) {
					eventList.innerHTML = '<p class="placeholder">No upcoming events in the next month.</p>';
					return;
				}

				eventList.innerHTML = '';
				data.forEach((event) => {
					const card = document.createElement('article');
					card.className = 'event-card';
					const start = getEventDate(event.start);
					const end = getEventDate(event.end);
					card.innerHTML = `
						<div class="event-summary">
							<h3>${sanitize(event.summary || 'Untitled event')}</h3>
							<p class="event-time">${start}${end ? ` · Ends ${end}` : ''}</p>
						</div>
						${event.description ? `<p class="event-description">${sanitize(event.description)}</p>` : ''}
					`;
					eventList.appendChild(card);
				});
			} catch (error) {
				eventList.innerHTML = `<p class="placeholder">${sanitize(error.message)}</p>`;
			}
		}

		function updateEventStatus(message, tone = 'info') {
			if (!statusEl) return;
			const tones = {
				info: '#a29bfe',
				danger: '#ff6b6b',
				success: '#00cec9',
			};
			statusEl.textContent = message;
			statusEl.style.color = tones[tone] || tones.info;
		}
	}

	function getEventDate(eventTime = {}) {
		if (eventTime.dateTime) {
			return new Date(eventTime.dateTime).toLocaleString();
		}
		if (eventTime.date) {
			return new Date(eventTime.date).toLocaleDateString();
		}
		return 'TBD';
	}

	function sanitize(value) {
		return String(value)
			.replace(/&/g, '&amp;')
			.replace(/</g, '&lt;')
			.replace(/>/g, '&gt;');
	}
})();
