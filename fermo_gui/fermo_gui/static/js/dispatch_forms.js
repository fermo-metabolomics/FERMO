/* Functionality for forms.html

Copyright (c) 2025-present Mitja M. Zdouc, PhD

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/


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
 * @param {number} maxSize - the maximum upload size in bytes (if 0, == offline)
 */
function checkFile(id, ext, targetErrorId, paramId, maxSize) {
  const maxSizeHuman = maxSize / 1024 / 1024;
  const fileInput = document.getElementById(id);
  const files = fileInput.files;
  const filesArray = Array.from(files);
  const isValidExt = filesArray.every(file => file.name.endsWith(ext));
  var isValidSize = filesArray.every(file => file.size < maxSize);
  const paramEl = document.getElementById(paramId);
  const alertContainer = document.getElementById(targetErrorId);

  if (maxSize === 0) {
    isValidSize = true;
  }

  function showFileAlert(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-warning alert-dismissible fade show';
    alertDiv.role = 'alert';
    alertDiv.innerHTML = `
      ${message}
      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    alertContainer.appendChild(alertDiv);
    fileInput.value = ""; // Clear invalid selection

    if (paramEl && paramEl.classList.contains("show")) {
      bootstrap.Collapse.getOrCreateInstance(paramEl).hide();
    }
  }

  if (!isValidExt) {
    showFileAlert(`Invalid file type. Please upload only <b>${ext}</b> files.`);
    return;
  }

  if (!isValidSize) {
    showFileAlert(`Invalid file size. Please upload files smaller than <b>${maxSizeHuman}</b> MB.`);
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

