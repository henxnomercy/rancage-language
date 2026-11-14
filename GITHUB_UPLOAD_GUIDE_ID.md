# Panduan Upload RANCAGE 0.1.0 ke GitHub (Windows + VS Code)

## A. Siapkan folder lokal

1. Unduh `RANCAGE-v0.1.0-GitHub-Ready.zip`.
2. Extract ke folder sederhana, misalnya `C:\Projects\RANCAGE`.
3. Buka VS Code → File → Open Folder → pilih folder `RANCAGE` yang berisi `README.md`, `src`, `tests`, dan `cage.cmd`.
4. Pastikan yang dibuka adalah root proyek, bukan folder `src` atau folder ZIP.

## B. Periksa sebelum upload

Buka Terminal → New Terminal di VS Code (PowerShell), lalu jalankan:

```powershell
python --version
.\cage.cmd --version
.\run-tests.cmd
.\cage.cmd check examples\hello.cage
.\cage.cmd run examples\hello.cage
```

Python harus 3.10 atau lebih baru. Jika `python` tidak dikenali, install Python dan centang opsi **Add Python to PATH**, lalu buka ulang terminal VS Code.

## C. Buat repository GitHub kosong

1. Masuk ke https://github.com/new.
2. Repository name: `rancage-language` (atau nama yang kamu pilih).
3. Description: `RANCAGE — experimental universal programming language reference compiler`.
4. Pilih **Private** untuk upload pertama.
5. Jangan centang Add a README, .gitignore, atau license. File-file itu sudah ada di folder lokal.
6. Klik Create repository dan salin URL HTTPS repository yang diberikan GitHub.

Repository Private direkomendasikan karena pemberitahuan lisensi core RANCAGE masih provisional dan pemilik/hak distribusinya belum difinalisasi. Public repository membuat source terlihat oleh semua orang. Jangan membuatnya Public sebelum kebijakan lisensi diselesaikan.

## D. Hubungkan folder VS Code ke GitHub

Pastikan Git for Windows sudah terpasang. Di terminal VS Code, pastikan current directory adalah root RANCAGE. Jalankan satu per satu:

```powershell
git --version
git init
git branch -M main
git add .
git status
git commit -m "chore: publish RANCAGE v0.1.0 baseline"
git remote add origin https://github.com/USERNAME/rancage-language.git
git remote -v
git push -u origin main
```

Ganti `USERNAME` dengan username GitHub kamu dan ganti URL sesuai URL repository milikmu. Ketika Git meminta autentikasi, selesaikan login di browser atau credential manager. Jangan menaruh password atau token di dalam source code.

## E. Cek hasil upload

1. Refresh halaman repository GitHub.
2. Pastikan `README.md`, `src/`, `tests/`, `.github/workflows/ci.yml`, dan dokumentasi terlihat.
3. Buka tab **Actions**.
4. Buka workflow **RANCAGE 0.1 CI** dan tunggu sampai semua versi Python (3.10–3.13) berstatus hijau.
5. Jika gagal, buka detail job, salin pesan error yang relevan, lalu perbaiki di branch terpisah.

## F. Alur update berikutnya

Setelah project terhubung, update rutin dilakukan dari folder VS Code:

```powershell
git status
git add .
git commit -m "docs: update RANCAGE project notes"
git push
```

Jangan gunakan `git push --force`, `git reset --hard`, atau `git clean -fd` sebagai cara memperbaiki error upload.

## Catatan penting

- ZIP sumber ini belum otomatis membuat repository GitHub dan belum di-push oleh ChatGPT.
- Simpan ZIP asli sebagai backup sebelum mengubah file.
- `.rcb`, virtual environment, cache Python, dan secret lokal diabaikan oleh `.gitignore`.
- Jangan mengunggah API key, password, token, Android keystore, atau file signing.
- Jangan menandai RANCAGE sebagai production-ready: v0.1.0 adalah reference implementation eksperimental. Hanya reference VM yang sudah diimplementasikan.
