
DROP TABLE IF EXISTS books;
CREATE TABLE books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title text NOT NULL,
    authorFName text,
    authorLName text,
    publishDate date,
    heldBy text
);

DROP TABLE IF EXISTS users;
CREATE TABLE users (
    username text PRIMARY KEY,
    password text,
    fName text,
    lName text,
    email text NOT NULL
);

DROP TABLE IF EXISTS checkouts;
CREATE TABLE checkouts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bookId INTEGER NOT NULL,
    uName text NOT NULL,
    dateOut date NOT NULL,
    dateIn date
);


