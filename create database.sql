-- 1. Create the database if it doesn't already exist
CREATE DATABASE IF NOT EXISTS chronoquest;

-- Switch to the new database
USE chronoquest;

-- 2. Create the 'users' table with correct data types
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,

    -- Columns derived from the original user data structure
    credits INT DEFAULT 1000,
    energy INT DEFAULT 1000,
    current_location VARCHAR(10) DEFAULT 'EFHK',

    -- CRITICAL FIX: These columns store JSON data and MUST be TEXT or LONGTEXT
    shards TEXT NULL, 
    playerBadges TEXT NULL, 

    -- Columns for persistent player statistics
    playerHowManyWins INT DEFAULT 0,
    playerHowManyLoses INT DEFAULT 0,
    playerHowManyTimesPlayed INT DEFAULT 0,
    jetstream_uses INT DEFAULT 0,

    -- CRITICAL FIX: Stores the full, resumable game state
    game_state_save LONGTEXT NULL 
);

-- 3. Create the 'airports' table
CREATE TABLE IF NOT EXISTS airports (
    ident VARCHAR(10) PRIMARY KEY, -- ICAO code
    name VARCHAR(255) NOT NULL,
    code VARCHAR(5) NULL, -- IATA code
    city VARCHAR(100) NULL,
    country VARCHAR(100) NULL,
    lat DECIMAL(10, 6) NOT NULL,
    lon DECIMAL(10, 6) NOT NULL,
    distance INT DEFAULT 0
);

-- Switch to the chronoquest database
USE chronoquest;

INSERT INTO airports (ident, name, code, city, country, lat, lon, distance) VALUES
-- Starting Location
('EFHK', 'Helsinki-Vantaa Airport', 'HEL', 'Helsinki', 'Finland', 60.317222, 24.963333, 0),

-- Major International Hubs
('EGLL', 'London Heathrow Airport', 'LHR', 'London', 'United Kingdom', 51.470000, -0.454300, 0),
('KJFK', 'John F. Kennedy International Airport', 'JFK', 'New York', 'United States', 40.641300, -73.778100, 0),
('RJTT', 'Tokyo Haneda Airport', 'HND', 'Tokyo', 'Japan', 35.552300, 139.779600, 0),
('OMDB', 'Dubai International Airport', 'DXB', 'Dubai', 'United Arab Emirates', 25.253200, 55.365100, 0),
('YSSY', 'Sydney Airport', 'SYD', 'Sydney', 'Australia', -33.946100, 151.177200, 0),
('SBGR', 'São Paulo-Guarulhos International Airport', 'GRU', 'São Paulo', 'Brazil', -23.435600, -46.473100, 0),
('FACT', 'Cape Town International Airport', 'CPT', 'Cape Town', 'South Africa', -33.968300, 18.601700, 0),
('UUEE', 'Sheremetyevo International Airport', 'SVO', 'Moscow', 'Russia', 55.972600, 37.414600, 0),
('ZBAA', 'Beijing Capital International Airport', 'PEK', 'Beijing', 'China', 40.079900, 116.603100, 0),
('WSSS', 'Singapore Changi Airport', 'SIN', 'Singapore', 1.364400, 103.991500, 0),
('CYYZ', 'Toronto Pearson International Airport', 'YYZ', 'Toronto', 'Canada', 43.677700, -79.624800, 0),
('EDDF', 'Frankfurt Airport', 'FRA', 'Frankfurt', 'Germany', 50.037900, 8.562200, 0),
('VIDP', 'Indira Gandhi International Airport', 'DEL', 'Delhi', 'India', 28.566500, 77.103100, 0),
('HECA', 'Cairo International Airport', 'CAI', 'Cairo', 'Egypt', 30.121900, 31.405600, 0),
('KLAX', 'Los Angeles International Airport', 'LAX', 'Los Angeles', 'United States', 33.942500, -118.408000, 0),
('LFPG', 'Paris Charles de Gaulle Airport', 'CDG', 'Paris', 'France', 49.009700, 2.547900, 0),
('EHAM', 'Amsterdam Airport Schiphol', 'AMS', 'Amsterdam', 'Netherlands', 52.308600, 4.763900, 0),
('VTBS', 'Suvarnabhumi Airport', 'BKK', 'Bangkok', 'Thailand', 13.681100, 100.747200, 0),
('VHHH', 'Hong Kong International Airport', 'HKG', 'Hong Kong', 'China', 22.308900, 113.914700, 0),
('SCEL', 'Santiago International Airport', 'SCL', 'Santiago', 'Chile', -33.393000, -70.785800, 0);
