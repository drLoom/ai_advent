let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;

async function initMediaRecorder() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);

        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };

        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            audioChunks = [];

            // Send to backend for transcription
            await transcribeAudio(audioBlob);
        };

        return mediaRecorder;
    } catch (error) {
        console.error('Failed to initialize media recorder:', error);
        if (error.name === 'NotAllowedError') {
            alert('Microphone access denied. Please allow microphone access in your browser settings.');
        } else {
            alert('Failed to access microphone: ' + error.message);
        }
        return null;
    }
}

async function transcribeAudio(audioBlob) {
    const messageInput = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendButton');

    try {
        // Disable input while transcribing
        messageInput.disabled = true;
        sendButton.disabled = true;
        updateMicButtonState(false, 'Transcribing...');

        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.webm');

        const response = await fetch('/transcribe', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success && data.text) {
            // Append transcribed text to input
            const currentText = messageInput.value;
            const separator = currentText && !currentText.endsWith(' ') ? ' ' : '';
            messageInput.value = currentText + separator + data.text;
            messageInput.dispatchEvent(new Event('input'));
            sendButton.disabled = false;
            sendButton.click();
        } else {
            console.error('Transcription failed:', data.error);
            alert('Transcription failed: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Transcription error:', error);
        alert('Failed to transcribe audio: ' + error.message);
    } finally {
        // Re-enable input
        messageInput.disabled = false;
        sendButton.disabled = false;
        updateMicButtonState(false);
        messageInput.focus();
    }
}

async function toggleSpeechRecognition() {
    if (isRecording) {
        // Stop recording
        if (mediaRecorder && mediaRecorder.state === 'recording') {
            mediaRecorder.stop();
            // Stop all tracks in the stream
            mediaRecorder.stream.getTracks().forEach(track => track.stop());
        }
        isRecording = false;
        updateMicButtonState(false);
    } else {
        // Start recording
        if (!mediaRecorder) {
            mediaRecorder = await initMediaRecorder();
            if (!mediaRecorder) {
                return;
            }
        } else {
            // Reinitialize if needed
            if (mediaRecorder.state === 'inactive') {
                mediaRecorder = await initMediaRecorder();
                if (!mediaRecorder) {
                    return;
                }
            }
        }

        try {
            audioChunks = [];
            mediaRecorder.start();
            isRecording = true;
            updateMicButtonState(true);
            console.log('Recording started');
        } catch (error) {
            console.error('Failed to start recording:', error);
            isRecording = false;
            updateMicButtonState(false);
            alert('Failed to start recording: ' + error.message);
        }
    }
}

function updateMicButtonState(recording, customTitle = null) {
    const micButton = document.getElementById('micButton');
    if (recording) {
        micButton.classList.add('recording');
        micButton.title = 'Stop recording';
    } else {
        micButton.classList.remove('recording');
        micButton.title = customTitle || 'Voice input';
    }
}
