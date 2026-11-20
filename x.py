import sqlite3
import time
import requests
from bs4 import BeautifulSoup

db_name = "google_repos.db"
conn = sqlite3.connect(db_name)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS repositories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    language TEXT,
    stars TEXT
)
""")
cursor.execute("DELETE FROM repositories")
conn.commit()

base_url = "https://github.com/orgs/google/repositories"
page = 1
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

while True:
    url = f"{base_url}?page={page}"
    print(f"Fetching: {url}")
    
    response = requests.get(url, headers=headers)
    time.sleep(1)

    if response.status_code != 200:
        print(f"Status code {response.status_code}. Stopping.")
        break

    soup = BeautifulSoup(response.text, "html.parser")
    
    # GitHubの現在のリスト構造（ul内のli、またはh3/h4見出しを含むブロック）を広く探す
    repo_items = soup.select("ul li")
    
    found_in_page = 0
    for item in repo_items:
        # リポジトリ名のリンクを探す（/google/リポジトリ名 の形式）
        name_tag = item.select_one("h3 a, h4 a, a[data-testid='listitem-title-link']")
        if not name_tag:
            continue
            
        href = name_tag.get("href", "")
        # /google/xxx の形式（スラッシュが2つだけ）のリンクを対象にする
        if not href.startswith("/google/") or href.count("/") != 2:
            continue

        repo_name = name_tag.get_text(strip=True)

        # 主要な言語の取得
        lang_tag = item.select_one("span[itemprop='programmingLanguage'], span[aria-label*='language']")
        if not lang_tag:
            # 言語表示の丸いアイコンの隣にあるテキストを探すフォールバック
            lang_span = item.find("span", class_=lambda c: c and "repo-language-color" in c)
            language = lang_span.find_next_sibling("span").get_text(strip=True) if (lang_span and lang_span.find_next_sibling("span")) else "None"
        else:
            language = lang_tag.get_text(strip=True)

        # スター数の取得
        star_tag = item.select_one("a[href$='/stargazers']")
        stars = star_tag.get_text(strip=True) if star_tag else "0"

        cursor.execute(
            "INSERT INTO repositories (name, language, stars) VALUES (?, ?, ?)",
            (repo_name, language, stars)
        )
        found_in_page += 1

    print(f"  -> {found_in_page} 件取得")
    if found_in_page == 0:
        print("全ページの取得が完了しました。")
        break

    conn.commit()
    page += 1

print("\n--- 保存されたデータ一覧（先頭20件） ---")
cursor.execute("SELECT id, name, language, stars FROM repositories")
rows = cursor.fetchall()

for row in rows[:20]:
    print(f"ID: {row[0]} | リポジトリ名: {row[1]} | 言語: {row[2]} | スター数: {row[3]}")

print(f"\n合計件数: {len(rows)} 件")
conn.close()