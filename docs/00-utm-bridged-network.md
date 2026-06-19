# 00 - UTM Network Cho 3 MacBook

Mục tiêu là mỗi Ubuntu VM nhận được một IP cùng lớp mạng LAN, để master có thể
`ping`, `ssh`, mount NFS và chạy OpenMPI trên node1/node2.

## Giai đoạn đầu: Shared Network vẫn được

Khi mới setup từng VM riêng lẻ, UTM Shared Network là đủ. IP kiểu
`192.168.64.x` thường là Shared Network của macOS, dùng được để SSH từ Mac host
vào VM nhưng không phù hợp cho cụm nhiều laptop.

## Khi bắt đầu nối 3 MacBook: đổi sang Bridged

Trên từng MacBook:

1. Tắt Ubuntu VM.
2. Mở UTM.
3. Chọn VM.
4. Vào Settings -> Network.
5. Đổi Network Mode thành Bridged.
6. Chọn interface đang dùng cùng LAN, thường là Wi-Fi `en0` hoặc USB Ethernet.
7. Start VM lại.

Trong Ubuntu VM, kiểm tra:

```bash
hostname -I
```

IP nên giống cùng dải với các MacBook khác, ví dụ:

```text
192.168.1.10
192.168.1.11
192.168.1.12
```

Nếu vẫn chỉ thấy `192.168.64.x`, VM có thể vẫn đang ở Shared Network.

## Lưu ý Wi-Fi

- Cả 3 MacBook phải ở cùng Wi-Fi/router.
- Một số hotspot hoặc Wi-Fi trường học bật client isolation, làm các máy không
ping được nhau.
- Nếu `ping` giữa các VM fail dù IP đúng, dùng router khác hoặc USB-C Ethernet
adapter sẽ ổn hơn.

