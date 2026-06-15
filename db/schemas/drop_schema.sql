-- =======================================================================
-- FILE: drop_schema.sql
-- DESCRIPTION: Xóa toàn bộ các bảng trong hệ thống Flight Booking CDC
-- =======================================================================
USE FlightBookingCDC;
GO

-- 1. Xóa các bảng phụ thuộc ở mức sâu nhất (bảng cháu)
DROP TABLE IF EXISTS tickets;
GO

-- 2. Xóa các bảng con (phụ thuộc vào pnr_records hoặc passengers)
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS booking_events;
DROP TABLE IF EXISTS flight_segments;
DROP TABLE IF EXISTS passengers;
GO

-- 3. Xóa bảng gốc (bảng cha)
DROP TABLE IF EXISTS pnr_records;
GO

PRINT 'Đã xóa toàn bộ các bảng thành công!';
