document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('fileInput');
    const fileList = document.getElementById('fileList');
    const uploadForm = document.getElementById('uploadForm');
    const previewZone = document.getElementById('previewZone');
    const descriptionInput = document.getElementById('description');
    const groups = JSON.parse(document.body.getAttribute('data-groups') || '[]');
    const waitingBlock = document.getElementById('waiting-block');
    const uploadBlock = document.getElementById('upload-block');
    const groupItems = document.querySelectorAll('.group-select');
    let selectedGroup = null;

    // Définition des extensions autorisées par groupe
    const groupExtensions = {
        'Upload Format BNP PARIBAS': ['.txt', '.csv', '.pdf'],
        'Injection fichier Finifac': ['.xlsx', '.docx', '.pdf', '.csv', '.png']
    };
    let allowedExtensions = [];
    groups.forEach(g => {
        if (groupExtensions[g]) {
            allowedExtensions = allowedExtensions.concat(groupExtensions[g]);
        }
    });
    allowedExtensions = Array.from(new Set(allowedExtensions));

    let filesArray = [];

    function isExtensionAllowed(filename) {
        if (allowedExtensions.length === 0) return true;
        const ext = filename.slice(filename.lastIndexOf('.')).toLowerCase();
        return allowedExtensions.includes(ext);
    }

    function renderPreview(file) {
        previewZone.innerHTML = '';
        if (!file) return;
        if (file.type.startsWith('image/')) {
            const img = document.createElement('img');
            img.style.maxWidth = '100%';
            img.style.maxHeight = '200px';
            img.style.display = 'block';
            img.style.margin = '0 auto';
            const reader = new FileReader();
            reader.onload = function(e) {
                img.src = e.target.result;
            };
            reader.readAsDataURL(file);
            previewZone.appendChild(img);
        } else if (file.type.startsWith('text/') || file.name.endsWith('.txt') || file.name.endsWith('.csv')) {
            const pre = document.createElement('pre');
            pre.style.maxHeight = '200px';
            pre.style.overflow = 'auto';
            pre.style.background = '#f7fafd';
            pre.style.borderRadius = '6px';
            pre.style.padding = '8px';
            pre.style.fontSize = '13px';
            pre.style.margin = '0';
            const reader = new FileReader();
            reader.onload = function(e) {
                pre.textContent = e.target.result.substring(0, 2000) + (e.target.result.length > 2000 ? '\n... (aperçu tronqué)' : '');
            };
            reader.readAsText(file);
            previewZone.appendChild(pre);
        } else {
            const span = document.createElement('span');
            span.textContent = 'Aperçu non disponible pour ce type de fichier.';
            previewZone.appendChild(span);
        }
    }

    fileInput.addEventListener('change', function(e) {
        const newFiles = Array.from(fileInput.files);
        let rejected = [];
        newFiles.forEach(newFile => {
            if (!isExtensionAllowed(newFile.name)) {
                rejected.push(newFile.name);
                return;
            }
            if (!filesArray.some(f => f.name === newFile.name && f.size === newFile.size && f.lastModified === newFile.lastModified)) {
                filesArray.push(newFile);
            }
        });
        if (rejected.length > 0) {
            alert('Fichiers non autorisés :\n' + rejected.join('\n') + '\n\nExtensions autorisées : ' + allowedExtensions.join(', '));
        }
        renderFileList();
        updateFileInput();
        if (filesArray.length > 0) {
            renderPreview(filesArray[0]);
        } else {
            previewZone.innerHTML = '';
        }
    });

    function renderFileList() {
        fileList.innerHTML = '';
        filesArray.forEach((file, idx) => {
            const li = document.createElement('li');
            li.textContent = `${file.name} (${(file.size/1024).toFixed(2)} Ko)`;
            li.style.cursor = 'pointer';
            li.onclick = function() {
                renderPreview(file);
            };
            const removeBtn = document.createElement('button');
            removeBtn.type = 'button';
            removeBtn.textContent = 'Supprimer';
            removeBtn.style.marginLeft = '10px';
            removeBtn.onclick = function(event) {
                event.stopPropagation();
                filesArray.splice(idx, 1);
                updateFileInput();
                renderFileList();
                if (filesArray.length > 0) {
                    renderPreview(filesArray[0]);
                } else {
                    previewZone.innerHTML = '';
                }
            };
            li.appendChild(removeBtn);
            fileList.appendChild(li);
        });
    }

    function updateFileInput() {
        const dt = new DataTransfer();
        filesArray.forEach(file => dt.items.add(file));
        fileInput.files = dt.files;
    }

    // Barre de progression upload
    uploadForm.addEventListener('submit', function(e) {
        if (filesArray.length === 0) {
            e.preventDefault();
            alert('Veuillez sélectionner au moins un fichier.');
            return;
        }
        e.preventDefault();
        const formData = new FormData();
        filesArray.forEach(file => formData.append('file', file));
        formData.append('description', descriptionInput.value);
        // Création de la barre de progression
        let progressBar = document.getElementById('progress-bar');
        if (!progressBar) {
            progressBar = document.createElement('div');
            progressBar.id = 'progress-bar';
            progressBar.style.height = '8px';
            progressBar.style.width = '0';
            progressBar.style.background = 'linear-gradient(90deg,#38b2ac,#4299e1)';
            progressBar.style.borderRadius = '6px';
            progressBar.style.transition = 'width 0.3s';
            progressBar.style.marginBottom = '12px';
            uploadForm.insertBefore(progressBar, uploadForm.firstChild);
        }
        progressBar.style.width = '0';
        const xhr = new XMLHttpRequest();
        xhr.open('POST', uploadForm.action, true);
        xhr.upload.onprogress = function(e) {
            if (e.lengthComputable) {
                const percent = Math.round((e.loaded / e.total) * 100);
                progressBar.style.width = percent + '%';
            }
        };
        xhr.onload = function() {
            if (xhr.status === 200 || xhr.status === 302) {
                progressBar.style.width = '100%';
                setTimeout(() => {
                    progressBar.style.width = '0';
                    window.location.reload();
                }, 800);
            } else {
                alert('Erreur lors de l\'upload');
            }
        };
        xhr.onerror = function() {
            alert('Erreur réseau lors de l\'upload');
        };
        xhr.send(formData);
    });

    function setAllowedExtensionsForGroup(group) {
        allowedExtensions = groupExtensions[group] ? groupExtensions[group] : [];
    }

    function showUploadForGroup(group) {
        if (!group) return;
        setAllowedExtensionsForGroup(group);
        if (waitingBlock) waitingBlock.style.display = 'none';
        if (uploadBlock) uploadBlock.style.display = '';
        selectedGroup = group;
        // Optionnel : afficher le nom du groupe sélectionné dans le formulaire
        const uploadSection = document.getElementById('upload-section');
        if (uploadSection) uploadSection.textContent = 'Uploader un fichier pour le groupe : ' + group;
    }

    // Initialisation à l'ouverture de la page : bloc d'attente par défaut
    if (waitingBlock) waitingBlock.style.display = '';
    if (uploadBlock) uploadBlock.style.display = 'none';

    groupItems.forEach(item => {
        item.addEventListener('click', function() {
            const group = this.getAttribute('data-group');
            localStorage.setItem('selectedGroup', group);
            showUploadForGroup(group);
        });
    });

    // À l'ouverture de la page, si un groupe est mémorisé, l'afficher
    const storedGroup = localStorage.getItem('selectedGroup');
    if (storedGroup && groups.includes(storedGroup)) {
        showUploadForGroup(storedGroup);
    } else {
        if (waitingBlock) waitingBlock.style.display = '';
        if (uploadBlock) uploadBlock.style.display = 'none';
    }

    const toggleBtn = document.getElementById('toggle-history-btn');
    const historyBlock = document.getElementById('history-list-block');
    if (toggleBtn && historyBlock) {
        toggleBtn.addEventListener('click', function() {
            if (historyBlock.style.display === 'none') {
                historyBlock.style.display = '';
                toggleBtn.textContent = 'Masquer l\'historique';
            } else {
                historyBlock.style.display = 'none';
                toggleBtn.textContent = 'Afficher l\'historique';
            }
        });
    }

    function attachToggleFolderHistory() {
        const toggleFolderBtn = document.getElementById('toggle-folder-history-btn');
        const folderHistoryBlock = document.getElementById('folder-history-list-block');
        if (toggleFolderBtn && folderHistoryBlock) {
            toggleFolderBtn.addEventListener('click', function() {
                if (folderHistoryBlock.style.display === 'none') {
                    folderHistoryBlock.style.display = '';
                    toggleFolderBtn.textContent = 'Masquer l\'historique';
                } else {
                    folderHistoryBlock.style.display = 'none';
                    toggleFolderBtn.textContent = 'Afficher l\'historique';
                }
            });
        }
    }

    attachToggleFolderHistory();
}); 