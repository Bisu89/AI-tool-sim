# Danh sách tính năng AI Sim Designer

## Cập nhật: Offline Fake CAS Simulator

Ứng dụng mặc định hiện chạy simulator. Các mục 1-6 bên dưới lưu lại phạm vi
Milestone 1 và kế hoạch tích hợp game thật trước đó. Trạng thái simulator hiện tại:

| Nhóm tính năng | Simulator offline | Game thật |
|---|---|---|
| Model mặt 12 tham số [0, 1], renderer 2D | Đã triển khai | Không áp dụng trực tiếp |
| Landmarks hình học và trích xuất đặc trưng | Ground truth tổng hợp, có kiểm thử | Backend ảnh thật chưa xác minh |
| Sai số từng đặc trưng, nhóm và trọng số | Đã triển khai | Chưa hiệu chuẩn độ giống |
| Nhận diện CAS/popup/menu/unknown | Marker riêng của simulator | Chưa triển khai detector đã xác minh |
| Calibration đo đáp ứng và lưu profile | Đã triển khai, khôi phục baseline chính xác | Chưa có profile thật |
| Planner một action, giới hạn bước, safety guard | Đã triển khai | Input bị khóa |
| Drag trong canvas bằng sự kiện Qt | Đã triển khai, không điều khiển chuột OS | Không có executor thật |
| Optimizer, pause/stop, giới hạn vòng lặp | Đã triển khai | Chưa tích hợp game |
| Checkpoint, restore best, rollback khi xấu đi | Chính xác cho simulator | Không hỗ trợ restore chính xác |
| Lịch sử JSON, export không ghi đè, load paused | Đã triển khai | Không khôi phục trạng thái game |
| Dashboard target/current, overlay, bảng sai số | Đã triển khai, có test Qt | Viewer quan sát cũ vẫn có |
| CLI headless không cần GUI, game hoặc mạng | Đã triển khai | Không áp dụng |
| RealCASAdapter | Interface, config, safety guards, lỗi có cấu trúc | UNVERIFIED; thao tác input chưa hỗ trợ |

Xem [hướng dẫn simulator](SIMULATOR.md) để chạy và hiểu phạm vi của ground truth.

## Lịch sử: Milestone 1 và kế hoạch tích hợp game thật

Tài liệu mô tả tính năng hiện tại và các chức năng dự kiến theo yêu cầu dự án.
Phiên bản hiện tại tập trung vào Milestone 1: Capture + Landmark Viewer.

## 1. Tính năng đã triển khai

| Tính năng | Mô tả | Trạng thái kiểm chứng |
|---|---|---|
| Giao diện desktop | Dashboard PySide6 hiển thị ảnh tham chiếu và ảnh chụp cạnh nhau | Đã kiểm tra khởi động và vẽ giao diện; chưa kiểm tra đầy đủ thao tác sử dụng |
| Nạp ảnh tham chiếu | Chọn ảnh PNG, JPG, JPEG, BMP hoặc WebP từ máy; hỗ trợ đường dẫn Unicode | Đã triển khai; cần kiểm tra thao tác chọn ảnh thực tế |
| Chụp màn hình | Chụp màn hình chính bằng MSS, chọn theo cờ màn hình chính thay vì thứ tự màn hình | Logic chọn màn hình đã có unit test; chụp thật gặp lỗi Windows BitBlt trong phiên kiểm tra |
| Chọn vùng chụp | Kéo chọn vùng trên ảnh màn hình; có thể nhấn Esc để hủy; quy đổi tọa độ theo tỉ lệ hiển thị | Đã triển khai; chưa kiểm chứng tương tác thực tế và các cấu hình DPI |
| Metadata ảnh chụp | Ghi nhận kích thước, thời gian UTC, nguồn ảnh và vùng chụp trong bộ nhớ | Đã triển khai |
| Phát hiện khuôn mặt | Dùng Haar cascade đi kèm OpenCV để xác định khung khuôn mặt | Đã kiểm tra ảnh trống và đầu vào không hợp lệ; chưa xác minh độ chính xác trên CAS |
| Facial landmarks | Backend MediaPipe Face Mesh tùy chọn, trả về điểm chuẩn hóa theo kích thước ảnh | Backend đã khởi tạo thành công; chưa xác minh phát hiện landmarks trên ảnh mặt thực tế hoặc CAS |
| Overlay | Vẽ khung mặt và landmarks trên ảnh; có công tắc bật/tắt | Giao diện đã vẽ thành công; cần kiểm tra overlay với kết quả phát hiện thực tế |
| Giữ tỉ lệ ảnh | Co giãn ảnh theo vùng hiển thị và giữ nguyên tỉ lệ | Đã triển khai |
| Chế độ degraded | Vẫn xem ảnh và phát hiện khung mặt khi backend landmarks không khả dụng | Provider dự phòng đã có unit test |
| Thông báo lỗi | Hiển thị lỗi đọc ảnh, lỗi chụp màn hình, không tìm thấy mặt hoặc landmarks | Đã triển khai; lỗi capture đã được quan sát trong lần chẩn đoán |
| Cấu hình | Đọc YAML và xác thực bằng Pydantic | Đã có unit tests |
| Logging | Ghi log ra console bằng Python logging | Đã hoạt động trong kiểm tra khởi động |
| Chẩn đoán môi trường | Báo phiên bản Python và các thư viện liên quan | Đã chạy thành công trên Python 3.11.4 |
| Chẩn đoán màn hình | Liệt kê màn hình và thử chụp ảnh không lưu ra đĩa | Đã liệt kê hai màn hình; thao tác chụp gặp lỗi BitBlt |
| Scripts phát triển | Tạo môi trường ảo, cài dependencies và khởi chạy ứng dụng bằng PowerShell | Đã tạo; chưa kiểm chứng toàn bộ script setup trong môi trường ảo mới |
| Kiểm thử tự động | Unit tests cho cấu hình, capture giả lập và vision | Lần chạy gần nhất: 9/9 bài qua |

