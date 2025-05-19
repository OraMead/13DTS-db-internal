SELECT
    n.note_id,
    n.title,
    s.name,
    n.fk_subject_id,
    (
        SELECT GROUP_CONCAT(t.tag_id || ':' || t.name, '|')
        FROM note_tag nt
        JOIN tag t ON nt.fk_tag_id = t.tag_id
        WHERE nt.fk_note_id = n.note_id
    ) AS tags,
    (
        SELECT GROUP_CONCAT(u.user_id || ':' || u.fname || ' ' || u.lname || ':' || sn2.permission, '|')
        FROM shared_note sn2
        JOIN user u ON sn2.fk_user_id = u.user_id
        WHERE sn2.fk_note_id = n.note_id
    ) AS shared,
    u.fname || ' ' || u.lname AS owner
FROM note n
JOIN subject s ON n.fk_subject_id = s.subject_id
JOIN user u ON n.fk_user_id = u.user_id
ORDER BY n.updated_at DESC