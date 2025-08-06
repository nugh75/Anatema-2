from flask import Blueprint, render_template, request
from flask_login import login_required
from models import ExcelFile, TextCell, Label, CellAnnotation, db
from collections import defaultdict

file_annotation_bp = Blueprint('file_annotation', __name__)

@file_annotation_bp.route('/file/<int:file_id>/annota')
@login_required
def file_annota(file_id):
    """Pagina unificata: visualizzazione e annotazione celle per file, con filtri e tabella riga/colonna o per domanda"""
    mode = request.args.get('mode', 'view')  # 'view', 'annotate', 'per_domanda'
    sheet = request.args.get('sheet', '')
    column = request.args.get('column', '')
    annotated_only = request.args.get('annotated_only', '')

    excel_file = ExcelFile.query.get_or_404(file_id)
    query = TextCell.query.filter_by(excel_file_id=file_id)

    if sheet:
        query = query.filter_by(sheet_name=sheet)
    if column:
        query = query.filter_by(column_name=column)
    if annotated_only == '1':
        query = query.join(CellAnnotation)
    elif annotated_only == '0':
        query = query.outerjoin(CellAnnotation).filter(CellAnnotation.id is None)

    cells = query.order_by(TextCell.row_index, TextCell.column_index).all()

    # Ricava tutte le righe e colonne presenti
    row_indices = sorted({cell.row_index for cell in cells})
    col_names = sorted({cell.column_name for cell in cells})

    # Organizza le celle in una matrice [riga][colonna]
    cell_matrix = {row: {col: None for col in col_names} for row in row_indices}
    for cell in cells:
        cell_matrix[cell.row_index][cell.column_name] = cell

    # Raggruppamento per domanda/colonna
    cells_by_question = defaultdict(list)
    for cell in cells:
        cells_by_question[cell.column_name].append(cell)

    # Per i filtri
    sheets = db.session.query(TextCell.sheet_name).filter_by(excel_file_id=file_id).distinct().all()
    sheet_names = [s[0] for s in sheets]
    columns = db.session.query(TextCell.column_name).filter_by(excel_file_id=file_id).distinct().all()
    column_names = [c[0] for c in columns if c[0]]

    return render_template('file_annotation/file_annota.html',
        excel_file=excel_file,
        cell_matrix=cell_matrix,
        row_indices=row_indices,
        col_names=col_names,
        mode=mode,
        sheet_names=sheet_names,
        column_names=column_names,
        current_sheet=sheet,
        current_column=column,
        annotated_only=annotated_only,
        cells_by_question=cells_by_question
    )
