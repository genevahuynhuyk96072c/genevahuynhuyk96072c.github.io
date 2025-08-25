import os
from datetime import datetime
import requests
from tqdm import tqdm

# API Key của bạn (lấy từ tài khoản GoFile)
GOFILE_API_KEY = "vc5njCimJvXwoDEtsidgrTWoU9ZW61w6"

# ID của thư mục cố định trên GoFile (ví dụ: "scd")
GOFILE_FOLDER_ID = "d65cd8bd-5b11-44ba-83ad-7589970bbda4"

# Thư mục log file
LOG_FOLDER = "./logs"

if not os.path.exists(LOG_FOLDER):
    os.makedirs(LOG_FOLDER)  # Tạo thư mục logs nếu chưa tồn tại


def get_best_server():
    """
    Lấy server tốt nhất từ GoFile API.
    """
    url = "https://api.gofile.io/servers"
    try:
        response = requests.get(url, timeout=10)  # Gửi yêu cầu GET
        if response.status_code == 200:
            response_json = response.json()
            if response_json["status"] == "ok" and "servers" in response_json["data"]:
                return response_json["data"]["servers"][0]["name"]  # Lấy server đầu tiên
            else:
                raise Exception("API không trả về danh sách server hợp lệ.")
        else:
            raise Exception(f"Lỗi HTTP: {response.status_code}")
    except Exception as e:
        print(f"Lỗi khi lấy thông tin server: {e}")
        raise Exception("Không thể lấy server tốt nhất từ GoFile.")


def upload_file_to_gofile(file_path, folder_id):
    """
    Tải file lên thư mục được chỉ định qua folder_id trên GoFile.
    """
    if not os.path.isfile(file_path):
        raise Exception(f"Tệp tin không tồn tại: {file_path}")

    server = get_best_server()
    url = f"https://{server}.gofile.io/contents/uploadfile"

    headers = {"Authorization": f"Bearer {GOFILE_API_KEY}"}
    file_size = os.path.getsize(file_path)
    file_name = os.path.basename(file_path)

    with open(file_path, "rb") as file:
        with tqdm(total=file_size, unit="B", unit_scale=True, desc=f"Đang tải lên {file_name}") as progress_bar:
            files = {"file": file}
            data = {"folderId": folder_id}  # Chỉ định folderId để tải file vào thư mục
            response = requests.post(url, headers=headers, files=files, data=data)
            progress_bar.update(file_size)

    # Kiểm tra phản hồi từ API
    if response.status_code == 200:
        response_json = response.json()
        if response_json["status"] == "ok":
            return response_json["data"]["downloadPage"]  # Link tải file
        else:
            raise Exception(f"Lỗi khi tải file lên: {response_json.get('status')}")
    else:
        raise Exception(f"Lỗi HTTP: {response.status_code}, Phản hồi: {response.text}")


def sync_path(path, folder_id):
    """
    Đồng bộ đường dẫn tới GoFile (có thể là tệp tin hoặc thư mục).
    """
    start_time = datetime.now()
    log_file_name = start_time.strftime("%Y-%m-%d_%H-%M-%S") + ".log"
    log_file_path = os.path.join(LOG_FOLDER, log_file_name)

    with open(log_file_path, "w", encoding="utf-8") as log_file:
        log_file.write(f"Đồng bộ bắt đầu từ: {start_time}\n")
        log_file.write(f"Đường dẫn: {path}\n")
        log_file.write(f"Thư mục GoFile: {folder_id}\n")
        log_file.write("\nCác file đã tải lên:\n")

        if os.path.isfile(path):
            # Nếu là file, tải lên trực tiếp
            try:
                log_file.write(f"Tải tệp tin: {path}\n")
                upload_start_time = datetime.now()

                download_link = upload_file_to_gofile(path, folder_id)

                upload_end_time = datetime.now()
                log_file.write(f"Tải thành công: {path}\n")
                log_file.write(f"Link Download: {download_link}\n")
                log_file.write(f"Bắt đầu: {upload_start_time}, Kết thúc: {upload_end_time}\n\n")
            except Exception as e:
                log_file.write(f"Lỗi khi tải file {path}: {str(e)}\n")
        elif os.path.isdir(path):
            # Nếu là thư mục, tải lên từng file trong thư mục
            for root, _, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        log_file.write(f"Tải tệp tin: {file_path}\n")
                        upload_start_time = datetime.now()

                        download_link = upload_file_to_gofile(file_path, folder_id)

                        upload_end_time = datetime.now()
                        log_file.write(f"Tải thành công: {file_path}\n")
                        log_file.write(f"Link Download: {download_link}\n")
                        log_file.write(f"Bắt đầu: {upload_start_time}, Kết thúc: {upload_end_time}\n\n")
                    except Exception as e:
                        log_file.write(f"Lỗi khi tải file {file_path}: {str(e)}\n")
        else:
            print("Đường dẫn không hợp lệ.")
            return

        end_time = datetime.now()
        log_file.write(f"\nĐồng bộ hoàn tất lúc: {end_time}\n")
        log_file.write(f"Thời gian thực thi: {end_time - start_time}\n")


def main():
    print("=== Đồng Bộ Dữ Liệu Lên GoFile ===")
    print("Vui lòng chọn thư mục hoặc tệp tin để tải lên.")
    path = input("Nhập đường dẫn tới thư mục hoặc tệp tin (ví dụ: C:\\Users\\Hoang\\Desktop\\thumuc hoặc C:\\Users\\Hoang\\Desktop\\file.txt): ")

    # Kiểm tra nếu đường dẫn không hợp lệ
    if not os.path.exists(path):
        print("Đường dẫn không tồn tại. Vui lòng thử lại.")
        return

    print("Đang xử lý...")
    sync_path(path, GOFILE_FOLDER_ID)
    print(f"Hoàn tất. Xem log trong thư mục: {LOG_FOLDER}")


if __name__ == "__main__":
    main()
