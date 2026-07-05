import json
import os
import re
import hashlib
import sys

# --- 設定 ---
TARGET_FOLDERS = ["1", "2", "3"]
BASE_DIR = "definitions"
INPUT_FILE_NAME = "definitions.json"

# 判定用の正規表現
RE_JA = re.compile(r"[\u3000-\u303f\u3040-\u309f\u30a0-\u30ff\uff00-\uffef\u4e00-\u9faf]")
RE_EN = re.compile(r"[A-Za-z]")

def should_extract(text, base_mode, key_prefix):
    """テキストが抽出対象かどうかを判定する（Puffish独自のシステムキーは除外）"""
    if not isinstance(text, str):
        return False
    if "puffish_skills." in text:
        return False
    if base_mode == "en":
        return bool(RE_EN.search(text))
    else:
        return bool(RE_JA.search(text))

def get_text_hash(text):
    return hashlib.md5(text.encode("utf-8")).hexdigest()[:4]

def process_target_value(value, key_prefix, translation_map, text_to_key_map, base_mode):
    """
    title や description の中身を解析し、どんな構文からであっても
    最終的に必ず {"translate": "key"} の形に統一して返す。
    """
    # ----------------------------------------------------
    # パターン2: 文字列直書き型の場合 (例: "title": "覚醒")
    # ----------------------------------------------------
    if isinstance(value, str):
        if should_extract(value, base_mode, key_prefix):
            if value in text_to_key_map:
                transport_key = text_to_key_map[value]
            else:
                # すでにキーの形をしている場合はそれをそのまま使い、そうでなければ新規ハッシュ
                if "shared." in value or f"{key_prefix}." in value:
                    transport_key = value
                else:
                    text_hash = get_text_hash(value)
                    transport_key = f"{key_prefix}.shared.{text_hash}"
                
                text_to_key_map[value] = transport_key
                translation_map[transport_key] = value
            # 💡 必ずこのオブジェクト構文にして返す
            return {"translate": transport_key}
        return value

    # ----------------------------------------------------
    # パターン3 or パターン1 の中身: 辞書型の場合
    # ----------------------------------------------------
    elif isinstance(value, dict):
        # すでに {"translate": "..."} になっている構造の場合
        if "translate" in value:
            tr_key = value["translate"]
            if isinstance(tr_key, str) and should_extract(tr_key, base_mode, key_prefix):
                if tr_key not in translation_map:
                    translation_map[tr_key] = tr_key
                return value
            return value
        
        # {"text": "..."} という構造が含まれている場合（入れ子を剥ぎ取る）
        if "text" in value:
            return process_target_value(value["text"], key_prefix, translation_map, text_to_key_map, base_mode)
            
        return {k: process_target_value(v, key_prefix, translation_map, text_to_key_map, base_mode) for k, v in value.items()}

    # ----------------------------------------------------
    # パターン1: 配列型の場合 (例: "description": [{"text": "..."}])
    # ----------------------------------------------------
    elif isinstance(value, list):
        # 配列の中に要素が1つだけで、それが {"text": "..."} のパターンの場合は、
        # 配列構造ごと剥ぎ取って {"translate": "..."} 単体に綺麗に一本化する
        if len(value) == 1:
            return process_target_value(value[0], key_prefix, translation_map, text_to_key_map, base_mode)
            
        return [process_target_value(item, key_prefix, translation_map, text_to_key_map, base_mode) for item in value]

    return value

def process_node(node, key_prefix, translation_map, text_to_key_map, base_mode):
    """JSONツリーを巡回し、'title' と 'description' の中身だけを処理する"""
    if isinstance(node, dict):
        new_dict = {}
        for key, value in node.items():
            if key in ("title", "description"):
                new_dict[key] = process_target_value(value, key_prefix, translation_map, text_to_key_map, base_mode)
            else:
                new_dict[key] = process_node(value, key_prefix, translation_map, text_to_key_map, base_mode)
        return new_dict
    elif isinstance(node, list):
        return [process_node(item, key_prefix, translation_map, text_to_key_map, base_mode) for item in node]
    else:
        return node

