SELECT * 
FROM all_teams 
WHERE (season = 2026 OR season = '2026')
  AND (playoffGame = 0 OR playoffGame = '0')
  AND LOWER(situation) = 'all'
