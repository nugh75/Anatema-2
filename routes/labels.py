"""
Routes per la gestione delle etichette
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user

from models import Label, CellAnnotation, Category, db
from forms import LabelForm, CategoryForm

labels_bp = Blueprint('labels', __name__)

@labels_bp.route('/')
@login_required
def list_labels():
    """Lista di tutte le etichette"""
    page = request.args.get('page', 1, type=int)
    category_filter = request.args.get('category')
    show_inactive = request.args.get('show_inactive', False, type=bool)
    show_all = request.args.get('show_all', False, type=bool)

    # Query di base per etichette attive con JOIN esplicito per categoria
    query = Label.query.options(db.joinedload(Label.category_obj))
    if not show_inactive:
        query = query.filter_by(is_active=True)

    current_category = None
    if category_filter == 'none':
        query = query.filter(Label.category_id == None)
        current_category = 'none'
    elif category_filter and category_filter.isdigit():
        query = query.filter_by(category_id=int(category_filter))
        current_category = int(category_filter)

    # Gestione paginazione: se show_all è True, mostra tutto senza paginazione
    if show_all:
        labels = query.order_by(Label.name).all()
        # Simula oggetto paginazione per compatibilità template
        class FakePagination:
            def __init__(self, items):
                self.items = items
                self.page = 1
                self.pages = 1
                self.has_prev = False
                self.has_next = False
                self.prev_num = None
                self.next_num = None
                self.total = len(items)
                self.per_page = len(items)
        
        labels = FakePagination(labels)
    else:
        labels = query.order_by(Label.name).paginate(
            page=page, per_page=20, error_out=False
        )

    # Liste delle categorie attive per il filtro
    categories = Category.query.filter_by(is_active=True).order_by(Category.name).all()
    
    # Statistiche per etichette senza categoria
    uncategorized_count = Label.query.filter(Label.category_id.is_(None)).filter_by(is_active=True).count()

    return render_template('labels/list_labels.html', 
                         labels=labels,
                         categories=categories,
                         current_category=current_category,
                         show_inactive=show_inactive,
                         show_all=show_all,
                         uncategorized_count=uncategorized_count)

@labels_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_label():
    """Crea una nuova etichetta"""
    form = LabelForm()
    next_url = request.args.get('next') or request.form.get('next')
    
    if form.validate_on_submit():
        # Verifica se l'etichetta esiste già
        existing_label = Label.query.filter_by(name=form.name.data).first()
        
        if existing_label:
            flash('Un\'etichetta con questo nome esiste già!', 'error')
            return render_template('labels/create_label.html', form=form)
        
        # Gestione della categoria
        category_id = None
        if form.new_category.data:
            # Crea una nuova categoria se specificata
            new_category = Category(
                name=form.new_category.data.strip(),
                description=form.new_category_description.data,
                color='#6c757d',
                is_active=True
            )
            
            # Verifica se la categoria esiste già
            existing_category = Category.query.filter_by(name=form.new_category.data.strip()).first()
            if existing_category:
                category_id = existing_category.id
            else:
                db.session.add(new_category)
                db.session.flush()  # Per ottenere l'ID
                category_id = new_category.id
        elif form.category_id.data and form.category_id.data != 0:
            category_id = form.category_id.data
        
        # Determina il colore dell'etichetta
        label_color = form.color.data
        if category_id:
            # Se ha una categoria, usa il colore della categoria a meno che non sia stato specificato un colore diverso nel form
            category = Category.query.get(category_id)
            if category and (not form.color.data or form.color.data == '#007bff'):  # Se colore non specificato o è il default
                label_color = category.color
        
        # Crea l'etichetta
        label = Label(
            name=form.name.data.strip(),
            description=form.description.data,
            category_id=category_id,
            color=label_color,
            is_active=True
        )
        
        try:
            db.session.add(label)
            db.session.commit()
            flash('Etichetta creata con successo!', 'success')
            if next_url:
                return redirect(next_url)
            return redirect(url_for('labels.list_labels'))
        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante la creazione: {str(e)}', 'error')
    
    # Prepara i colori delle categorie per il template
    categories = Category.query.filter_by(is_active=True).all()
    category_colors = {cat.id: cat.color for cat in categories}
    
    return render_template('labels/create_label.html', form=form, category_colors=category_colors)

@labels_bp.route('/edit/<int:label_id>', methods=['GET', 'POST'])
@login_required
def edit_label(label_id):
    """Modifica un'etichetta esistente"""
    label = Label.query.get_or_404(label_id)
    form = LabelForm(obj=label)
    
    if form.validate_on_submit():
        # Verifica se un'altra etichetta ha già questo nome
        existing_label = Label.query.filter(
            Label.name == form.name.data,
            Label.id != label_id
        ).first()
        
        if existing_label:
            flash('Un\'altra etichetta con questo nome esiste già.', 'error')
        else:
            label.name = form.name.data
            label.description = form.description.data
            
            # Gestione categoria e colore
            old_category_id = label.category_id
            new_category_id = form.category_id.data
            label.category_id = new_category_id
            
            # Se la categoria è cambiata, aggiorna il colore se l'etichetta non ha un colore personalizzato
            if old_category_id != new_category_id:
                if new_category_id:
                    # Ha una nuova categoria: eredita il colore se non personalizzato
                    category = Category.query.get(new_category_id)
                    if category and not label.has_custom_color():
                        label.color = category.color
                # Se viene rimossa la categoria, mantiene il colore attuale
            else:
                # Se la categoria non è cambiata, aggiorna comunque il colore dal form
                label.color = form.color.data
            
            db.session.commit()
            
            flash('Etichetta aggiornata con successo!', 'success')
            return redirect(url_for('labels.list_labels'))
    
    return render_template('labels/edit_label.html', form=form, label=label)

