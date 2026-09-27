SELECT * 
FROM all_teams 
WHERE (season = 2025 OR season = '2025')
  AND (playoffGame = 0 OR playoffGame = '0')
  AND LOWER(situation) = 'all'
