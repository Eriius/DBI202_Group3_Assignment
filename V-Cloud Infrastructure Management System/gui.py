import tkinter as tk
from tkinter import messagebox
from tkinter import ttk  
from database import check_login, get_all_vps, delete_vps, add_package, get_all_packages, delete_package, get_user_vps, rent_vps
from database import get_infra_stats 
def center_window(window, width, height):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    x = int((screen_width / 2) - (width / 2))
    y = int((screen_height / 2) - (height / 2))

    window.geometry(f"{width}x{height}+{x}+{y}")


def logout(window):
    window.destroy()
    run_login()


def open_admin_window(username):
    admin_window = tk.Tk()
    admin_window.title("Admin Dashboard - Quản Lý Hệ Thống VPS")
    
    screen_width = admin_window.winfo_screenwidth()
    screen_height = admin_window.winfo_screenheight()
    width, height = 900, 700
    x = int((screen_width / 2) - (width / 2))
    y = int((screen_height / 2) - (height / 2))
    admin_window.geometry(f"{width}x{height}+{x}+{y}")

    tk.Label(admin_window, text=f"GIAO DIỆN ADMIN: {username.upper()}", font=("Arial", 16, "bold")).pack(pady=10)

    # --- KHU VỰC 1: BẢNG DANH SÁCH MÁY ẢO ---
    frame_vps = tk.Frame(admin_window)
    frame_vps.pack(fill="both", expand=True, padx=20, pady=5)
    tk.Label(frame_vps, text="1. Danh sách Máy chủ ảo (VPS) đang cho thuê:", font=("Arial", 11, "bold")).pack(anchor="w")

    columns_vps = ("MaVM", "TenVM", "KhachHang", "RAM", "CPU", "IP", "NgayTao")
    tree_vps = ttk.Treeview(frame_vps, columns=columns_vps, show="headings", height=6)
    tree_vps.heading("MaVM", text="Mã VM")
    tree_vps.column("MaVM", width=50, anchor="center")
    tree_vps.heading("TenVM", text="Tên VPS")
    tree_vps.heading("KhachHang", text="Khách Hàng")
    tree_vps.heading("RAM", text="RAM (GB)")
    tree_vps.column("RAM", width=80, anchor="center")
    tree_vps.heading("CPU", text="CPU (Core)")
    tree_vps.column("CPU", width=80, anchor="center")
    tree_vps.heading("IP", text="Địa Chỉ IP")
    tree_vps.column("IP", width=120, anchor="center")
    tree_vps.heading("NgayTao", text="Ngày Tạo")
    
    tree_vps.pack(side="left", fill="both", expand=True)
    scrollbar_vps = ttk.Scrollbar(frame_vps, orient=tk.VERTICAL, command=tree_vps.yview)
    tree_vps.configure(yscroll=scrollbar_vps.set)
    scrollbar_vps.pack(side="right", fill="y")

    # --- LẤY DỮ LIỆU THẬT TỪ DATABASE ---
    stats = get_infra_stats()
    if stats:
        infra_text = (f" | Infrastructure: {stats['servers']} Servers "
                        f" | RAM: {stats['free_ram']}GB Free / {stats['total_ram']}GB Total "
                        f" | CPU: {stats['free_cpu']} Cores Free")
    else:
        infra_text = " | Infrastructure data unavailable"

    # --- HIỂN THỊ LÊN GIAO DIỆN ---
    health_frame = tk.Frame(admin_window)
    health_frame.pack(fill="x", padx=20, pady=5)
    
    tk.Label(health_frame, text=infra_text, font=("Arial", 10)).pack(side="left")
    

    def handle_delete():
        selected_item = tree_vps.selection()
        if not selected_item:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn 1 máy ảo trên bảng để xóa!")
            return
        ma_vm = tree_vps.item(selected_item[0])['values'][0]
        if messagebox.askyesno("Xác nhận", f"Xóa VPS mã {ma_vm} và thu hồi IP?"):
            success, msg = delete_vps(ma_vm)
            if success:
                messagebox.showinfo("Thành công", "Đã xóa máy ảo!")
                load_vps_data()
            else:
                messagebox.showerror("Lỗi SQL", msg)

    tk.Button(admin_window, text="⚠ Xóa VPS Đang Chọn", command=handle_delete, bg="red", fg="white", font=("Arial", 10, "bold")).pack(pady=5)

    # --- KHU VỰC 2: BẢNG DANH SÁCH GÓI CƯỚC ---
    frame_pkg = tk.Frame(admin_window)
    frame_pkg.pack(fill="both", expand=True, padx=20, pady=10)
    tk.Label(frame_pkg, text="2. Danh sách Gói Dịch Vụ đang mở bán:", font=("Arial", 11, "bold")).pack(anchor="w")

    columns_pkg = ("MaGoi", "TenGoi", "RAM", "CPU", "GiaTien")
    tree_pkg = ttk.Treeview(frame_pkg, columns=columns_pkg, show="headings", height=4)
    tree_pkg.heading("MaGoi", text="Mã Gói")
    tree_pkg.column("MaGoi", width=60, anchor="center")
    tree_pkg.heading("TenGoi", text="Tên Gói Dịch Vụ")
    tree_pkg.heading("RAM", text="RAM (GB)")
    tree_pkg.column("RAM", width=80, anchor="center")
    tree_pkg.heading("CPU", text="CPU (Core)")
    tree_pkg.column("CPU", width=80, anchor="center")
    tree_pkg.heading("GiaTien", text="Giá Tiền (VNĐ)")
    tree_pkg.column("GiaTien", width=120, anchor="e") # Đã sửa lỗi căn lề phải (e = east)
    
    tree_pkg.pack(side="left", fill="both", expand=True)
    scrollbar_pkg = ttk.Scrollbar(frame_pkg, orient=tk.VERTICAL, command=tree_pkg.yview)
    tree_pkg.configure(yscroll=scrollbar_pkg.set)
    scrollbar_pkg.pack(side="right", fill="y")

    # Hàm xử lý khi bấm nút Xóa Gói Cước
    def handle_delete_package():
        selected_item = tree_pkg.selection()
        if not selected_item:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn 1 gói cước trên bảng để xóa!")
            return
        
        ma_goi = tree_pkg.item(selected_item[0])['values'][0]
        ten_goi = tree_pkg.item(selected_item[0])['values'][1]
        
        if messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xóa gói [{ten_goi}] không?\nLưu ý: Không thể xóa nếu đang có khách dùng gói này!"):
            success, msg = delete_package(ma_goi)
            if success:
                messagebox.showinfo("Thành công", msg)
                load_pkg_data() # Tải lại bảng ngay lập tức
            else:
                messagebox.showerror("Lỗi SQL", msg)

    # Nút Xóa Gói
    tk.Button(admin_window, text="⚠ Xóa Gói Đang Chọn", command=handle_delete_package, bg="orange", fg="black", font=("Arial", 10, "bold")).pack(pady=5)

    def load_vps_data():
        for item in tree_vps.get_children(): tree_vps.delete(item)
        vps_list = get_all_vps()
        if vps_list:
            for vps in vps_list:
                tree_vps.insert("", tk.END, values=(vps[0], vps[1], vps[6], vps[3], vps[4], vps[9], str(vps[10])[:16]))

    def load_pkg_data():
        for item in tree_pkg.get_children(): tree_pkg.delete(item)
        pkg_list = get_all_packages()
        if pkg_list:
            for pkg in pkg_list:
                formatted_price = f"{int(pkg[4]):,}"
                tree_pkg.insert("", tk.END, values=(pkg[0], pkg[1], pkg[2], pkg[3], formatted_price))

    # --- KHU VỰC 3: FORM THÊM GÓI DỊCH VỤ ---
    frame_add = tk.LabelFrame(admin_window, text="Tạo Gói Dịch Vụ Mới", font=("Arial", 10, "bold"))
    frame_add.pack(fill="x", padx=20, pady=5)

    tk.Label(frame_add, text="Tên Gói:").grid(row=0, column=0, padx=5, pady=5)
    ent_tengoi = tk.Entry(frame_add, width=15)
    ent_tengoi.grid(row=0, column=1, padx=5, pady=5)
    tk.Label(frame_add, text="RAM:").grid(row=0, column=2, padx=5, pady=5)
    ent_ram = tk.Entry(frame_add, width=8)
    ent_ram.grid(row=0, column=3, padx=5, pady=5)
    tk.Label(frame_add, text="CPU:").grid(row=0, column=4, padx=5, pady=5)
    ent_cpu = tk.Entry(frame_add, width=8)
    ent_cpu.grid(row=0, column=5, padx=5, pady=5)
    tk.Label(frame_add, text="Giá Tiền:").grid(row=0, column=6, padx=5, pady=5)
    ent_gia = tk.Entry(frame_add, width=12)
    ent_gia.grid(row=0, column=7, padx=5, pady=5)

    def handle_add_package():
        tengoi = ent_tengoi.get()
        ram = ent_ram.get()
        cpu = ent_cpu.get()
        gia = ent_gia.get()
        if not all([tengoi, ram, cpu, gia]):
            messagebox.showwarning("Thiếu thông tin", "Nhập đủ thông tin gói!")
            return
        try:
            success, msg = add_package(tengoi, int(ram), int(cpu), float(gia))
            if success:
                messagebox.showinfo("Thành công", f"Đã thêm gói [{tengoi}]!")
                ent_tengoi.delete(0, tk.END); ent_ram.delete(0, tk.END); ent_cpu.delete(0, tk.END); ent_gia.delete(0, tk.END)
                load_pkg_data()
            else: 
                messagebox.showerror("Lỗi SQL", msg)
        except ValueError: 
            messagebox.showerror("Lỗi nhập liệu", "RAM, CPU và Giá phải là số!")

    tk.Button(frame_add, text="➕ Thêm Gói", command=handle_add_package, bg="green", fg="white", font=("Arial", 10, "bold")).grid(row=0, column=8, padx=15, pady=5)

    load_vps_data()
    load_pkg_data()

    tk.Button(admin_window, text="Đăng xuất", width=15, command=lambda: logout(admin_window)).pack(pady=10)
    admin_window.mainloop()

