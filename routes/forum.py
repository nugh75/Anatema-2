"""
Route per il sistema di forum degli annotatori.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from sqlalchemy import func, desc, or_
from models import db, ExcelFile, ForumCategory, ForumPost, ForumComment, TextCell
from datetime import datetime

forum_bp = Blueprint('forum', __name__, url_prefix='/forum')

@forum_bp.route('/')
@login_required
def index():
    """Pagina principale del forum - lista dei file Excel con i loro forum"""
    # Ottieni tutti i file Excel
    files = ExcelFile.query.order_by(ExcelFile.uploaded_at.desc()).all()
    
    # Calcola le statistiche per ogni file
    files_with_stats = []
    for file in files:
        # Conta le categorie per questo file
        category_count = ForumCategory.query.filter_by(excel_file_id=file.id).count()
        
        # Conta i post totali per questo file usando una query più semplice
        post_count = 0
        categories = ForumCategory.query.filter_by(excel_file_id=file.id).all()
        for category in categories:
            post_count += len(category.posts)
            
        files_with_stats.append((file, category_count, post_count))
    
    return render_template('forum/index.html', files_with_stats=files_with_stats)

@forum_bp.route('/file/<int:file_id>')
@login_required  
def file_forum(file_id):
    """Forum per un file Excel specifico"""
    excel_file = ExcelFile.query.get_or_404(file_id)
    
    # Ottieni tutte le categorie del forum per questo file
    categories = ForumCategory.query.filter_by(excel_file_id=file_id)\
                                   .order_by(ForumCategory.is_system.desc(), ForumCategory.created_at)\
                                   .all()
    
    # Se non ci sono categorie, crea quelle predefinite per le domande
    if not categories:
        create_default_categories(file_id)
        categories = ForumCategory.query.filter_by(excel_file_id=file_id)\
                                       .order_by(ForumCategory.is_system.desc(), ForumCategory.created_at)\
                                       .all()
    
    # Trova la categoria generale per i post diretti
    general_category = next((cat for cat in categories if cat.name.startswith("💬")), categories[0] if categories else None)
    
    # Statistiche generali
    total_posts = db.session.query(func.count(ForumPost.id))\
                           .join(ForumCategory)\
                           .filter(ForumCategory.excel_file_id == file_id)\
                           .scalar() or 0
    
    total_comments = db.session.query(func.count(ForumComment.id))\
                              .join(ForumPost)\
                              .join(ForumCategory)\
                              .filter(ForumCategory.excel_file_id == file_id)\
                              .scalar() or 0
    
    # Ultimi post (tutti i post, non divisi per categoria)
    recent_posts = db.session.query(ForumPost)\
                            .join(ForumCategory)\
                            .filter(ForumCategory.excel_file_id == file_id)\
                            .order_by(ForumPost.created_at.desc())\
                            .limit(10)\
                            .all()
    
    # Prepara statistiche per le categorie
    categories_with_stats = []
    for category in categories:
        post_count = len(category.posts)
        last_activity = category.posts[0].created_at if category.posts else None
        categories_with_stats.append((category, post_count, last_activity))
    
    return render_template('forum/file_forum.html', 
                         excel_file=excel_file,
                         categories=categories,
                         categories_with_stats=categories_with_stats,
                         general_category=general_category,
                         total_posts=total_posts,
                         total_comments=total_comments,
                         recent_posts=recent_posts)

@forum_bp.route('/category/<int:category_id>')
@login_required
def category(category_id):
    """Lista dei post in una categoria"""
    category = ForumCategory.query.get_or_404(category_id)
    
    # Paginazione
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    posts = ForumPost.query.filter_by(category_id=category_id)\
                          .order_by(ForumPost.is_pinned.desc(), ForumPost.created_at.desc())\
                          .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('forum/category.html', category=category, posts=posts)

@forum_bp.route('/post/<int:post_id>')
@login_required
def view_post(post_id):
    """Visualizza un post singolo con i commenti"""
    post = ForumPost.query.get_or_404(post_id)
    
    # Incrementa le visualizzazioni
    post.increment_views()
    
    # Ottieni i commenti (solo di primo livello, le reply sono annidate)
    comments = ForumComment.query.filter_by(post_id=post_id, parent_id=None)\
                                 .order_by(ForumComment.created_at.asc())\
                                 .all()
    
    return render_template('forum/post.html', post=post, comments=comments)

@forum_bp.route('/category/<int:category_id>/create_post', methods=['GET', 'POST'])
@login_required
def create_post(category_id):
    """Crea un nuovo post"""
    category = ForumCategory.query.get_or_404(category_id)
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        
        if not title or not content:
            flash('Titolo e contenuto sono obbligatori', 'error')
            return redirect(url_for('forum.create_post', category_id=category_id))
        
        # Crea il post
        post = ForumPost(
            title=title,
            content=content,
            category_id=category_id,
            author_id=current_user.id
        )
        
        db.session.add(post)
        db.session.commit()
        
        flash('Post creato con successo!', 'success')
        return redirect(url_for('forum.view_post', post_id=post.id))
    
    return render_template('forum/create_post.html', category=category)

@forum_bp.route('/file/<int:file_id>/create_post', methods=['GET', 'POST'])
@login_required
def create_post_direct(file_id):
    """Crea un nuovo post direttamente nel file, senza scegliere categoria"""
    excel_file = ExcelFile.query.get_or_404(file_id)
    
    # Trova o crea la categoria generale
    general_category = ForumCategory.query.filter_by(
        excel_file_id=file_id,
        name="💬 Discussioni"
    ).first()
    
    if not general_category:
        create_general_category(file_id)
        general_category = ForumCategory.query.filter_by(
            excel_file_id=file_id,
            name="💬 Discussioni"
        ).first()
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        
        if not title or not content:
            flash('Titolo e contenuto sono obbligatori', 'error')
            return redirect(url_for('forum.create_post_direct', file_id=file_id))
        
        # Crea il post nella categoria generale
        post = ForumPost(
            title=title,
            content=content,
            category_id=general_category.id,
            author_id=current_user.id
        )
        
        db.session.add(post)
        db.session.commit()
        
        flash('Post creato con successo!', 'success')
        return redirect(url_for('forum.view_post', post_id=post.id))
    
    return render_template('forum/create_post.html', 
                         category=general_category, 
                         excel_file=excel_file,
                         direct_mode=True)

@forum_bp.route('/file/<int:file_id>/regenerate_categories', methods=['POST'])
@login_required
def regenerate_categories(file_id):
    """Rigenera le categorie per un file Excel"""
    excel_file = ExcelFile.query.get_or_404(file_id)
    
    # Elimina le categorie esistenti di sistema (non quelle create dall'utente)
    ForumCategory.query.filter_by(excel_file_id=file_id, is_system=True).delete()
    db.session.commit()
    
    # Ricrea le categorie predefinite
    create_default_categories(file_id)
    
    flash(f'Categorie rigenerate con successo per il file {excel_file.original_filename}!', 'success')
    return redirect(url_for('forum.file_forum', file_id=file_id))

@forum_bp.route('/file/<int:file_id>/new_category', methods=['GET', 'POST'])
@login_required
def create_category(file_id):
    """Crea una nuova categoria personalizzata"""
    excel_file = ExcelFile.query.get_or_404(file_id)
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        icon = request.form.get('icon', 'bi-chat-dots')
        color = request.form.get('color', 'primary')
        
        if not name:
            flash('Il nome della categoria è obbligatorio', 'error')
            return redirect(url_for('forum.create_category', file_id=file_id))
        
        # Controlla che non esista già una categoria con lo stesso nome per questo file
        existing = ForumCategory.query.filter_by(
            excel_file_id=file_id,
            name=name
        ).first()
        
        if existing:
            flash('Esiste già una categoria con questo nome per questo file', 'error')
            return redirect(url_for('forum.create_category', file_id=file_id))
        
        # Crea la categoria
        category = ForumCategory(
            name=name,
            description=description,
            icon=icon,
            color=color,
            is_system=False,
            excel_file_id=file_id,
            created_by=current_user.id
        )
        
        db.session.add(category)
        db.session.commit()
        
        flash('Categoria creata con successo!', 'success')
        return redirect(url_for('forum.file_forum', file_id=file_id))
    
    return render_template('forum/create_category.html', excel_file=excel_file)

@forum_bp.route('/post/<int:post_id>/comment', methods=['POST'])
@login_required
def add_comment(post_id):
    """Aggiunge un commento a un post"""
    post = ForumPost.query.get_or_404(post_id)
    
    content = request.form.get('content', '').strip()
    parent_id = request.form.get('parent_id', type=int)
    
    if not content:
        flash('Il contenuto del commento è obbligatorio', 'error')
        return redirect(url_for('forum.view_post', post_id=post_id))
    
    comment = ForumComment(
        content=content,
        post_id=post_id,
        author_id=current_user.id,
        parent_id=parent_id
    )
    
    db.session.add(comment)
    db.session.commit()
    
    flash('Commento aggiunto con successo!', 'success')
    return redirect(url_for('forum.view_post', post_id=post_id))

@forum_bp.route('/search')
@login_required
def search():
    """Ricerca nel forum"""
    query = request.args.get('q', '').strip()
    file_id = request.args.get('file_id', type=int)
    
    excel_file = None
    if file_id:
        excel_file = ExcelFile.query.get_or_404(file_id)
    
    results = []
    
    if query:
        # Ricerca nei post
        post_query = ForumPost.query
        if file_id:
            post_query = post_query.join(ForumCategory).filter(ForumCategory.excel_file_id == file_id)
        
        posts = post_query.filter(
            or_(ForumPost.title.contains(query), ForumPost.content.contains(query))
        ).order_by(ForumPost.created_at.desc()).limit(20).all()
        
        for post in posts:
            results.append({
                'type': 'post',
                'title': post.title,
                'content': post.content[:200] + '...' if len(post.content) > 200 else post.content,
                'author': post.author.username,
                'created_at': post.created_at,
                'url': url_for('forum.view_post', post_id=post.id)
            })
    
    return render_template('forum/search_results.html', 
                         query=query, 
                         results=results, 
                         file_id=file_id, 
                         excel_file=excel_file)

def create_general_category(file_id):
    """Crea solo una categoria generale semplice per un file Excel"""
    excel_file = ExcelFile.query.get(file_id)
    if not excel_file:
        return
    
    # Solo categoria generale
    general_category = ForumCategory(
        name="💬 Discussioni",
        description="Tutte le discussioni su questo dataset",
        icon="bi-chat-dots",
        color="primary",
        is_system=True,
        excel_file_id=file_id,
        created_by=current_user.id
    )
    db.session.add(general_category)
    db.session.commit()

def create_default_categories(file_id):
    """Crea le categorie predefinite per un file Excel"""
    excel_file = ExcelFile.query.get(file_id)
    if not excel_file:
        return
    
    # Categoria generale
    general_category = ForumCategory(
        name="💬 Discussioni Generali",
        description="Discussioni generali su questo dataset",
        icon="bi-chat-dots",
        color="primary",
        is_system=True,
        excel_file_id=file_id,
        created_by=current_user.id
    )
    db.session.add(general_category)
    
    # Categorie per ogni domanda (colonna)
    questions = db.session.query(TextCell.column_name)\
                         .filter_by(excel_file_id=file_id)\
                         .distinct()\
                         .all()
    
    for question_tuple in questions:
        question_name = question_tuple[0]
        if question_name:  # Evita colonne senza nome
            category = ForumCategory(
                name=f"❓ {question_name[:60]}{'...' if len(question_name) > 60 else ''}",
                description=f"Discussioni sulla domanda: {question_name}",
                icon="bi-question-circle",
                color="info",
                is_system=True,
                excel_file_id=file_id,
                question_name=question_name,
                created_by=current_user.id
            )
            db.session.add(category)
    
    db.session.commit()
