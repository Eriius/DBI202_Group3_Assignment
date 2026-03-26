USE master;
GO

-- 1. XÓA VÀ TẠO MỚI DATABASE (Để đảm bảo sạch dữ liệu cũ)
IF EXISTS (SELECT * FROM sys.databases WHERE name = 'QuanLyMayChuAo')
BEGIN
    ALTER DATABASE QuanLyMayChuAo SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE QuanLyMayChuAo;
END
GO

CREATE DATABASE QuanLyMayChuAo;
GO
USE QuanLyMayChuAo;
GO

-- 1. Bảng Máy chủ vật lý 
CREATE TABLE PhysicalServer (
    MaServer INT PRIMARY KEY IDENTITY(1,1),
    TenServer NVARCHAR(50) NOT NULL,
    IP_QuanLy VARCHAR(15) UNIQUE,
    TongRAM_GB INT,
    TongCPU_Core INT,
    TrangThai NVARCHAR(20) DEFAULT N'Hoạt động'
);

-- 2. Bảng Khách hàng
CREATE TABLE KhachHang (
    MaKH INT PRIMARY KEY IDENTITY(1,1),
    HoTen NVARCHAR(100),
    Email VARCHAR(100) UNIQUE,
    SoDT VARCHAR(15)
);

-- 3. Bảng Tài khoản
CREATE TABLE TaiKhoan (
    Username VARCHAR(50) PRIMARY KEY,
    Password VARCHAR(50) NOT NULL,
    Role NVARCHAR(20) NOT NULL, 
    MaKH INT NULL,              
    --- [FIX]: Thêm ON DELETE CASCADE để không bị lỗi khóa ngoại khi xóa khách hàng
    FOREIGN KEY (MaKH) REFERENCES KhachHang(MaKH) ON DELETE CASCADE
);

-- 4. Bảng Gói dịch vụ 
CREATE TABLE GoiDichVu (
    MaGoi INT PRIMARY KEY IDENTITY(1,1),
    TenGoi NVARCHAR(50),
    RAM_GB INT,
    CPU_Core INT,
    GiaTien DECIMAL(18,0)
);

-- 5. Bảng Máy ảo 
CREATE TABLE VirtualMachine (
    MaVM INT PRIMARY KEY IDENTITY(1,1),
    TenVM NVARCHAR(50),
    HeDieuHanh NVARCHAR(50),
    RAM_Cap_GB INT,
    CPU_Cap_Core INT,
    MaServer INT,
    MaKH INT,
    MaGoi INT,
    NgayTao DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (MaServer) REFERENCES PhysicalServer(MaServer) ON DELETE CASCADE, 
    FOREIGN KEY (MaKH) REFERENCES KhachHang(MaKH) ON DELETE CASCADE,
    FOREIGN KEY (MaGoi) REFERENCES GoiDichVu(MaGoi)
);

-- 6. Bảng Kho IP 
CREATE TABLE IPPool (
    IPAddress VARCHAR(15) PRIMARY KEY,
    TrangThai NVARCHAR(20) DEFAULT N'Trống',
    MaVM INT NULL,
    FOREIGN KEY (MaVM) REFERENCES VirtualMachine(MaVM) ON DELETE SET NULL
);
GO

CREATE PROCEDURE sp_DangKyTaiKhoan
    @Username VARCHAR(50),
    @Password VARCHAR(50),
    @HoTen NVARCHAR(100),
    @Email VARCHAR(100),
    @SoDT VARCHAR(15)
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        -- 1. Kiểm tra trùng lặp Username
        IF EXISTS (SELECT 1 FROM TaiKhoan WHERE Username = @Username)
        BEGIN
            RAISERROR(N'Lỗi: Tên đăng nhập này đã có người sử dụng!', 16, 1);
        END

        -- 2. Kiểm tra trùng lặp Email
        IF EXISTS (SELECT 1 FROM KhachHang WHERE Email = @Email)
        BEGIN
            RAISERROR(N'Lỗi: Email này đã được đăng ký cho một tài khoản khác!', 16, 1);
        END

        -- 3. Lưu thông tin Khách hàng
        INSERT INTO KhachHang (HoTen, Email, SoDT)
        VALUES (@HoTen, @Email, @SoDT);
        
        DECLARE @NewMaKH INT = SCOPE_IDENTITY();

        -- 4. Tạo tài khoản đăng nhập với quyền User
        INSERT INTO TaiKhoan (Username, Password, Role, MaKH)
        VALUES (@Username, @Password, 'User', @NewMaKH);

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
        DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE();
        RAISERROR (@ErrorMessage, 16, 1);
    END CATCH
END
GO

