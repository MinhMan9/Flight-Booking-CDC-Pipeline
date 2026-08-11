-- =======================================================================
-- SCRIPT RESET SYSTEM DATA
-- =======================================================================
USE FlightBookingCDC;
GO
-- 1. DELETE DATA FROM LEAF TO ROOT (AVOID FOREIGN KEY)
DELETE FROM tickets;

DELETE FROM payments;
DELETE FROM booking_events;
DELETE FROM flight_segments;
DELETE FROM passengers;

DELETE FROM pnr_records;
GO

-- 2. RESET AUTO INCREASE ID (IDENTITY) TO 0
DBCC CHECKIDENT ('passengers', RESEED, 0);
DBCC CHECKIDENT ('flight_segments', RESEED, 0);
DBCC CHECKIDENT ('booking_events', RESEED, 0);
GO

PRINT 'Successfully delete all data and reset ID counter!';