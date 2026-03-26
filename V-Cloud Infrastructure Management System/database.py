import pyodbc


def get_connection():
    try:
        conn = pyodbc.connect(
            "DRIVER={SQL Server};"
            "SERVER=(local)\\SQLEXPRESS;"
            "DATABASE=QuanLyMayChuAo;"
            "Trusted_Connection=yes;"
        )
        return conn
    except Exception as e:
        print("Lỗi kết nối database:", e)
        return None


def check_login(username, password):
    conn = get_connection()
    if conn is None:
        return None

    try:
        cursor = conn.cursor()

        query = """
        SELECT Username, Role, MaKH
        FROM TaiKhoan
        WHERE Username = ? AND Password = ?
        """

        cursor.execute(query, (username, password))
        result = cursor.fetchone()

        if result:
            return {
                "username": result[0],
                "role": result[1],
                "makh": result[2]
            }

        return None

    except Exception as e:
        print("Lỗi truy vấn:", e)
        return None

    finally:
        conn.close()


# --- CODE DÀNH CHO ADMIN 

def get_all_vps():
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("EXEC sp_Admin_HienThiMayAoDaThue")
        return cursor.fetchall()
    except Exception as e:
        print("Lỗi tải danh sách VPS:", e)
        return []
    finally:
        conn.close()
def get_all_packages():
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        # Lấy danh sách các gói dịch vụ đang có
        cursor.execute("SELECT MaGoi, TenGoi, RAM_GB, CPU_Core, GiaTien FROM GoiDichVu")
        return cursor.fetchall()
    except Exception as e:
        print("Lỗi tải danh sách gói cước:", e)
        return []
    finally:
        conn.close()
# --------

def delete_vps(ma_vm):
    conn = get_connection()
    if conn is None: return False, "Lỗi kết nối database"
    try:
        conn.autocommit = True  #lưu thay đổi xuống SQL ngay lập tức
        cursor = conn.cursor()
        # Dùng cú pháp chuẩn của ODBC để không bị lỗi ẩn
        cursor.execute("{CALL sp_HuyMayAo (?)}", (ma_vm,))
        return True, "Xóa thành công"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def add_package(ten_goi, ram, cpu, gia):
    conn = get_connection()
    if conn is None: return False, "Lỗi kết nối database"
    try:
        conn.autocommit = True  # lưu thay đổi ngay lập tức
        cursor = conn.cursor()
        # Dùng cú pháp chuẩn của ODBC để không bị lỗi ẩn
        cursor.execute("{CALL sp_Admin_TaoCauHinhSan (?, ?, ?, ?)}", (ten_goi, ram, cpu, gia))
        return True, "Thêm thành công"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()
def delete_package(ma_goi):
    conn = get_connection()
    if conn is None: return False, "Lỗi kết nối database"
    try:
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute("DELETE FROM GoiDichVu WHERE MaGoi = ?", (ma_goi,))
        return True, "Xóa gói dịch vụ thành công"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

# --- CODE DÀNH CHO KHÁCH HÀNG (USER) ---

def get_user_vps(makh):
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        #  lấy máy ảo của khách đang đăng nhập
        query = """
        SELECT vm.MaVM, vm.TenVM, gdv.TenGoi, vm.RAM_Cap_GB, vm.CPU_Cap_Core, vm.HeDieuHanh, ip.IPAddress, vm.NgayTao
        FROM VirtualMachine vm
        LEFT JOIN GoiDichVu gdv ON vm.MaGoi = gdv.MaGoi
        LEFT JOIN IPPool ip ON vm.MaVM = ip.MaVM
        WHERE vm.MaKH = ?
        ORDER BY vm.NgayTao DESC
        """
        cursor.execute(query, (makh,))
        return cursor.fetchall()
    except Exception as e:
        print("Lỗi tải VPS khách hàng:", e)
        return []
    finally:
        conn.close()

def rent_vps(makh, magoi, tenvm, os):
    conn = get_connection()
    if conn is None: return False, "Lỗi kết nối database"
    try:
        conn.autocommit = True
        cursor = conn.cursor()
        # Gọi Stored Procedure tự động cấp IP và tìm Server trống
        cursor.execute("{CALL sp_ThueMayAo (?, ?, ?, ?)}", (makh, magoi, tenvm, os))
        return True, "Thuê máy ảo thành công!"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()



def register_user(username, password, hoten, email, sodt):
    conn = get_connection()
    if conn is None: return False, "Lỗi kết nối database"
    try:
        cursor = conn.cursor()
        # Thay đổi cú pháp gọi Procedure sang EXEC
        sql = "EXEC sp_DangKyTaiKhoan ?, ?, ?, ?, ?"
        params = (username, password, hoten, email, sodt)
        
        cursor.execute(sql, params)
        
        # Đảm bảo chốt dữ liệu
        conn.commit() 
        return True, "Đăng ký thành công!"
    except Exception as e:
        print("Lỗi Python:", e)
        return False, str(e)
    finally:
        conn.close()

def get_infra_stats():
    conn = get_connection()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        # Query tính toán trực tiếp từ 2 bảng PhysicalServer và VirtualMachine
        query = """
        SELECT 
            (SELECT COUNT(*) FROM PhysicalServer) as TotalServers,
            (SELECT SUM(TongRAM_GB) FROM PhysicalServer) as TotalRAM,
            (SELECT ISNULL(SUM(RAM_Cap_GB), 0) FROM VirtualMachine) as UsedRAM,
            (SELECT SUM(TongCPU_Core) FROM PhysicalServer) as TotalCPU,
            (SELECT ISNULL(SUM(CPU_Cap_Core), 0) FROM VirtualMachine) as UsedCPU
        """
        cursor.execute(query)
        r = cursor.fetchone()
        
        return {
            "servers": r[0] if r[0] else 0,
            "total_ram": r[1] if r[1] else 0,
            "free_ram": (r[1] if r[1] else 0) - (r[2] if r[2] else 0),
            "total_cpu": r[3] if r[3] else 0,
            "free_cpu": (r[3] if r[3] else 0) - (r[4] if r[4] else 0)
        }
    except Exception as e:
        print("Lỗi tính tài nguyên:", e)
        return None
    finally:
        conn.close()