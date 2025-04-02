SELECT note.title, note.content, subject.name
FROM note
JOIN subject ON note.fk_subject_id = subject.subject_id
WHERE note.fk_user_id=2