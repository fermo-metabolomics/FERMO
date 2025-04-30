/**
 * Shows a analysis section and hides others.
 * If 'all' is passed, all sections are hidden.
 * @param {string} id - The selector ID of the element to show (e.g. '#PhenoQualAssgnParameters') OR 'all'
 */
function selectAnalysis(id) {
  const collapseTargets = [
    "#startAnalysisContent",
    "#loadParamsContent",
    "#loadSessionContent"
  ];

  collapseTargets.forEach(selector => {
    const el = document.querySelector(selector);
    if (el && el.classList.contains("show")) {
      bootstrap.Collapse.getOrCreateInstance(el).hide();
    }
  });

  const selected = document.querySelector(id);
  if (selected) {
    bootstrap.Collapse.getOrCreateInstance(selected).show();
  }
}


/**
 * Checks FERMO session ID and opens submit field
 * @param {string} id - the input field ID
 * @param {string} targetErrorId - The selector ID of the error report field
 * @param {string} submitId - The selector ID to show submission field after file upload
 */
function checkSessionId(id, targetErrorId, submitId) {
  const inputEl = document.getElementById(id);
  const alertContainer = document.getElementById(targetErrorId);
  const submitEl = document.getElementById(submitId);
  const regex = /^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$/;

  // Hide submission element
  if (submitEl && submitEl.classList.contains("show")) {
    bootstrap.Collapse.getOrCreateInstance(submitEl).hide();
  }

  // check for value and raise alert
  if (!regex.test(inputEl.value)) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-warning alert-dismissible fade show';
    alertDiv.role = 'alert';
    alertDiv.innerHTML = `
      Invalid session id. Please specify a valid <i>FERMO</i> session ID.
      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    alertContainer.appendChild(alertDiv);
    inputEl.value = ""; // Clear invalid selection
    return;
  }

  // If valid, show the associated parameter field
  if (submitEl && !submitEl.classList.contains("show")) {
    bootstrap.Collapse.getOrCreateInstance(submitEl).show();
  }
}


//Checks file extension client-side
/**
 * Checks for the correct file extension.
 * @param {string} id - The selector ID of the file input field
 * @param {string} ext - The extension to check for (e.g. 'csv')
 * @param {string} targetErrorId - The selector ID of the error report field
 * @param {string} paramId - The selector ID to show parameter field after file upload
 */
function checkFileExtension(id, ext, targetErrorId, paramId) {
  const fileInput = document.getElementById(id);
  const files = fileInput.files;
  const filesArray = Array.from(files);
  const isValid = filesArray.every(file => file.name.endsWith(ext));
  const paramEl = document.getElementById(paramId);
  const alertContainer = document.getElementById(targetErrorId);

  if (!isValid) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-warning alert-dismissible fade show';
    alertDiv.role = 'alert';
    alertDiv.innerHTML = `
      Invalid file type. Please upload only <b>${ext}</b> files.
      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    alertContainer.appendChild(alertDiv);
    fileInput.value = ""; // Clear invalid selection

    if (paramEl && paramEl.classList.contains("show")) {
      bootstrap.Collapse.getOrCreateInstance(paramEl).hide();
    }
    return;
  }

  // If valid, show the associated parameter field
  if (paramEl && !paramEl.classList.contains("show")) {
    bootstrap.Collapse.getOrCreateInstance(paramEl).show();
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

