/**
 * Sistema di annotazione di testo per documenti
 */
class TextAnnotationSystem {
    constructor(options) {
        this.documentId = options.documentId;
        this.container = document.getElementById(options.containerId);
        this.annotations = options.annotations || [];
        this.labels = options.labels || [];
        
        this.selectedText = null;
        this.selectedRange = null;
        this.lineNumbersVisible = false;
        
        this.init();
    }
    
    init() {
        // Salva il contenuto originale
        this.originalContent = this.container.textContent;
        
        this.setupEventListeners();
        this.renderAnnotations();
        this.setupModals();
        
        // Popola la lista compatta delle annotazioni
        this.rebuildAnnotationsList();
        
        // Aggiorna i conteggi iniziali
        this.updateStats();
    }
    
    setupEventListeners() {
        // Selezione testo
        this.container.addEventListener('mouseup', (e) => {
            setTimeout(() => this.handleTextSelection(e), 10);
        });
        
        // Anche per touch devices
        this.container.addEventListener('touchend', (e) => {
            setTimeout(() => this.handleTextSelection(e), 10);
        });
        
        // Click su annotazioni esistenti
        this.container.addEventListener('click', (e) => {
            if (e.target.classList.contains('annotation-highlight')) {
                e.preventDefault();
                
                // Gestisci annotazioni multiple
                if (e.target.dataset.multipleAnnotations) {
                    const annotationIds = e.target.dataset.multipleAnnotations.split(',').map(id => parseInt(id));
                    const annotations = this.annotations.filter(a => annotationIds.includes(a.id));
                    this.showMultipleAnnotationsModal(annotations);
                } else if (e.target.dataset.annotationId) {
                    // Annotazione singola
                    this.showAnnotationDetails(e.target.dataset.annotationId);
                }
            }
        });
        
        // Previeni selezione su annotazioni esistenti durante la creazione
        this.container.addEventListener('selectstart', (e) => {
            if (e.target.classList.contains('annotation-highlight')) {
                e.preventDefault();
            }
        });
        
        // Aggiungi listener per il reset quando si clicca fuori dal container
        document.addEventListener('click', (e) => {
            if (!this.container.contains(e.target) && !e.target.closest('.modal')) {
                this.clearSelection();
            }
        });
    }
    
    reattachEventListeners() {
        // Rimuovi tutti i listener esistenti dal container per evitare duplicati
        const newContainer = this.container.cloneNode(true);
        this.container.parentNode.replaceChild(newContainer, this.container);
        this.container = newContainer;
        
        // Riattiva i listener degli eventi
        // Selezione testo
        this.container.addEventListener('mouseup', (e) => {
            setTimeout(() => this.handleTextSelection(e), 10);
        });
        
        // Anche per touch devices
        this.container.addEventListener('touchend', (e) => {
            setTimeout(() => this.handleTextSelection(e), 10);
        });
        
        // Click su annotazioni esistenti
        this.container.addEventListener('click', (e) => {
            if (e.target.classList.contains('annotation-highlight')) {
                e.preventDefault();
                
                // Gestisci annotazioni multiple
                if (e.target.dataset.multipleAnnotations) {
                    const annotationIds = e.target.dataset.multipleAnnotations.split(',').map(id => parseInt(id));
                    const annotations = this.annotations.filter(a => annotationIds.includes(a.id));
                    this.showMultipleAnnotationsModal(annotations);
                } else if (e.target.dataset.annotationId) {
                    // Annotazione singola
                    this.showAnnotationDetails(e.target.dataset.annotationId);
                }
            }
        });
        
        // Previeni selezione su annotazioni esistenti durante la creazione
        this.container.addEventListener('selectstart', (e) => {
            if (e.target.classList.contains('annotation-highlight')) {
                e.preventDefault();
            }
        });
    }
    
