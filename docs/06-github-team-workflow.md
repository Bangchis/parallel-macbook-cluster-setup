# GitHub Cho Nhom

Nen dua repo setup nay len GitHub de ca nhom co mot ban chuan. Gui file zip
chi dung duoc luc dau, nhung sau moi lan sua script/tai lieu thi cac may khac
khong tu cap nhat duoc.

GitHub giup ca nhom:

- Cap nhat bang `git pull`.
- Xem lich su thay doi.
- Dung chung README, docs va scripts.
- Tranh moi nguoi giu mot ban zip khac nhau.

## Ban Dang Dung Zip Thi Lam Gi?

Tren Ubuntu VM cua tung node:

```bash
cd ~
mv parallel-macbook-cluster-setup parallel-macbook-cluster-setup-zip-backup-$(date +%Y%m%d-%H%M) 2>/dev/null || true
git clone REPLACE_WITH_GITHUB_URL parallel-macbook-cluster-setup
cd parallel-macbook-cluster-setup
```

Neu chua co Git:

```bash
sudo apt update
sudo apt install -y git
```

## Cap Nhat Ve Sau

Moi khi master bao co thay doi moi:

```bash
cd ~/parallel-macbook-cluster-setup
git pull
```

## File Config Rieng

Khong commit `configs/cluster.env`. Moi LAN moi co IP rieng, nen file nay nam
rieng tren tung may/master. Repo chi commit file mau:

```text
configs/cluster.env.example
```

## Repo Private Hay Public?

Public: ban be clone truc tiep duoc link.

Private: an toan hon cho bai cuoi ki, nhung can add GitHub username cua tung
ban vao Collaborators.

Neu dung private repo, vao GitHub:

```text
Repo -> Settings -> Collaborators -> Add people
```

Sau khi duoc moi, cac ban clone/pull nhu binh thuong.
