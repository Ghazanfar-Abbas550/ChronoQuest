-- Create the database (if not exists)
CREATE DATABASE IF NOT EXISTS chronoquest;
USE chronoquest;

-- -----------------------
-- Table: users
-- -----------------------
DROP TABLE IF EXISTS users;
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    credits INT(11) DEFAULT 1000,
    energy INT(11) DEFAULT 1000,
    current_location VARCHAR(10) DEFAULT 'EFHK',
    shards INT(11) DEFAULT 0,
    playerBadges TEXT,
    playerLoseBadges TEXT,
    playerHowManyWins INT(11) DEFAULT 0,
    playerHowManyLoses INT(11) DEFAULT 0,
    playerHowManyTimesPlayed INT(11) DEFAULT 0,
    jetstream_uses INT(11) DEFAULT 0,
    game_state_save TEXT
);

-- -----------------------
-- Table: airports
-- -----------------------
DROP TABLE IF EXISTS airports;
CREATE TABLE airports (
    ident VARCHAR(10) NOT NULL PRIMARY KEY,
    name VARCHAR(255),
    code VARCHAR(10),
    city VARCHAR(100),
    country VARCHAR(100),
    distance INT(11),
    lat DOUBLE,
    lon DOUBLE
);

-- -----------------------
-- Insert sample airports
-- -----------------------
INSERT INTO airports (ident, name, code, city, country, distance, lat, lon) VALUES
('EBBR','Brussels Airport','EBBR','Brussels','Belgium',1647,50.9014,4.4844),
('EDDB','Berlin Brandenburg Airport','EDDB','Berlin','Germany',1128,52.3667,13.5033),
('EDDM','Munich Airport','EDDM','Munich','Germany',1575,48.353783,11.786086),
('EDDS','Stuttgart Airport','EDDS','Stuttgart','Germany',1636,48.6889,9.2222),
('EFHK','Helsinki-Vantaa Airport','EFHK','Helsinki','Finland',0,60.317222,24.963333),
('EGLL','London Heathrow Airport','EGLL','London','United Kingdom',1848,51.47002,-0.454295),
('EHAM','Amsterdam Airport Schiphol','EHAM','Amsterdam','Netherlands',1521,52.308611,4.763889),
('EIDW','Dublin Airport','EIDW','Dublin','Ireland',2022,53.4264,-6.2499),
('EKCH','Copenhagen Airport','EKCH','Copenhagen','Denmark',892,55.617917,12.655972),
('ENGM','Oslo Airport','ENGM','Oslo','Norway',763,60.1939,11.1004),
('ENTC','Trondheim Airport','ENTC','Trondheim','Norway',812,63.457,10.923),
('ENZV','Stavanger Airport','ENZV','Stavanger','Norway',1095,58.876,5.637),
('EPWA','Warsaw Chopin Airport','EPWA','Warsaw','Poland',939,52.1658,20.9671),
('ESSA','Stockholm Arlanda Airport','ESSA','Stockholm','Sweden',398,59.64999,17.92389),
('EVRA','Riga International Airport','EVRA','Riga','Latvia',382,56.9236,23.9711),
('LEBL','Barcelona–El Prat Airport','LEBL','Barcelona','Spain',2628,41.2974,2.0833),
('LEMD','Adolfo Suárez Madrid–Barajas Airport','LEMD','Madrid','Spain',2947,40.483936,-3.567954),
('LFPG','Charles de Gaulle Airport','LFPG','Paris','France',1896,49.009691,2.547926),
('LGAV','Athens International Airport','LGAV','Athens','Greece',2490,37.9363,23.9474),
('LHBP','Budapest Ferenc Liszt International Airport','LHBP','Budapest','Hungary',1480,47.4333,19.2333),
('LIPE','Pescara Airport','LIPE','Pescara','Italy',2118,42.431,14.187),
('LIPZ','Venice Marco Polo Airport','LIPZ','Venice','Italy',1844,45.5052,12.3519),
('LIRF','Leonardo da Vinci–Fiumicino Airport','LIRF','Rome','Italy',2234,41.800278,12.238889),
('LIRN','Naples Airport','LIRN','Naples','Italy',2281,40.886,14.29),
('LOWW','Vienna International Airport','LOWW','Vienna','Austria',1460,48.110278,16.569722),
('LPFR','Porto Airport','LPFR','Porto','Portugal',3116,41.242,-8.678),
('LPPT','Lisbon Airport','LPPT','Lisbon','Portugal',3364,38.775,-9.135),
('LROP','Henri Coandă International Airport','LROP','Bucharest','Romania',1753,44.5705,26.1022),
('LSZH','Zurich Airport','LSZH','Zurich','Switzerland',1779,47.451389,8.564444);