Ảnh được xử lý local. Ứng dụng hiện hiển thị ảnh chụp trong bộ nhớ, không tự lưu
capture hoặc sửa ảnh tham chiếu gốc. Khi phát hiện nhiều mặt, landmarks hiện chỉ
được yêu cầu cho khuôn mặt đầu tiên mà detector trả về.

## 2. Tính năng dự kiến: CAS Calibration

- Nhận diện trạng thái CAS qua UI anchors hoặc template đã kiểm chứng.
- Trả về UNKNOWN khi không đủ tin cậy để xác định trạng thái game.
- Cho người dùng kiểm tra và xác nhận landmarks.
- Wizard hiệu chuẩn vùng có thể kéo trong CAS.
- Ghi ảnh trước/sau và đo tác động của thao tác hiệu chuẩn.
- Lưu profile gồm phiên bản bố cục CAS, độ phân giải, vùng cửa sổ game, điểm kéo
  chuẩn hóa, hướng kéo, giới hạn, đặc trưng bị ảnh hưởng và kết quả đo.
- Phân biệt profile draft với profile đã kiểm thử.
- Yêu cầu người dùng bật automation rõ ràng sau khi có calibration hợp lệ.

## 3. Tính năng dự kiến: Single-action Automation

- Chuyển tọa độ chuẩn hóa thành tọa độ màn hình qua calibration.
- Kiểm tra cửa sổ game, focus và trạng thái CAS trước mỗi thao tác.
- Từ chối thao tác khi có popup, menu lạ hoặc trạng thái không xác định.
- Đề xuất và thực hiện tối đa một thao tác kéo đã hiệu chuẩn mỗi vòng.
- Giới hạn khoảng cách, tốc độ kéo và thời gian chờ sau thao tác.
- Nút Stop và phím tắt dừng khẩn cấp.
- Chụp ảnh sau thao tác và đánh giá thay đổi.
- Dừng khi kết quả bất thường hoặc xấu đi.

## 4. Tính năng dự kiến: So sánh và tối ưu

- Chuẩn hóa vị trí và kích thước khuôn mặt để so sánh hình học tương đối.
- Tính sai số riêng cho đường viền mặt, mắt, mũi, miệng và hàm/cằm.
- Điều chỉnh trọng số từng nhóm đặc trưng qua cấu hình.
- Hiển thị điểm tổng, sai số từng nhóm và mức tin cậy của phép đo.
- Planner dựa trên sai số và tác động đo được từ calibration.
- Trả về NO_SAFE_ACTION khi không có thao tác đủ dữ liệu để thực hiện.
- Vòng lặp evaluate → propose → execute → capture → evaluate.
- Giới hạn số bước và kích thước mỗi bước; dừng khi hội tụ hoặc vượt giới hạn.
- Lưu điểm tốt nhất đã quan sát và báo cáo các thao tác đã thử.

Điểm so sánh dự kiến là chỉ số hình học; chưa có mô hình hiệu chuẩn để diễn giải
thành xác suất giống nhau.

## 5. Tính năng dự kiến: Phiên làm việc và khôi phục

- Lịch sử ảnh, thời gian, thao tác, điểm số và kết quả.
- Xuất báo cáo phiên dưới dạng JSON.
- Checkpoint ứng dụng và ghi nhận trạng thái tốt nhất đã quan sát.
- Pause, Stop và tiếp tục phiên làm việc.
- Hỗ trợ Undo/Restore khi cơ chế khôi phục đã được kiểm chứng.
- Dừng và yêu cầu phục hồi thủ công nếu không thể xác minh khôi phục tự động.
- Nhật ký phiên, bảng sai số đặc trưng và trạng thái calibration trong dashboard.

Checkpoint ứng dụng không tự khôi phục hình học khuôn mặt trong game. Kéo ngược
chuột cũng chưa được xác minh là một cơ chế undo chính xác.

## 6. Giới hạn và bước kiểm tra tiếp theo

- Chưa kiểm thử tích hợp trên The Sims 4 thực tế.
- Chưa có profile CAS đã hiệu chuẩn hoặc khả năng tự động điều khiển game.
- Capture thật chưa thành công trong phiên kiểm tra do lỗi BitBlt; cần thử lại
  trong phiên desktop Windows tương tác bằng `py -3.11 scripts/diagnose_screen.py`.
- Cần kiểm tra nạp ảnh mặt, capture vùng chọn, landmarks và overlay bằng thao tác
  thực tế trước khi xác nhận toàn bộ tiêu chí Milestone 1.
- Chất lượng landmark trên mặt Sim, Alpha CC, tóc che mặt và các góc nhìn khác nhau
  chưa được kiểm chứng.
- Tạo mesh, Blender và tự động lưu Sim vào My Library không thuộc MVP hiện tại.
  Người dùng dự kiến lưu Sim thủ công trong game.

Xem thêm [README](../README.md), [Kiến trúc](ARCHITECTURE.md),
[Kế hoạch MVP](MVP_PLAN.md) và [Giới hạn](LIMITATIONS.md).
