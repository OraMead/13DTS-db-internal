SELECT 
                            n.note_id,
                            n.title,
                            s.name,
                            null,
                            GROUP_CONCAT(t.tag_id || ':' || t.name, '|') AS tags,
                            GROUP_CONCAT(u.user_id || ':' || u.fname || ' ' || u.lname, '|') AS shared
                        FROM note n
                                JOIN subject s ON n.fk_subject_id = s.subject_id
                                LEFT JOIN note_tag nt ON n.note_id = nt.fk_note_id
                                LEFT JOIN tag t ON nt.fk_tag_id = t.tag_id
                                LEFT JOIN shared_note sn ON n.note_id = sn.fk_note_id
                                LEFT JOIN user u ON sn.fk_user_id = user_id
                        WHERE n.fk_user_id = 3
                        GROUP BY n.note_id, n.title, s.name, n.updated_at
                        ORDER BY n.updated_at DESC;