def clean_todo_text(text, base_mode):
    if not isinstance(text, str):
        return text
    match = re.search(r"TODO:\s*Translate\s*\[(.*?)\]", text, re.DOTALL | re.IGNORECASE)
    if match:
        content = match.group(1).strip()
        if base_mode == "ja" and RE_JA.search(content):
            return content.replace("[", "").replace("]", "").strip()
        else:
            text_stripped = re.sub(r"^TODO:\s*Translate\s*\[\s*", "", text, flags=re.IGNORECASE)
            if text_stripped != text:
                text_stripped = text_stripped.rstrip()
                if text_stripped.endswith("]"):
                    text_stripped = text_stripped[:-1]
            return text_stripped.strip()
    return text.strip()

def run_step1(user_namespace, base_mode):
    output_dir = f"output_{user_namespace}"
    os.makedirs(output_dir, exist_ok=True)

    translation_map = {}
    text_to_key_map = {}

    for folder in TARGET_FOLDERS:
        input_path = os.path.join(BASE_DIR, folder, INPUT_FILE_NAME)
        if not os.path.exists(input_path):
            print(f"⚠️ スキップ: {input_path} が見つかりません。")
            continue

        print(f"--- 処理中 ({base_mode}モード): {input_path} ---")
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        patched_data = process_node(data, user_namespace, translation_map, text_to_key_map, base_mode)

        output_patched_path = os.path.join(BASE_DIR, folder, "definitions_patched.json")
        with open(output_patched_path, "w", encoding="utf-8") as f:
            json.dump(patched_data, f, ensure_ascii=False, indent=2)
        print(f"  └ パッチ完了: {output_patched_path}")

    if not translation_map:
        print("処理すべきテキストデータが見つかりませんでした。")
        return

    src_lang_file = "ja_jp.json" if base_mode == "ja" else "en_us.json"
    src_file_path = os.path.join(output_dir, src_lang_file)
    with open(src_file_path, "w", encoding="utf-8") as f:
        json.dump(translation_map, f, ensure_ascii=False, indent=2)
    print(f"\n元言語ファイルを保存しました: {src_file_path}")

    blank_file_path = os.path.join(output_dir, "blank.json")
    lang_dict = {key: f"TODO: Translate [{text}]" for key, text in translation_map.items()}
    with open(blank_file_path, "w", encoding="utf-8") as f:
        json.dump(lang_dict, f, ensure_ascii=False, indent=2)
    print(f"📝 翻訳前テンプレートを保存しました: {blank_file_path}")
    print("\n[ステップ1完了] blank.json を翻訳してください。")

def run_step2(user_namespace, lang_filename="en_us", base_mode="ja"):
    output_dir = f"output_{user_namespace}"
    blank_file_path = os.path.join(output_dir, "blank.json")
    
    if not lang_filename.endswith(".json"):
        lang_filename += ".json"
        
    out_file_path = os.path.join(output_dir, lang_filename)

    if not os.path.exists(blank_file_path):
        print(f"エラー: 翻訳元のファイル {blank_file_path} が見つかりません。")
        return

    print(f"--- 翻訳クリーンアップ中: {blank_file_path} ---")
    with open(blank_file_path, "r", encoding="utf-8") as f:
        translated_data = json.load(f)

    cleaned_data = {}
    for key, value in translated_data.items():
        cleaned_data[key] = clean_todo_text(value, base_mode)

    with open(out_file_path, "w", encoding="utf-8") as f:
        json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
    print(f"✨ クリーンアップされた言語ファイルを保存しました: {out_file_path}")
    print(f"\n[ステップ2完了] {lang_filename} が完成しました！")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("引数が足りません。")
        sys.exit(1)
        
    mode = sys.argv[1]
    namespace = sys.argv[2]
    
    base_mode = "ja"
    
    if mode == "1":
        if len(sys.argv) > 3:
            base_mode = sys.argv[3]
        run_step1(namespace, base_mode)
    elif mode == "2":
        lang_name = sys.argv[3] if len(sys.argv) > 3 else "en_us"
        run_step2(namespace, lang_name, base_mode)