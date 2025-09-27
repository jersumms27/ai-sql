DROP DATABASE IF EXISTS golf;
CREATE DATABASE golf;
USE golf;

CREATE TABLE Course (
    course_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    country VARCHAR(100),
    city VARCHAR(100),
    rating DECIMAL(4, 1),
    slope SMALLINT UNSIGNED,

    PRIMARY KEY (course_id)
);

CREATE TABLE Hole (
    course_id BIGINT UNSIGNED NOT NULL,
    hole_number TINYINT UNSIGNED NOT NULL,
    par TINYINT UNSIGNED NOT NULL,
    length SMALLINT UNSIGNED NOT NULL,

    PRIMARY KEY (course_id, hole_number),
    FOREIGN KEY (course_id) REFERENCES Course(course_id)
);

CREATE TABLE `Match` (
    match_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    course_id BIGINT UNSIGNED NOT NULL,
    name VARCHAR(100) NOT NULL,

    PRIMARY KEY (match_id),
    FOREIGN KEY (course_id) REFERENCES Course(course_id)
);

CREATE TABLE Brand (
    brand_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    name VARCHAR(100),

    PRIMARY KEY (brand_id)
);

CREATE TABLE GolfBag (
    bag_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    brand_id BIGINT UNSIGNED NOT NULL,

    PRIMARY KEY (bag_id),
    FOREIGN KEY (brand_id) REFERENCES Brand(brand_id)
);

CREATE TABLE GolfClub (
    club_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    bag_id BIGINT UNSIGNED NOT NULL,
    brand_id BIGINT UNSIGNED NOT NULL,
    loft TINYINT UNSIGNED,
    type ENUM('Iron', 'Wood', 'Hybrid', 'Putter'),

    PRIMARY KEY (club_id),
    FOREIGN KEY (bag_id) REFERENCES GolfBag(bag_id),
    FOREIGN KEY (brand_id) REFERENCES Brand(brand_id)
);

CREATE TABLE GolfBall (
    ball_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    bag_id BIGINT UNSIGNED NOT NULL,
    brand_id BIGINT UNSIGNED NOT NULL,
    number TINYINT UNSIGNED,
    softness ENUM('Hard', 'Soft', 'Super soft', 'Ultra soft'),

    PRIMARY KEY (ball_id),
    FOREIGN KEY (bag_id) REFERENCES GolfBag(bag_id),
    FOREIGN KEY (brand_id) REFERENCES Brand(brand_id)
);

CREATE TABLE Player (
    player_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    golf_bag_id BIGINT UNSIGNED UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    team VARCHAR(100),
    handicap DECIMAL(4, 1),
    handedness ENUM('Left', 'Right'),

    PRIMARY KEY (player_id),
    FOREIGN KEY (golf_bag_id) REFERENCES GolfBag(bag_id)
);

CREATE TABLE Scorecard (
    match_id BIGINT UNSIGNED NOT NULL,
    player_id BIGINT UNSIGNED NOT NULL,

    PRIMARY KEY (match_id, player_id),
    FOREIGN KEY (match_id) REFERENCES `Match`(match_id),
    FOREIGN KEY (player_id) REFERENCES Player(player_id)
);

CREATE TABLE ScoreCardEntry (
    match_id BIGINT UNSIGNED NOT NULL,
    player_id BIGINT UNSIGNED NOT NULL,
    course_id BIGINT UNSIGNED NOT NULL,
    hole_number TINYINT UNSIGNED NOT NULL,
    score TINYINT UNSIGNED,

    PRIMARY KEY (match_id, player_id, course_id, hole_number),
    FOREIGN KEY (match_id, player_id) REFERENCES Scorecard(match_id, player_id),
    FOREIGN KEY (course_id, hole_number) REFERENCES Hole(course_id, hole_number)
);