def open_user_window(username, makh):
    user_window = tk.Tk()
    user_window.title("Customer Dashboard - Thuê Máy Chủ Ảo")
    
    screen_width = user_window.winfo_screenwidth()
    screen_height = user_window.winfo_screenheight()
    width, height = 850, 650 
    x = int((screen_width / 2) - (width / 2))
    y = int((screen_height / 2) - (height / 2))
    user_window.geometry(f"{width}x{height}+{x}+{y}")

    tk.Label(user_window, text=f"XIN CHÀO KHÁCH HÀNG: {username.upper()}", font=("Arial", 16, "bold"), fg="blue").pack(pady=10)

    # --- KHU VỰC 1: BẢNG VPS CỦA TÔI ---
    frame_vps = tk.LabelFrame(user_window, text="1. Các Máy Chủ Ảo (VPS) Đang Thuê Của Bạn", font=("Arial", 11, "bold"))
    frame_vps.pack(fill="both", expand=True, padx=20, pady=5)

    columns_vps = ("MaVM", "TenVM", "TenGoi", "RAM", "CPU", "OS", "IP", "NgayTao")
    tree_vps = ttk.Treeview(frame_vps, columns=columns_vps, show="headings", height=6)
    tree_vps.heading("MaVM", text="Mã VM"); tree_vps.column("MaVM", width=50, anchor="center")
    tree_vps.heading("TenVM", text="Tên Máy Ảo"); tree_vps.column("TenVM", width=120)
    tree_vps.heading("TenGoi", text="Gói Cước"); tree_vps.column("TenGoi", width=100)
    tree_vps.heading("RAM", text="RAM"); tree_vps.column("RAM", width=50, anchor="center")
    tree_vps.heading("CPU", text="CPU"); tree_vps.column("CPU", width=50, anchor="center")
    tree_vps.heading("OS", text="Hệ Điều Hành"); tree_vps.column("OS", width=100)
    tree_vps.heading("IP", text="Địa Chỉ IP"); tree_vps.column("IP", width=100, anchor="center")
    tree_vps.heading("NgayTao", text="Ngày Thuê")

    tree_vps.pack(side="left", fill="both", expand=True)
    scrollbar_vps = ttk.Scrollbar(frame_vps, orient=tk.VERTICAL, command=tree_vps.yview)
    tree_vps.configure(yscroll=scrollbar_vps.set)
    scrollbar_vps.pack(side="right", fill="y")

    # Khung quy định hệ thống (Bên cạnh hoặc dưới nút Thuê)
    policy_frame = tk.LabelFrame(user_window, text="🔔 Chính sách dịch vụ", font=("Arial", 10, "bold"), fg="darkblue")
    policy_frame.pack(fill="x", padx=20, pady=10)

    policies = ("• Mỗi tài khoản được thuê tối đa 05 máy chủ ảo cùng lúc.\n"
                "• Hệ thống tự động thu hồi IP ngay sau khi bạn dừng thuê.\n"
                "• Tài nguyên (RAM/CPU) được cấp phát thực tế từ Server vật lý.\n"
                "• Vui lòng đảm bảo số dư tài khoản để duy trì dịch vụ.")
    tk.Label(policy_frame, text=policies, justify="left", font=("Arial", 9)).pack(padx=10, pady=5)

    # --- THÊM CHỨC NĂNG DỪNG THUÊ Ở ĐÂY ---
    def handle_cancel_vps():
        selected_item = tree_vps.selection()
        if not selected_item:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn 1 máy ảo trên bảng để hủy thuê!")
            return
        
        ma_vm = tree_vps.item(selected_item[0])['values'][0]
        ten_vm = tree_vps.item(selected_item[0])['values'][1]
        
        if messagebox.askyesno("Xác nhận trả máy", f"Bạn có chắc chắn muốn DỪNG THUÊ máy '{ten_vm}' không?\nHành động này sẽ xóa dữ liệu và trả lại IP cho hệ thống!"):
            success, msg = delete_vps(ma_vm) # Gọi chung hàm xóa máy của Admin
            if success:
                messagebox.showinfo("Thành công", f"Đã trả máy '{ten_vm}' thành công!")
                load_user_vps() # Tải lại bảng
            else:
                messagebox.showerror("Lỗi SQL", msg)

    tk.Button(user_window, text="❌ Trả Máy / Dừng Thuê", command=handle_cancel_vps, bg="red", fg="white", font=("Arial", 10, "bold")).pack(pady=5)

    def load_user_vps():
        for item in tree_vps.get_children(): tree_vps.delete(item)
        vps_list = get_user_vps(makh)
        if vps_list:
            for vps in vps_list:
                tree_vps.insert("", tk.END, values=(vps[0], vps[1], vps[2], f"{vps[3]}GB", f"{vps[4]}Core", vps[5], vps[6], str(vps[7])[:16]))

    # --- KHU VỰC 2: CỬA HÀNG (THUÊ MÁY MỚI) ---
    frame_rent = tk.LabelFrame(user_window, text="2. Cửa Hàng - Thuê Máy Chủ Ảo Mới", font=("Arial", 11, "bold"))
    frame_rent.pack(fill="x", padx=20, pady=10)

    tk.Label(frame_rent, text="Tên Máy Ảo (Tự đặt):").grid(row=0, column=0, padx=10, pady=10, sticky="e")
    ent_tenvm = tk.Entry(frame_rent, width=25)
    ent_tenvm.grid(row=0, column=1, padx=10, pady=10)

    tk.Label(frame_rent, text="Hệ Điều Hành:").grid(row=0, column=2, padx=10, pady=10, sticky="e")
    os_list = ["Ubuntu 22.04", "Windows Server 2022", "CentOS 8", "Debian 11"]
    cb_os = ttk.Combobox(frame_rent, values=os_list, width=20, state="readonly")
    cb_os.grid(row=0, column=3, padx=10, pady=10)
    cb_os.current(0) 

    tk.Label(frame_rent, text="Chọn Gói Cước:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
    
    packages = get_all_packages()
    pkg_display_list = []
    pkg_dict = {} 
    for p in packages:
        display_text = f"[{p[1]}] - {p[2]}GB RAM - {p[3]} Core - {int(p[4]):,} VNĐ"
        pkg_display_list.append(display_text)
        pkg_dict[display_text] = p[0]

    cb_pkg = ttk.Combobox(frame_rent, values=pkg_display_list, width=40, state="readonly")
    cb_pkg.grid(row=1, column=1, columnspan=2, padx=10, pady=10, sticky="w")
    if pkg_display_list:
        cb_pkg.current(0)

    def handle_rent():
        tenvm = ent_tenvm.get().strip()
        selected_os = cb_os.get()
        selected_pkg_text = cb_pkg.get()

        if not tenvm:
            messagebox.showwarning("Lỗi", "Vui lòng nhập tên cho máy ảo!")
            return
        if not selected_pkg_text:
            messagebox.showwarning("Lỗi", "Vui lòng chọn 1 gói cước!")
            return

        magoi = pkg_dict[selected_pkg_text]

        if messagebox.askyesno("Xác nhận thuê", f"Bạn muốn thuê máy '{tenvm}'?\nHệ thống sẽ tự động gán Server và IP cho bạn!"):
            success, msg = rent_vps(makh, magoi, tenvm, selected_os)
            if success:
                messagebox.showinfo("Thành công! 🎉", "Chốt đơn thành công! Đã cấp phát IP và máy chủ.")
                ent_tenvm.delete(0, tk.END)
                load_user_vps() 
            else:
                messagebox.showerror("Lỗi hệ thống", msg) 

    tk.Button(frame_rent, text="🛒 THUÊ NGAY", command=handle_rent, bg="green", fg="white", font=("Arial", 12, "bold"), width=15).grid(row=1, column=3, padx=10, pady=10)

    load_user_vps() 

    tk.Button(user_window, text="Đăng xuất", width=15, command=lambda: logout(user_window)).pack(pady=10)
    user_window.mainloop()


def run_login():
    login_window = tk.Tk()

    login_window.title("Đăng nhập hệ thống máy chủ ảo")

    center_window(login_window, 600, 550)

    def show_about():
        about_msg = (
            "V-Cloud Infrastructure Management System\n"
            "------------------------------------------\n"
            "Nhóm thực hiện: Group 3 - IA2001\n"
            "Công nghệ: Python & SQL Server\n\n"
            "Tính năng nổi bật:\n"
            "● Quản lý RAM/CPU vật lý bằng Trigger.\n"
            "● Tự động cấp phát IP và Server.\n"
            "● Phân quyền Admin và Khách hàng."
        )
        messagebox.showinfo("Thông tin hệ thống", about_msg)

    # Nút "i" (Information) ở góc trên bên phải
    tk.Button(login_window, text="ⓘ", command=show_about, 
                relief=tk.FLAT, font=("Arial", 12, "bold"), fg="blue", cursor="hand2").place(x=520, y=5)

    tk.Label(
        login_window,
        text="ĐĂNG NHẬP HỆ THỐNG",
        font=("Arial", 20, "bold")
    ).pack(pady=30)

    tk.Button(
        login_window,
        text="Chưa có tài khoản? Đăng ký",
        width=25,
        command=open_register_window,
        relief=tk.FLAT, fg="blue", cursor="hand2"
    ).pack(pady=5)

    frame = tk.Frame(login_window)
    frame.pack(pady=10)

    tk.Label(frame, text="Username").grid(row=0, column=0, padx=10, pady=15)
    entry_username = tk.Entry(frame)
    entry_username.grid(row=0, column=1)

    tk.Label(frame, text="Password").grid(row=1, column=0, padx=10, pady=15)
    entry_password = tk.Entry(frame, show="*")
    entry_password.grid(row=1, column=1)

    # Khung giới thiệu hệ thống
    info_frame = tk.LabelFrame(login_window, text="V-Cloud System Information", font=("Arial", 9, "italic"), fg="gray")
    info_frame.pack(fill="x", padx=20, pady=10)
    
    desc = ("Hệ thống quản lý máy chủ ảo thế hệ mới.\n"
            "● Tự động cấp phát tài nguyên thông minh.\n"
            "● Bảo mật dữ liệu với lớp Layer Trigger.\n"
            "● Hỗ trợ đa nền tảng OS (Ubuntu, Windows...).")
    tk.Label(info_frame, text=desc, justify="left", font=("Arial", 9)).pack(padx=10, pady=5)

    def handle_login():
        username = entry_username.get()
        password = entry_password.get()

        if username == "" or password == "":
            messagebox.showwarning("Lỗi", "Nhập username và password")
            return

        user = check_login(username, password)

        if user is None:
            messagebox.showerror("Lỗi", "Sai tài khoản hoặc mật khẩu")
            return

        role = user["role"].lower()

        login_window.destroy()

        if role == "admin":
            open_admin_window(user["username"])
        else:
            open_user_window(user["username"], user["makh"])

    tk.Button(
        login_window,
        text="Đăng nhập",
        width=20, height=2,
        command=handle_login
    ).pack(pady=10)

    login_window.mainloop()



from database import register_user # Nhớ import thêm hàm này ở đầu file

def open_register_window():
    reg_window = tk.Toplevel() # Mở cửa sổ mới đè lên cửa sổ login
    reg_window.title("Đăng ký tài khoản mới")
    center_window(reg_window, 400, 450)

    tk.Label(reg_window, text="ĐĂNG KÝ THÀNH VIÊN", font=("Arial", 14, "bold")).pack(pady=10)
    
    frame = tk.Frame(reg_window)
    frame.pack(padx=20, pady=10)

    # Các ô nhập liệu
    tk.Label(frame, text="Họ tên:").grid(row=0, column=0, sticky="w", pady=5)
    ent_name = tk.Entry(frame, width=30); ent_name.grid(row=0, column=1, pady=5)

    tk.Label(frame, text="Email:").grid(row=1, column=0, sticky="w", pady=5)
    ent_email = tk.Entry(frame, width=30); ent_email.grid(row=1, column=1, pady=5)

    tk.Label(frame, text="Số điện thoại:").grid(row=2, column=0, sticky="w", pady=5)
    ent_phone = tk.Entry(frame, width=30); ent_phone.grid(row=2, column=1, pady=5)

    tk.Label(frame, text="Username:").grid(row=3, column=0, sticky="w", pady=5)
    ent_user = tk.Entry(frame, width=30); ent_user.grid(row=3, column=1, pady=5)

    tk.Label(frame, text="Password:").grid(row=4, column=0, sticky="w", pady=5)
    ent_pass = tk.Entry(frame, width=30, show="*"); ent_pass.grid(row=4, column=1, pady=5)

    def handle_submit():
        name = ent_name.get().strip()
        email = ent_email.get().strip()
        phone = ent_phone.get().strip()
        user = ent_user.get().strip()
        pwd = ent_pass.get().strip()

        if not all([name, email, phone, user, pwd]):
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập đầy đủ thông tin!")
            return

        success, msg = register_user(user, pwd, name, email, phone)
        if success:
            messagebox.showinfo("Thành công", "Đăng ký thành công! Bạn có thể đăng nhập ngay.")
            reg_window.destroy()
        else:
            messagebox.showerror("Lỗi", msg)

    tk.Button(reg_window, text="ĐĂNG KÝ NGAY", command=handle_submit, 
                bg="blue", fg="white", font=("Arial", 10, "bold"), width=20).pack(pady=20)
    

