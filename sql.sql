SELECT t.tag_id, t.name
FROM tag t
JOIN note_tag nt ON t.tag_id=nt.fk_tag_id
WHERE nt.fk_note_id=1
ORDER BY t.tag_id;