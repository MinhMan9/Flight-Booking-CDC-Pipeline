-- =======================================================================
-- SCRIPT RESET DỮ LIỆU TOÀN BỘ HỆ THỐNG
-- =======================================================================
USE FlightBookingCDC;
GO
-- 1. XÓA DỮ LIỆU THEO THỨ TỰ TỪ NGỌN VỀ GỐC (Tránh lỗi Foreign Key)
-- Xóa bảng cháu (phụ thuộc vào hành khách)
DELETE FROM tickets;

-- Xóa các bảng con (phụ thuộc vào PNR)
DELETE FROM payments;
DELETE FROM booking_events;
DELETE FROM flight_segments;
DELETE FROM passengers;

-- Xóa bảng cha (Gốc)
DELETE FROM pnr_records;
GO

-- 2. RESET LẠI CÁC CỘT ID TỰ TĂNG (IDENTITY) VỀ 0
-- Để lần chạy script Python tiếp theo, ID sẽ lại bắt đầu đẹp đẽ từ số 1
DBCC CHECKIDENT ('passengers', RESEED, 0);
DBCC CHECKIDENT ('flight_segments', RESEED, 0);
DBCC CHECKIDENT ('booking_events', RESEED, 0);
GO

PRINT 'Đã xóa toàn bộ dữ liệu và reset ID thành công!';