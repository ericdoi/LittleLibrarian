/* Initialize DB tables */

DROP TABLE IF EXISTS books;
CREATE TABLE books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title text NOT NULL,
    authorFName text,
    authorLName text,
    productUrl text,
    publishDate date,
    acquireDate date,
    location text,
    heldBy text,
    checkoutId INTEGER,
    reportedMissingBy text
);
CREATE INDEX borrower ON books ( heldBy );

DROP TABLE IF EXISTS users;
CREATE TABLE users (
    username text PRIMARY KEY NOT NULL,
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
CREATE INDEX book_user ON checkouts ( bookId, uName );


