SELECT user_id,
       GROUP_CONCAT(fname || ' ' || lname, '|') AS name
FROM user
WHERE user_id=1
GROUP BY user_id