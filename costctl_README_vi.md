# costctl — Bộ khởi động thử thách phụ XBrain W6

Một scaffold khởi đầu cho CLI nhỏ dùng để quản lý tài nguyên AWS. **Cấu trúc CLI đã được dựng sẵn; bạn sẽ triển khai logic cho từng command.** Hãy fork repo này, hoàn thiện các phần stub, làm cho test pass, tùy chỉnh theo nhóm của bạn, rồi nộp bài.

> **Thử thách phụ là TÙY CHỌN và KHÔNG tính vào điểm W6 hoặc giới hạn điểm thưởng.**
> Việc ghi nhận thành tích được tách riêng (Slack callout / lựa chọn Phase 2 / portfolio).
> Xem `outputs/W6/W6_downtime_exercises.md` trong repo chương trình XBrain để đọc brief đầy đủ.

---

## Phần đã có sẵn và phần bạn cần xây dựng

| Đã cung cấp (đừng viết lại) | Việc của bạn |
|-----------------------------|--------------|
| `costctl.py` — entrypoint argparse, dispatch table | Triển khai `run(args)` cho từng command |
| `commands/_common.py` — `parse_kv`, `tags_to_dict`, `tags_match`, `confirm` | Dùng các helper này, đừng tự viết lại |
| `tests/test_common.py` — 10 unit test cho helper (đều xanh) | Đừng chỉnh sửa — chúng kiểm tra helper vẫn hoạt động đúng |
| `tests/test_list.py`, `tests/test_terminate.py`, `tests/test_clean.py` — các test đang fail, định nghĩa hành vi của từng command | Làm cho các test này xanh |
| Module docstring trong mọi file `commands/*_cmd.py` — spec đầy đủ, gợi ý, AWS API cần dùng | Đọc kỹ trước khi code |
| `Makefile`, `requirements*.txt`, `.gitignore`, `LICENSE` | Giữ nguyên |
| `sample_output/*_example.txt` | Thay bằng output THẬT sau khi phần triển khai của bạn chạy được |

**Trạng thái ban đầu của `make test`:** 10 passed (helper), 15 failed (command).
Bạn hoàn thành khi toàn bộ 25 test đều pass.

---

## Bắt đầu nhanh (5 phút)

```bash
# 1. Fork / clone
git clone <your-fork-url> g<N>-costctl && cd g<N>-costctl

# 2. Cài đặt
make install-dev                   # hoặc: pip install -r requirements-dev.txt

# 3. Xác nhận baseline — 10 passed, 15 failed
make test

# 4. Xác nhận --help hoạt động (CLI scaffolding đã được nối sẵn)
./costctl.py --help

# 5. Mở commands/list_cmd.py và bắt đầu triển khai.
#    Module docstring cho bạn biết cần xây dựng gì. Làm cho test_list.py xanh.
```

Cấu hình AWS credentials khi bạn đã sẵn sàng chạy với account của mình:

```bash
aws configure                      # hoặc set biến môi trường AWS_*
./costctl.py list ec2              # sẽ báo NotImplementedError cho đến khi bạn hoàn thành bước 5
```

---

## Lộ trình triển khai

Thứ tự khuyến nghị. Bạn cần `list` + ít nhất 2 trong 3 command tiếp theo.

### Bắt buộc

| # | File | Làm pass | Thời gian |
|---|------|----------|-----------|
| 1 | `commands/list_cmd.py` | `pytest tests/test_list.py` (7 test) | ~45 phút |
| 2 | Chọn **ít nhất 2** trong các command sau: | | |
|   | • `commands/cost_cmd.py` | (không có file test — kiểm tra thủ công bằng `./costctl.py cost --tag X=Y --days 7` và so sánh với AWS Console) | ~30 phút |
|   | • `commands/terminate_cmd.py` | `pytest tests/test_terminate.py` (4 test) | ~40 phút |
|   | • `commands/tag_cmd.py` | (không có test — kiểm tra bằng vòng lặp `tag` + `list`) | ~30 phút |

### Mở rộng (tùy chọn — tăng giá trị portfolio)

| File | Làm pass | Thời gian |
|------|----------|-----------|
| `commands/clean_cmd.py` | `pytest tests/test_clean.py` (4 test) | ~30 phút |
| `commands/idle_cmd.py` | (không có test — kiểm tra thủ công) | ~45 phút |
| `commands/migrate_gp3_cmd.py` | (không có test — kiểm tra thủ công, sau đó chạy `--apply` một lần thật) | ~30 phút |

### Cách đọc một stub

Mọi file `commands/*_cmd.py` đều bắt đầu bằng module docstring, trong đó có:

