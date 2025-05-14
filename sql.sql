CREATE TRIGGER update_shared_note_updated_at
AFTER UPDATE OF permission ON shared_note
BEGIN
    UPDATE shared_note
    SET updated_at = CURRENT_TIMESTAMP
    WHERE fk_note_id = NEW.fk_note_id AND fk_user_id = NEW.fk_user_id;
END;
