"""單一 CSV 檔案匯入工具（中文簡化版）

用途：一次匯入一個檔案，避免批次流程過於複雜。

來源 CSV 欄位（需要存在）：
"img-fit-cover src","entity_localized_name","anime_tag","anime_summary","anime_story",
"steam-site-name","steam-site-name 2","steam-site-name 3","anime_tag 2","anime_tag 3",
"scormem-item","scormem-item 2","image_path"

欄位對應：
- title ← entity_localized_name
- season ← 由檔名推得：YYYY_1→Winter, YYYY_4→Spring, YYYY_7→Summer, YYYY_10→Fall  => 例如 2024_1_with_image.csv -> 2024-Winter
- rating ← scormem-item （空字串→NULL）
- viewers_count ← scormem-item 2 （原樣字串 e.g. "487K"）
- genres_json ← anime_tag / anime_tag 2 / anime_tag 3 合併去重 JSON 陣列
- platforms_json ← steam-site-name 1/2/3 合併去重 JSON 陣列
- synopsis ← anime_story（空字串→NULL）
- image_path ← image_path
- is_disliked ← 預設 0（資料表 default）
- created_at ← DB default

使用方式：
python utils/database/import_single_csv.py anime_data/data/2024_1_with_image.csv

選項：
--replace 同季同名若已存在則覆蓋（以 title + season 當唯一條件）

未來可擴充：新增 viewers_numeric（把 487K / 1.2M 轉成整數）
"""
from __future__ import annotations
import csv
import json
import sqlite3
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# --- 動態匯入（支援直接 python 執行無套件語境） ---
try:  # 嘗試套件式相對匯入
    from .create_schema import DB_PATH, create_schema  # type: ignore
except Exception:  # 直接執行時會失敗：attempted relative import
    ROOT = Path(__file__).resolve().parents[2]  # 專案根目錄
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from utils.database.create_schema import DB_PATH, create_schema  # type: ignore

SEASON_CODE_MAP = {"1": "Winter", "4": "Spring", "7": "Summer", "10": "Fall"}
REQUIRED_COLUMNS = [
    "img-fit-cover src",
    "entity_localized_name",
    "anime_tag",
    "anime_summary",
    "anime_story",
    "steam-site-name",
    "steam-site-name 2",
    "steam-site-name 3",
    "anime_tag 2",
    # "anime_tag 3" 改為可選
    "scormem-item",
    "scormem-item 2",
    "image_path",
]


def derive_season(csv_path: Path) -> Optional[str]:
    stem = csv_path.stem  # 2024_1_with_image
    parts = stem.split("_")
    if len(parts) < 2:
        return None
    year, code = parts[0], parts[1]
    if not year.isdigit():
        return None
    season_word = SEASON_CODE_MAP.get(code)
    if not season_word:
        return None
    return f"{year}-{season_word}"


def build_unique_list(values: List[str]) -> List[str]:
    seen = set()
    result = []
    for v in values:
        if v and v not in seen:
            seen.add(v)
            result.append(v)
    return result


def parse_csv_row(row: Dict[str, str]) -> Dict:
    title = (row.get("entity_localized_name") or "").strip()
    rating_raw = (row.get("scormem-item") or "").strip()
    rating = float(rating_raw) if rating_raw else None
    viewers_count = (row.get("scormem-item 2") or "").strip() or None

    tags = build_unique_list([
        (row.get("anime_tag") or "").strip(),
        (row.get("anime_tag 2") or "").strip(),
        (row.get("anime_tag 3") or "").strip(),  # 可能不存在，row.get 會回傳 None
    ])
    platforms = build_unique_list([
        (row.get("steam-site-name") or "").strip(),
        (row.get("steam-site-name 2") or "").strip(),
        (row.get("steam-site-name 3") or "").strip(),
    ])
    synopsis = (row.get("anime_story") or "").strip() or None
    image_path = (row.get("image_path") or "").strip() or None

    return {
        "title": title,
        "rating": rating,
        "viewers_count": viewers_count,
        "genres_json": json.dumps(tags, ensure_ascii=False),
        "platforms_json": json.dumps(platforms, ensure_ascii=False),
        "synopsis": synopsis,
        "image_path": image_path,
    }


