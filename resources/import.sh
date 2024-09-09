mongoimport --host localhost --db stories --collection templates --type json --file /docker-entrypoint-initdb.d/story_cards_template_test.json
mongoimport --host localhost --db stories --collection parameters --type json --file /docker-entrypoint-initdb.d/gameParameters_test.json
mongoimport --host localhost --db stories --collection players --type json --file /docker-entrypoint-initdb.d/players_test.json