@labels_bp.route('/delete/<int:label_id>', methods=['POST'])
@login_required
def delete_label(label_id):
    """Elimina un'etichetta (soft delete o eliminazione definitiva)"""
    label = Label.query.get_or_404(label_id)
    force_delete = request.form.get('force_delete') == 'true'
    
    # Conta le annotazioni associate
    annotation_count = CellAnnotation.query.filter_by(label_id=label_id).count()
    
    if annotation_count > 0 and not force_delete:
        # Solo soft delete
        label.is_active = False
        db.session.commit()
        flash(f'Etichetta "{label.name}" disattivata. Le annotazioni rimangono intatte.', 'success')
    elif annotation_count > 0 and force_delete:
        flash(f'Non è possibile eliminare l\'etichetta: è utilizzata in {annotation_count} annotazioni.', 'error')
    else:
        # Eliminazione definitiva se non ci sono annotazioni
        db.session.delete(label)
        db.session.commit()
        flash('Etichetta eliminata definitivamente.', 'success')
    
    return redirect(url_for('labels.list_labels'))

@labels_bp.route('/toggle-active/<int:label_id>', methods=['POST'])
@login_required
def toggle_label_active(label_id):
    """Attiva/disattiva un'etichetta"""
    label = Label.query.get_or_404(label_id)
    
    # Cambia lo stato
    label.is_active = not label.is_active
    status = "attivata" if label.is_active else "disattivata"
    
    db.session.commit()
    flash(f'Etichetta "{label.name}" {status} con successo.', 'success')
    
    return redirect(url_for('labels.list_labels', show_inactive=True))

@labels_bp.route('/api/search')
@login_required
def api_search_labels():
    """API per la ricerca di etichette (per autocompletamento)"""
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify([])
    
    labels = Label.query.options(db.joinedload(Label.category_obj))\
                       .filter(Label.name.contains(query))\
                       .filter_by(is_active=True)\
                       .order_by(Label.name)\
                       .limit(10)\
                       .all()
    
    return jsonify([{
        'id': label.id,
        'name': label.name,
        'description': label.description,
        'category': label.category_obj.name if label.category_obj else None,
        'color': label.get_effective_color()
    } for label in labels])

