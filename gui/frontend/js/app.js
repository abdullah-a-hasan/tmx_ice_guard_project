/**
 * gui/frontend/js/app.js
 * All frontend logic for TMX Ice Guard.
 * Plain ES6 – no bundler, no npm required.
 */

'use strict';

// ── State ─────────────────────────────────────────────────────────────────
let selectedFiles  = [];   // array of absolute paths
let selectedFolder = null; // string or null
let liveRowsAdded  = 0;    // rows already inserted via onConversionProgress

// ── DOM refs ──────────────────────────────────────────────────────────────
const fileListBox       = document.getElementById('file-list-box');
const filePlaceholder   = document.getElementById('file-list-placeholder');
const folderPathInput   = document.getElementById('folder-path');
const sourcePlatformSel = document.getElementById('source-platform');
const targetPlatformSel = document.getElementById('target-platform');
const prettyCheckbox    = document.getElementById('pretty-print');
const inlineAlert       = document.getElementById('inline-alert');
const btnConvert        = document.getElementById('btn-convert');
const convertStatus     = document.getElementById('convert-status');
const resultsSection    = document.getElementById('results-section');
const resultsSummary    = document.getElementById('results-summary');
const resultsTbody      = document.getElementById('results-tbody');
const btnBrowseFiles    = document.getElementById('btn-browse-files');
const btnBrowseFolder   = document.getElementById('btn-browse-folder');

// ── Helpers ───────────────────────────────────────────────────────────────

function showAlert(message) {
  inlineAlert.textContent = message;
  inlineAlert.hidden = false;
}

function hideAlert() {
  inlineAlert.hidden = true;
  inlineAlert.textContent = '';
}

function basename(path) {
  return path.replace(/\\/g, '/').split('/').pop();
}

// ── Render selected files list ────────────────────────────────────────────

function renderFileList() {
  // Remove all children except the placeholder span
  while (fileListBox.firstChild) {
    fileListBox.removeChild(fileListBox.firstChild);
  }

  if (selectedFiles.length === 0) {
    const span = document.createElement('span');
    span.id = 'file-list-placeholder';
    span.textContent = 'No files selected';
    fileListBox.appendChild(span);
    fileListBox.classList.remove('has-files');
    return;
  }

  fileListBox.classList.add('has-files');

  // Count badge
  const badge = document.createElement('span');
  badge.className = 'file-count-badge';
  badge.textContent = selectedFiles.length;
  fileListBox.appendChild(badge);

  // File names
  selectedFiles.forEach((path, i) => {
    const name = basename(path);
    const span = document.createElement('span');
    span.textContent = name + (i < selectedFiles.length - 1 ? ', ' : '');
    fileListBox.appendChild(span);
  });
}

// ── Populate platform dropdowns ───────────────────────────────────────────

function populatePlatforms(platforms) {
  [sourcePlatformSel, targetPlatformSel].forEach(sel => {
    sel.innerHTML = '';
    platforms.forEach(item => {
      const opt = document.createElement('option');
      opt.value = item.key;
      opt.textContent = item.label;
      sel.appendChild(opt);
    });
  });

  // Defaults: source = "auto", target = "xtm"
  sourcePlatformSel.value = 'auto';
  if ([...targetPlatformSel.options].some(o => o.value === 'xtm')) {
    targetPlatformSel.value = 'xtm';
  }
}

// ── Live progress callback (called by Python via evaluate_js) ─────────────

window.onConversionProgress = function (event) {
  const fileNum   = (event.file_index ?? 0) + 1;
  const fileTotal = event.total_files ?? 1;
  const prefix    = `File ${fileNum} / ${fileTotal}`;

  if (event.type === 'flavor') {
    convertStatus.textContent = `${prefix} — Detected: ${event.platform}`;
  } else if (event.type === 'tu_progress') {
    convertStatus.textContent = `${prefix} — TU ${event.count.toLocaleString()}`;
  } else if (event.type === 'file_done') {
    // Append a result row immediately
    appendResultRow(event);
    liveRowsAdded++;

    // Update running summary
    const successSoFar = resultsTbody.querySelectorAll('.status-ok').length;
    const totalSoFar   = liveRowsAdded;
    const tusSoFar     = [...resultsTbody.querySelectorAll('td:nth-child(2)')]
      .reduce((sum, td) => sum + (parseInt(td.dataset.tuCount, 10) || 0), 0);

    resultsSummary.textContent =
      `${successSoFar} of ${totalSoFar} file${totalSoFar !== 1 ? 's' : ''} converted` +
      ` — ${tusSoFar.toLocaleString()} TU${tusSoFar !== 1 ? 's' : ''} total`;
    resultsSection.hidden = false;
  }
};

