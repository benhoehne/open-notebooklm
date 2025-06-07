// NotebookLM Flask App JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize app
    initializeApp();
});

function initializeApp() {
    setupFormHandling();
    setupFileUpload();
    setupFormValidation();
}

function setupFormHandling() {
    const form = document.getElementById('podcast-form');
    if (!form) {
        console.log('ERROR: Form not found!');
        return;
    }

    console.log('Form found, setting up submit handler');

    form.addEventListener('submit', function(e) {
        console.log('=== FORM SUBMIT EVENT ===');
        console.log('Form submit triggered');
        
        // Debug form data before validation
        const formData = new FormData(form);
        console.log('FormData entries:');
        for (let [key, value] of formData.entries()) {
            console.log(`  ${key}:`, value);
        }
        
        if (!validateForm()) {
            console.log('Form validation failed, preventing submit');
            e.preventDefault();
            return;
        }
        
        console.log('Form validation passed, showing loading and submitting');
        showLoading();
        // Form will submit normally
    });
}

function setupFileUpload() {
    const fileInput = document.getElementById('pdf_files');
    if (!fileInput) return;

    // File drag and drop functionality
    const dropZone = fileInput.closest('.border-dashed');
    
    if (dropZone) {
        dropZone.addEventListener('dragover', function(e) {
            e.preventDefault();
            dropZone.classList.add('border-indigo-500', 'bg-indigo-500/10');
        });

        dropZone.addEventListener('dragleave', function(e) {
            e.preventDefault();
            dropZone.classList.remove('border-indigo-500', 'bg-indigo-500/10');
        });

        dropZone.addEventListener('drop', function(e) {
            e.preventDefault();
            dropZone.classList.remove('border-indigo-500', 'bg-indigo-500/10');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                fileInput.files = files;
                updateFileDisplays();
            }
        });
    }

    // File input change
    fileInput.addEventListener('change', function() {
        console.log('File input changed:', this.files);
        updateFileDisplays();
    });
}

function updateFileDisplays() {
    const fileInput = document.getElementById('pdf_files');
    if (!fileInput) {
        console.log('ERROR: File input not found!');
        return;
    }
    
    const files = fileInput.files;
    console.log('updateFileDisplays called, files:', files);
    
    // Get the separate display areas (DO NOT touch the upload area with the file input)
    const selectedFilesDisplay = document.getElementById('selected-files-display');
    const fileCountDisplay = document.getElementById('file-count-display');
    const fileListDisplay = document.getElementById('file-list-display');
    
    if (!selectedFilesDisplay || !fileCountDisplay || !fileListDisplay) {
        console.log('ERROR: Display areas not found!');
        return;
    }

    if (files.length > 0) {
        // Show the selected files display area
        selectedFilesDisplay.classList.remove('hidden');
        
        // Update the file count
        fileCountDisplay.textContent = `${files.length} file${files.length > 1 ? 's' : ''} selected`;
        
        // Create the file list
        let fileListHTML = '';
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            const sizeKB = Math.round(file.size / 1024);
            fileListHTML += `
                <div class="flex items-center justify-between text-sm text-indigo-200 bg-indigo-900/30 rounded px-3 py-2">
                    <div class="flex items-center">
                        <svg class="w-4 h-4 text-indigo-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clip-rule="evenodd" />
                        </svg>
                        <span class="truncate">${file.name}</span>
                    </div>
                    <span class="text-xs text-indigo-300 ml-2">${sizeKB} KB</span>
                </div>
            `;
        }
        fileListDisplay.innerHTML = fileListHTML;
        
        console.log('Files displayed successfully without DOM manipulation of file input');
    } else {
        // Hide the display area if no files
        selectedFilesDisplay.classList.add('hidden');
        console.log('No files to display');
    }
}