@labels_bp.route('/merge', methods=['GET', 'POST'])
@login_required
def merge_labels():
    """Unisce due o più etichette in una sola"""
    if request.method == 'POST':
        source_label_ids = request.form.getlist('source_labels')
        target_label_id = request.form.get('target_label')
        
        if not source_label_ids or not target_label_id:
            flash('Seleziona almeno un\'etichetta di origine e una di destinazione.', 'error')
            return redirect(url_for('labels.merge_labels'))
        
        # Converte gli ID in interi
        try:
            source_label_ids = [int(id) for id in source_label_ids]
            target_label_id = int(target_label_id)
        except ValueError:
            flash('ID etichette non validi.', 'error')
            return redirect(url_for('labels.merge_labels'))
        
        # Verifica che l'etichetta target non sia tra quelle di origine
        if target_label_id in source_label_ids:
            flash('L\'etichetta di destinazione non può essere tra quelle di origine.', 'error')
            return redirect(url_for('labels.merge_labels'))
        
        # Ottieni le etichette
        source_labels = Label.query.filter(Label.id.in_(source_label_ids)).all()
        target_label = Label.query.get_or_404(target_label_id)
        
        if len(source_labels) != len(source_label_ids):
            flash('Alcune etichette di origine non sono state trovate.', 'error')
            return redirect(url_for('labels.merge_labels'))
        
        try:
            # Conta le annotazioni che verranno spostate
            total_annotations = 0
            for source_label in source_labels:
                annotation_count = CellAnnotation.query.filter_by(label_id=source_label.id).count()
                total_annotations += annotation_count
            
            # Sposta tutte le annotazioni dalle etichette di origine a quella di destinazione
            for source_label in source_labels:
                CellAnnotation.query.filter_by(label_id=source_label.id)\
                                  .update({'label_id': target_label_id})
            
            # Elimina le etichette di origine
            source_names = [label.name for label in source_labels]
            for source_label in source_labels:
                db.session.delete(source_label)
            
            db.session.commit()
            
            flash(f'Merge completato! {total_annotations} annotazioni spostate da {", ".join(source_names)} a "{target_label.name}".', 'success')
            return redirect(url_for('labels.list_labels'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante il merge: {str(e)}', 'error')
            return redirect(url_for('labels.merge_labels'))
    
    # GET: mostra il form di merge
    labels = Label.query.options(db.joinedload(Label.category_obj)).order_by(Label.category, Label.name).all()
    
    # Raggruppa le etichette per categoria
    labels_by_category = {}
    for label in labels:
        category = label.category_obj.name if label.category_obj else 'Senza categoria'
        if category not in labels_by_category:
            labels_by_category[category] = []
        
        # Conta le annotazioni per ogni etichetta
        annotation_count = CellAnnotation.query.filter_by(label_id=label.id).count()
        label_data = {
            'id': label.id,
            'name': label.name,
            'description': label.description,
            'color': label.get_effective_color(),
            'annotation_count': annotation_count
        }
        labels_by_category[category].append(label_data)
    
    return render_template('labels/merge_labels.html', labels_by_category=labels_by_category)

@labels_bp.route('/api/suggest-merge')
@login_required
def api_suggest_merge():
    """API per suggerire etichette simili che potrebbero essere unite"""
    # Trova etichette con nomi simili o nella stessa categoria
    labels = Label.query.options(db.joinedload(Label.category_obj)).order_by(Label.category, Label.name).all()
    
    suggestions = []
    
    # Raggruppa per categoria
    category_groups = {}
    for label in labels:
        category = label.category_obj.name if label.category_obj else 'Senza categoria'
        if category not in category_groups:
            category_groups[category] = []
        category_groups[category].append(label)
    
    # Trova etichette con nomi simili nella stessa categoria
    for category, cat_labels in category_groups.items():
        if len(cat_labels) > 1:
            # Cerca nomi simili (case-insensitive, ignora spazi)
            normalized_names = {}
            for label in cat_labels:
                normalized = label.name.lower().replace(' ', '').replace('-', '').replace('_', '')
                if normalized not in normalized_names:
                    normalized_names[normalized] = []
                normalized_names[normalized].append(label)
            
            # Trova gruppi con più di un'etichetta
            for normalized, group_labels in normalized_names.items():
                if len(group_labels) > 1:
                    suggestion = {
                        'category': category,
                        'reason': 'Nomi simili',
                        'labels': [{
                            'id': label.id,
                            'name': label.name,
                            'description': label.description,
                            'color': label.get_effective_color(),
                            'annotation_count': CellAnnotation.query.filter_by(label_id=label.id).count()
                        } for label in group_labels]
                    }
                    suggestions.append(suggestion)
    
    return jsonify(suggestions)

@labels_bp.route('/categories')
@login_required
def list_categories():
    """Lista di tutte le categorie"""
    page = request.args.get('page', 1, type=int)
    show_inactive = request.args.get('show_inactive', False, type=bool)
    
    # Query di base per categorie attive
    query = Category.query
    if not show_inactive:
        query = query.filter_by(is_active=True)
    
    categories = query.order_by(Category.name).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Conta le etichette per categoria (solo quelle attive)
    category_stats = {}
    for category in categories.items:
        category_stats[category.id] = Label.query.filter_by(category_id=category.id, is_active=True).count()
    
    return render_template('labels/list_categories.html', 
                         categories=categories,
                         category_stats=category_stats,
                         show_inactive=show_inactive)

@labels_bp.route('/categories/create', methods=['GET', 'POST'])
@login_required
def create_category():
    """Crea una nuova categoria"""
    if not current_user.is_admin:
        flash('Non hai i permessi per questa operazione.', 'error')
        return redirect(url_for('labels.list_categories'))
    
    form = CategoryForm()
    
    if form.validate_on_submit():
        # Verifica se la categoria esiste già
        existing_category = Category.query.filter_by(name=form.name.data).first()
        
        if existing_category:
            flash('Una categoria con questo nome esiste già!', 'error')
        else:
            category = Category(
                name=form.name.data,
                description=form.description.data,
                color=form.color.data,
                is_active=True
            )
            
            db.session.add(category)
            db.session.commit()
            
            flash('Categoria creata con successo!', 'success')
            return redirect(url_for('labels.list_categories'))
    
    return render_template('labels/create_category.html', form=form)

@labels_bp.route('/categories/edit/<int:category_id>', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
    """Modifica una categoria"""
    if not current_user.is_admin:
        flash('Non hai i permessi per questa operazione.', 'error')
        return redirect(url_for('labels.list_categories'))
    
    category = Category.query.get_or_404(category_id)
    form = CategoryForm(obj=category)
    
    if form.validate_on_submit():
        # Verifica se un'altra categoria ha già questo nome
        existing_category = Category.query.filter(
            Category.name == form.name.data,
            Category.id != category_id
        ).first()
        
        if existing_category:
            flash('Un\'altra categoria con questo nome esiste già.', 'error')
        else:
            category.name = form.name.data
            category.description = form.description.data
            category.color = form.color.data
            
            db.session.commit()
            
            flash('Categoria aggiornata con successo!', 'success')
            return redirect(url_for('labels.list_categories'))
    
    return render_template('labels/edit_category.html', form=form, category=category)

@labels_bp.route('/categories/delete/<int:category_id>', methods=['POST'])
@login_required
def delete_category(category_id):
    """Elimina una categoria con migrazione automatica delle etichette"""
    if not current_user.is_admin:
        flash('Non hai i permessi per questa operazione.', 'error')
        return redirect(url_for('labels.list_categories'))
    
    category = Category.query.get_or_404(category_id)
    force_delete = request.form.get('force_delete') == 'true'
    
    # Conta le etichette associate (tutte, attive e inattive)
    all_labels = Label.query.filter_by(category_id=category_id).all()
    active_label_count = Label.query.filter_by(category_id=category_id, is_active=True).count()
    
    try:
        if len(all_labels) > 0:
            # MIGRAZIONE AUTOMATICA: Sposta tutte le etichette in "Nessuna categoria"
            migrated_labels = []
            for label in all_labels:
                label.category_id = None
                migrated_labels.append(label.name)
            
            # Elimina la categoria
            db.session.delete(category)
            db.session.commit()
            
            # REFRESH: Aggiorna la sessione per riflettere i cambiamenti
            db.session.expire_all()
            
            # Messaggio informativo dettagliato
            flash(f'Categoria "{category.name}" eliminata con successo. {len(migrated_labels)} etichette spostate in "Nessuna categoria": {", ".join(migrated_labels[:5])}{"..." if len(migrated_labels) > 5 else ""}.', 'success')
            
            # Suggerimento per gestire le etichette migrate
            if active_label_count > 0:
                flash(f'Suggerimento: Puoi ora gestire le {active_label_count} etichette attive usando il filtro "Nessuna categoria" nella pagina etichette.', 'info')
        else:
            # Categoria vuota: eliminazione diretta
            db.session.delete(category)
            db.session.commit()
            flash(f'Categoria "{category.name}" eliminata definitivamente (era vuota).', 'success')
            
    except Exception as e:
        db.session.rollback()
        flash(f'Errore durante l\'eliminazione: {str(e)}', 'error')
    
    return redirect(url_for('labels.list_categories'))

@labels_bp.route('/categories/toggle-active/<int:category_id>', methods=['POST'])
@login_required
def toggle_category_active(category_id):
    """Attiva/disattiva una categoria"""
    if not current_user.is_admin:
        flash('Non hai i permessi per questa operazione.', 'error')
        return redirect(url_for('labels.list_categories'))
    
    category = Category.query.get_or_404(category_id)
    
    # Cambia lo stato
    category.is_active = not category.is_active
    status = "attivata" if category.is_active else "disattivata"
    
    db.session.commit()
    flash(f'Categoria "{category.name}" {status} con successo.', 'success')
    
    return redirect(url_for('labels.list_categories', show_inactive=True))

@labels_bp.route('/categories/bulk-actions', methods=['POST'])
@login_required
def bulk_category_actions():
    """Gestisce le azioni in blocco per le categorie"""
    if not current_user.is_admin:
        flash('Non hai i permessi per questa operazione.', 'error')
        return redirect(url_for('labels.list_categories'))
    
    action = request.form.get('action')
    selected_categories = request.form.getlist('selected_categories')
    
    if not selected_categories:
        flash('Nessuna categoria selezionata.', 'warning')
        return redirect(url_for('labels.list_categories'))
    
    if action == 'delete':
        return bulk_delete_categories(selected_categories)
    elif action == 'merge':
        target_category_id = request.form.get('target_category_id')
        return bulk_merge_categories(selected_categories, target_category_id)
    else:
        flash('Azione non riconosciuta.', 'error')
        return redirect(url_for('labels.list_categories'))

@labels_bp.route('/bulk-actions', methods=['POST'])
@login_required
def bulk_actions():
    """Gestisce le azioni in blocco per le etichette"""
    if not current_user.is_admin:
        flash('Non hai i permessi per questa operazione.', 'error')
        return redirect(url_for('labels.list_labels'))
    
    action = request.form.get('action')
    selected_labels = request.form.getlist('selected_labels')
    
    if not selected_labels:
        flash('Nessuna etichetta selezionata.', 'warning')
        return redirect(url_for('labels.list_labels'))
    
    if action == 'delete':
        return bulk_delete_labels(selected_labels)
    elif action == 'assign_category':
        category_id = request.form.get('category_id')
        return bulk_assign_category(selected_labels, category_id)
    elif action == 'change_color':
        color = request.form.get('color')
        return bulk_change_color(selected_labels, color)
    else:
        flash('Azione non riconosciuta.', 'error')
        return redirect(url_for('labels.list_labels'))

def bulk_delete_labels(label_ids):
    """Elimina più etichette in blocco"""
    try:
        labels_to_delete = Label.query.filter(Label.id.in_(label_ids)).all()
        labels_with_annotations = []
        labels_to_remove = []
        
        for label in labels_to_delete:
            annotation_count = CellAnnotation.query.filter_by(label_id=label.id).count()
            if annotation_count > 0:
                labels_with_annotations.append(f"{label.name} ({annotation_count} annotazioni)")
            else:
                labels_to_remove.append(label)
        
        if labels_with_annotations:
            flash(f'Alcune etichette non possono essere eliminate perché in uso: {", ".join(labels_with_annotations)}', 'warning')
        
        if labels_to_remove:
            for label in labels_to_remove:
                db.session.delete(label)
            db.session.commit()
            flash(f'Eliminate {len(labels_to_remove)} etichette con successo.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Errore durante l\'eliminazione: {str(e)}', 'error')
    
    return redirect(url_for('labels.list_labels'))

def bulk_assign_category(label_ids, category_id):
    """Assegna una categoria a più etichette"""
    try:
        category_id = int(category_id) if category_id and category_id != '0' else None
        
        labels = Label.query.filter(Label.id.in_(label_ids)).all()
        for label in labels:
            label.category_id = category_id
        
        db.session.commit()
        category_name = Category.query.get(category_id).name if category_id else "Nessuna categoria"
        flash(f'Assegnata la categoria "{category_name}" a {len(labels)} etichette.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Errore durante l\'assegnazione: {str(e)}', 'error')
    
    return redirect(url_for('labels.list_labels'))

def bulk_change_color(label_ids, color):
    """Cambia il colore di più etichette"""
    try:
        if not color:
            flash('Colore non specificato.', 'error')
            return redirect(url_for('labels.list_labels'))
        
        labels = Label.query.filter(Label.id.in_(label_ids)).all()
        for label in labels:
            label.color = color
        
        db.session.commit()
        flash(f'Cambiato il colore di {len(labels)} etichette.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Errore durante il cambio colore: {str(e)}', 'error')
    
    return redirect(url_for('labels.list_labels'))

def bulk_delete_categories(category_ids):
    """Elimina più categorie in blocco con migrazione automatica delle etichette"""
    try:
        categories_to_delete = Category.query.filter(Category.id.in_(category_ids)).all()
        
        total_migrated_labels = 0
        deleted_categories = []
        
        for category in categories_to_delete:
            # Trova tutte le etichette della categoria
            labels_in_category = Label.query.filter_by(category_id=category.id).all()
            
            # Migra le etichette a "Nessuna categoria"
            for label in labels_in_category:
                label.category_id = None
                total_migrated_labels += 1
            
            deleted_categories.append(category.name)
            db.session.delete(category)
        
        db.session.commit()
        
        # REFRESH: Aggiorna la sessione per riflettere i cambiamenti
        db.session.expire_all()
        
        if total_migrated_labels > 0:
            flash(f'Eliminate {len(deleted_categories)} categorie: {", ".join(deleted_categories)}. {total_migrated_labels} etichette spostate in "Nessuna categoria".', 'success')
            flash('Suggerimento: Usa il filtro "Nessuna categoria" per gestire le etichette migrate.', 'info')
        else:
            flash(f'Eliminate {len(deleted_categories)} categorie vuote con successo.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Errore durante l\'eliminazione: {str(e)}', 'error')
    
    return redirect(url_for('labels.list_categories'))

def bulk_merge_categories(category_ids, target_category_id):
    """Unisce più categorie in una sola"""
    try:
        if not target_category_id:
            flash('Categoria di destinazione non specificata.', 'error')
            return redirect(url_for('labels.list_categories'))
        
        target_category = Category.query.get_or_404(target_category_id)
        source_categories = Category.query.filter(Category.id.in_(category_ids)).all()
        
        # Sposta tutte le etichette dalla categoria sorgente a quella di destinazione
        moved_labels = 0
        for source_category in source_categories:
            if source_category.id == target_category.id:
                continue
            
            labels = Label.query.filter_by(category_id=source_category.id).all()
            for label in labels:
                label.category_id = target_category.id
                moved_labels += 1
            
            db.session.delete(source_category)
        
        db.session.commit()
        flash(f'Unite {len(source_categories)} categorie in "{target_category.name}". Spostate {moved_labels} etichette.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Errore durante l\'unione: {str(e)}', 'error')
    
    return redirect(url_for('labels.list_categories'))

# API per l'integrazione con l'AI

@labels_bp.route('/api/labels-for-ai')
@login_required
def api_labels_for_ai():
    """API per ottenere tutte le etichette per l'AI"""
    labels = Label.query.options(db.joinedload(Label.category_obj)).filter_by(is_active=True).order_by(Label.name).all()
    
    labels_data = []
    for label in labels:
        category_name = label.category_obj.name if label.category_obj else 'Senza categoria'
        labels_data.append({
            'id': label.id,
            'name': label.name,
            'description': label.description,
            'category': category_name,
            'color': label.get_effective_color()
        })
    
    return jsonify(labels_data)

@labels_bp.route('/api/categories-for-ai')
@login_required
def api_categories_for_ai():
    """API per ottenere tutte le categorie per l'AI"""
    categories = Category.query.filter_by(is_active=True).order_by(Category.name).all()
    
    categories_data = []
    for category in categories:
        labels_in_category = Label.query.filter_by(category_id=category.id, is_active=True).all()
        categories_data.append({
            'id': category.id,
            'name': category.name,
            'description': category.description,
            'color': category.color,
            'labels': [{'id': label.id, 'name': label.name, 'description': label.description} for label in labels_in_category]
        })
    
    return jsonify(categories_data)


# NUOVE ROUTES PER GESTIONE COLORI

@labels_bp.route('/categories/colors')
@login_required
def manage_category_colors():
    """Pagina per gestire i colori delle categorie con slider"""
    if not current_user.is_admin:
        flash('Non hai i permessi per questa operazione.', 'error')
        return redirect(url_for('labels.list_categories'))
    
    categories = Category.query.filter_by(is_active=True).order_by(Category.name).all()
    
    # Calcola statistiche per ogni categoria
    category_stats = {}
    for category in categories:
        category_stats[category.id] = {
            'label_count': Label.query.filter_by(category_id=category.id, is_active=True).count(),
            'annotation_count': db.session.query(CellAnnotation).join(Label).filter(
                Label.category_id == category.id,
                Label.is_active == True
            ).count()
        }
    
    return render_template('labels/category_colors.html', 
                         categories=categories,
                         category_stats=category_stats)

@labels_bp.route('/test-csrf')
@login_required
def test_csrf():
    """Route di test per il CSRF"""
    return render_template('labels/test_csrf.html')

@labels_bp.route('/categories/colors/update', methods=['POST'])
@login_required
def update_category_colors():
    """Aggiorna i colori delle categorie"""
    if not current_user.is_admin:
        flash('Non hai i permessi per questa operazione.', 'error')
        return redirect(url_for('labels.list_categories'))
    
    try:
        # Processa i dati inviati dal form
        updated_count = 0
        errors = []
        
        for key, value in request.form.items():
            if key.startswith('color_'):
                category_id = int(key.replace('color_', ''))
                category = Category.query.get_or_404(category_id)
                
                try:
                    # Valida e aggiorna il colore
                    category.update_color(value)
                    updated_count += 1
                except ValueError as e:
                    errors.append(f"Categoria '{category.name}': {str(e)}")
        
        if errors:
            for error in errors:
                flash(error, 'error')
        
        if updated_count > 0:
            db.session.commit()
            flash(f'Aggiornati i colori di {updated_count} categorie.', 'success')
        else:
            flash('Nessun colore è stato modificato.', 'info')
    
    except Exception as e:
        db.session.rollback()
        flash(f'Errore durante l\'aggiornamento: {str(e)}', 'error')
    
    return redirect(url_for('labels.manage_category_colors'))

@labels_bp.route('/categories/colors/sync', methods=['POST'])
@login_required
def sync_label_colors():
    """Sincronizza i colori delle etichette con le categorie"""
    if not current_user.is_admin:
        flash('Non hai i permessi per questa operazione.', 'error')
        return redirect(url_for('labels.list_categories'))
    
    try:
        # Verifica se forzare la sincronizzazione
        force_sync = request.form.get('force_sync') == 'true'
        
        # Trova tutte le etichette che hanno una categoria
        labels_with_category = Label.query.filter(Label.category_id.isnot(None)).all()
        
        updated_count = 0
        updated_labels = []
        
        for label in labels_with_category:
            if label.category_obj:
                old_color = label.color
                # Se force_sync è True, aggiorna tutte le etichette
                # Altrimenti solo quelle che non hanno un colore personalizzato
                if force_sync or not label.has_custom_color():
                    label.color = label.category_obj.color
                    updated_count += 1
                    updated_labels.append({
                        'name': label.name,
                        'old_color': old_color,
                        'new_color': label.color,
                        'category': label.category_obj.name
                    })
        
        if updated_count > 0:
            db.session.commit()
            sync_type = "forzata" if force_sync else "standard"
            flash(f'Sincronizzazione {sync_type} completata: aggiornate {updated_count} etichette con i colori delle categorie.', 'success')
        else:
            flash('Tutte le etichette sono già sincronizzate.', 'info')
    
    except Exception as e:
        db.session.rollback()
        flash(f'Errore durante la sincronizzazione: {str(e)}', 'error')
    
    return redirect(url_for('labels.manage_category_colors'))

@labels_bp.route('/api/sync-colors', methods=['POST'])
@login_required
def api_sync_label_colors():
    """API endpoint per sincronizzare i colori delle etichette con le categorie"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Non hai i permessi per questa operazione.'}), 403
    
    try:
        # Verifica se forzare la sincronizzazione
        force_sync = request.json.get('force_sync', False) if request.is_json else request.form.get('force_sync') == 'true'
        
        # Trova tutte le etichette che hanno una categoria
        labels_with_category = Label.query.filter(Label.category_id.isnot(None)).all()
        
        updated_count = 0
        updated_labels = []
        skipped_labels = []
        
        for label in labels_with_category:
            if label.category_obj:
                old_color = label.color
                # Se force_sync è True, aggiorna tutte le etichette
                # Altrimenti solo quelle che non hanno un colore personalizzato
                if force_sync or not label.has_custom_color():
                    label.color = label.category_obj.color
                    updated_count += 1
                    updated_labels.append({
                        'id': label.id,
                        'name': label.name,
                        'old_color': old_color,
                        'new_color': label.color,
                        'category': label.category_obj.name,
                        'reason': 'forced' if force_sync else 'no_custom_color'
                    })
                else:
                    skipped_labels.append({
                        'id': label.id,
                        'name': label.name,
                        'color': label.color,
                        'category': label.category_obj.name,
                        'reason': 'has_custom_color'
                    })
        
        if updated_count > 0:
            db.session.commit()
        
        sync_type = "forzata" if force_sync else "standard"
        
        return jsonify({
            'success': True,
            'updated_count': updated_count,
            'total_count': len(labels_with_category),
            'sync_type': sync_type,
            'updated_labels': updated_labels,
            'skipped_labels': skipped_labels,
            'message': f'Sincronizzazione {sync_type} completata: aggiornate {updated_count} etichette.'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Errore durante la sincronizzazione: {str(e)}'
        }), 500

@labels_bp.route('/categories/colors/reset/<int:category_id>', methods=['POST'])
@login_required
def reset_category_color(category_id):
    """Reset del colore di una categoria al default della palette"""
    if not current_user.is_admin:
        flash('Non hai i permessi per questa operazione.', 'error')
        return redirect(url_for('labels.list_categories'))
    
    try:
        category = Category.query.get_or_404(category_id)
        
        # Assegna un nuovo colore dalla palette
        new_color = Category.assign_next_color()
        category.update_color(new_color)
        
        db.session.commit()
        flash(f'Colore della categoria "{category.name}" ripristinato.', 'success')
    
    except Exception as e:
        db.session.rollback()
        flash(f'Errore durante il ripristino: {str(e)}', 'error')
    
    return redirect(url_for('labels.manage_category_colors'))

@labels_bp.route('/api/category-color-preview')
@login_required
def api_category_color_preview():
    """API per l'anteprima dei colori delle categorie"""
    category_id = request.args.get('category_id', type=int)
    hue = request.args.get('hue', type=float)
    saturation = request.args.get('saturation', type=float)
    lightness = request.args.get('lightness', type=float)
    
    if not all([category_id, hue is not None, saturation is not None, lightness is not None]):
        return jsonify({'error': 'Parametri mancanti'}), 400
    
    try:
        from utils.color_palette import ColorPalette
        
        # Converti HSL in esadecimale
        new_color = ColorPalette.hsl_to_hex(hue, saturation / 100, lightness / 100)
        text_color = ColorPalette.get_contrasting_text_color(new_color)
        
        # Trova alcune etichette di esempio per l'anteprima
        category = Category.query.get_or_404(category_id)
        sample_labels = Label.query.filter_by(category_id=category_id, is_active=True).limit(3).all()
        
        return jsonify({
            'color': new_color,
            'text_color': text_color,
            'sample_labels': [{'id': label.id, 'name': label.name} for label in sample_labels],
            'valid': ColorPalette.validate_color(new_color)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