- **WHAT YOU MUST BUILD** — hành vi tổng quan
- **HELPERS YOU CAN USE** — trỏ đến `commands/_common.py`
- **AWS APIS YOU'LL NEED** — các lệnh gọi boto3 cụ thể
- **EXPECTED OUTPUT FORMAT** — copy chính xác phần này khi bạn `print(...)`
- **VERIFY** — lệnh pytest hoặc công thức kiểm tra thủ công

Đừng bỏ qua docstring rồi nhảy thẳng đến `raise NotImplementedError`. Docstring chính là spec của bạn.

---

## Các command (hình dạng cuối cùng sau khi bạn triển khai)

| Command | Chức năng | Cấp độ |
|---------|-----------|--------|
| `list <type>` | Liệt kê EC2/RDS/S3/Volume, lọc theo tag hoặc tag bị thiếu | core |
| `cost --tag k=v` | Tính tổng chi phí trong N ngày cho các tài nguyên khớp với tag | core |
| `terminate <type> --id` | Terminate/delete một tài nguyên (có hỏi xác nhận) | core |
| `tag <type> --id --set` | Thêm/cập nhật tag trên một tài nguyên | core |
| `clean --tag k=v` | Terminate hàng loạt tài nguyên theo tag (mặc định là dry-run) | stretch |
| `idle` | Tìm EC2 idle theo CPU trung bình 24 giờ | stretch |
| `migrate-gp3` | Lập kế hoạch hoặc áp dụng migration EBS gp2 → gp3 | stretch |

Loại tài nguyên: `ec2`, `rds`, `s3`, `volume`.

### Ví dụ cách gọi (sau khi triển khai)

```bash
# List
./costctl.py list ec2 --tag Environment=dev
./costctl.py list ec2 --missing-tag Application
./costctl.py list s3

# Cost (dữ liệu có độ trễ 8–24 giờ; nếu "no cost data", thử tăng --days)
./costctl.py cost --tag Application=HealthBot --days 7

# Terminate (hỏi y/N)
./costctl.py terminate ec2 --id i-0abc123
./costctl.py terminate ec2 --id i-0abc123 --force

# Tag
./costctl.py tag ec2 --id i-0abc --set Owner=alice --set Application=HealthBot

# One-liner: sửa một tài nguyên đang thiếu tag
./costctl.py tag ec2 \
  --id $(./costctl.py list ec2 --missing-tag Application | awk 'NR==4{print $1}') \
  --set Application=HealthBot

# Stretch
./costctl.py clean --tag purpose=practice          # dry-run
./costctl.py clean --tag purpose=practice --apply
./costctl.py idle --threshold 5 --hours 24
./costctl.py migrate-gp3
./costctl.py migrate-gp3 --apply --volume-id vol-0xyz
```

---

## Yêu cầu

- Python 3.11+
- `boto3` (thông qua `make install`)
- AWS credentials có quyền:
  - **Read**: EC2, RDS, S3, CloudWatch, Cost Explorer
  - **Write** (chỉ dành cho `terminate`/`tag`/`clean`/`migrate-gp3`): EC2, RDS, S3

Đối với test:
- `moto`, `pytest`, `pytest-cov` (thông qua `make install-dev`)

---

## Cấu trúc dự án

```text
costctl-starter/
├── costctl.py                # argparse entrypoint (đã cung cấp)
├── commands/
│   ├── _common.py            # helper — ĐÃ TRIỂN KHAI, để nguyên
│   ├── list_cmd.py           # STUB → triển khai
│   ├── cost_cmd.py           # STUB → triển khai
│   ├── terminate_cmd.py      # STUB → triển khai
│   ├── tag_cmd.py            # STUB → triển khai
│   ├── clean_cmd.py          # STUB → stretch
│   ├── idle_cmd.py           # STUB → stretch
│   └── migrate_gp3_cmd.py    # STUB → stretch
├── tests/                    # TẤT CẢ đã được cung cấp; một số pass, một số fail cho đến khi bạn triển khai
│   ├── conftest.py
│   ├── test_common.py        # 10 test, xanh từ ngày đầu
│   ├── test_list.py          # 7 test — triển khai list_cmd để làm xanh
│   ├── test_terminate.py     # 4 test
│   └── test_clean.py         # 4 test (stretch)
├── sample_output/            # output ví dụ — thay bằng output của bạn
├── Makefile
├── requirements.txt
├── requirements-dev.txt
├── LICENSE
└── README.md (file này)
```

---

## Vòng lặp TDD

```bash
# 1. Chọn một test đang fail
pytest tests/test_list.py::test_list_ec2_empty -v

# 2. Mở commands/list_cmd.py, tìm function mà test tham chiếu (_list_ec2)
# 3. Triển khai vừa đủ để test ĐÓ pass
# 4. Chạy lại — xanh chưa?
pytest tests/test_list.py::test_list_ec2_empty -v

# 5. Chuyển sang test tiếp theo trong file
pytest tests/test_list.py::test_list_ec2_no_filter_returns_all -v

# Lặp lại. Khi toàn bộ test trong file pass, command đó hoàn thành.
```

