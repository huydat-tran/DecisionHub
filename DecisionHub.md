**DECISIONHUB**

**HỆ THỐNG HỖ TRỢ RA QUYẾT ĐỊNH**

**TÀI LIỆU XÁC ĐỊNH PHẠM VI\
VÀ KẾ HOẠCH TRIỂN KHAI DỰ ÁN**

**Phiên bản 1.1 \| Ngày 09/11/2026\
**Thời gian dự kiến: 3 tuần \| Quy mô nhóm: 6 thành viên

**NGUYÊN TẮC XUYÊN SUỐT**

> **Hoàn thiện Food trước -- mở rộng Travel sau -- chỉ triển khai
> History và Group Voting khi đáp ứng điều kiện ưu tiên.**

# QUẢN LÝ TÀI LIỆU

  -----------------------------------------------------------------------
  **Thuộc tính**                      **Nội dung**
  ----------------------------------- -----------------------------------
  Tên tài liệu                        DecisionHub -- Tài liệu xác định
                                      phạm vi và kế hoạch triển khai dự
                                      án

  Phiên bản                           1.0

  Mục đích                            Làm căn cứ thống nhất những gì nhóm
                                      cần xây dựng, thứ tự thực hiện, đầu
                                      ra và tiêu chí nghiệm thu.

  Đối tượng sử dụng                   Toàn bộ 6 thành viên; dùng trong
                                      họp nhóm, phân công, theo dõi tiến
                                      độ, review và nghiệm thu.

  Phạm vi áp dụng                     MVP DecisionHub trong kế hoạch 3
                                      tuần; mọi thay đổi cần được nhóm
                                      thống nhất và ghi nhận.

  Tài liệu tham chiếu                 DecisionHub Project Development
                                      Document v2.0; quyết định điều
                                      chỉnh phạm vi tại Sprint 1 -- Ngày
                                      1.
  -----------------------------------------------------------------------

## Quy tắc sử dụng

-   Đây là tài liệu định hướng và kiểm soát phạm vi, không phải danh
    sách ý tưởng mở rộng.

-   Mọi thành viên sử dụng cùng một phiên bản tài liệu khi phân công và
    nghiệm thu.

-   Nếu phát sinh yêu cầu mới, phải xác định mức ưu tiên, chi phí thời
    gian và chức năng nào sẽ bị thay thế hoặc lùi lại.

-   Không tự ý nâng một tính năng SHOULD/OPTIONAL thành MUST nếu chưa
    được cả nhóm thống nhất.

# Contents {#contents .TOC-Heading}

