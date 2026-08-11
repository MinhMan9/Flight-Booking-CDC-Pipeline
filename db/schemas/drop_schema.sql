-- =======================================================================
-- FILE: drop_schema.sql
-- DESCRIPTION: Delete all table in FlightBookingCDC system
-- =======================================================================
USE FlightBookingCDC;
GO

-- 1.
DROP TABLE IF EXISTS tickets;
GO

-- 2.
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS booking_events;
DROP TABLE IF EXISTS flight_segments;
DROP TABLE IF EXISTS passengers;
GO

-- 3.
DROP TABLE IF EXISTS pnr_records;
GO

PRINT 'Successfully delete all tables!';
