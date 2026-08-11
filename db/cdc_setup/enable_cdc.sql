USE FlightBookingCDC;
GO

-- ======================================================================
-- STEP 1: ENABLE CDC AT DATABASE LEVEL
-- ======================================================================
-- Enable CDC if DB not yet start it
IF (SELECT is_cdc_enabled FROM sys.databases WHERE name = 'FlightBookingCDC') = 0
BEGIN
    EXEC sys.sp_cdc_enable_db;
    PRINT N'Successfully enable CDC for Database: FlightBookingCDC';
END
ELSE
BEGIN
    PRINT N'Database FlightBookingCDC has been enabled for CDC before!';
END
GO

-- ======================================================================
-- BƯỚC 2: ENABLE CDC AT TABLE LEVEL
-- ======================================================================
-- 1. pnr_records table
EXEC sys.sp_cdc_enable_table
    @source_schema = N'dbo',
    @source_name   = N'pnr_records',
    @role_name     = NULL, 
    @supports_net_changes = 0;

-- 2. passengers table
EXEC sys.sp_cdc_enable_table
    @source_schema = N'dbo',
    @source_name   = N'passengers',
    @role_name     = NULL,
    @supports_net_changes = 0;

-- 3. flight_segments table
EXEC sys.sp_cdc_enable_table
    @source_schema = N'dbo',
    @source_name   = N'flight_segments',
    @role_name     = NULL,
    @supports_net_changes = 0;

-- 4. tickets table
EXEC sys.sp_cdc_enable_table
    @source_schema = N'dbo',
    @source_name   = N'tickets',
    @role_name     = NULL,
    @supports_net_changes = 0;

-- 5. payments table
EXEC sys.sp_cdc_enable_table
    @source_schema = N'dbo',
    @source_name   = N'payments',
    @role_name     = NULL,
    @supports_net_changes = 0;

-- 6. booking_events table
EXEC sys.sp_cdc_enable_table
    @source_schema = N'dbo',
    @source_name   = N'booking_events',
    @role_name     = NULL,
    @supports_net_changes = 0;
GO

PRINT N'Successfully enable CDC for all 6 tables!';