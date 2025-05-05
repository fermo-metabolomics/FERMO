var logContent = new ClipboardJS('#logContentButton');

logContent.on('success', function(e) {
    alert('Copied to clipboard!');
    e.clearSelection();
});

logContent.on('error', function(e) {
    alert('Copy failed:', e);
});