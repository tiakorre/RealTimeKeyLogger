document.addEventListener('DOMContentLoaded', () => {
    const socket = io();
    const toggleButton = document.getElementById('toggleButton');
    const keyLog = document.getElementById('keyLog');
    const analytics = document.getElementById('analytics');

    toggleButton.addEventListener('click', toggleLogging);

    // Function to fetch logs
    function fetchLogs() {
        fetch('/logs')
            .then(response => response.json())
            .then(data => {
                keyLog.textContent = data.join(''); // Inline display
            })
            .catch(error => console.error('Error fetching logs:', error));
    }

    // Function to toggle logging state
    function toggleLogging() {
        fetch('/toggle_logging', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.logging_enabled) {
                toggleButton.textContent = 'Stop Tracking';
                toggleButton.classList.add('tracking');
            } else {
                toggleButton.textContent = 'Start Tracking';
                toggleButton.classList.remove('tracking');
            }
        })
        .catch(error => console.error('Error toggling logging:', error));
    }

    // Function to clear logs
    function clearLogs() {
        fetch('/clear_logs', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            keyLog.textContent = '';
            console.log(data.status);
        })
        .catch(error => console.error('Error clearing logs:', error));
    }

    // Listen for new keystrokes
    socket.on('new_keystroke', (data) => {
        keyLog.textContent += data.char;
    });

    // Listen for analytics data
    socket.on('analytics', (data) => {
        analytics.textContent = `Duration: ${data.duration} seconds\nTotal keystrokes: ${data.total_keys}\nUnique keystrokes: ${data.unique_keys}`;
    });

    // Export functions to be used in inline event handler
    window.fetchLogs = fetchLogs;
    window.clearLogs = clearLogs;
});