-- 1. SP: THUÊ MÁY ẢO 
CREATE PROCEDURE sp_ThueMayAo
    @MaKH INT,
    @MaGoi INT,
    @TenVM NVARCHAR(50),
    @HeDieuHanh NVARCHAR(50)
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        DECLARE @RAM_Required INT, @CPU_Required INT;
        SELECT @RAM_Required = RAM_GB, @CPU_Required = CPU_Core
        FROM GoiDichVu WHERE MaGoi = @MaGoi;

        IF @RAM_Required IS NULL
        BEGIN
            RAISERROR(N'Lỗi: Gói dịch vụ không tồn tại!', 16, 1);
        END

        DECLARE @MaServer INT;
        SELECT TOP 1 @MaServer = ps.MaServer
        FROM PhysicalServer ps
        LEFT JOIN VirtualMachine vm ON ps.MaServer = vm.MaServer
        GROUP BY ps.MaServer, ps.TongRAM_GB, ps.TongCPU_Core
        HAVING (ps.TongRAM_GB - ISNULL(SUM(vm.RAM_Cap_GB), 0)) >= @RAM_Required
            AND (ps.TongCPU_Core - ISNULL(SUM(vm.CPU_Cap_Core), 0)) >= @CPU_Required
        ORDER BY ps.MaServer;

        IF @MaServer IS NULL
        BEGIN
            RAISERROR(N'Lỗi: Không có máy chủ vật lý nào còn đủ tài nguyên!', 16, 1);
        END

        DECLARE @IPAddress VARCHAR(15);
        SELECT TOP 1 @IPAddress = IPAddress
        FROM IPPool WITH (UPDLOCK, READPAST)
        WHERE TrangThai = N'Trống';

        IF @IPAddress IS NULL
        BEGIN
            RAISERROR(N'Lỗi: Kho IP đã hết địa chỉ trống!', 16, 1);
        END

        INSERT INTO VirtualMachine (TenVM, HeDieuHanh, RAM_Cap_GB, CPU_Cap_Core, MaServer, MaKH, MaGoi)
        VALUES (@TenVM, @HeDieuHanh, @RAM_Required, @CPU_Required, @MaServer, @MaKH, @MaGoi);

        DECLARE @NewMaVM INT = SCOPE_IDENTITY();

        UPDATE IPPool
        SET TrangThai = N'Đã dùng', MaVM = @NewMaVM
        WHERE IPAddress = @IPAddress;

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
        DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE();
        RAISERROR (@ErrorMessage, 16, 1);
    END CATCH
END
GO

-- 2. SP: HỦY MÁY ẢO
CREATE PROCEDURE sp_HuyMayAo
    @MaVM INT
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        IF NOT EXISTS (SELECT 1 FROM VirtualMachine WHERE MaVM = @MaVM)
        BEGIN
            RAISERROR(N'Lỗi: Máy ảo không tồn tại!', 16, 1);
        END

        -- Giải phóng IP 
        UPDATE IPPool
        SET TrangThai = N'Trống', MaVM = NULL
        WHERE MaVM = @MaVM;

        DELETE FROM VirtualMachine WHERE MaVM = @MaVM;

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
        DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE();
        RAISERROR (@ErrorMessage, 16, 1);
    END CATCH
END
GO

-- 3. SP: THỐNG KÊ TÀI NGUYÊN 
CREATE PROCEDURE sp_ThongKeTaiNguyen
AS
BEGIN
    SET NOCOUNT ON;
    SELECT 
        ps.MaServer, ps.TenServer,
        ps.TongRAM_GB AS Tong_RAM,
        ISNULL(SUM(vm.RAM_Cap_GB), 0) AS RAM_DaSuDung,
        (ps.TongRAM_GB - ISNULL(SUM(vm.RAM_Cap_GB), 0)) AS RAM_ConLai,
        ps.TongCPU_Core AS Tong_CPU,
        ISNULL(SUM(vm.CPU_Cap_Core), 0) AS CPU_DaSuDung,
        (ps.TongCPU_Core - ISNULL(SUM(vm.CPU_Cap_Core), 0)) AS CPU_ConLai
    FROM PhysicalServer ps
    LEFT JOIN VirtualMachine vm ON ps.MaServer = vm.MaServer
    GROUP BY ps.MaServer, ps.TenServer, ps.TongRAM_GB, ps.TongCPU_Core;
END
GO

-- DỮ LIỆU MẪU
INSERT INTO PhysicalServer (TenServer, IP_QuanLy, TongRAM_GB, TongCPU_Core)
VALUES (N'Super-Server-01', '192.168.1.99', 512, 128);

INSERT INTO KhachHang (HoTen, Email, SoDT) VALUES (N'Khách Hàng VIP', 'vip@email.com', '0909123456');