    setupModals() {
        this.annotationModal = new bootstrap.Modal(document.getElementById('annotationModal'));
        this.detailsModal = new bootstrap.Modal(document.getElementById('annotationDetailsModal'));
        
        // Salva annotazione
        document.getElementById('saveAnnotation').addEventListener('click', () => {
            this.saveAnnotation();
        });
    }
    
    handleTextSelection(e) {
        const selection = window.getSelection();
        
        if (selection.rangeCount === 0 || selection.isCollapsed) {
            return;
        }
        
        const range = selection.getRangeAt(0);
        
        // Verifica che la selezione sia all'interno del container
        if (!this.container.contains(range.commonAncestorContainer)) {
            return;
        }
        
        // Verifica che non stiamo selezionando parti di annotazioni esistenti
        const startElement = range.startContainer.nodeType === Node.TEXT_NODE ? 
                            range.startContainer.parentElement : range.startContainer;
        const endElement = range.endContainer.nodeType === Node.TEXT_NODE ? 
                          range.endContainer.parentElement : range.endContainer;
        
        // Se stiamo selezionando all'interno di un'annotazione esistente, ignora
        if (startElement.closest('.annotation-highlight') || endElement.closest('.annotation-highlight')) {
            console.log('Selezione all\'interno di annotazione esistente, ignorata');
            selection.removeAllRanges();
            return;
        }
        
        const selectedText = selection.toString().trim();
        
        if (selectedText.length < 3) {
            this.showToast('Seleziona almeno 3 caratteri per creare un\'annotazione', 'warning');
            selection.removeAllRanges();
            return;
        }
        
        if (selectedText.length > 1000) {
            this.showToast('La selezione è troppo lunga (massimo 1000 caratteri)', 'warning');
            selection.removeAllRanges();
            return;
        }
        
        // Calcola posizioni
        const startPos = this.getTextPosition(range.startContainer, range.startOffset);
        const endPos = this.getTextPosition(range.endContainer, range.endOffset);
        
        this.selectedText = selectedText;
        this.selectedRange = {
            start: startPos,
            end: endPos,
            range: range.cloneRange()
        };
        
        console.log('Testo selezionato:', selectedText, 'Posizioni:', startPos, '-', endPos);
        
        this.showAnnotationModal();
    }
    
    getTextPosition(node, offset) {
        const walker = document.createTreeWalker(
            this.container,
            NodeFilter.SHOW_TEXT,
            null,
            false
        );
        
        let position = 0;
        let currentNode;
        
        while (currentNode = walker.nextNode()) {
            if (currentNode === node) {
                return position + offset;
            }
            position += currentNode.textContent.length;
        }
        
        return position;
    }
    
    showAnnotationModal() {
        document.getElementById('selectedText').textContent = this.selectedText;
        document.getElementById('positionInfo').textContent = 
            `${this.selectedRange.start} - ${this.selectedRange.end} (${this.selectedText.length} caratteri)`;
        
        // Reset label selection
        document.getElementById('labelSelect').value = '';
        
        this.annotationModal.show();
    }
    