[QUẢN LÝ TÀI LIỆU [2](#quản-lý-tài-liệu)](#quản-lý-tài-liệu)

[Quy tắc sử dụng [2](#quy-tắc-sử-dụng)](#quy-tắc-sử-dụng)

[1. TỔNG QUAN VÀ MỤC TIÊU DỰ ÁN
[3](#tổng-quan-và-mục-tiêu-dự-án)](#tổng-quan-và-mục-tiêu-dự-án)

[1.1. Giới thiệu [3](#giới-thiệu)](#giới-thiệu)

[1.2. Các phân hệ định hướng
[3](#các-phân-hệ-định-hướng)](#các-phân-hệ-định-hướng)

[1.3. Mục tiêu MVP [3](#mục-tiêu-mvp)](#mục-tiêu-mvp)

[1.4. Giá trị cốt lõi [3](#giá-trị-cốt-lõi)](#giá-trị-cốt-lõi)

[2. PHẠM VI MVP VÀ THỨ TỰ ƯU TIÊN
[3](#phạm-vi-mvp-và-thứ-tự-ưu-tiên)](#phạm-vi-mvp-và-thứ-tự-ưu-tiên)

[2.1. Quyết định phạm vi [3](#quyết-định-phạm-vi)](#quyết-định-phạm-vi)

[2.2. Nguyên tắc khóa phạm vi
[4](#nguyên-tắc-khóa-phạm-vi)](#nguyên-tắc-khóa-phạm-vi)

[2.3. Quy tắc ưu tiên khi thiếu thời gian
[4](#quy-tắc-ưu-tiên-khi-thiếu-thời-gian)](#quy-tắc-ưu-tiên-khi-thiếu-thời-gian)

[3. ĐỐI TƯỢNG SỬ DỤNG VÀ LUỒNG NGHIỆP VỤ TỔNG THỂ
[4](#đối-tượng-sử-dụng-và-luồng-nghiệp-vụ-tổng-thể)](#đối-tượng-sử-dụng-và-luồng-nghiệp-vụ-tổng-thể)

[3.1. Đối tượng sử dụng MVP
[4](#đối-tượng-sử-dụng-mvp)](#đối-tượng-sử-dụng-mvp)

[3.2. Luồng Quick Search [4](#luồng-quick-search)](#luồng-quick-search)

[3.3. Luồng Smart Recommendation
[4](#luồng-smart-recommendation)](#luồng-smart-recommendation)

[4. ĐẶC TẢ CHỨC NĂNG FOOD -- PHẠM VI BẮT BUỘC
[5](#đặc-tả-chức-năng-food-phạm-vi-bắt-buộc)](#đặc-tả-chức-năng-food-phạm-vi-bắt-buộc)

[4.1. Mục tiêu [5](#mục-tiêu)](#mục-tiêu)

[4.2. Quick Search món ăn
[5](#quick-search-món-ăn)](#quick-search-món-ăn)

[4.3. Gợi ý món ăn theo tiêu chí
[5](#gợi-ý-món-ăn-theo-tiêu-chí)](#gợi-ý-món-ăn-theo-tiêu-chí)

[4.4. Trang chi tiết món ăn
[5](#trang-chi-tiết-món-ăn)](#trang-chi-tiết-món-ăn)

[4.5. Không thuộc phạm vi Food
[6](#không-thuộc-phạm-vi-food)](#không-thuộc-phạm-vi-food)

[5. ĐẶC TẢ CHỨC NĂNG TRAVEL -- PHẠM VI CƠ BẢN
[6](#đặc-tả-chức-năng-travel-phạm-vi-cơ-bản)](#đặc-tả-chức-năng-travel-phạm-vi-cơ-bản)

[5.1. Mục tiêu và điều kiện bắt đầu
[6](#mục-tiêu-và-điều-kiện-bắt-đầu)](#mục-tiêu-và-điều-kiện-bắt-đầu)

[5.2. Quick Search địa điểm
[6](#quick-search-địa-điểm)](#quick-search-địa-điểm)

[5.3. Gợi ý theo điều kiện -- chỉ làm khi khả thi
[6](#gợi-ý-theo-điều-kiện-chỉ-làm-khi-khả-thi)](#gợi-ý-theo-điều-kiện-chỉ-làm-khi-khả-thi)

[5.4. Không thuộc phạm vi Travel
[6](#không-thuộc-phạm-vi-travel)](#không-thuộc-phạm-vi-travel)

[6. HISTORY VÀ GROUP VOTING -- ĐIỀU KIỆN TRIỂN KHAI
[6](#history-và-group-voting-điều-kiện-triển-khai)](#history-và-group-voting-điều-kiện-triển-khai)

[6.1. History [6](#history)](#history)

[6.2. Group Voting [7](#group-voting)](#group-voting)

[6.3. Cổng quyết định triển khai
[7](#cổng-quyết-định-triển-khai)](#cổng-quyết-định-triển-khai)

[7. DECISION ENGINE -- LỌC, CHẤM ĐIỂM VÀ XẾP HẠNG
[7](#decision-engine-lọc-chấm-điểm-và-xếp-hạng)](#decision-engine-lọc-chấm-điểm-và-xếp-hạng)

[7.1. Trách nhiệm [7](#trách-nhiệm)](#trách-nhiệm)

[7.2. Quy trình [7](#quy-trình)](#quy-trình)

[7.3. Công thức WSM [8](#công-thức-wsm)](#công-thức-wsm)

[7.4. Rubric Food mặc định
[8](#rubric-food-mặc-định)](#rubric-food-mặc-định)

[7.5. Quy tắc xử lý [8](#quy-tắc-xử-lý)](#quy-tắc-xử-lý)

[8. DỮ LIỆU VÀ THIẾT KẾ CƠ SỞ DỮ LIỆU
[8](#dữ-liệu-và-thiết-kế-cơ-sở-dữ-liệu)](#dữ-liệu-và-thiết-kế-cơ-sở-dữ-liệu)

[8.1. Nguyên tắc [8](#nguyên-tắc)](#nguyên-tắc)

[8.2. Các bảng lõi đề xuất
[8](#các-bảng-lõi-đề-xuất)](#các-bảng-lõi-đề-xuất)

[8.3. Dữ liệu mẫu tối thiểu
[9](#dữ-liệu-mẫu-tối-thiểu)](#dữ-liệu-mẫu-tối-thiểu)

[9. API VÀ NGUYÊN TẮC TÍCH HỢP
[9](#api-và-nguyên-tắc-tích-hợp)](#api-và-nguyên-tắc-tích-hợp)

[9.1. API Food bắt buộc [9](#api-food-bắt-buộc)](#api-food-bắt-buộc)

[9.2. API Travel cơ bản [9](#api-travel-cơ-bản)](#api-travel-cơ-bản)

[9.3. API chung [9](#api-chung)](#api-chung)

[9.4. Quy tắc API [9](#quy-tắc-api)](#quy-tắc-api)

[10. GIAO DIỆN VÀ YÊU CẦU TRẢI NGHIỆM
[10](#giao-diện-và-yêu-cầu-trải-nghiệm)](#giao-diện-và-yêu-cầu-trải-nghiệm)

[10.1. Màn hình bắt buộc [10](#màn-hình-bắt-buộc)](#màn-hình-bắt-buộc)

[10.2. Nguyên tắc UX [10](#nguyên-tắc-ux)](#nguyên-tắc-ux)

[11. KIẾN TRÚC, CÔNG NGHỆ VÀ CẤU TRÚC MÃ NGUỒN
[10](#kiến-trúc-công-nghệ-và-cấu-trúc-mã-nguồn)](#kiến-trúc-công-nghệ-và-cấu-trúc-mã-nguồn)

[11.1. Kiến trúc [10](#kiến-trúc)](#kiến-trúc)

[11.2. Công nghệ [10](#công-nghệ)](#công-nghệ)

[11.3. Cấu trúc backend tham khảo
[11](#cấu-trúc-backend-tham-khảo)](#cấu-trúc-backend-tham-khảo)

[11.4. Nguyên tắc phụ thuộc
[11](#nguyên-tắc-phụ-thuộc)](#nguyên-tắc-phụ-thuộc)

[12. PHÂN CÔNG NHÓM VÀ QUY TẮC PHỐI HỢP
[11](#phân-công-nhóm-và-quy-tắc-phối-hợp)](#phân-công-nhóm-và-quy-tắc-phối-hợp)

[12.1. Quy tắc làm việc Git
[12](#quy-tắc-làm-việc-git)](#quy-tắc-làm-việc-git)

[12.2. Quy tắc phối hợp [12](#quy-tắc-phối-hợp)](#quy-tắc-phối-hợp)

[14. KIỂM THỬ, NGHIỆM THU VÀ DEFINITION OF DONE
[12](#kiểm-thử-nghiệm-thu-và-definition-of-done)](#kiểm-thử-nghiệm-thu-và-definition-of-done)

[14.1. Kiểm thử tối thiểu
[12](#kiểm-thử-tối-thiểu)](#kiểm-thử-tối-thiểu)

[14.2. Definition of Done cho Food
[12](#definition-of-done-cho-food)](#definition-of-done-cho-food)

[14.3. Definition of Done cho toàn dự án
[13](#definition-of-done-cho-toàn-dự-án)](#definition-of-done-cho-toàn-dự-án)

# 1. TỔNG QUAN VÀ MỤC TIÊU DỰ ÁN

## 1.1. Giới thiệu

DecisionHub là website hỗ trợ người dùng đưa ra lựa chọn phù hợp dựa
trên nhu cầu và các điều kiện cụ thể. Thay vì phải tìm kiếm ở nhiều nơi
rồi tự so sánh, người dùng có thể tìm nhanh hoặc nhập một số tiêu chí để
hệ thống lọc, chấm điểm và sắp xếp các phương án.

## 1.2. Các phân hệ định hướng

  -----------------------------------------------------------------------
  **Phân hệ**             **Vai trò trong sản     **Mức ưu tiên**
                          phẩm**                  
  ----------------------- ----------------------- -----------------------
  WhatShouldIEat (Food)   Tìm kiếm và gợi ý món   Bắt buộc -- hoàn thiện
                          ăn theo ngân sách, bữa  trước
                          ăn, thời gian chuẩn bị  
                          và sở thích.            

  WhereShouldITravel      Tìm kiếm và gợi ý địa   Cơ bản -- sau Food
  (Travel)                điểm theo khu vực, ngân 
                          sách, thời lượng và     
                          loại hình trải nghiệm.  

  History                 Cho phép xem lại hoạt   Sau khi Food hoàn thành
                          động tìm kiếm/gợi ý     
                          trước đây.              

  Group Voting            Hỗ trợ nhóm cùng xem và Tùy chọn -- chỉ khi còn
                          bình chọn phương án.    thời gian
  -----------------------------------------------------------------------

## 1.3. Mục tiêu MVP

-   Có một luồng Food hoàn chỉnh từ giao diện đến API và cơ sở dữ liệu.

-   Người dùng tìm món bằng từ khóa và bộ lọc thiết yếu.

-   Người dùng nhận được danh sách gợi ý có thứ hạng, điểm phù hợp và lý
    do giải thích.

-   Có thể tái sử dụng quy trình lọc -- chấm điểm -- xếp hạng cho Travel
    ở mức phù hợp.

-   Có bản chạy ổn định, dữ liệu mẫu, hướng dẫn cài đặt và kịch bản
    demo.

## 1.4. Giá trị cốt lõi

-   Tìm nhanh: bắt đầu bằng một ô tìm kiếm, không cần điền biểu mẫu dài.

-   Lọc đúng: loại phương án vi phạm điều kiện bắt buộc.

-   Xếp hạng dễ hiểu: kết quả được sắp xếp theo mức độ phù hợp.

-   Giải thích được: nêu lý do dựa trên dữ liệu và tiêu chí thực tế.

# 2. PHẠM VI MVP VÀ THỨ TỰ ƯU TIÊN

## 2.1. Quyết định phạm vi

  -----------------------------------------------------------------------
  **Mức**           **Phân hệ/chức    **Phạm vi cam     **Điều kiện
                    năng**            kết**             chuyển bước**
  ----------------- ----------------- ----------------- -----------------
  P0 -- MUST        Food              Quick Search, bộ  Phải chạy
                                      lọc cơ bản, gợi ý end-to-end và qua
                                      theo tiêu chí,    kiểm thử trọng
                                      lọc điều kiện,    yếu.
                                      xếp hạng, giải    
                                      thích, trang chi  
                                      tiết.             

  P1 -- SHOULD      Travel            Tìm kiếm cơ bản,  Chỉ bắt đầu khi
                                      bộ lọc thiết yếu, Food ổn định;
                                      danh sách và      không làm ảnh
                                      trang chi tiết;   hưởng Food.
                                      gợi ý nếu nền     
                                      tảng dùng chung   
                                      đã sẵn sàng.      

  P2 -- OPTIONAL    History           Lưu/xem lịch sử   Chỉ triển khai
                                      tìm kiếm hoặc gợi sau Food; cần
                                      ý ở mức tối       thống nhất có yêu
                                      thiểu.            cầu đăng nhập hay
                                                        không.

  P3 -- OPTIONAL    Group Voting      Tạo nhóm/bình     Chỉ làm khi P0,
                                      chọn phương án ở  P1 và kiểm thử
                                      phạm vi tối giản  chính đã hoàn
                                      nếu đủ thời gian. thành.

  OUT OF SCOPE      Các tính năng mở  Không triển khai  Không tự ý bổ
                    rộng khác         trong MVP trừ khi sung.
                                      nhóm thay thế một 
                                      hạng mục khác     
                                      bằng quyết định   
                                      chính thức.       
  -----------------------------------------------------------------------

## 2.2. Nguyên tắc khóa phạm vi

-   Không phát triển thêm module thứ ba.

-   Không triển khai Group Voting trước Food và Travel.

-   Không tích hợp AI/LLM hội thoại trong MVP; Quick Search sử dụng từ
    khóa và bộ lọc có cấu trúc.

-   Không phụ thuộc API bên ngoài để có dữ liệu cốt lõi; sử dụng dữ liệu
    mẫu do nhóm chuẩn bị.

-   Không làm bản đồ tương tác, GPS, định tuyến, đặt vé/đặt bàn, thanh
    toán hoặc cập nhật giá thời gian thực.

-   Không xây RBAC phức tạp, dashboard quản trị lớn, microservices hoặc
    cá nhân hóa nâng cao.

## 2.3. Quy tắc ưu tiên khi thiếu thời gian

Khi tiến độ chậm, nhóm cắt giảm theo thứ tự ngược với mức ưu tiên: Group
Voting → History → phần mở rộng của Travel. Không cắt bỏ các phần cốt
lõi của Food để giữ lại tính năng phụ.

# 3. ĐỐI TƯỢNG SỬ DỤNG VÀ LUỒNG NGHIỆP VỤ TỔNG THỂ

## 3.1. Đối tượng sử dụng MVP

-   Người dùng thông thường muốn tìm món ăn hoặc địa điểm phù hợp.

-   Trong phạm vi MVP cơ bản, người dùng có thể sử dụng tìm kiếm mà
    không cần đăng nhập.

-   Nếu triển khai History hoặc Group Voting, nhóm phải thống nhất cách
    nhận diện người dùng và phạm vi dữ liệu trước khi thiết kế.

## 3.2. Luồng Quick Search

1.  Người dùng mở module Food hoặc Travel.

2.  Nhập tên món/địa điểm, nguyên liệu, danh mục hoặc từ khóa mô tả.

3.  Có thể chọn chip lọc nhanh hoặc mở bộ lọc bổ sung.

4.  Backend truy vấn dữ liệu và áp dụng các bộ lọc.

5.  Frontend hiển thị danh sách kết quả hoặc trạng thái không có kết
    quả.

6.  Người dùng mở trang chi tiết của một kết quả.

## 3.3. Luồng Smart Recommendation

7.  Người dùng chọn các điều kiện cần thiết trong biểu mẫu ngắn.

8.  Backend lấy danh sách ứng viên từ cơ sở dữ liệu.

9.  Hệ thống loại các phương án vi phạm điều kiện bắt buộc.

10. Decision Engine chấm điểm các phương án còn lại theo tiêu chí và
    trọng số.

11. Hệ thống sắp xếp kết quả, trả về Top 5 cùng điểm số và lý do.

12. Frontend hiển thị kết quả và cho phép mở trang chi tiết.

Quick Search ưu tiên độ liên quan của từ khóa; Smart Recommendation ưu
tiên mức độ phù hợp với tiêu chí. Hai luồng dùng chung kho dữ liệu nhưng
có mục đích sắp xếp khác nhau.

# 4. ĐẶC TẢ CHỨC NĂNG FOOD -- PHẠM VI BẮT BUỘC

## 4.1. Mục tiêu

Food là luồng trọng tâm và là cơ sở để nhóm hoàn thiện dữ liệu, API,
Decision Engine và cách tích hợp frontend/backend. Chỉ chuyển trọng tâm
sang Travel khi Food đạt tiêu chí nghiệm thu.

## 4.2. Quick Search món ăn

  -----------------------------------------------------------------------
  **Thành phần**          **Yêu cầu chức năng**   **Ghi chú phạm vi**
  ----------------------- ----------------------- -----------------------
  Ô tìm kiếm              Tìm theo tên món,       Không bắt buộc
                          nguyên liệu, danh mục   debounce; nút Search là
                          hoặc từ khóa mô tả; hỗ  đủ.
                          trợ Enter hoặc nút      
                          Search.                 

  Chip lọc nhanh          Bữa sáng/trưa/tối; mức  Chỉ hiển thị chip có dữ
                          giá tham khảo; thời     liệu hỗ trợ.
                          gian chuẩn bị.          

  Bộ lọc bổ sung          Loại món, giá tối đa,   Trường tùy chọn;
                          thời gian chuẩn bị tối  validate dữ liệu đầu
                          đa, nguyên liệu cần     vào.
                          tránh.                  

  Sắp xếp                 Mặc định theo độ liên   Không cần thuật toán
                          quan; có thể chọn giá   tìm kiếm phức tạp.
                          thấp đến cao hoặc thời  
                          gian ngắn đến dài.      

  Kết quả                 Tên món, ảnh nếu có,    Ảnh có thể dùng ảnh mặc
                          giá tham khảo, thời     định.
                          gian chuẩn bị, loại bữa 
                          ăn và nhãn phù hợp.     

  Không có kết quả        Thông báo rõ ràng; gợi  Bắt buộc có empty
                          ý bỏ bớt bộ lọc hoặc    state.
                          đổi từ khóa.            
  -----------------------------------------------------------------------

## 4.3. Gợi ý món ăn theo tiêu chí

  -----------------------------------------------------------------------
  **Thành phần**                      **Yêu cầu**
  ----------------------------------- -----------------------------------
  Điều kiện đầu vào                   Ngân sách tối đa; loại bữa ăn; thời
                                      gian chuẩn bị tối đa; nguyên liệu
                                      cần tránh.

  Trọng số mặc định                   Giá 40%; mức phù hợp nhu cầu/khẩu
                                      vị 35%; thời gian chuẩn bị 25%.

  Lọc bắt buộc                        Loại món vượt ngân sách, sai loại
                                      bữa ăn nếu được chọn là điều kiện
                                      bắt buộc, hoặc chứa nguyên liệu cần
                                      tránh.

  Chấm điểm                           Chấm từng tiêu chí theo thang
                                      0--100, sau đó tính tổng điểm có
                                      trọng số.

  Kết quả                             Trả về tối đa 5 món theo thứ tự
                                      điểm giảm dần.

  Giải thích                          Hiển thị 1--3 lý do có căn cứ, ví
                                      dụ: nằm trong ngân sách, chuẩn bị
                                      nhanh, phù hợp loại bữa ăn.
  -----------------------------------------------------------------------

## 4.4. Trang chi tiết món ăn

-   Tên món và mô tả ngắn.

-   Ảnh minh họa nếu có; nếu thiếu ảnh phải có ảnh mặc định.

-   Giá tham khảo, thời gian chuẩn bị và loại bữa ăn.

-   Danh sách nguyên liệu chính và danh mục.

-   Nút quay lại danh sách; cố gắng giữ từ khóa và bộ lọc trước đó.

## 4.5. Không thuộc phạm vi Food

-   Công thức nấu ăn đầy đủ, hướng dẫn từng bước.

-   Giỏ hàng, đặt món, giao hàng hoặc thanh toán.

-   Tính toán dinh dưỡng y khoa hoặc tư vấn sức khỏe.

-   Nhận diện ảnh nguyên liệu, chatbot đầu bếp hoặc cá nhân hóa nâng
    cao.

# 5. ĐẶC TẢ CHỨC NĂNG TRAVEL -- PHẠM VI CƠ BẢN

## 5.1. Mục tiêu và điều kiện bắt đầu

Travel là phân hệ thứ hai, chỉ triển khai sau khi Food chạy ổn định.
Travel ưu tiên trải nghiệm tìm kiếm địa điểm và hiển thị thông tin cơ
bản; không đặt yêu cầu ngang với Food nếu nguồn lực không đủ.

## 5.2. Quick Search địa điểm

  -----------------------------------------------------------------------
  **Thành phần**                      **Yêu cầu chức năng**
  ----------------------------------- -----------------------------------
  Ô tìm kiếm                          Tìm theo tên địa điểm, tỉnh/thành,
                                      khu vực, loại hình hoặc từ khóa mô
                                      tả.

  Chip lọc nhanh                      Loại hình trải nghiệm, thời lượng
                                      chuyến đi hoặc mức ngân sách phổ
                                      biến.

  Bộ lọc cơ bản                       Khu vực, ngân sách tham khảo, thời
                                      lượng chuyến đi và loại hình trải
                                      nghiệm.

  Kết quả                             Tên địa điểm, khu vực, chi phí tham
                                      khảo, thời lượng gợi ý và loại
                                      hình.

  Trang chi tiết                      Mô tả ngắn, hoạt động nổi bật, khu
                                      vực, chi phí tham khảo và thời
                                      lượng.
  -----------------------------------------------------------------------

## 5.3. Gợi ý theo điều kiện -- chỉ làm khi khả thi

-   Có thể tái sử dụng quy trình lọc và xếp hạng đã hoàn thiện ở Food.

-   Điều kiện cơ bản: ngân sách tối đa, thời lượng, khu vực và loại hình
    trải nghiệm.

-   Nếu triển khai scoring, tiêu chí và trọng số phải được nhóm thống
    nhất riêng cho Travel.

-   Nếu không đủ thời gian, ưu tiên Quick Search, bộ lọc và trang chi
    tiết; không cố hoàn thiện Recommendation bằng mọi giá.

## 5.4. Không thuộc phạm vi Travel

-   Bản đồ tương tác, định vị GPS, quãng đường và ETA.

-   Lập lịch trình nhiều chặng, đặt vé, đặt phòng hoặc đặt bàn.

-   Cập nhật giá thời gian thực hoặc đồng bộ dữ liệu du lịch bên thứ ba.

-   Đảm bảo chi phí tham khảo là giá thực tế tại thời điểm người dùng
    đi.

# 6. HISTORY VÀ GROUP VOTING -- ĐIỀU KIỆN TRIỂN KHAI

## 6.1. History

History là chức năng tùy chọn, chỉ được xem xét sau khi Food đã hoàn
thành và ổn định.

-   Phạm vi tối thiểu có thể gồm danh sách các lần tìm kiếm/gợi ý gần
    đây.

-   Mỗi bản ghi nên lưu loại hoạt động, từ khóa/điều kiện chính, thời
    điểm và kết quả tham chiếu nếu phù hợp.

-   Nhóm phải quyết định History lưu theo tài khoản hay theo phiên trình
    duyệt trước khi thiết kế database.

-   Không triển khai nếu việc nhận diện người dùng làm phát sinh thêm hệ
    thống đăng nhập/phân quyền vượt khả năng.

## 6.2. Group Voting

Group Voting là tính năng mở rộng, không phải điều kiện để nghiệm thu
MVP.

-   Chỉ bắt đầu khi Food hoàn thành, Travel đạt mức mục tiêu và thời
    gian kiểm thử vẫn được bảo đảm.

-   Nếu được duyệt, nhóm cần chốt rõ: tạo nhóm, tham gia nhóm, danh sách
    phương án, cách bỏ phiếu và cách công bố kết quả.

-   Không tự động triển khai chat, realtime, nhiều vai trò hoặc thuật
    toán bình chọn phức tạp.

## 6.3. Cổng quyết định triển khai

  -----------------------------------------------------------------------
  **Cổng kiểm soát**      **Điều kiện tối thiểu** **Quyết định**
  ----------------------- ----------------------- -----------------------
  Gate 1 -- Food          Food chạy end-to-end;   Được phép chuyển nguồn
                          API, dữ liệu và các     lực sang Travel.
                          test trọng yếu hoạt     
                          động.                   

  Gate 2 -- Travel        Travel đạt phạm vi cơ   Có thể xem xét History.
                          bản; không còn lỗi      
                          nghiêm trọng ở Food.    

  Gate 3 -- Hoàn thiện    Các luồng chính đã tích Có thể xem xét Group
                          hợp; còn đủ thời gian   Voting.
                          regression test và      
                          demo.                   

  Gate 4 -- Chốt dự án    Không còn lỗi blocker;  Đóng phạm vi, không
                          README, seed và demo    thêm tính năng.
                          sẵn sàng.               
  -----------------------------------------------------------------------

# 7. DECISION ENGINE -- LỌC, CHẤM ĐIỂM VÀ XẾP HẠNG

## 7.1. Trách nhiệm

Decision Engine xử lý danh sách ứng viên đã được module Food hoặc Travel
chuẩn bị. Engine không truy vấn database và không chứa logic đặc thù của
từng domain.

## 7.2. Quy trình

  -----------------------------------------------------------------------
  **Bước**          **Tên**           **Mô tả**         **Đầu ra**
  ----------------- ----------------- ----------------- -----------------
  1                 Candidate         Module lấy danh   Danh sách ứng
                    Retrieval         sách ứng viên từ  viên.
                                      database theo từ  
                                      khóa/điều kiện    
                                      truy vấn.         

  2                 Constraint        Loại các phương   Danh sách hợp lệ.
                    Filtering         án vi phạm điều   
                                      kiện bắt buộc.    

  3                 Criteria Scoring  Chuyển từng tiêu  Điểm từng tiêu
                                      chí thành điểm    chí.
                                      0--100 theo       
                                      rubric.           

  4                 Weighted Sum      Nhân điểm tiêu    Điểm tổng.
                    Model             chí với trọng số  
                                      và cộng lại.      

  5                 Ranking           Sắp xếp giảm dần  Danh sách xếp
                                      và chọn Top N.    hạng.

  6                 Explanation       Sinh lý do dựa    Điểm và lý do.
                                      trên dữ liệu và   
                                      điều kiện đạt     
                                      được.             
  -----------------------------------------------------------------------

## 7.3. Công thức WSM

Score(A) = Σ (wᵢ × sᵢ(A))

Trong đó wᵢ là trọng số tiêu chí i, tổng trọng số bằng 1; sᵢ(A) là điểm
của phương án A trên tiêu chí i, nằm trong khoảng 0--100. Điểm tổng cũng
nằm trong khoảng 0--100.

## 7.4. Rubric Food mặc định

  -----------------------------------------------------------------------
  **Tiêu chí**            **Trọng số**            **Hướng chấm**
  ----------------------- ----------------------- -----------------------
  Giá                     40%                     Giá càng phù hợp và
                                                  thấp hơn ngân sách tối
                                                  đa thì điểm càng cao.

  Mức phù hợp nhu         35%                     Mapping theo loại bữa
  cầu/khẩu vị                                     ăn, danh mục hoặc nhãn
                                                  mà người dùng chọn.

  Thời gian chuẩn bị      25%                     Thời gian càng phù hợp
                                                  giới hạn người dùng đặt
                                                  ra thì điểm càng cao.
  -----------------------------------------------------------------------

## 7.5. Quy tắc xử lý

-   Điều kiện bắt buộc được lọc trước, không dùng điểm số để bù trừ vi
    phạm.

-   Không tự suy diễn điểm cho trường dữ liệu bị thiếu.

-   Nếu không còn phương án hợp lệ, trả danh sách rỗng và thông báo
    người dùng nới điều kiện.

-   Nếu bằng điểm, ưu tiên chi phí thấp hơn; nếu vẫn bằng, sắp xếp theo
    tên hoặc ID để ổn định.

-   Quick Search mặc định theo độ liên quan từ khóa; Recommendation mới
    áp dụng Filtering + WSM + Ranking.

-   Kết quả là phương án phù hợp theo dữ liệu và tiêu chí đầu vào, không
    phải lựa chọn tốt nhất tuyệt đối.

# 8. DỮ LIỆU VÀ THIẾT KẾ CƠ SỞ DỮ LIỆU

## 8.1. Nguyên tắc

-   Thiết kế database theo tính năng thực sự được triển khai; không tạo
    bảng cho tính năng chưa được duyệt.

-   Thống nhất kiểu dữ liệu, tên trường, khóa chính/ngoại và đơn vị tiền
    tệ.

-   Giá/chi phí là dữ liệu tham khảo; thống nhất đơn vị VND.

-   Có seed script để mọi thành viên sử dụng cùng bộ dữ liệu.

## 8.2. Các bảng lõi đề xuất

  ----------------------------------------------------------------------------
  **Phân hệ**             **Bảng**                     **Trường cốt lõi gợi
                                                       ý**
  ----------------------- ---------------------------- -----------------------
  Food                    foods                        id, name, description,
                                                       price, meal_type,
                                                       prep_time, image_url,
                                                       is_active

  Food                    ingredients                  id, name

  Food                    food_ingredients             food_id, ingredient_id

  Food                    food_categories              id, name

  Food                    food_category_items          food_id, category_id

  Travel                  destinations                 id, name, description,
                                                       region, estimated_cost,
                                                       estimated_duration,
                                                       image_url, is_active

  Travel                  destination_categories       id, name

  Travel                  destination_category_items   destination_id,
                                                       category_id

  History -- tùy chọn     search_history /             Chỉ thiết kế sau khi
                          recommendation_history       nhóm chốt cách nhận
                                                       diện người dùng và nội
                                                       dung cần lưu.

  Group Voting -- tùy     Các bảng nhóm/bình chọn      Chỉ thiết kế nếu tính
  chọn                                                 năng được duyệt; không
                                                       tạo trước.
  ----------------------------------------------------------------------------

## 8.3. Dữ liệu mẫu tối thiểu

-   Food phải đủ dữ liệu để kiểm tra tìm theo tên, nguyên liệu, danh
    mục, giá, bữa ăn và thời gian.

-   Có trường hợp dữ liệu chứa nguyên liệu cần tránh và trường hợp không
    có kết quả.

-   Travel cần tên, khu vực, chi phí tham khảo, thời lượng, loại hình và
    mô tả.

-   Ảnh có thể để trống nhưng giao diện phải có ảnh mặc định.

# 9. API VÀ NGUYÊN TẮC TÍCH HỢP

## 9.1. API Food bắt buộc

  ---------------------------------------------------------------------------
  **Method**              **Endpoint đề xuất**        **Mục đích**
  ----------------------- --------------------------- -----------------------
  GET                     /api/v1/food/quick-search   Tìm món theo keyword và
                                                      filter.

  GET                     /api/v1/food/{food_id}      Xem chi tiết món.

  POST                    /api/v1/food/recommend      Gợi ý món theo điều
                                                      kiện và WSM.
  ---------------------------------------------------------------------------

## 9.2. API Travel cơ bản

  ---------------------------------------------------------------------------------
  **Method**              **Endpoint đề xuất**              **Mục đích**
  ----------------------- --------------------------------- -----------------------
  GET                     /api/v1/travel/quick-search       Tìm địa điểm theo
                                                            keyword và filter.

  GET                     /api/v1/travel/{destination_id}   Xem chi tiết địa điểm.

  POST                    /api/v1/travel/recommend          Chỉ triển khai nếu nhóm
                                                            quyết định làm gợi ý
                                                            Travel.
  ---------------------------------------------------------------------------------

## 9.3. API chung

  -----------------------------------------------------------------------
  **Method**              **Endpoint**            **Mục đích**
  ----------------------- ----------------------- -----------------------
  GET                     /health                 Kiểm tra backend hoạt
                                                  động.

  -----------------------------------------------------------------------

## 9.4. Quy tắc API

-   Chốt request/response trước khi frontend và backend phát triển song
    song.

-   Quick Search dùng GET; Recommendation dùng POST.

-   Validate giá trị âm, thời gian âm, limit vượt giới hạn và enum không
    hợp lệ.

-   Response danh sách nên thống nhất cấu trúc, ví dụ items/results,
    total và filters_applied.

-   Có trạng thái lỗi rõ ràng; không để frontend tự tính điểm cuối cùng.

# 10. GIAO DIỆN VÀ YÊU CẦU TRẢI NGHIỆM

## 10.1. Màn hình bắt buộc

  -----------------------------------------------------------------------
  **Màn hình**                        **Nội dung**
  ----------------------------------- -----------------------------------
  Trang chủ                           Giới thiệu ngắn; đường dẫn rõ ràng
                                      đến Food và Travel.

  Food Search                         Ô tìm kiếm nổi bật, chip lọc, bộ
                                      lọc bổ sung, danh sách món.

  Food Detail                         Thông tin món, giá, thời gian,
                                      nguyên liệu và nút quay lại.

  Food Recommendation                 Form ngắn, kết quả Top 5, điểm và
                                      lý do.

  Travel Search                       Ô tìm kiếm, bộ lọc cơ bản và danh
                                      sách địa điểm.

  Travel Detail                       Thông tin địa điểm, khu vực, chi
                                      phí và thời lượng.
  -----------------------------------------------------------------------

Travel Recommendation, History và Group Voting không nằm trong danh sách
màn hình bắt buộc; chỉ bổ sung sau khi qua cổng ưu tiên tương ứng.

## 10.2. Nguyên tắc UX

-   Ô tìm kiếm phải là thành phần nổi bật nhất khi mở module.

-   Không bắt buộc đăng nhập hoặc điền hết bộ lọc mới được tìm.

-   Bộ lọc nâng cao nên được thu gọn để tránh màn hình quá dài.

-   Có nút xóa bộ lọc và trạng thái loading, empty, error.

-   Giữ từ khóa và bộ lọc khi người dùng mở chi tiết rồi quay lại nếu
    khả thi.

-   Mục tiêu là tìm được kết quả trong 1--2 thao tác.

# 11. KIẾN TRÚC, CÔNG NGHỆ VÀ CẤU TRÚC MÃ NGUỒN

## 11.1. Kiến trúc

Sử dụng Modular Monolith: một ứng dụng FastAPI được chia module theo
trách nhiệm. Không triển khai microservices trong MVP.

  -----------------------------------------------------------------------
  **Lớp**                             **Trách nhiệm**
  ----------------------------------- -----------------------------------
  Frontend                            HTML, CSS, JavaScript, Bootstrap 5;
                                      trang chủ, tìm kiếm, bộ lọc, danh
                                      sách và chi tiết.

  API/Router                          Nhận request, validate schema, gọi
                                      service và trả response.

  Food Service                        Truy vấn món ăn, xử lý điều kiện
                                      Food, chuẩn bị tiêu chí cho Engine.

  Travel Service                      Truy vấn địa điểm, xử lý điều kiện
                                      Travel, chuẩn bị tiêu chí nếu triển
                                      khai.

  Decision Engine                     Filtering, scoring, ranking,
                                      explanation; không phụ thuộc
                                      database.

  Database                            MySQL lưu catalog món ăn, nguyên
                                      liệu, địa điểm và danh mục.
  -----------------------------------------------------------------------

## 11.2. Công nghệ

  -----------------------------------------------------------------------
  **Thành phần**                      **Công nghệ**
  ----------------------------------- -----------------------------------
  Frontend                            HTML, CSS, JavaScript, Bootstrap 5

  Backend                             Python, FastAPI

  ORM/Validation                      SQLAlchemy 2.x, Pydantic v2

  Database                            MySQL

  Testing                             Pytest

  Version Control                     Git + GitHub; branch, Pull Request,
                                      review
  -----------------------------------------------------------------------

## 11.3. Cấu trúc backend tham khảo


backend/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── database.py
│   │   └── security.py
│   │
│   ├── common/
│   │   ├── __init__.py
│   │   ├── exceptions.py
│   │   └── responses.py
│   │
│   └── modules/
│       ├── __init__.py
│       │
│       ├── auth/
│       │   ├── __init__.py
│       │   ├── router.py
│       │   ├── schemas.py
│       │   ├── service.py
│       │   └── models.py
│       │
│       ├── users/
│       │   └── __init__.py
│       │
│       ├── food/
│       │   └── __init__.py
│       │
│       ├── travel/
│       │   └── __init__.py
│       │
│       ├── decision/
│       │   ├── __init__.py
│       │   └── engine/
│       │       ├── __init__.py
│       │       ├── filters.py
│       │       ├── scoring.py
│       │       ├── ranking.py
│       │       └── explanations.py
│       
│       
│           
│
├── tests/
├── seed/
│
├── .env
├── .env.example
├── .gitignore
├── pyproject.toml
└── requirements.txt

## 11.4. Nguyên tắc phụ thuộc

-   Router không chứa logic nghiệp vụ dài; gọi service.

-   Food/Travel chịu trách nhiệm truy vấn dữ liệu và chuẩn bị tiêu chí
    domain.

-   Decision Engine nhận dữ liệu đã chuẩn hóa; không truy vấn DB.

-   Frontend không tự tính điểm cuối cùng; backend là nguồn kết quả
    chuẩn.

-   Chỉ trừu tượng hóa phần hai module thực sự dùng chung.

# 12. PHÂN CÔNG NHÓM VÀ QUY TẮC PHỐI HỢP

Phân công dưới đây là khung gợi ý cho nhóm 6 người. Nhóm điền tên thành
viên cụ thể trong buổi Sprint 1 -- Ngày 1 và có thể điều chỉnh owner
nhưng phải giữ rõ đầu ra.

  -----------------------------------------------------------------------
  **Vị trí**              **Vai trò chính**       **Đầu việc/đầu ra**
  ----------------------- ----------------------- -----------------------
  A                       Điều phối + Backend     Chốt API contract, cấu
                          Integration             hình FastAPI/MySQL, cấu
                                                  trúc project, tích hợp
                                                  service, xử lý lỗi
                                                  chung và theo dõi tiến
                                                  độ.

  B                       Decision Engine         Filtering, rubric
                                                  scoring, WSM, ranking,
                                                  explanation; unit test
                                                  và ví dụ tính tay.

  C                       Food Backend + Dataset  Thiết kế bảng Food,
                                                  seed món/nguyên
                                                  liệu/danh mục; Quick
                                                  Search API, Detail API,
                                                  Food adapter.

  D                       Travel Backend +        Thiết kế bảng Travel,
                          Dataset                 seed địa điểm/danh mục;
                                                  Quick Search API và
                                                  Detail API cơ bản sau
                                                  khi Food ổn định.

  E                       Frontend Food           Food Search, chip lọc,
                                                  bộ lọc, danh sách, chi
                                                  tiết, form gợi ý và
                                                  hiển thị lý do.

  F                       Frontend Travel + QA    Travel Search/Detail cơ
                                                  bản sau Food; kiểm thử
                                                  tích hợp, hỗ trợ README
                                                  và demo.
  -----------------------------------------------------------------------

## 12.1. Quy tắc làm việc Git

-   Không commit trực tiếp lên nhánh main.

-   Mỗi nhiệm vụ phát triển trên branch riêng, đặt tên rõ ràng theo
    feature/fix.

-   Pull Request phải có mô tả, phạm vi thay đổi và cách kiểm thử; kèm
    ảnh hoặc ví dụ API khi phù hợp.

-   Mỗi PR cần ít nhất một thành viên khác review trước khi merge.

-   Không commit file .env, mật khẩu, token hoặc dữ liệu bí mật.

-   Thống nhất quy tắc merge và xử lý conflict trong buổi đầu.

## 12.2. Quy tắc phối hợp

-   Backend công bố API contract và mock response sớm để frontend không
    phải chờ.

-   Food và Engine thống nhất interface dữ liệu trước khi triển khai
    sâu.

-   Travel chỉ nhận nguồn lực sau Gate 1 -- Food.

-   Tích hợp thường xuyên; không dồn toàn bộ tích hợp vào ngày cuối.

-   Mỗi đầu việc phải có owner, reviewer, ngày dự kiến và tiêu chí hoàn
    thành.

# 14. KIỂM THỬ, NGHIỆM THU VÀ DEFINITION OF DONE

## 14.1. Kiểm thử tối thiểu

  -----------------------------------------------------------------------
  **Nhóm kiểm thử**       **Tình huống**          **Kết quả mong đợi**
  ----------------------- ----------------------- -----------------------
  Food Quick Search       Tìm theo tên một phần;  Trả đúng kết quả hoặc
                          từ khóa không tồn tại;  empty state.
                          kết hợp keyword và      
                          filter.                 

  Food Filtering          Món vượt giá; sai loại  Phương án vi phạm điều
                          bữa ăn; chứa nguyên     kiện bị loại.
                          liệu cần tránh.         

  Scoring                 Kiểm tra điểm từng tiêu Điểm chính xác, tổng
                          chí, trọng số và tổng   trọng số hợp lệ.
                          điểm với ví dụ tính     
                          tay.                    

  Ranking                 Thứ tự giảm dần; điểm   Thứ tự nhất quán, không
                          bằng nhau; giới hạn Top vượt limit.
                          N.                      

  Explanation             Kiểm tra lý do của từng Lý do dựa trên dữ
                          kết quả.                liệu/điều kiện, không
                                                  bịa.

  Integration             Frontend gọi API;       Luồng không bị treo;
                          loading, lỗi mạng, danh thông báo phù hợp.
                          sách rỗng.              

  Data                    Chạy seed trên máy      Các thành viên có cùng
                          thành viên khác.        dữ liệu mẫu.

  Travel cơ bản           Tìm theo tên/khu vực;   Các chức năng trong
                          lọc và mở chi tiết.     phạm vi đã chốt hoạt
                                                  động.
  -----------------------------------------------------------------------

## 14.2. Definition of Done cho Food

-   Người dùng thao tác được từ giao diện đến API và database.

-   Quick Search và bộ lọc thiết yếu hoạt động.

-   Recommendation lọc điều kiện, tính điểm, xếp hạng và giải thích
    đúng.

-   Trang chi tiết hiển thị đủ trường dữ liệu đã thống nhất.

-   Có loading, empty state và error state.

-   Các test trọng yếu của filtering/scoring/ranking pass.

-   Seed chạy được; README hướng dẫn cài đặt, cấu hình .env, tạo DB,
    seed và chạy frontend/backend.

-   Code đã review; không commit secret hoặc mật khẩu.

## 14.3. Definition of Done cho toàn dự án

-   Food đạt toàn bộ tiêu chí nghiệm thu bắt buộc.

-   Travel đạt phạm vi cơ bản mà nhóm đã chốt; nếu bị cắt giảm phải ghi
    rõ trong biên bản.

-   Không còn lỗi blocker trong kịch bản demo.

-   Có README, dữ liệu seed và hướng dẫn chạy dự án.

-   Có báo cáo kiểm thử và kịch bản demo thống nhất.

-   History/Group Voting chỉ được tính là hoàn thành nếu đã được nhóm
    duyệt và có tiêu chí nghiệm thu riêng.
