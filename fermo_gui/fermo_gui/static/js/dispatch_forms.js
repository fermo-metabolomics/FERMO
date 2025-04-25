
//Checks wich analysis dispatch was selected TODO(MMZ 25.4.25)



//Checks file extension client-side
/**
 * Checks for the correct file extension.
 * @param {string} id - The selector ID of the file input field
 * @param {string} ext - The extension to check for (e.g. 'csv')
 * @param {string} targetErrorId - The selector ID of the error report field
 */
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


/**
 * Shows a specific phenotype parameter section and hides others.
 * If 'all' is passed, all sections are hidden.
 * @param {string} id - The selector ID of the element to show (e.g. '#PhenoQualAssgnParameters') OR 'all'
 */
function collapseOtherPhenoParams(id) {
  const collapseTargets = [
    "#PhenoQualAssgnParameters",
    "#PhenoQuantPercentAssgnParameters",
    "#PhenoQuantConcAssgnParameters"
  ];

  // Hide all collapsible sections
  collapseTargets.forEach(selector => {
    const el = document.querySelector(selector);
    if (el && el.classList.contains("show")) {
      bootstrap.Collapse.getOrCreateInstance(el).hide();
    }
  });

  // Show selected section unless "all"
  if (id === 'all') return;

  const selected = document.querySelector(id);
  if (selected) {
    bootstrap.Collapse.getOrCreateInstance(selected).show();
  }
}