function setupFormValidation() {
    // Real-time validation for file size
    const fileInput = document.getElementById('pdf_files');
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            const files = this.files;
            const maxSize = 10 * 1024 * 1024; // 10MB
            
            console.log('File validation started, files:', files);
            
            for (let file of files) {
                console.log(`Validating file: ${file.name}, size: ${file.size}, type: ${file.type}`);
                
                if (file.size > maxSize) {
                    alert(`File "${file.name}" is too large. Maximum size is 10MB.`);
                    this.value = ''; // Clear the input
                    return;
                }
                
                // More flexible PDF validation - check file extension and MIME type
                const fileName = file.name.toLowerCase();
                const isPdfByName = fileName.endsWith('.pdf');
                const isPdfByType = file.type === 'application/pdf' || file.type.includes('pdf');
                
                if (!isPdfByName && !isPdfByType) {
                    alert(`File "${file.name}" is not a PDF file. Please upload only PDF files.`);
                    this.value = ''; // Clear the input
                    return;
                }
                
                console.log(`File "${file.name}" passed validation`);
            }
        });
    }
}

function validateForm() {
    const fileInput = document.getElementById('pdf_files');
    const urlInput = document.getElementById('url');
    const scriptInput = document.getElementById('script_file');
    
    // Debug logging
    console.log('=== FORM VALIDATION DEBUG ===');
    console.log('File input element:', fileInput);
    console.log('File input exists:', !!fileInput);
    console.log('File input type:', fileInput ? fileInput.type : 'N/A');
    console.log('File input name:', fileInput ? fileInput.name : 'N/A');
    console.log('File input id:', fileInput ? fileInput.id : 'N/A');
    console.log('Files object:', fileInput ? fileInput.files : 'No file input');
    console.log('Number of files:', fileInput ? fileInput.files.length : 0);
    console.log('URL input:', urlInput);
    console.log('URL value:', urlInput ? urlInput.value : 'No URL input');
    console.log('Script input:', scriptInput);
    console.log('Script files:', scriptInput ? scriptInput.files : 'No script input');
    console.log('Number of script files:', scriptInput ? scriptInput.files.length : 0);
    
    // Additional debugging - check all file inputs on the page
    const allFileInputs = document.querySelectorAll('input[type="file"]');
    console.log('All file inputs on page:', allFileInputs);
    allFileInputs.forEach((input, index) => {
        console.log(`File input ${index}:`, input, 'files:', input.files);
    });
    
    // Check if at least one content source is provided
    const hasFiles = fileInput && fileInput.files && fileInput.files.length > 0;
    const hasUrl = urlInput && urlInput.value.trim() !== '';
    const hasScript = scriptInput && scriptInput.files && scriptInput.files.length > 0;
    
    console.log('Has files:', hasFiles);
    console.log('Has URL:', hasUrl);
    console.log('Has script:', hasScript);
    
    if (!hasFiles && !hasUrl && !hasScript) {
        console.log('VALIDATION FAILED: No files, no URL, and no script');
        alert('Please provide at least one content source: upload PDF files, enter a website URL, or import a script file.');
        return false;
    }
    
    // Debug file details if files are present
    if (hasFiles) {
        console.log('PDF file details:');
        for (let i = 0; i < fileInput.files.length; i++) {
            const file = fileInput.files[i];
            console.log(`  File ${i}: ${file.name}, Size: ${file.size}, Type: ${file.type}`);
        }
    }
    
    // Debug script file details if script is present
    if (hasScript) {
        console.log('Script file details:');
        for (let i = 0; i < scriptInput.files.length; i++) {
            const file = scriptInput.files[i];
            console.log(`  Script ${i}: ${file.name}, Size: ${file.size}, Type: ${file.type}`);
        }
    }
    
    console.log('VALIDATION PASSED');
    return true;
}

// Loading indicator functions (already defined in base.html)
function showLoading() {
    const loading = document.getElementById('loading');
    if (loading) {
        loading.classList.remove('hidden');
    }
}

function hideLoading() {
    const loading = document.getElementById('loading');
    if (loading) {
        loading.classList.add('hidden');
    }
}

// Clear form function
function clearForm() {
    const form = document.getElementById('podcast-form');
    if (form) {
        form.reset();
        updateFileDisplays(); // Reset file display
    }
}

// Export functions for global access
window.clearForm = clearForm;
window.showLoading = showLoading;
window.hideLoading = hideLoading; 