function appendResultRow(r) {
  const tr = document.createElement('tr');

  // Filename
  const tdFile = document.createElement('td');
  tdFile.textContent = r.filename;
  tr.appendChild(tdFile);

  // TU count (store raw value for running total calculation)
  const tdTU = document.createElement('td');
  const tuCount = r.success ? (r.tu_count || 0) : 0;
  tdTU.textContent = r.success ? tuCount.toLocaleString() : '\u2014';
  tdTU.dataset.tuCount = tuCount;
  tr.appendChild(tdTU);

  // Detected source
  const tdSrc = document.createElement('td');
  tdSrc.textContent = r.detected_source || '\u2014';
  tr.appendChild(tdSrc);

  // Status
  const tdStatus = document.createElement('td');
  if (r.success) {
    tdStatus.innerHTML = '<span class="status-ok">✓</span>';
  } else {
    tdStatus.innerHTML = `<span class="status-err">✗ ${escapeHtml(r.error || 'Unknown error')}</span>`;
  }
  tr.appendChild(tdStatus);

  resultsTbody.appendChild(tr);
}



function renderResults(results) {
  resultsTbody.innerHTML = '';

  let successCount = 0;
  let totalTUs     = 0;

  results.forEach(r => {
    if (r.success) {
      successCount++;
      totalTUs += r.tu_count || 0;
    }

    const tr = document.createElement('tr');

    // Filename
    const tdFile = document.createElement('td');
    tdFile.textContent = r.filename;
    tr.appendChild(tdFile);

    // TU count
    const tdTU = document.createElement('td');
    tdTU.textContent = r.success ? r.tu_count.toLocaleString() : '\u2014';
    tr.appendChild(tdTU);

    // Detected source
    const tdSrc = document.createElement('td');
    tdSrc.textContent = r.detected_source || '\u2014';
    tr.appendChild(tdSrc);

    // Status
    const tdStatus = document.createElement('td');
    if (r.success) {
      tdStatus.innerHTML = '<span class="status-ok">✓</span>';
    } else {
      tdStatus.innerHTML = `<span class="status-err">✗ ${escapeHtml(r.error || 'Unknown error')}</span>`;
    }
    tr.appendChild(tdStatus);

    resultsTbody.appendChild(tr);
  });

  resultsSummary.textContent =
    `${successCount} of ${results.length} file${results.length !== 1 ? 's' : ''} converted successfully` +
    ` — ${totalTUs.toLocaleString()} TU${totalTUs !== 1 ? 's' : ''} total`;

  resultsSection.hidden = false;
}

function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// ── Event handlers ────────────────────────────────────────────────────────

btnBrowseFiles.addEventListener('click', async () => {
  hideAlert();
  try {
    const files = await window.pywebview.api.open_files();
    if (files && files.length > 0) {
      selectedFiles = files;
      renderFileList();
    }
  } catch (err) {
    showAlert('Could not open file dialog: ' + err);
  }
});

btnBrowseFolder.addEventListener('click', async () => {
  hideAlert();
  try {
    const folder = await window.pywebview.api.open_folder();
    if (folder) {
      selectedFolder = folder;
      folderPathInput.value = folder;
      folderPathInput.classList.add('has-path');
    }
  } catch (err) {
    showAlert('Could not open folder dialog: ' + err);
  }
});

btnConvert.addEventListener('click', async () => {
  hideAlert();

  // Validate
  if (selectedFiles.length === 0) {
    showAlert('Please select at least one TMX file.');
    return;
  }
  if (!selectedFolder) {
    showAlert('Please select an output folder.');
    return;
  }

  // Disable button, show spinner
  btnConvert.disabled = true;
  btnConvert.innerHTML = '<span class="spinner"></span> Converting…';
  convertStatus.textContent = '';
  resultsSection.hidden = true;
  resultsTbody.innerHTML = '';
  liveRowsAdded = 0;

  try {
    const results = await window.pywebview.api.convert_files(
      selectedFiles,
      selectedFolder,
      sourcePlatformSel.value,
      targetPlatformSel.value,
      prettyCheckbox.checked
    );
    // Only fall back to renderResults if live events weren't received
    if (liveRowsAdded === 0) {
      renderResults(results);
    }
  } catch (err) {
    showAlert('Conversion failed: ' + err);
  } finally {
    btnConvert.disabled = false;
    btnConvert.textContent = 'Convert';
    convertStatus.textContent = '';
  }
});

// ── Initialise ────────────────────────────────────────────────────────────

async function init() {
  // pywebview injects window.pywebview when the DOM is ready, but the
  // bridge may not be available immediately on page load. Retry briefly.
  const MAX_RETRIES = 20;
  let retries = 0;

  const tryInit = async () => {
    if (window.pywebview && window.pywebview.api) {
      try {
        const platforms = await window.pywebview.api.get_platforms();
        populatePlatforms(platforms);
      } catch (err) {
        showAlert('Failed to load platform list: ' + err);
      }
      return;
    }
    if (++retries < MAX_RETRIES) {
      setTimeout(tryInit, 150);
    } else {
      showAlert('Could not connect to the Python backend. Please restart the application.');
    }
  };

  await tryInit();
}

window.addEventListener('pywebviewready', init);
// Fallback: also try on DOMContentLoaded in case the event already fired
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
