-- =======================================================================
-- FILE: init_schema.sql
-- DESCRIPTION: Create database schema for Flight Booking PNR System
-- =======================================================================

-- (Optional) Create Database
CREATE DATABASE FlightBookingCDC;
GO
USE FlightBookingCDC;
GO

-- -----------------------------------------------------------------------
-- 1. pnr_records
-- -----------------------------------------------------------------------
CREATE TABLE pnr_records (
    pnr_id VARCHAR(6) PRIMARY KEY,
    booking_channel VARCHAR(50) NOT NULL,
    booking_status VARCHAR(20) NOT NULL 
        CHECK (booking_status IN ('CREATED', 'TICKETED', 'CHANGED', 'CANCELLED', 'REFUNDED')),
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE()
);
GO

-- -----------------------------------------------------------------------
-- 2. 
-- -----------------------------------------------------------------------

-- Passenger table
CREATE TABLE passengers (
    passenger_id INT IDENTITY(1,1) PRIMARY KEY,
    pnr_id VARCHAR(6) NOT NULL FOREIGN KEY REFERENCES pnr_records(pnr_id),
    first_name NVARCHAR(50) NOT NULL,
    last_name NVARCHAR(50) NOT NULL,
    email VARCHAR(100),
    passport_number VARCHAR(20) NOT NULL,
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE()
);
GO

-- Flight segment table
CREATE TABLE flight_segments (
    segment_id INT IDENTITY(1,1) PRIMARY KEY,
    pnr_id VARCHAR(6) NOT NULL FOREIGN KEY REFERENCES pnr_records(pnr_id),
    origin_airport VARCHAR(3) NOT NULL,
    dest_airport VARCHAR(3) NOT NULL,
    flight_date DATE NOT NULL,
    airline_code VARCHAR(2) NOT NULL,
    flight_number VARCHAR(10) NOT NULL,
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE()
);
GO

-- Payment table
CREATE TABLE payments (
    payment_id VARCHAR(50) PRIMARY KEY,
    pnr_id VARCHAR(6) NOT NULL FOREIGN KEY REFERENCES pnr_records(pnr_id),
    payment_method VARCHAR(20) 
        CHECK (payment_method IN ('CREDIT_CARD', 'ATM_CARD', 'E_WALLET', 'CASH')),
    amount DECIMAL(12,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'VND',
    payment_status VARCHAR(20) 
        CHECK (payment_status IN ('PENDING', 'SUCCESS', 'FAILED', 'REFUNDED')),
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE()
);
GO

-- Booking event table
CREATE TABLE booking_events (
    event_id INT IDENTITY(1,1) PRIMARY KEY,
    pnr_id VARCHAR(6) NOT NULL FOREIGN KEY REFERENCES pnr_records(pnr_id),
    event_type VARCHAR(50) NOT NULL
        CHECK (event_type IN ('CREATED', 'TICKETED', 'CHANGED', 'CANCELLED', 'REFUNDED')),
    created_at DATETIME DEFAULT GETDATE()
);
GO

-- -----------------------------------------------------------------------
-- 3.
-- -----------------------------------------------------------------------

-- Ticket table (1 passenger - 1 ticket)
CREATE TABLE tickets (
    ticket_number VARCHAR(20) PRIMARY KEY,
    passenger_id INT NOT NULL UNIQUE FOREIGN KEY REFERENCES passengers(passenger_id),
    fare_class VARCHAR(10) NOT NULL,
    ticket_status VARCHAR(20) NOT NULL 
        CHECK (ticket_status IN ('ISSUED', 'USED', 'REFUNDED')),
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE()
);
GO