INSERT INTO TaiKhoan VALUES ('admin', '123', 'Admin', NULL); 
INSERT INTO TaiKhoan VALUES ('khachhang', '123', 'User', 1); 

INSERT INTO GoiDichVu VALUES (N'Gói Sinh Viên', 2, 1, 50000);
INSERT INTO GoiDichVu VALUES (N'Gói Game Thủ', 8, 4, 300000);
INSERT INTO GoiDichVu VALUES (N'Gói Doanh Nghiệp', 32, 16, 2000000);

DECLARE @i INT = 10;
WHILE @i <= 40
BEGIN
    INSERT INTO IPPool (IPAddress) VALUES ('10.0.0.' + CAST(@i AS VARCHAR));
    SET @i = @i + 1;
END
GO

--- Trigger 1: bảo vệ tài nguyên
CREATE TRIGGER trg_VirtualMachine_CheckResource
ON VirtualMachine
AFTER INSERT, UPDATE
AS
BEGIN
    IF EXISTS (
        SELECT ps.MaServer
        FROM PhysicalServer ps
        JOIN VirtualMachine vm ON ps.MaServer = vm.MaServer
        GROUP BY ps.MaServer, ps.TongRAM_GB, ps.TongCPU_Core
        HAVING SUM(vm.RAM_Cap_GB) > ps.TongRAM_GB 
           OR SUM(vm.CPU_Cap_Core) > ps.TongCPU_Core
    )
    BEGIN
        RAISERROR(N'Lỗi: Tài nguyên máy chủ vật lý không đủ để thực hiện thao tác này!', 16, 1);
        ROLLBACK TRANSACTION;
    END
END
GO

--- Trigger 2: bảo vệ địa chỉ IP
CREATE TRIGGER trg_IPPool_ProtectUsage
ON IPPool
FOR UPDATE
AS
BEGIN
    IF EXISTS (
        SELECT 1 FROM deleted d
        JOIN inserted i ON d.IPAddress = i.IPAddress
        WHERE d.TrangThai = N'Đã dùng' 
          AND i.MaVM <> d.MaVM
    )
    BEGIN
        RAISERROR(N'Lỗi: IP này đang được sử dụng. Không thể gán cho máy ảo khác khi chưa giải phóng!', 16, 1);
        ROLLBACK TRANSACTION;
    END
END
GO

--- Trigger 3: Nhất quán dữ liệu IP
CREATE TRIGGER trg_IPPool_CheckLogic
ON IPPool
AFTER UPDATE
AS
BEGIN
    IF EXISTS (SELECT 1 FROM inserted WHERE TrangThai = N'Trống' AND MaVM IS NOT NULL)
    BEGIN
        RAISERROR(N'Lỗi logic: IP Trống thì không thể gán cho máy ảo nào!', 16, 1);
        ROLLBACK TRANSACTION;
    END
END
GO

CREATE TRIGGER trg_IPPool_AutoRelease
ON IPPool
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    -- Bắt sự kiện khi bảng IP bị ép MaVM thành NULL do xóa máy ảo
    UPDATE IPPool
    SET TrangThai = N'Trống'
    WHERE IPAddress IN (
        SELECT i.IPAddress 
        FROM inserted i
        JOIN deleted d ON i.IPAddress = d.IPAddress
        WHERE d.MaVM IS NOT NULL AND i.MaVM IS NULL
    );
END
GO

CREATE TRIGGER trg_TaiKhoan_ProtectAdmin
ON TaiKhoan
FOR DELETE
AS
BEGIN
    -- Chặn xóa bất kỳ ai có chức vụ là Admin (không chỉ giới hạn Username='admin')
    IF EXISTS (SELECT 1 FROM deleted WHERE Role = 'Admin')
    BEGIN
        RAISERROR(N'Lỗi nghiêm trọng: Không được phép xóa tài khoản thuộc nhóm Quản trị hệ thống (Admin)!', 16, 1);
        ROLLBACK TRANSACTION;
    END
END
GO

--- Trigger 5: Giới hạn máy chủ mỗi người
CREATE TRIGGER trg_VirtualMachine_QuotaCheck
ON VirtualMachine
FOR INSERT
AS
BEGIN
    IF EXISTS (
        SELECT MaKH FROM VirtualMachine 
        WHERE MaKH IN (SELECT MaKH FROM inserted)
        GROUP BY MaKH HAVING COUNT(MaVM) > 5
    )
    BEGIN
        RAISERROR(N'Lỗi: Mỗi khách hàng chỉ được sở hữu tối đa 5 máy chủ ảo!', 16, 1);
        ROLLBACK TRANSACTION;
    END
END
GO

