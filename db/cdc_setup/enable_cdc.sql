USE FlightBookingCDC;
GO

-- ======================================================================
-- BƯỚC 1: BẬT CDC Ở CẤP ĐỘ DATABASE
-- ======================================================================
-- Kiểm tra xem DB đã được bật CDC chưa, nếu chưa thì bật
IF (SELECT is_cdc_enabled FROM sys.databases WHERE name = 'FlightBookingCDC') = 0
BEGIN
    EXEC sys.sp_cdc_enable_db;
    PRINT N'Đã bật CDC thành công cho Database: FlightBookingCDC';
END
ELSE
BEGIN
    PRINT N'Database FlightBookingCDC đã được bật CDC từ trước!';
END
GO

-- ======================================================================
-- BƯỚC 2: BẬT CDC Ở CẤP ĐỘ BẢNG (TABLE-LEVEL)
-- ======================================================================
-- Mẫu lệnh chung để bật CDC cho từng bảng. 
-- Lặp lại cho cả 6 bảng trong thiết kế dữ liệu của bạn.

-- 1. Bảng pnr_records
EXEC sys.sp_cdc_enable_table
    @source_schema = N'dbo',
    @source_name   = N'pnr_records',
    @role_name     = NULL, 
    @supports_net_changes = 0;

-- 2. Bảng passengers
EXEC sys.sp_cdc_enable_table
    @source_schema = N'dbo',
    @source_name   = N'passengers',
    @role_name     = NULL,
    @supports_net_changes = 0;

-- 3. Bảng flight_segments
EXEC sys.sp_cdc_enable_table
    @source_schema = N'dbo',
    @source_name   = N'flight_segments',
    @role_name     = NULL,
    @supports_net_changes = 0;

-- 4. Bảng tickets
EXEC sys.sp_cdc_enable_table
    @source_schema = N'dbo',
    @source_name   = N'tickets',
    @role_name     = NULL,
    @supports_net_changes = 0;

-- 5. Bảng payments
EXEC sys.sp_cdc_enable_table
    @source_schema = N'dbo',
    @source_name   = N'payments',
    @role_name     = NULL,
    @supports_net_changes = 0;

-- 6. Bảng booking_events
EXEC sys.sp_cdc_enable_table
    @source_schema = N'dbo',
    @source_name   = N'booking_events',
    @role_name     = NULL,
    @supports_net_changes = 0;
GO

PRINT N'Đã bật CDC thành công cho toàn bộ 6 bảng!';