    saveAnnotation() {
        const labelSelect = document.getElementById('labelSelect');
        const labelId = labelSelect.value;
        
        if (!labelId) {
            this.showToast('Seleziona un\'etichetta', 'error');
            return;
        }
        
        const label = this.labels.find(l => l.id == labelId);
        if (!label) {
            this.showToast('Etichetta non valida', 'error');
            return;
        }
        
        // Calcola contesto
        const context = this.getContext(this.selectedRange.start, this.selectedRange.end);
        
        const annotationData = {
            document_id: this.documentId,
            text_selection: this.selectedText,
            start_position: this.selectedRange.start,
            end_position: this.selectedRange.end,
            label_id: labelId,
            context_before: context.before,
            context_after: context.after
        };
        
        fetch('/text-documents/api/annotate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
            },
            body: JSON.stringify(annotationData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showToast(data.message, 'success');
                this.annotationModal.hide();
                
                // Aggiorna l'interfaccia
                this.addAnnotationToList(data.annotation);
                
                // Aggiorna l'array locale delle annotazioni
                this.annotations.push({
                    id: data.annotation.id,
                    start_position: data.annotation.start_position,
                    end_position: data.annotation.end_position,
                    text_selection: data.annotation.text_selection,
                    label_id: data.annotation.label_id,
                    label_name: data.annotation.label_name,
                    label_color: data.annotation.label_color,
                    label_category: data.annotation.label_category,
                    user_id: data.annotation.user_id,
                    user_name: data.annotation.user_name,
                    created_at: data.annotation.created_at
                });

                console.log('Nuova annotazione aggiunta:', data.annotation);
                console.log('Totale annotazioni:', this.annotations.length);

                // Ricostruisci il rendering delle annotazioni
                this.renderAnnotations();
                
                // Aggiorna la lista compatta "Annotazione (n)"
                this.rebuildAnnotationsList();
                
                // Pulisci la selezione
                this.clearSelection();
                
                // Aggiorna contatori
                this.updateStats();
                
            } else {
                this.showToast('Errore: ' + data.message, 'error');
            }
        })
        .catch(error => {
            this.showToast('Errore di connessione: ' + error.message, 'error');
        });
    }
    
    getContext(start, end) {
        const fullText = this.container.textContent;
        const contextLength = 100;
        
        const beforeStart = Math.max(0, start - contextLength);
        const afterEnd = Math.min(fullText.length, end + contextLength);
        
        return {
            before: fullText.substring(beforeStart, start),
            after: fullText.substring(end, afterEnd)
        };
    }
    
    renderAnnotations() {
        // Salva il contenuto originale se non è già salvato
        if (!this.originalContent) {
            this.originalContent = this.container.textContent;
        }

        const textContent = this.originalContent;
        this.container.innerHTML = '';

        if (this.annotations.length === 0) {
            this.container.textContent = textContent;
            // Riattiva i listener dopo aver ricreato il contenuto
            this.reattachEventListeners();
            return;
        }

        // Crea eventi per ogni inizio e fine annotazione
        const events = [];
        this.annotations.forEach(annotation => {
            events.push({
                position: annotation.start_position,
                type: 'start',
                annotation: annotation
            });
            events.push({
                position: annotation.end_position,
                type: 'end',
                annotation: annotation
            });
        });

        // Ordina eventi per posizione
        events.sort((a, b) => {
            if (a.position !== b.position) {
                return a.position - b.position;
            }
            // Se alla stessa posizione, prima 'end' poi 'start'
            return a.type === 'end' ? -1 : 1;
        });

        let currentPosition = 0;
        const activeAnnotations = [];

        events.forEach((event, index) => {
            // Aggiungi testo prima dell'evento (se non sovrapposto)
            if (event.position > currentPosition) {
                const segmentText = textContent.substring(currentPosition, event.position);
                if (activeAnnotations.length === 0) {
                    // Testo normale
                    this.container.appendChild(document.createTextNode(segmentText));
                } else {
                    // Testo con annotazioni attive
                    this.createAnnotatedSegment(segmentText, [...activeAnnotations]);
                }
                currentPosition = event.position;
            }

            // Gestisci l'evento
            if (event.type === 'start') {
                activeAnnotations.push(event.annotation);
            } else {
                const index = activeAnnotations.findIndex(a => a.id === event.annotation.id);
                if (index > -1) {
                    activeAnnotations.splice(index, 1);
                }
            }
        });

        // Aggiungi testo rimanente
        if (currentPosition < textContent.length) {
            const remainingText = textContent.substring(currentPosition);
            this.container.appendChild(document.createTextNode(remainingText));
        }

        // Assicurati che il container sia selezionabile
        this.container.style.userSelect = 'text';
        this.container.style.webkitUserSelect = 'text';
        this.container.style.mozUserSelect = 'text';
        
        // IMPORTANTE: Riattiva i listener dopo aver ricreato il contenuto
        this.reattachEventListeners();
    }

    /**
     * Assicura che il container sia selezionabile per nuove annotazioni
     */
    ensureContainerSelectable() {
        // Ripristina le proprietà di selezione del testo
        this.container.style.userSelect = 'text';
        this.container.style.webkitUserSelect = 'text';
        this.container.style.mozUserSelect = 'text';
        this.container.style.msUserSelect = 'text';
        
        // Assicurati che il container mantenga il focus per la selezione
        this.container.setAttribute('tabindex', '0');
        
        // Riattiva la capacità di selezione
        this.container.style.cursor = 'text';
        
        // Force reflow per assicurarsi che i cambiamenti siano applicati
        this.container.offsetHeight;
        
        console.log('Container reso selezionabile per nuove annotazioni');
    }

    createAnnotatedSegment(text, annotations) {
        const span = document.createElement('span');
        span.className = 'annotation-highlight';
        span.textContent = text;
        span.style.cursor = 'pointer';
        span.style.position = 'relative';
        
        // IMPORTANTE: Non rendere selezionabile il contenuto delle annotazioni esistenti
        span.style.userSelect = 'none';
        span.style.webkitUserSelect = 'none';
        span.style.mozUserSelect = 'none';
        span.style.msUserSelect = 'none';

        if (annotations.length === 1) {
            // Singola annotazione
            const annotation = annotations[0];
            const label = this.labels.find(l => l.id === annotation.label_id);
            span.style.backgroundColor = this.hexToRgba(label?.color || '#007bff', 0.3);
            span.style.borderBottom = `2px solid ${label?.color || '#007bff'}`;
            span.dataset.annotationId = annotation.id;
            span.title = `${label?.name || 'Unknown'}: ${annotation.text_selection?.substring(0, 50) || text.substring(0, 50)}...`;
        } else {
            // Annotazioni multiple - crea stile sovrapposto
            span.style.background = this.createMultipleAnnotationBackground(annotations);
            span.style.borderBottom = `3px double #333`;
            span.dataset.multipleAnnotations = annotations.map(a => a.id).join(',');
            
            const labelNames = annotations.map(a => {
                const label = this.labels.find(l => l.id === a.label_id);
                return label?.name || 'Unknown';
            });
            span.title = `Multiple Labels: ${labelNames.join(', ')}`;
            
            // Aggiungi listener per click su annotazioni multiple
            span.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.showMultipleAnnotationsModal(annotations);
            });
        }

        this.container.appendChild(span);
    }

    createMultipleAnnotationBackground(annotations) {
        // Crea un gradiente con i colori delle diverse annotazioni
        const colors = annotations.map(annotation => {
            const label = this.labels.find(l => l.id === annotation.label_id);
            return this.hexToRgba(label?.color || '#007bff', 0.4);
        });
        
        if (colors.length === 2) {
            return `linear-gradient(90deg, ${colors[0]} 50%, ${colors[1]} 50%)`;
        } else if (colors.length === 3) {
            return `linear-gradient(90deg, ${colors[0]} 33%, ${colors[1]} 33%, ${colors[1]} 66%, ${colors[2]} 66%)`;
        } else {
            // Per più di 3 colori, usa strisce
            const percentage = 100 / colors.length;
            let gradient = 'linear-gradient(90deg, ';
            colors.forEach((color, index) => {
                const start = index * percentage;
                const end = (index + 1) * percentage;
                gradient += `${color} ${start}%, ${color} ${end}%`;
                if (index < colors.length - 1) gradient += ', ';
            });
            gradient += ')';
            return gradient;
        }
    }

    showMultipleAnnotationsModal(annotations) {
        // Crea e mostra un modal per gestire annotazioni multiple
        let modalContent = '<div class="mb-3"><h6>Annotazioni Multiple:</h6><ul>';
        annotations.forEach(annotation => {
            const label = this.labels.find(l => l.id === annotation.label_id);
            modalContent += `
                <li class="mb-2">
                    <span class="badge" style="background-color: ${label?.color || '#007bff'}">
                        ${label?.name || 'Unknown'}
                    </span>
                    <br><small class="text-muted">"${annotation.text_selection?.substring(0, 100) || ''}..."</small>
                    <button class="btn btn-sm btn-outline-danger ms-2" onclick="annotationSystem.deleteAnnotation(${annotation.id})">
                        <i class="bi bi-trash"></i>
                    </button>
                </li>
            `;
        });
        modalContent += '</ul></div>';
        
        document.getElementById('annotationDetailsContent').innerHTML = modalContent;
        this.detailsModal.show();
    }
    
    addAnnotationToList(annotation) {
        const annotationsList = document.getElementById('annotationsList');
        
        // Se la lista era vuota, rimuovi il messaggio placeholder
        const placeholder = annotationsList.querySelector('.text-center.text-muted');
        if (placeholder) {
            placeholder.remove();
        }
        
        const annotationItem = document.createElement('div');
        annotationItem.className = 'annotation-item p-2 border-bottom';
        annotationItem.dataset.annotationId = annotation.id;
        
        const label = this.labels.find(l => l.id == annotation.label_id);
        
        // Usa i dati dal server se disponibili, altrimenti cerca nei labels locali
        const labelName = annotation.label_name || (label ? label.name : `Etichetta ${annotation.label_id}`);
        const labelColor = annotation.label_color || (label ? label.color : '#007bff');
        
        // Determina il nome utente da mostrare
        let userDisplayName = 'Utente sconosciuto';
        if (annotation.user_id && annotation.user_id == window.currentUserId) {
            userDisplayName = window.currentUserName || 'Tu';
        } else if (annotation.user_name) {
            userDisplayName = annotation.user_name;
        } else if (annotation.user_id == window.currentUserId) {
            userDisplayName = 'Tu';
        }
        
        annotationItem.innerHTML = `
            <div class="d-flex align-items-start">
                <div class="label-color-indicator me-2 mt-1" 
                     style="width: 8px; height: 8px; background-color: ${labelColor}; border-radius: 50%;"></div>
                <div class="flex-grow-1">
                    <div class="fw-bold small">${labelName}</div>
                    <div class="text-truncate small text-muted" style="max-width: 200px;">
                        "${annotation.text_selection?.substring(0, 50) || 'Testo selezionato'}..."
                    </div>
                    <div class="small text-muted">
                        ${userDisplayName} - ${annotation.created_at || 'Adesso'}
                    </div>
                </div>
                <button class="btn btn-sm btn-outline-danger delete-annotation" 
                        data-annotation-id="${annotation.id}" title="Elimina">
                    <i class="bi bi-trash" style="font-size: 0.7rem;"></i>
                </button>
            </div>
        `;
        
        annotationsList.insertBefore(annotationItem, annotationsList.firstChild);
        
        // Aggiungi listener per eliminazione
        annotationItem.querySelector('.delete-annotation').addEventListener('click', (e) => {
            if (confirm('Sei sicuro di voler eliminare questa annotazione?')) {
                this.deleteAnnotation(annotation.id);
            }
        });
    }
    
    deleteAnnotation(annotationId) {
        fetch(`/text-documents/api/annotations/${annotationId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showToast(data.message, 'success');
                
                // Rimuovi dall'array locale
                this.annotations = this.annotations.filter(a => a.id != annotationId);
                
                // Ricostruisci il rendering
                this.renderAnnotations();
                
                // Rimuovi dalla lista delle annotazioni
                const listItem = document.querySelector(`.annotation-item[data-annotation-id="${annotationId}"]`);
                if (listItem) {
                    listItem.remove();
                }
                
                // Aggiorna contatori
                this.updateStats();
                
                // Se non ci sono più annotazioni, mostra il messaggio placeholder
                const annotationsList = document.getElementById('annotationsList');
                if (annotationsList && annotationsList.children.length === 0) {
                    annotationsList.innerHTML = `
                        <div class="p-3 text-center text-muted">
                            <i class="bi bi-info-circle"></i><br>
                            Nessuna annotazione presente.<br>
                            Seleziona del testo per iniziare.
                        </div>
                    `;
                }
                
            } else {
                this.showToast('Errore: ' + data.message, 'error');
            }
        })
        .catch(error => {
            console.error('Errore eliminazione annotazione:', error);
            this.showToast('Errore di connessione: ' + error.message, 'error');
        });
    }
    
    showAnnotationDetails(annotationId) {
        const annotation = this.annotations.find(a => a.id == annotationId);
        if (!annotation) return;
        
        const label = this.labels.find(l => l.id === annotation.label_id);
        
        const content = `
            <div class="row">
                <div class="col-md-6">
                    <h6>Etichetta</h6>
                    <div class="d-flex align-items-center mb-3">
                        <div class="label-color-indicator me-2" 
                             style="width: 16px; height: 16px; background-color: ${label?.color || '#007bff'}; border-radius: 3px;"></div>
                        <span class="fw-bold">${label?.name || 'Unknown'}</span>
                    </div>
                </div>
                <div class="col-md-6">
                    <h6>Informazioni</h6>
                    <p class="small mb-1"><strong>Utente:</strong> ${annotation.user?.username || 'Unknown'}</p>
                    <p class="small mb-1"><strong>Data:</strong> ${annotation.created_at}</p>
                    <p class="small mb-3"><strong>Posizione:</strong> ${annotation.start_position} - ${annotation.end_position}</p>
                </div>
            </div>
            
            <h6>Testo Selezionato</h6>
            <div class="bg-light p-3 rounded border mb-3" style="max-height: 200px; overflow-y: auto;">
                "${annotation.text_selection}"
            </div>
            
            ${annotation.context_before || annotation.context_after ? `
                <h6>Contesto</h6>
                <div class="bg-light p-3 rounded border small">
                    ${annotation.context_before ? `<span class="text-muted">${annotation.context_before}</span>` : ''}
                    <span class="fw-bold text-primary">${annotation.text_selection}</span>
                    ${annotation.context_after ? `<span class="text-muted">${annotation.context_after}</span>` : ''}
                </div>
            ` : ''}
        `;
        
        document.getElementById('annotationDetailsContent').innerHTML = content;
        this.detailsModal.show();
    }
    
    toggleLineNumbers() {
        this.lineNumbersVisible = !this.lineNumbersVisible;
        
        if (this.lineNumbersVisible) {
            this.addLineNumbers();
        } else {
            this.removeLineNumbers();
        }
    }
    
    addLineNumbers() {
        const lines = this.container.textContent.split('\\n');
        this.container.innerHTML = '';
        
        lines.forEach((line, index) => {
            const lineDiv = document.createElement('div');
            lineDiv.className = 'text-line';
            lineDiv.style.display = 'flex';
            
            const lineNumber = document.createElement('span');
            lineNumber.className = 'line-number';
            lineNumber.style.minWidth = '40px';
            lineNumber.style.color = '#6c757d';
            lineNumber.style.fontSize = '0.85em';
            lineNumber.style.marginRight = '10px';
            lineNumber.style.textAlign = 'right';
            lineNumber.textContent = index + 1;
            
            const lineContent = document.createElement('span');
            lineContent.className = 'line-content';
            lineContent.style.flex = '1';
            lineContent.textContent = line;
            
            lineDiv.appendChild(lineNumber);
            lineDiv.appendChild(lineContent);
            this.container.appendChild(lineDiv);
        });
    }
    
    removeLineNumbers() {
        // Ricostruisci il contenuto senza numeri di riga
        this.renderAnnotations();
    }
    
    clearSelection() {
        // Rimuovi tutte le selezioni
        if (window.getSelection) {
            window.getSelection().removeAllRanges();
        } else if (document.selection) {
            document.selection.empty();
        }
        
        // Reset variabili interne
        this.selectedText = null;
        this.selectedRange = null;
        
        // Chiudi eventuali modali aperti
        if (this.annotationModal) {
            this.annotationModal.hide();
        }
        
        // IMPORTANTE: Mantieni il container selezionabile per future annotazioni
        this.ensureContainerSelectable();
        
        console.log('Selezione pulita, container pronto per nuove annotazioni');
    }
    
    updateStats() {
        // Aggiorna i contatori nell'interfaccia
        const annotationsCount = this.annotations.length;
        
        // Trova l'elemento delle statistiche nelle info del documento
        const statsElements = document.querySelectorAll('.card-body .row .col-md-3');
        statsElements.forEach(element => {
            const strongElement = element.querySelector('strong');
            if (strongElement && strongElement.textContent.includes('Annotazioni:')) {
                // Aggiorna il conteggio delle annotazioni
                element.innerHTML = `<strong>Annotazioni:</strong> ${annotationsCount}`;
            }
        });
        
        // Aggiorna anche il titolo della sezione annotazioni
        const annotationsTitle = document.querySelector('.card-header h6');
        if (annotationsTitle && annotationsTitle.textContent.includes('Annotazioni')) {
            annotationsTitle.innerHTML = `
                <i class="bi bi-list-check"></i> Annotazioni (${annotationsCount})
            `;
        }
        
        // Aggiorna la sidebar delle etichette con i nuovi conteggi
        this.updateLabelsSidebar();
    }
    
    hexToRgba(hex, alpha) {
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }
    
    showToast(message, type = 'info') {
        // Implementazione toast semplice
        const alertClass = type === 'success' ? 'alert-success' : 
                          type === 'error' ? 'alert-danger' : 
                          type === 'warning' ? 'alert-warning' : 'alert-info';
        
        const toast = document.createElement('div');
        toast.className = `alert ${alertClass} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
        toast.style.zIndex = '9999';
        toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(toast);
        
        // Rimuovi automaticamente dopo 5 secondi
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 5000);
    }
    
    /**
     * Ricarica le etichette disponibili dal server
     */
    async reloadLabels() {
        try {
            const response = await fetch('/text-documents/api/labels', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Aggiorna l'array delle etichette
                this.labels = data.labels;
                
                // Aggiorna le annotazioni esistenti con i nuovi dati delle etichette
                this.updateExistingAnnotationsWithLabels();
                
                // Aggiorna la select del modal
                this.updateLabelSelect();
                
                // Aggiorna la lista delle etichette disponibili nella sidebar
                this.updateLabelsSidebar();
                
                // Ricostruisci la lista delle annotazioni per mostrare i nomi corretti
                this.rebuildAnnotationsList();
                
                return true;
            } else {
                console.error('Errore nel caricamento etichette:', data.message);
                return false;
            }
        } catch (error) {
            console.error('Errore di rete nel caricamento etichette:', error);
            return false;
        }
    }
    
    /**
     * Aggiorna le annotazioni esistenti con i nuovi dati delle etichette
     */
    updateExistingAnnotationsWithLabels() {
        this.annotations.forEach(annotation => {
            const label = this.labels.find(l => l.id == annotation.label_id);
            if (label) {
                annotation.label_name = label.name;
                annotation.label_color = label.color;
                annotation.label_category = label.category;
            }
            
            // Assicurati che ci siano dati utente di base
            if (!annotation.user_name && annotation.user_id == window.currentUserId) {
                annotation.user_name = window.currentUserName || 'Tu';
            }
            if (!annotation.user_name && annotation.user_id) {
                annotation.user_name = `Utente ${annotation.user_id}`;
            }
        });
    }
    
    /**
     * Ricostruisce completamente la lista delle annotazioni
     */
    rebuildAnnotationsList() {
        const annotationsList = document.getElementById('annotationsList');
        if (!annotationsList) return;
        
        // Svuota la lista
        annotationsList.innerHTML = '';
        
        // Ricostruisci ogni annotazione con i dati aggiornati
        this.annotations.forEach(annotation => {
            this.addAnnotationToList(annotation);
        });
    }
    
    /**
     * Aggiorna la select delle etichette nel modal
     */
    updateLabelSelect() {
        const labelSelect = document.getElementById('labelSelect');
        if (!labelSelect) return;
        
        // Mantieni il valore attualmente selezionato
        const currentValue = labelSelect.value;
        
        // Svuota e ricompila
        labelSelect.innerHTML = '<option value="">-- Seleziona un\'etichetta --</option>';
        
        // Raggruppa le etichette per categoria
        const categories = {};
        this.labels.forEach(label => {
            const categoryName = label.category || 'Senza categoria';
            if (!categories[categoryName]) {
                categories[categoryName] = [];
            }
            categories[categoryName].push(label);
        });
        
        // Crea optgroups per ogni categoria
        Object.keys(categories).sort().forEach(categoryName => {
            const optgroup = document.createElement('optgroup');
            optgroup.label = categoryName;
            
            categories[categoryName].forEach(label => {
                const option = document.createElement('option');
                option.value = label.id;
                option.textContent = label.name;
                if (label.description && label.description.length > 0) {
                    const desc = label.description.length > 50 ? label.description.substring(0, 50) + '...' : label.description;
                    option.textContent += ` - ${desc}`;
                }
                option.dataset.color = label.color || '#007bff';
                optgroup.appendChild(option);
            });
            
            labelSelect.appendChild(optgroup);
        });
        
        // Ripristina la selezione se ancora valida
        if (currentValue && this.labels.find(l => l.id == currentValue)) {
            labelSelect.value = currentValue;
        }
    }
    
    /**
     * Aggiorna la lista delle etichette nella sidebar
     */
    updateLabelsSidebar() {
        const labelsContainer = document.querySelector('.card-body[style*="max-height: 300px"]');
        if (!labelsContainer) return;
        
        if (this.labels.length === 0) {
            labelsContainer.innerHTML = `
                <p class="text-muted small">Nessuna etichetta disponibile.</p>
                <a href="/labels/create" class="btn btn-sm btn-outline-primary">
                    Crea Etichette
                </a>
            `;
            return;
        }
        
        // Calcola il conteggio delle etichette usate
        const labelCounts = this.calculateLabelCounts();
        
        labelsContainer.innerHTML = '';
        
        this.labels.forEach(label => {
            const count = labelCounts[label.id] || 0;
            
            const labelItem = document.createElement('div');
            labelItem.className = 'd-flex align-items-center mb-2 label-item';
            labelItem.dataset.labelId = label.id;
            labelItem.dataset.labelName = label.name;
            labelItem.dataset.labelColor = label.color || '#007bff';
            
            labelItem.innerHTML = `
                <div class="label-color-indicator me-2" 
                     style="width: 12px; height: 12px; background-color: ${label.color || '#007bff'}; border-radius: 2px;"></div>
                <span class="flex-grow-1">${label.name}</span>
                <small class="text-muted">${count}</small>
            `;
            
            labelsContainer.appendChild(labelItem);
        });
    }
    
    /**
     * Calcola quante volte ogni etichetta è stata usata
     */
    calculateLabelCounts() {
        const counts = {};
        this.annotations.forEach(annotation => {
            const labelId = annotation.label_id;
            counts[labelId] = (counts[labelId] || 0) + 1;
        });
        return counts;
    }
}
