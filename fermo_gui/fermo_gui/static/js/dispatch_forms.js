
//Checks wich analysis dispatch was selected



//Checks file extension client-side
function checkFileExtension(id, ext, targetErrorId) {
  const fileInput = document.getElementById(id);
  const file = fileInput.files[0];

  if (file && !file.name.endsWith(ext)) {
    const alertContainer = document.getElementById(targetErrorId);

    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-warning alert-dismissible fade show';
    alertDiv.role = 'alert';
    alertDiv.innerHTML = `
      Invalid file type. Please upload a ${ext} file.
      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    alertContainer.appendChild(alertDiv);
    fileInput.value = ""; // Clear file selection
  }
}