import os, sys, time, atexit

def acquire_or_exit(name, stale_after=300):
    """Chặn một tiến trình song song vô tình chạy cùng script này.

    Môi trường này thỉnh thoảng khởi động một bản sao lệnh Python bằng
    interpreter khác ngay sau lệnh gốc (quan sát 2026-09-20, hai lần liên
    tiếp -- xem RPA_docs/TRACE.md). Hai phiên Selenium cùng gắn vào một cổng
    debug sẽ tranh giành thao tác chuột/phím. Khoá file đơn giản (không cần
    kiểm tra PID còn sống, đủ dùng cho một lệnh dò ngắn) khiến bản sao tự
    thoát thay vì tranh chấp.
    """
    lock_path = os.path.join(os.environ.get("TEMP", "C:/Users/Admin/AppData/Local/Temp"),
                              "rpa_lock_%s.pid" % name)
    if os.path.exists(lock_path):
        age = time.time() - os.path.getmtime(lock_path)
        if age < stale_after:
            print("[lock] %s da co tien trinh khac chay %.0fs truoc -- tu thoat"
                  % (name, age), file=sys.stderr)
            sys.exit(97)
    with open(lock_path, "w") as f:
        f.write(str(os.getpid()))
    atexit.register(lambda: os.path.exists(lock_path) and os.remove(lock_path))
