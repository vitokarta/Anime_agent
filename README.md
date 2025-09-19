# 動漫推薦 AI Agent

基於標籤過濾和評分排序的動漫推薦系統，使用 SQLite 資料庫儲存動漫資料。

## 功能特色

- 🏷️ **標籤過濾**: 根據動漫類型標籤進行精確搜尋
- ⭐ **評分排序**: 自動按評分降序排列推薦結果
- 🔢 **數量控制**: 可設定回傳前 N 筆推薦結果
- 📊 **評分門檻**: 支援最低評分限制篩選
- 💾 **本地儲存**: 使用 SQLite 進行永久資料儲存


## 環境設定（Windows，使用 uv）

以下流程使用 uv（極速的 Python 套件/環境管理工具）。做到「第四點」即可開始開發，之後若要進階鎖定版本再補充。

### 1. 安裝 uv（單檔執行檔，無需系統 Python）
```powershell
irm https://astral.sh/uv/install.ps1 | iex
# 若剛裝完當前視窗抓不到 uv，可：
$env:PATH += ";$HOME\.local\bin"; uv --version
```

### 2. 建立 / 啟用虛擬環境
```powershell
# 建立 .venv 目錄（若已存在可跳過）
uv venv .venv
# 啟用
\.\.venv\Scripts\Activate.ps1
#不能就換
.venv\Scripts\activate
```

### 3. 安裝專案相依套件
```powershell
uv pip install -r requirements.txt
```

### 4. 新增套件（範例：requests）
```powershell
uv pip install requests
uv pip freeze > requirements.txt   # 暫時寫回目前完整版本 (之後可改用 compile 流程產生鎖檔)
```

> 到這裡 (第 1~4 點) 你就可以開始開發與執行程式。

---

（後續：若要更乾淨「來源檔 + 鎖檔」模型，可把現在的 `requirements.txt` 改名成 `requirements.in`，再用 `uv pip compile` 產生新的鎖定 `requirements.txt`，此部分暫不展開。）

## Git 協作與分支命名

主線：main（保持可部署 / 穩定）

每一項功能或修復都開「短生命週期」分支，完成後透過 Pull Request 合併回 main。


### 流程（含本地直接合併模式）
#### 用 VS Code 終端切換 shell 為 Git Bash（有內建補全git指令功能）
1. 取得專案（第一次）
```bash
git clone <repo-url>
cd Anime_agent
git checkout -b <branch-name>   # 建分支
```

2. 每天開始作業先同步 main
```bash
git checkout main
git pull origin main
git checkout <branch-name> 
git rebase main     # 或：git merge main
```

3. 開發 & 提交
```bash
git add .
git commit -m "feat: 初始化匯入 CSV 功能"
```

4. 修改完推送遠端
```bash
git fetch origin
git checkout <branch-name> 
git rebase origin/main     # 解衝突 -> git add -> git rebase --continue
git push -u origin <branch-name> 
```
(不熟 rebase 可改用：git merge origin/main -> git push)


5. 合併回 main （無 PR 模式二選一）

	A) 建 merge commit（保留分支歷史）
	```bash
	git checkout main
	git pull origin main
	git merge --no-ff <branch-name>
	git push origin main
	```
	B) 線性歷史（rebase + fast-forward）
	```bash
	git checkout <branch-name>
	git fetch origin
	git rebase origin/main   # 解衝突後 git add / git rebase --continue
	git checkout main
	git pull origin main
	git merge --ff-only <branch-name>
	git push origin main
	```
	備註：若 A 已產生 merge commit，不要再 rebase 試圖重寫；若 B rebase 過程衝突太多可退回：`git rebase --abort` 改用 A。

6. 本地清理
```bash
git checkout main
git pull origin main
git branch -d feature/import-data   # 或 git branch -d <branch-name>
git fetch -p
```

### 快速對照
| 動作 | 指令 |
| ---- | ---- |
| 建新功能分支 | git checkout -b feature/<簡述> |
| 同步 main | git pull origin main |
| 更新功能分支 | git rebase main (或 git merge main) |
| 推送 | git push / 首次加 -u |
| 修衝突後續 | git add; git rebase --continue |
| 刪除本地分支 | git branch -d <branch> |
| 刪除遠端分支 | git push origin --delete <branch> |
| 本地合併（merge commit） | git merge --no-ff <branch> |
| 本地合併（線性） | git rebase main -> git merge --ff-only <branch> |

> 原則：不在 main 直接開發；小步提交；一功能一分支；PR 合併前保持可重播（rebase 或 merge）
