SELECT
    n.title,
    s.name,
    n.content,
    GROUP_CONCAT(t.name, ', ') AS tags
FROM note n
JOIN subject s ON n.fk_subject_id = s.subject_id
LEFT JOIN note_tag nt ON n.note_id = nt.fk_note_id
LEFT JOIN tag t ON nt.fk_tag_id = t.tag_id
GROUP BY n.note_id, n.title, n.content, s.name

SELECT
                            n.title,
                            s.name,
                            n.content,
                            GROUP_CONCAT(t.name, ', ') AS tags
                       FROM note n
                       JOIN subject s ON n.fk_subject_id = s.subject_id
                       LEFT JOIN note_tag nt ON n.note_id = nt.fk_note_id
                       LEFT JOIN tag t ON nt.fk_tag_id = t.tag_id
                       WHERE n.fk_user_id = 2
                       GROUP BY n.note_id, n.title, s.name, n.content