Các test được cung cấp dùng [moto](https://github.com/getmoto/moto) — không gọi AWS thật, không phát sinh chi phí, chạy trong vài giây.

---

## Cách mở rộng — thêm command mới

Giả sử bạn muốn thêm command `snapshot` để tạo EBS snapshot.

**1.** Tạo `commands/snapshot_cmd.py`:

```python
"""snapshot — tạo một EBS snapshot từ một volume."""
import boto3

def run(args):
    ec2 = boto3.client("ec2")
    resp = ec2.create_snapshot(
        VolumeId=args.volume_id,
        Description=f"costctl backup of {args.volume_id}",
    )
    print(f"Created snapshot {resp['SnapshotId']} (state: {resp['State']})")
```

**2.** Thêm parser block trong `build_parser()` của `costctl.py`:

```python
sn = sub.add_parser("snapshot", help="snapshot an EBS volume")
sn.add_argument("--volume-id", required=True)
```

**3.** Đăng ký trong `CMD_MODULE`:

```python
CMD_MODULE = {
    ...,
    "snapshot": "snapshot_cmd",
}
```

Chạy:

```bash
./costctl.py snapshot --volume-id vol-0xyz
```

Thêm `tests/test_snapshot.py` dựa theo mẫu của `test_list.py`. Moto hỗ trợ
`create_snapshot` sẵn.

---

## Reflections (dán ít nhất 2 câu trả lời trước khi nộp)

Thêm file `REFLECTIONS.md` vào repo của bạn. Gợi ý câu hỏi mẫu:

1. **Multi-account**: Để chạy `costctl` trên 100 AWS account (không chỉ account của bạn), cần thay đổi gì? Cross-account role? Vòng lặp profile? CSV tổng hợp theo từng account?
2. **`idle` so với Trusted Advisor**: `idle` dùng cửa sổ CPU 24 giờ. Trusted Advisor dùng 14 ngày. Khi nào bạn tin `idle` hơn, khi nào bạn tin TA hơn?
3. **Blast radius của `clean --apply`**: Nếu bạn vô tình chạy `clean --tag Environment=dev --apply` trong một account dùng chung với team khác, bạn muốn có cơ chế gì để giới hạn thiệt hại?
4. **Hỗ trợ từ AI**: Bao nhiêu phần trăm code đến từ AI tools (Claude / Cursor / Copilot) mà không chỉnh sửa? Phần nào bạn chủ động chỉnh sửa, vì sao?
5. **Mang sang W7**: Command nào bạn sẽ giữ khi sang W7 (multi-account kiểu production)? Command nào bạn sẽ bỏ và vì sao?

---

## Checklist nộp bài (W6 side challenge)

- [ ] Fork → đổi tên thành `g<N>-costctl` → clone về máy
- [ ] `make install-dev && make test` hiển thị 10 passed lúc bắt đầu
- [ ] Triển khai `list` → `pytest tests/test_list.py` xanh toàn bộ (thêm 7 test pass)
- [ ] Triển khai ≥ 2 trong (`cost`, `terminate`, `tag`) — test `terminate` xanh nếu bạn chọn command này
- [ ] (optional stretch) `clean` → `pytest tests/test_clean.py` xanh; hoặc `idle` / `migrate-gp3`
- [ ] Báo cáo điểm cuối cùng của `make test` trong README, ví dụ: "21/25 passing"
- [ ] Thay `sample_output/*_example.txt` bằng output thật từ account của bạn
- [ ] `REFLECTIONS.md` có ít nhất 2 câu trả lời
- [ ] Có ít nhất 3 commit có ý nghĩa (init → command đầu tiên hoạt động → polish cuối)
- [ ] Thay tất cả placeholder `g<N>` trong README bằng số nhóm thật
- [ ] Thêm phần Team với tên thành viên
- [ ] Tag: `git tag w6-sidechallenge-v1 && git push --tags`
- [ ] Đăng link vào thread Slack `#w6-sidechallenge`:
      `G<N> — <repo-url> — implemented: list, cost, terminate (21/25 tests passing)`

Nhắc lại: **TÙY CHỌN và KHÔNG tính vào điểm W6.** Việc ghi nhận thành tích
được tách riêng (Slack callout / lựa chọn Phase 2 / portfolio).

---

## License

MIT — xem `LICENSE`.

---

## Team

> Thay trước khi nộp:

- <name 1>
- <name 2>
- <name 3>

---

*Starter scaffold từ XBrain W6 side challenge —
`outputs/W6/costctl-starter/` trong repo chương trình.*