def upsert_anime(cur: sqlite3.Cursor, season: str, record: Dict, replace: bool):
    """依照 title 判斷是否已存在（忽略 season）。存在就 skip，不做更新。"""
    cur.execute("SELECT id FROM anime WHERE title = ?", (record["title"],))
    existing = cur.fetchone()
    if existing:
        return "skip"
    cur.execute(
        """
        INSERT INTO anime (title, season, rating, viewers_count, genres_json, platforms_json, image_path, synopsis)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            record["title"],
            season,
            record["rating"],
            record["viewers_count"],
            record["genres_json"],
            record["platforms_json"],
            record["image_path"],
            record["synopsis"],
        ),
    )
    return "insert"


def import_single(csv_file: Path, db_path: Path = DB_PATH, replace: bool = False) -> Tuple[int, int, int]:  # replace 參數保留但不再使用
    create_schema(db_path)
    season = derive_season(csv_file) or None
    with csv_file.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        missing = [c for c in REQUIRED_COLUMNS if c not in reader.fieldnames]
        if missing:
            raise ValueError(f"CSV 缺少欄位: {missing}")
        rows = [parse_csv_row(r) for r in reader if (r.get("entity_localized_name") or "").strip()]

    conn = sqlite3.connect(db_path.as_posix())
    try:
        cur = conn.cursor()
        inserted = updated = skipped = 0
        for rec in rows:
            action = upsert_anime(cur, season, rec, replace=replace)
            if action == "insert":
                inserted += 1
            else:
                skipped += 1
        conn.commit()
        print(f"✅ 完成: 新增 {inserted} 筆｜略過 {skipped} 筆（依 title 判斷重複跳過）｜Season={season}")
        return inserted, updated, skipped
    finally:
        conn.close()


def auto_import_all(data_dir: Path = Path("anime_data/data"), db_path: Path = DB_PATH) -> None:
    """自動匯入目錄下所有 *_with_image.csv 檔案（排序後），重複 title 直接略過。"""
    if not data_dir.exists():
        print(f"❌ 資料夾不存在: {data_dir}")
        return
    csv_files = sorted(data_dir.glob("*_with_image.csv"))
    if not csv_files:
        print("⚠️ 沒有找到任何 *_with_image.csv 檔案")
        return
    print("🚀 開始自動匯入所有檔案（重複 title 略過）...")
    total_insert = total_skip = 0
    for f in csv_files:
        print(f"--- 匯入 {f.name} ---")
        try:
            ins, _upd, skp = import_single(f, db_path=db_path, replace=False)
            total_insert += ins
            total_skip += skp
        except Exception as e:
            print(f"❌ 檔案 {f.name} 匯入失敗: {e}")
    print("📊 匯入總結：")
    print(f"  新增: {total_insert}｜略過(重複): {total_skip}")


if __name__ == "__main__":
    # 若使用者有帶參數，仍支援舊模式；若無參數 → 自動全部匯入
    if len(sys.argv) == 1:
        auto_import_all()
    else:
        import argparse
        parser = argparse.ArgumentParser(description="單一動畫 CSV 匯入工具 / 無參數 = 自動全部匯入")
        parser.add_argument("csv", type=Path, nargs="?", help="CSV 檔案路徑 e.g. anime_data/data/2024_1_with_image.csv")
        parser.add_argument("--db", type=Path, default=DB_PATH, help="SQLite DB 路徑")
        parser.add_argument("--replace", action="store_true", help="若同季同名存在則覆蓋 (預設 False；自動模式固定 True)")
        args = parser.parse_args()
        if args.csv:
            import_single(args.csv, args.db, replace=args.replace)
        else:
            auto_import_all(db_path=args.db)
