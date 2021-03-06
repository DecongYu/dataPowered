-- creating database at the app installation;
DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS well;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);

CREATE TABLE well (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  entered TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  well_id TEXT NOT NULL,
  on_prd_date DATE NOT NULL,
  tvd REAL NOT NULL,
  frac_len REAL NOT NULL,
  cum_frac_propp REAL NOT NULL,
  bh_long REAL NOT NULL,
  bh_lat REAL NOT NULL,
  latrl_len REAL,
  FOREIGN KEY (author_id) REFERENCES user (id)
);