--- Trigger 6: Chống xóa Gói DVu đang có người dùng
CREATE TRIGGER trg_GoiDichVu_ProtectActivePackages
ON GoiDichVu
INSTEAD OF DELETE
AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS (
        SELECT 1 FROM VirtualMachine vm
        INNER JOIN deleted d ON vm.MaGoi = d.MaGoi 
    )
    BEGIN
        RAISERROR(N'Lỗi: Không thể xóa gói dịch vụ này vì đang có máy ảo sử dụng! Hãy hủy các máy ảo liên quan trước.', 16, 1);
    END
    ELSE
    BEGIN
        DELETE FROM GoiDichVu WHERE MaGoi IN (SELECT MaGoi FROM deleted);
    END
END
GO

-- SP ADMIN: Hiển thị máy ảo
CREATE PROCEDURE sp_Admin_HienThiMayAoDaThue
AS
BEGIN
    SET NOCOUNT ON;
    SELECT 
        vm.MaVM, vm.TenVM, vm.HeDieuHanh, vm.RAM_Cap_GB, vm.CPU_Cap_Core,
        ps.TenServer AS ThuocServerVatLy, kh.HoTen AS TenKhachHang, kh.Email AS EmailKhachHang,
        gdv.TenGoi AS GoiDichVu, ip.IPAddress AS DiaChiIP, vm.NgayTao
    FROM VirtualMachine vm
    LEFT JOIN PhysicalServer ps ON vm.MaServer = ps.MaServer
    LEFT JOIN KhachHang kh ON vm.MaKH = kh.MaKH
    LEFT JOIN GoiDichVu gdv ON vm.MaGoi = gdv.MaGoi
    LEFT JOIN IPPool ip ON vm.MaVM = ip.MaVM
    ORDER BY vm.NgayTao DESC; 
END
GO

-- SP ADMIN: Tạo gói dịch vụ
CREATE PROCEDURE sp_Admin_TaoCauHinhSan
    @TenGoi NVARCHAR(50),
    @RAM_GB INT,
    @CPU_Core INT,
    @GiaTien DECIMAL(18,0)
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        IF EXISTS (SELECT 1 FROM GoiDichVu WHERE TenGoi = @TenGoi)
        BEGIN
            RAISERROR(N'Lỗi: Tên cấu hình này đã tồn tại, vui lòng đặt tên khác!', 16, 1);
        END
        INSERT INTO GoiDichVu (TenGoi, RAM_GB, CPU_Core, GiaTien)
        VALUES (@TenGoi, @RAM_GB, @CPU_Core, @GiaTien);
    END TRY
    BEGIN CATCH
        DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE();
        RAISERROR (@ErrorMessage, 16, 1);
    END CATCH
END
GO

ALTER TABLE TaiKhoan
ADD CONSTRAINT CHK_TaiKhoan_HopLe 
CHECK (LEN(TRIM(Username)) > 0 AND LEN(TRIM(Password)) > 0);

-- DỮ LIỆU MẪU MỞ RỘNG
INSERT INTO PhysicalServer (TenServer, IP_QuanLy, TongRAM_GB, TongCPU_Core)
VALUES 
(N'Dell-PowerEdge-R740', '192.168.1.100', 256, 64),
(N'HP-ProLiant-DL380', '192.168.1.101', 1024, 256);
GO

-- Đăng ký thử 2 tài khoản bằng SP vừa tạo
EXEC sp_DangKyTaiKhoan 'nguyenvana', '123', N'Nguyễn Văn A', 'nva@email.com', '0911222333';
EXEC sp_DangKyTaiKhoan 'tranthib', '123', N'Trần Thị B', 'ttb@email.com', '0988777666';
GO

-- THUÊ MÁY MẪU
EXEC sp_ThueMayAo @MaKH = 1, @MaGoi = 2, @TenVM = N'VPS-Game-Minecraft', @HeDieuHanh = N'Windows Server 2022';
EXEC sp_ThueMayAo @MaKH = 2, @MaGoi = 1, @TenVM = N'Web-Server-NVA', @HeDieuHanh = N'Ubuntu 22.04';
EXEC sp_ThueMayAo @MaKH = 3, @MaGoi = 3, @TenVM = N'Data-Center-TTB', @HeDieuHanh = N'CentOS 8';
EXEC sp_ThueMayAo @MaKH = 1, @MaGoi = 1, @TenVM = N'Test-Bot-Discord', @HeDieuHanh = N'Debian 11';
GO

--- xem dsach nguoi dung
SELECT 
    kh.MaKH, 
    kh.HoTen, 
    kh.Email, 
    kh.SoDT, 
    tk.Username, 
    tk.Role
FROM KhachHang kh
JOIN TaiKhoan tk ON kh.MaKH = tk.MaKH
ORDER BY kh.MaKH;