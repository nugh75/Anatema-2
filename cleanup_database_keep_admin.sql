-- Script SQL per pulire il database mantenendo solo gli amministratori
-- Mantiene tutte le tabelle ma rimuove tutti i dati tranne gli utenti con ruolo 'amministratore'

-- Disabilita i vincoli di chiave esterna temporaneamente
PRAGMA foreign_keys = OFF;

-- Inizia una transazione per garantire atomicità
BEGIN TRANSACTION;

-- Salva gli ID degli amministratori
CREATE TEMP TABLE temp_admin_ids AS 
SELECT id FROM user WHERE role = 'amministratore';

-- Elimina tutti i dati dalle tabelle dipendenti (ordine importante per i vincoli)

-- Tabelle del diario
DELETE FROM diary_attachments;
DELETE FROM diary_entries WHERE author_id NOT IN (SELECT id FROM temp_admin_ids);

-- Tabelle delle decisioni/votazioni
DELETE FROM label_decision_comment;
DELETE FROM label_decision_vote;
DELETE FROM label_grouping_proposal;
DELETE FROM decision_session WHERE created_by NOT IN (SELECT id FROM temp_admin_ids);

-- Tabelle del forum
DELETE FROM forum_comment;
DELETE FROM forum_post;
DELETE FROM forum_category WHERE created_by NOT IN (SELECT id FROM temp_admin_ids);

-- Tabelle delle annotazioni sui documenti di testo
DELETE FROM text_annotations;
DELETE FROM text_documents WHERE user_id NOT IN (SELECT id FROM temp_admin_ids);

-- Tabelle dei template prompt
DELETE FROM prompt_templates;
DELETE FROM prompt_template;
DELETE FROM ai_prompt_template;

-- Tabelle delle annotazioni delle celle
DELETE FROM annotation_action WHERE performed_by NOT IN (SELECT id FROM temp_admin_ids) 
    AND target_user_id NOT IN (SELECT id FROM temp_admin_ids);
DELETE FROM cell_annotation WHERE user_id NOT IN (SELECT id FROM temp_admin_ids);

-- Tabelle dei modelli AI
DELETE FROM ollama_model;
DELETE FROM openrouter_model;
DELETE FROM open_router_model;
DELETE FROM ai_configuration;

-- Tabelle dei dati principali
DELETE FROM text_cell;
DELETE FROM excel_file WHERE uploaded_by NOT IN (SELECT id FROM temp_admin_ids);

-- Tabelle delle etichette e categorie
DELETE FROM label;
DELETE FROM category;

-- Rimuovi tutti gli utenti tranne gli amministratori
DELETE FROM user WHERE role != 'amministratore';

-- Pulisci la tabella delle sequenze per reimpostare gli auto-increment
DELETE FROM sqlite_sequence WHERE name NOT IN ('user');

-- Opzionale: reimposta i contatori degli auto-increment per le tabelle svuotate
UPDATE sqlite_sequence SET seq = 0 WHERE name IN (
    'diary_attachments', 'diary_entries', 'label_decision_comment', 
    'label_decision_vote', 'label_grouping_proposal', 'decision_session',
    'forum_comment', 'forum_post', 'forum_category', 'text_annotations',
    'text_documents', 'prompt_templates', 'prompt_template', 'ai_prompt_template',
    'annotation_action', 'cell_annotation', 'ollama_model', 'openrouter_model',
    'open_router_model', 'ai_configuration', 'text_cell', 'excel_file',
    'label', 'category'
);

-- Rimuovi la tabella temporanea
DROP TABLE temp_admin_ids;

-- Conferma la transazione
COMMIT;

-- Riabilita i vincoli di chiave esterna
PRAGMA foreign_keys = ON;

-- Verifica il risultato mostrando gli utenti rimasti
SELECT 'Utenti rimasti dopo la pulizia:' as info;
SELECT id, username, email, role FROM user;

-- Mostra un riepilogo delle tabelle svuotate
SELECT 'Riepilogo pulizia completata:' as info;
SELECT 
    (SELECT COUNT(*) FROM user) as utenti_rimasti,
    (SELECT COUNT(*) FROM excel_file) as file_excel,
    (SELECT COUNT(*) FROM text_cell) as celle_di_testo,
    (SELECT COUNT(*) FROM label) as etichette,
    (SELECT COUNT(*) FROM category) as categorie,
    (SELECT COUNT(*) FROM cell_annotation) as annotazioni_celle,
    (SELECT COUNT(*) FROM text_annotations) as annotazioni_testo,
    (SELECT COUNT(*) FROM forum_post) as post_forum,
    (SELECT COUNT(*) FROM diary_entries) as voci_diario;
