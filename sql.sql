SELECT
    n.title,
    s.name,
    n.content,
    GROUP_CONCAT(t.name, ', ') AS tags,
    u.fname || ' ' || u.lname AS owner
FROM note n
JOIN subject s ON n.fk_subject_id = s.subject_id
LEFT JOIN note_tag nt ON n.note_id = nt.fk_note_id
LEFT JOIN tag t ON nt.fk_tag_id = t.tag_id
JOIN user u ON n.fk_user_id = u.user_id
JOIN shared_note sn ON n.note_id = sn .fk_note_id
WHERE sn.fk_user_id = 5
GROUP BY n.note_id, n.title, s.name, n.content
ORDER BY n.updated_at DESC;
