
# ============================================================
# THƯ VIỆN
# ============================================================
import os                       # Tương tác với hệ thống file
import json                     # Đọc/xử lý file JSON
import re                       # Biểu thức chính quy (regex)
import sys                      # Tương tác với hệ thống (sys.path)
import time                     # Sleep cho retry
from typing import List, Dict, Tuple, Optional    # Type hints
from collections import Counter # Đếm tần suất (dùng trong thống kê)
from fastapi import FastAPI, HTTPException        # Web framework
from fastapi.responses import HTMLResponse        # Trả HTML trang chủ
from fastapi.staticfiles import StaticFiles       # Phục vụ file tĩnh
from pydantic import BaseModel  # Validation dữ liệu đầu vào
from groq import Groq           # Client gọi API Groq
from dotenv import load_dotenv  # Đọc file .env
import httpx                    # HTTP client cho fallback API


# ============================================================
# ╔══════════════════════════════════════════════════════════╗
# ║  PHẦN 1: DIALECT MAPPING (dialect_map.py)              ║
# ║  Mục đích: Chuẩn hóa từ ngữ địa phương về tiếng Việt   ║
# ║  phổ thông trước khi gửi vào Groq LLM.                ║
# ╚══════════════════════════════════════════════════════════╝
# ============================================================

# ---------- TỪ ĐIỂN PHƯƠNG NGỮ ----------
# key = từ địa phương, value = từ phổ thông tương ứng
DIALECT_MAP = {
    # ===== MIỀN TRUNG → Phổ thông =====
    # Đại từ / Từ để hỏi
    "mô": "đâu",               # "đi mô" → "đi đâu"
    "răng": "sao",             # "răng rứa" → "sao vậy"
    "rứa": "vậy",              # "răng rứa" → "sao vậy"
    "chi": "gì",               # "làm chi" → "làm gì"
    "tê": "kia",               # "mô tê" → "đâu kia"
    "đâu": "đâu",
    "ni": "này",               # "ni" → "này"
    "nớ": "kia",               # "nớ" → "kia"
    "rú": "núi",
    "ngoe": "vậy",
    "chừ": "giờ",              # "chừ" → "giờ"
    "bây chừ": "bây giờ",     # "bây chừ" → "bây giờ"
    "hè": "nhỉ",
    "hè à": "nhỉ",
    "chừng": "khoảng",

    # Danh từ
    "mạ": "mẹ",               # "mạ" → "mẹ"
    "u": "mẹ",
    "bầm": "mẹ",
    "mệ": "bà",
    "cha": "bố",
    "bọ": "bố",
    "thầy": "bố",
    "tía": "bố",
    "chén": "bát",             # Miền Trung gọi "chén" = bát
    "đọi": "bát",
    "tô": "bát",
    "ly": "cốc",
    "bông": "hoa",             # Miền Trung gọi "bông" = hoa
    "trái": "quả",             # "trái cây" → "quả"

    # Động từ / Tính từ
    "dạn": "dày",
    "nhác": "lười",
    "vô": "vào",               # "vô" → "vào"
    "lộn": "về",               # "lộn" → "về"
    "lẹ": "nhanh",             # "lẹ lên" → "nhanh lên"
    "lẹ lên": "nhanh lên",
    "tốc": "nhanh",

    # Miền Trung đặc trưng
    "trốc": "đầu",             # "trốc" → "đầu"
    "tróc": "đầu",
    "răng rứa": "sao vậy",
    "mô răng rứa": "đâu sao vậy",
    "chi rứa": "gì vậy",
    "mô tê": "đâu kia",
    "ràng": "sao",
    "hắn": "nó",               # "hắn" → "nó"
    "o": "cô",                 # "o" → "cô"
    "tui": "tôi",
    "tau": "tao",
    "mi": "mày",
    "mấy o": "mấy cô",
    "mụ": "bà (xưng hô)",
    "đàng": "đường",
    "mấy chế": "mấy cô",

    # ===== MIỀN NAM → Phổ thông =====
    # Đại từ / Từ để hỏi
    "hông": "không",           # "hông" → "không"
    "hổng": "không",
    "hổng có": "không có",
    "đâu có": "không có",
    "đâu hông": "không đâu",
    "hen": "nhé",              # "hen" → "nhé"
    "nghen": "nhé",
    "nha": "nhé",
    "ná": "nhé",
    "chớ": "chứ",
    "zậy": "vậy",
    "vậy đó": "vậy đó",

    # Danh từ
    "má": "mẹ",
    "ba": "bố",
    "ly": "cốc",
    "cái ly": "cái cốc",
    "muỗng": "thìa",
    "thau": "chậu",
    "thau nhôm": "chậu nhôm",
    "trái": "quả",
    "trái cây": "hoa quả",
    "trái thơm": "quả dứa",
    "thơm": "dứa",
    "bông": "hoa",
    "bông hồng": "hoa hồng",
    "bông mai": "hoa mai",
    "đậu phộng": "lạc",
    "đậu phụng": "lạc",
    "khoai mì": "sắn",
    "bắp": "ngô",
    "trái bắp": "ngô",
    "mè": "vừng",
    "nếp": "gạo nếp",
    "ghe": "thuyền",
    "cái bóp": "cái ví",
    "bóp": "ví",
    "cái nón": "cái mũ",
    "nón": "mũ",
    "cây viết": "bút",
    "viết": "bút",
    "cây bút": "bút",
    "cái cặp": "cặp sách",
    "cặp": "cặp sách",
    "hột gà": "trứng gà",
    "hột vịt": "trứng vịt",
    "hột": "trứng",
    "thịt heo": "thịt lợn",
    "heo": "lợn",

    # Động từ / Tính từ
    "dzô": "vào",              # "dzô" → "vào"
    "vô": "vào",
    "dzìa": "về",
    "dzô đi": "vào đi",
    "bự": "to",                # "bự" → "to"
    "nhỏ": "bé",
    "ổng": "ông ấy",           # "ổng" → "ông ấy"
    "ảnh": "anh ấy",
    "chỉ": "chị ấy",
    "bã": "bà ấy",
    "hổng thấy": "không thấy",
    "hổng biết": "không biết",
    "hổng hiểu": "không hiểu",
    "hổng có gì": "không có gì",
    "hông có": "không có",
    "được hông": "được không",
    "đi hông": "đi không",
    "coi": "xem",
    "coi chừng": "cẩn thận",
    "coi bộ": "có vẻ",
    "nhức đầu": "đau đầu",
    "mắc cỡ": "ngượng",

    # Giao tiếp
    "dạ": "dạ",
    "vâng": "vâng",
    "dza": "dạ",
    "thưa": "thưa",
    "kêu": "gọi",
    "biểu": "bảo",
    "cám ơn": "cảm ơn",

    # Từ lóng / đặc trưng
    "sạo": "giả tạo",
    "xạo": "nói dối",
    "xạo ke": "nói dối",
    "đểu": "xấu tính",
    "dữ": "quá",
    "dữ thần": "quá trời",

    # Từ viết tắt / lóng từ điện thoại
    "otp": "mã OTP",
    "cọc": "tiền cọc",
    "chuyển khoản": "chuyển khoản",
    "ck": "chuyển khoản",
    "stk": "số tài khoản",
    "tk": "tài khoản",
    "qr": "mã QR",
    "qr code": "mã QR",
    "link": "đường dẫn",
}

# ---------- CỤM TỪ ĐẶC TRƯNG VÙNG MIỀN ----------
# Xử lý các cụm từ dài trước để tránh bị ghi đè bởi từ đơn
PHRASE_MAP = {
    # Miền Trung
    "mô răng rứa": "đâu sao vậy",
    "chi rứa": "gì vậy",
    "răng mà nói rứa": "sao mà nói vậy",
    "đi mô đó": "đi đâu đó",
    "về mô": "về đâu",
    "nhà mô": "nhà nào",
    "ai rứa": "ai vậy",
    "làm chi": "làm gì",
    "làm răng": "làm sao",
    "nói chi": "nói gì",
    "đi mô chơi": "đi đâu chơi",

    # Miền Nam
    "tui hổng biết": "tôi không biết",
    "tui hổng có": "tôi không có",
    "ổng nói vậy đó": "ông ấy nói vậy đó",
    "ảnh đi rồi": "anh ấy đi rồi",
    "chỉ nói vậy thôi": "chị ấy nói vậy thôi",
    "hông có gì đâu": "không có gì đâu",
}


def word_boundary_replace(text: str, old: str, new: str) -> str:
    """
    Thay thế từ có word boundary để tránh match substring.
    Ví dụ: "mô" không match vào "cơm", chỉ match "mô" đứng riêng.
    
    --- Args:
    text : str : Văn bản gốc
    old  : str : Từ cần thay thế
    new  : str : Từ thay thế

    --- Returns:
    str : Văn bản đã thay thế
    """
    # pattern: từ phải đứng ở đầu chuỗi hoặc sau ký tự phân cách, và kết thúc bởi ký tự phân cách
    pattern = re.compile(
        r'(^|[\s,.;:!?\"\'()\[\]{}])' + re.escape(old) + r'($|[\s,.;:!?\"\'()\[\]{}])',
        re.IGNORECASE
    )
    # Thay thế nhưng giữ lại ký tự phân cách ở đầu và cuối
    result = pattern.sub(r'\1' + new + r'\2', text)
    return result


def word_boundary_replace_dialect(text: str, old: str, new: str) -> str:
    """
    Giống word_boundary_replace nhưng nếu từ viết hoa (tên riêng "Chi"),
    vẫn thay thế nội dung nhưng giữ nguyên kiểu viết hoa của chữ cái đầu.
    """
    pattern = re.compile(
        r'(^|[\s,.;:!?\"\'()\[\]{}])' + re.escape(old) + r'($|[\s,.;:!?\"\'()\[\]{}])',
        re.IGNORECASE
    )
    result = []
    last_end = 0
    for m in pattern.finditer(text):
        word_start = m.start() + len(m.group(1))
        word_end = m.end() - len(m.group(2))
        matched_word = text[word_start:word_end]
        if matched_word and matched_word[0].isupper():
            # Giữ nguyên chữ hoa đầu từ, vẫn chuẩn hóa nội dung
            result.append(text[last_end:m.start()])
            result.append(m.group(1))
            result.append(new[0].upper() + new[1:])
            result.append(m.group(2))
        else:
            result.append(text[last_end:m.start()])
            result.append(m.group(1))
            result.append(new)
            result.append(m.group(2))
        last_end = m.end()
    result.append(text[last_end:])
    return ''.join(result)


def normalize_dialect(text: str) -> str:
    """
    Chuẩn hóa văn bản từ phương ngữ về tiếng Việt phổ thông.
    Áp dụng theo thứ tự: phrase → word (từ dài → ngắn) để tránh ghi đè sai.
    Giữ nguyên chữ hoa/chữ thường gốc để phát hiện tên riêng
    (ví dụ: "Chi" là tên → không đổi thành "gì").

    --- Args:
    text : str : Câu nói của người dùng (có thể chứa từ địa phương)

    --- Returns:
    str : Câu đã chuẩn hóa về phổ thông
    """
    normalized = text.strip()  # Bỏ khoảng trắng đầu/cuối

    # Bước 1: Chuẩn hóa khoảng trắng
    normalized = re.sub(r'\s+', ' ', normalized)  # Nén nhiều khoảng trắng thành 1
    # KHÔNG lower — word_boundary_replace đã có IGNORECASE
    # Giữ nguyên case gốc để phân biệt tên riêng vs từ địa phương

    # Bước 2: Xử lý cụm từ dài trước (phrase map)
    for phrase in sorted(PHRASE_MAP.keys(), key=len, reverse=True):
        replacement = PHRASE_MAP[phrase]
        normalized = word_boundary_replace(normalized, phrase, replacement)

    # Bước 3: Xử lý từ đơn (DIALECT_MAP), bỏ qua tên riêng (viết hoa)
    sorted_words = sorted(
        [word for word in DIALECT_MAP if word],
        key=len,
        reverse=True  # Từ dài trước, từ ngắn sau
    )
    for word in sorted_words:
        normalized = word_boundary_replace_dialect(normalized, word, DIALECT_MAP[word])

    # Bước 4: Nén khoảng trắng thừa (xuất hiện sau khi thay thế)
    normalized = re.sub(r'\s+', ' ', normalized).strip()

    # Bước 5: Viết hoa chữ cái đầu câu
    if normalized:
        normalized = normalized[0].upper() + normalized[1:]

    return normalized


def detect_region(text: str) -> str:
    """
    Phát hiện vùng miền qua cách nói (heuristic).
    
    --- Args:
    text : str : Câu nói của người dùng

    --- Returns:
    str : "north" | "central" | "south" | "unknown"
    """
    text_lower = text.lower()

    # Đặc trưng miền Trung: "mô", "răng", "rứa", "chi rứa", "mạ ơi", ...
    central_markers = ["mô", "răng", "rứa", "chi rứa", "mạ ơi",
                       "đi mô", "về mô", "làm chi", "o ơi"]
    central_score = sum(1 for m in central_markers if m in text_lower)

    # Đặc trưng miền Nam: "hổng", "hông", "chỉ ơi", "má ơi", "ổng", ...
    south_markers = ["hổng", "hông", "chỉ ơi", "má ơi", "ba ơi",
                     "dzô", "vô đây", "coi chừng", "mắc cỡ", "ổng", "ảnh",
                     "thơm", "bông", "chén", "trái cây"]
    south_score = sum(1 for m in south_markers if m in text_lower)

    # Đặc trưng miền Bắc: "bố ơi", "mẹ ơi", "bát", "cốc", ...
    north_markers = ["bố ơi", "mẹ ơi", "bát", "cốc"]
    north_score = sum(1 for m in north_markers if m in text_lower)

    # Tạo danh sách điểm số và sắp xếp giảm dần
    scores = [
        ("central", central_score),
        ("south", south_score),
        ("north", north_score),
    ]
    scores.sort(key=lambda x: x[1], reverse=True)

    # Trả về vùng miền có điểm cao nhất, hoặc "unknown" nếu không có marker nào
    if scores[0][1] > 0:
        return scores[0][0]
    return "unknown"


# ============================================================
# BẢN ĐỒ XƯNG HÔ THEO VÙNG MIỀN
# Dùng để phát hiện cách người dùng xưng hô và chọn cách
# trả lời phù hợp: user_term (gọi người dùng), self_term (AI xưng)
# ============================================================

XUNG_HO_MAP: Dict[str, Tuple[str, str, str]] = {
    # (từ người dùng dùng) -> (gọi người dùng là, AI xưng là, vùng miền)
    # --- Cha mẹ (AI xưng "con") ---
    "mạ":   ("mạ",   "con",   "central"),
    "má":   ("má",   "con",   "south"),
    "u":    ("u",    "con",   "north"),
    "bầm":  ("bầm",  "con",   "north"),
    "mẹ":   ("mẹ",   "con",   "general"),
    "ba":   ("ba",   "con",   "south"),
    "bố":   ("bố",   "con",   "north"),
    "thầy":  ("thầy",  "con",   "north"),
    "tía":  ("tía",  "con",   "south"),
    "cha":  ("cha",  "con",   "general"),
    # --- Ông bà, cụ (AI xưng "cháu") ---
    "ông":  ("ông",  "cháu",  "general"),
    "bà":   ("bà",   "cháu",  "general"),
    "cụ":   ("cụ",   "cháu",  "general"),
    "ôn":   ("ôn",   "cháu",  "central"),
    "mệ":   ("mệ",   "cháu",  "central"),
    "già":  ("già",  "cháu",  "general"),
    # --- Bác, chú, dì, cô, anh, chị (AI xưng "cháu" hoặc "em") ---
    "bác":  ("bác",  "cháu",  "general"),
    "chú":  ("chú",  "cháu",  "general"),
    "dì":   ("dì",   "cháu",  "general"),
    "o":    ("o",    "cháu",  "central"),
    "cô":   ("cô",   "cháu",  "general"),
    "dượng":("dượng","cháu",  "general"),
    "mợ":   ("mợ",   "cháu",  "general"),
    "cậu":  ("cậu",  "cháu",  "general"),
    "mụ":   ("mụ",   "cháu",  "central"),
    "thím": ("thím", "cháu",  "general"),
    # --- Anh, chị (AI xưng "em") ---
    "anh":  ("em",   "anh",   "general"),
    "chị":  ("em",   "chị",   "general"),
    # --- Em (AI xưng "anh/chị") ---
    "em":   ("anh/chị", "em", "general"),
}

# Người dùng gọi AI là con/cháu (cần reverse lookup để tìm user_term)
REVERSE_MAP = {
    "con":  ("con", "parent"),    # user gọi AI là con → AI tìm từ cha mẹ trong tin nhắn
    "cháu": ("cháu", "elder"),    # user gọi AI là cháu → AI tìm từ ông bà/bác/chú trong tin nhắn
}

PARENT_TERMS = ["mạ", "má", "u", "bầm", "mẹ", "ba", "bố", "thầy", "tía", "cha"]
ELDER_TERMS = ["ông", "bà", "cụ", "già", "ôn", "mệ", "bác", "chú", "dì", "o", "cô", "dượng", "mợ", "cậu", "mụ", "thím"]

XUNG_HO_TERMS = "|".join(re.escape(t) for t in XUNG_HO_MAP.keys())


def _reverse_xung_ho(msg: str, child_term: str) -> Tuple[str, str]:
    """
    Khi người dùng gọi AI là 'con' hoặc 'cháu', tìm từ người dùng tự xưng.
    
    --- Args:
    msg        : str : Câu nói gốc của người dùng (lowercase)
    child_term : str : "con" hoặc "cháu" (cách user gọi AI)
    
    --- Returns:
    Tuple[str, str] : (user_term - gọi người dùng, self_term - AI xưng)
    """
    search_terms = PARENT_TERMS if child_term == "con" else ELDER_TERMS
    
    for term in search_terms:
        if re.search(rf"\b{re.escape(term)}\b", msg):
            data = XUNG_HO_MAP.get(term)
            if data:
                return data[0], "con" if child_term == "con" else "cháu"
    
    # Fallback: thử search nhóm còn lại
    fallback = ELDER_TERMS if child_term == "con" else PARENT_TERMS
    for term in fallback:
        if re.search(rf"\b{re.escape(term)}\b", msg):
            data = XUNG_HO_MAP.get(term)
            if data:
                return data[0], "con" if child_term == "con" else "cháu"
    
    # Không tìm thấy từ nào → dùng mặc định theo vai
    if child_term == "con":
        return "mẹ", "con"  # mặc định: user là cha/mẹ
    return "ông/bà", "cháu"  # mặc định: user là ông/bà


def detect_xung_ho(message: str) -> Tuple[str, str]:
    """
    Phát hiện cách xưng hô người dùng dùng để gọi AI.
    
    --- Args:
    message : str : Câu nói gốc của người dùng (chưa chuẩn hóa)
    
    --- Returns:
    Tuple[str, str] : (user_term - gọi người dùng, self_term - AI xưng)
                      Mặc định: ("ông/bà", "cháu")
    """
    msg_lower = message.lower().strip()
    
    # Pattern 1: "con ơi / cháu ơi" ở đầu câu → reverse lookup
    m = re.match(r"^(con|cháu)\s*ơi\b", msg_lower)
    if m:
        return _reverse_xung_ho(msg_lower, m.group(1))
    
    # Pattern 2: "X ơi ..." ở đầu câu (X = bác, mạ, u, ông, ...)
    m = re.match(rf"^({XUNG_HO_TERMS})\s*ơi\b", msg_lower)
    if m:
        data = XUNG_HO_MAP.get(m.group(1))
        if data:
            return data[0], data[1]
    
    # Pattern 3: "con ơi / cháu ơi" ở giữa câu
    m = re.search(r"(?<!\w)(con|cháu)\s+ơi\b", msg_lower)
    if m:
        return _reverse_xung_ho(msg_lower, m.group(1))
    
    # Pattern 4: "X ơi" ở giữa câu
    m = re.search(rf"(?<!\w)({XUNG_HO_TERMS})\s+ơi\b", msg_lower)
    if m:
        data = XUNG_HO_MAP.get(m.group(1))
        if data:
            return data[0], data[1]
    
    # Pattern 5: "X ..." từ đầu câu (không có ơi)
    m = re.match(rf"^({XUNG_HO_TERMS})\b", msg_lower)
    if m:
        data = XUNG_HO_MAP.get(m.group(1))
        if data:
            return data[0], data[1]
    
    # Pattern 6: "X công an" hoặc "X ấy" ở cuối câu (vd: "hông chú công an?")
    m = re.search(rf"(?<!\w)({XUNG_HO_TERMS})\s+(công an|cảnh sát|bộ đội|huyện|xã)\s*[?.!]*\s*$", msg_lower)
    if m:
        data = XUNG_HO_MAP.get(m.group(1))
        if data:
            return data[0], data[1]
    
    # Pattern 7: term ở cuối câu hỏi (vd: "hông chú?", "phải không bác?")
    # Chỉ match khi term nằm trong 50 ký tự cuối
    if len(msg_lower) > 50:
        tail = msg_lower[-50:]
    else:
        tail = msg_lower
    m = re.search(rf"(?<!\w)({XUNG_HO_TERMS})\s*[\?\.!]?\s*$", tail)
    if m:
        data = XUNG_HO_MAP.get(m.group(1))
        if data:
            return data[0], data[1]
    
    # Mặc định: không phát hiện được → ông/bà - cháu
    return "ông/bà", "cháu"


# ============================================================
# ╔══════════════════════════════════════════════════════════╗
# ║  PHẦN 2: RAG ENGINE (rag_engine.py)                    ║
# ║  Mục đích: Chunk dữ liệu JSON, tính relevance score,   ║
# ║  chỉ lấy top-K chunks liên quan nhất.                  ║
# ╚══════════════════════════════════════════════════════════╝
# ============================================================

class RAGChunk:
    """
    Một chunk dữ liệu - đại diện cho một kịch bản lừa đảo.
    Chứa hội thoại, file nguồn, loại lừa đảo và các từ khóa.
    """
    def __init__(self, id: int, dialogue: List[Dict], source_file: str, fraud_type: str):
        """
        --- Args:
        id          : int          : ID của chunk
        dialogue    : List[Dict]   : Mảng các đoạn hội thoại [{role, content}, ...]
        source_file : str          : Tên file JSON nguồn
        fraud_type  : str          : Loại lừa đảo (tên thư mục cha)
        """
        self.id = id                        # ID định danh chunk
        self.dialogue = dialogue            # Mảng hội thoại gốc
        self.source_file = source_file      # File nguồn
        self.fraud_type = fraud_type        # Loại lừa đảo
        self.full_text = self._build_full_text()    # Text đầy đủ từ dialogue
        self.keywords = self._extract_keywords()    # Tập từ khóa lừa đảo trong chunk

    def _build_full_text(self) -> str:
        """
        Xây dựng text đầy đủ từ mảng dialogue (dạng [role]: content).
        
        --- Returns:
        str : Toàn bộ hội thoại dạng text
        """
        lines = []
        for turn in self.dialogue:
            role = turn.get("role", "unknown")       # Vai trò người nói
            content = turn.get("content", "")         # Nội dung lời thoại
            lines.append(f"[{role}]: {content}")     # Gộp lại
        return "\n".join(lines)

    def _extract_keywords(self) -> set:
        """
        Trích xuất từ khóa lừa đảo xuất hiện trong dialogue.
        So khớp với danh sách scam_keywords định nghĩa sẵn.

        --- Returns:
        set : Tập các từ khóa lừa đảo tìm được
        """
        text = self.full_text.lower()  # Đưa về chữ thường

        # Danh sách từ khóa lừa đảo phổ biến
        scam_keywords = {
            "chuyển khoản", "chuyển tiền", "cọc", "đặt cọc", "otp",
            "mã otp", "mật khẩu", "pin", "tài khoản", "số tài khoản",
            "stk", "link", "bấm vào", "cài ứng dụng", "ứng dụng",
            "công an", "toà án", "viện kiểm sát", "ngân hàng",
            "bắt giữ", "đe dọa", "khóa tài khoản", "nhận thưởng",
            "trúng thưởng", "quà tặng", "lợi nhuận", "đầu tư",
            "tiền ảo", "cccd", "căn cước", "định danh",
            "tuyển sinh", "tuyển dụng", "từ thiện", "quyên góp",
            "hoàn tiền", "chuyển lại", "phí xác thực", "phí ưu tiên",
            "tài khoản cá nhân", "bảo trì hệ thống", "hệ thống đang lỗi"
        }
        words = set(re.findall(r'\b\w+\b', text))      # Tách từ
        # So khớp cả từ đơn lẫn cụm từ nhiều chữ
        for kw in scam_keywords:
            if " " in kw:
                if kw in text:
                    words.add(kw)
            # Nếu là từ đơn, đã được thêm vào words bởi re.findall ở trên
        return words & scam_keywords  # Giao giữa từ trong text và từ khóa


class RAGEngine:
    """
    RAG Engine với chunking + relevance scoring.
    Cách hoạt động:
      1. Đọc tất cả file JSON từ Data_Kich_Ban/
      2. Chia mỗi kịch bản thành một chunk riêng
      3. Khi có câu hỏi, tính relevance score cho từng chunk
      4. Chỉ lấy top-K chunks liên quan nhất (tránh nhiễu)
    """
    def __init__(self, data_folder: Optional[str] = None):
        """
        --- Args:
        data_folder : str (optional) : Đường dẫn đến thư mục chứa dữ liệu JSON
        """
        self.chunks: List[RAGChunk] = []           # Danh sách tất cả chunks
        self.data_folder = data_folder or self._find_data_folder()
        self._load_data()  # Tự động load dữ liệu khi khởi tạo

    def _find_data_folder(self) -> str:
        """
        Tự động phát hiện thư mục chứa dữ liệu.
        Thử các tên: Data_Kich_Ban, data_kich_ban, ...
        
        --- Returns:
        str : Đường dẫn thư mục dữ liệu
        """
        possible_names = ["Data_Kich_Ban", "data_kich_ban", "Data_Kich_Ban/"]
        for name in possible_names:
            if os.path.exists(name) and os.path.isdir(name):
                return name

        # Fallback: tìm bất kỳ thư mục nào có chứa "kich_ban" hoặc "data"
        for item in os.listdir("."):
            if os.path.isdir(item) and ("kich_ban" in item.lower() or "data" in item.lower()):
                return item
        return "Data_Kich_Ban"  # Mặc định

    def _load_data(self):
        """
        Đọc tất cả file JSON từ thư mục dữ liệu và tạo chunks.
        Duyệt đệ quy tất cả thư mục con.
        """
        if not os.path.exists(self.data_folder):
            print(f"[RAG Engine] Warning: Folder '{self.data_folder}' not found.")
            return

        file_count = 0    # Đếm số file JSON
        chunk_count = 0   # Đếm số chunk tạo được

        for root, dirs, files in os.walk(self.data_folder):  # Duyệt đệ quy
            for file in files:
                if file.endswith(".json"):     # Chỉ xử lý file JSON
                    filepath = os.path.join(root, file)
                    fraud_type = os.path.basename(root)  # Tên thư mục = loại lừa đảo

                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            data_list = json.load(f)  # Load JSON

                        for kich_ban in data_list:
                            kich_ban_id = kich_ban.get("_id", chunk_count + 1)
                            dialogue = kich_ban.get("dialogue", [])

                            if dialogue:  # Chỉ tạo chunk nếu có hội thoại
                                chunk = RAGChunk(
                                    id=kich_ban_id,
                                    dialogue=dialogue,
                                    source_file=file,
                                    fraud_type=fraud_type
                                )
                                self.chunks.append(chunk)
                                chunk_count += 1
                        file_count += 1

                    except Exception as e:
                        print(f"[RAG Engine] Lỗi đọc {file}: {e}")

        print(f"[RAG Engine] Loaded {file_count} files, {chunk_count} chunks")

    DOMAIN_KEYWORDS = {
        "đặt bàn ăn": ["bàn", "ăn", "nhà hàng", "đặt bàn", "sinh nhật", "tiệc", "món"],
        "đặt phòng khách sạn": ["khách sạn", "phòng", "đặt phòng", "du lịch", "nghỉ", "lưu trú"],
        "đầu tư tiền ảo": ["đầu tư", "tiền ảo", "lợi nhuận", "crypto", "cổ phiếu", "vốn"],
        "định danh cccd": ["cccd", "căn cước", "định danh", "công an", "otp", "mật khẩu", "link"],
        "từ thiện": ["từ thiện", "quỹ", "ủng hộ", "quyên góp", "bé", "ung thư", "bệnh viện"],
        "trúng tuyển": ["trúng tuyển", "tuyển sinh", "trường", "đại học", "thi cử", "nhập học"],
    }

    def _domain_match(self, query_lower: str, fraud_type: str) -> bool:
        for ftype, keywords in self.DOMAIN_KEYWORDS.items():
            if ftype in fraud_type.lower():
                query_words = set(re.findall(r'\b\w+\b', query_lower))
                match_count = 0
                for kw in keywords:
                    kw_words = kw.split()
                    if len(kw_words) == 1 and kw in query_words:
                        match_count += 1
                    elif len(kw_words) > 1 and kw in query_lower:
                        match_count += 1
                return match_count >= 2
        return True

    def calculate_relevance(self, query: str, chunk: RAGChunk) -> float:
        """
        Tính điểm relevance giữa câu hỏi user và chunk.
        Scoring factors:
          1. Fraud keyword match: Từ khóa lừa đảo trong query
          2. Word overlap: Từ trong query xuất hiện trong chunk
          3. Domain match: Query có liên quan đến loại lừa đảo của chunk không

        --- Args:
        query : str      : Câu hỏi của người dùng
        chunk : RAGChunk : Chunk dữ liệu cần so sánh

        --- Returns:
        float : Điểm relevance (0.0 → 1.0)
        """
        if not query or not chunk:
            return 0.0

        query_lower = query.lower()
        query_words = set(re.findall(r'\b\w+\b', query_lower))

        # Factor 1: Từ khóa lừa đảo trong query (fraud_score)
        fraud_match = 0
        for kw in chunk.keywords:
            if kw in query_lower:
                fraud_match += 1

        # Factor 2: Các từ trong query xuất hiện trong chunk (word overlap)
        chunk_text_lower = chunk.full_text.lower()
        query_word_match = sum(
            1 for word in query_words
            if len(word) > 2 and word in chunk_text_lower
        )

        query_word_score = query_word_match / max(len(query_words), 1)
        fraud_score = fraud_match / max(len(chunk.keywords), 1) * 0.5

        total_score = query_word_score * 0.6 + fraud_score * 0.4

        # Factor 3: Domain mismatch penalty
        if not self._domain_match(query_lower, chunk.fraud_type):
            return 0.0

        return total_score

    def retrieve(self, query: str, top_k: int = 5, min_score: float = 0.05) -> Tuple[List[RAGChunk], str]:
        """
        Retrieve top-K chunks liên quan nhất.

        --- Args:
        query    : str   : Câu hỏi của người dùng
        top_k    : int   : Số chunk muốn lấy (mặc định: 5)
        min_score: float : Ngưỡng relevance tối thiểu (lọc nhiễu)

        --- Returns:
        (relevant_chunks : List[RAGChunk], context_string : str)
        """
        if not self.chunks:
            return [], "Chưa có dữ liệu tra cứu."

        # Tính score cho tất cả chunks
        scored_chunks: List[Tuple[float, RAGChunk]] = []
        for chunk in self.chunks:
            score = self.calculate_relevance(query, chunk)
            if score >= min_score:  # Lọc chunk có điểm dưới ngưỡng
                scored_chunks.append((score, chunk))

        # Sắp xếp giảm dần theo score và lấy top-K
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        top_chunks = [chunk for _, chunk in scored_chunks[:top_k]]

        # Nếu không có chunk nào đủ điểm
        if not top_chunks:
            return [], "Không tìm thấy kịch bản nào liên quan đến câu hỏi của ông/bà."

        # Xây dựng context string từ các chunks
        context_parts = []
        for i, chunk in enumerate(top_chunks, 1):
            context_parts.append(
                f"[KỊCH BẢN {i} - {chunk.fraud_type}]\n"
                f"{chunk.full_text}\n"
            )
        context_string = "\n---\n".join(context_parts)

        return top_chunks, context_string

    def get_statistics(self) -> Dict:
        """
        Lấy thống kê dữ liệu RAG.

        --- Returns:
        Dict: { "total_chunks": int, "fraud_types": Dict[str, int], "data_folder": str }
        """
        fraud_types = Counter()
        for chunk in self.chunks:
            fraud_types[chunk.fraud_type] += 1  # Đếm số chunk theo từng loại lừa đảo

        return {
            "total_chunks": len(self.chunks),
            "fraud_types": dict(fraud_types),
            "data_folder": self.data_folder,
        }


# ============================================================
# ╔══════════════════════════════════════════════════════════╗
# ║  PHẦN 3: HALLUCINATION GUARD (hallucination_guard.py)  ║
# ║  Mục đích: Kiểm tra response của Groq có bị "ảo giác"  ║
# ║  (hallucination) hay không bằng cách so với RAG context.║
# ╚══════════════════════════════════════════════════════════╝
# ============================================================

# Những từ "đóng mở" không mang thông tin (cần loại bỏ khi trích claims)
STOP_WORDS = {
    "dạ", "vâng", "ạ", "à", "ơi", "nhé", "nha", "nghen",
    "thì", "là", "và", "của", "có", "được", "sẽ", "đã",
    "đang", "cũng", "rất", "lắm", "quá", "nhỉ", "nhưng",
    "hoặc", "hay", "nếu", "vì", "nên", "mà", "bị", "đây",
    "đó", "kia", "này", "vậy", "thế", "nào", "sao", "gì",
    "cả", "những", "các", "mọi", "mỗi", "một", "như",
}


class HallucinationGuard:
    """
    Layer kiểm tra hallucination sau khi Groq trả response.
    
    Cơ chế:
      1. Trích xuất các "claim" (thông tin khẳng định) từ response.
      2. Tính grounding score = % claims được hỗ trợ bởi context RAG.
      3. Nếu score thấp → response có thể bị hallucination → fallback.
      4. Log các trường hợp hallucination để debug.
    """
    # Số điện thoại khẩn cấp toàn quốc — kiến thức phổ thông, luôn được phép
    UNIVERSAL_EMERGENCY_NUMBERS = {"113", "114", "115", "111", "112", "02437349974", "19009095", "02838351764", "02361022", "18008065"}

    def __init__(self, threshold: float = 0.25):
        """
        --- Args:
        threshold : float : Ngưỡng grounding score tối thiểu (0.0 - 1.0).
                           Thấp = cho phép nhiều (dễ bị hallucination)
                           Cao = an toàn hơn (nhưng dễ false positive)
        """
        self.threshold = threshold   # Ngưỡng phát hiện hallucination
        self.log: List[dict] = []    # Log lịch sử các lần kiểm tra

    def _extract_claims(self, text: str) -> set:
        """
        Trích xuất các "claim" (thông tin khẳng định) từ text.
        Claim = danh từ, số, tên riêng, hành động cụ thể.

        --- Args:
        text : str : Văn bản cần trích xuất

        --- Returns:
        set : Tập các claims
        """
        text_lower = text.lower()

        # Từ có độ dài > 2, không phải stop word
        words = set(re.findall(r'\b\w{3,}\b', text_lower))
        claims = words - STOP_WORDS

        # Thêm số (ví dụ: "2.5 triệu", "500 nghìn", ...)
        numbers = set(re.findall(
            r'\d+(?:[.,]\d+)*(?:\s*(?:triệu|nghìn|đồng|ngàn|trăm|tỷ))?',
            text_lower
        ))

        # Thêm entity: từ viết hoa (tên người, tổ chức)
        entities = set(re.findall(
            r'\b[AÀẢÃÁẠĂẰẮẶẲẴÂẤẦẨẪẬBCDĐEÈÉẺẼẸÊỀẾỂỄỆFGHIÌÍỈĨỊJKLMNÒÓỎÕỌÔỒỐỔỖỘƠỚỜỞỠỢPQRSTUÙÚỦŨỤƯỪỨỬỮỰVWXYÝỲỶỸỴZ][a-zàảãáạăằắặẳẵâấầẩẫậbcdđeèéẻẽẹêềếểễệfghiìíỉĩịjklmnoòóỏõọôồốổỗộơớờởỡợpqrstuùúủũụưừứửữựvwxyýỳỷỹỵz]+',
            text
        ))

        # Hợp tất cả các loại claims
        all_claims = claims | set(numbers) | set(entities)
        return all_claims

    def _calculate_grounding_score(self, context: str, response: str) -> Tuple[float, set, set]:
        """
        Tính grounding score = tỷ lệ claims trong response có xuất hiện trong context.

        --- Args:
        context  : str : Context RAG
        response : str : Response từ Groq

        --- Returns:
        (score : float, supported : set, unsupported : set)
        """
        if not response or not context:
            return 0.0, set(), set()

        response_claims = self._extract_claims(response)   # Lấy claims từ response
        context_lower = context.lower()

        supported = set()     # Claims được hỗ trợ (có trong context)
        unsupported = set()   # Claims không có trong context

        for claim in response_claims:
            if claim in context_lower:
                # Claim xuất hiện trực tiếp trong context
                supported.add(claim)
            else:
                # Kiểm tra fuzzy: claim có thể là một phần của từ trong context
                # Ví dụ: "chuyển" là một phần của "chuyển khoản"
                found = False
                for word in re.findall(r'\b\w+\b', context_lower):
                    if claim in word or word in claim:
                        found = True
                        supported.add(claim)
                        break
                if not found:
                    unsupported.add(claim)

        total = len(response_claims)
        if total == 0:
            return 1.0, set(), set()  # Không có claim = không hallucination

        score = len(supported) / max(total, 1)  # Tỷ lệ claims được hỗ trợ
        return score, supported, unsupported

    def _check_unsafe_patterns(self, response: str) -> bool:
        """
        Kiểm tra các pattern nguy hiểm trong response.
        Ví dụ: "Tôi khuyên bạn nên chuyển tiền" (ngược với nhiệm vụ).

        --- Args:
        response : str : Response từ Groq

        --- Returns:
        bool : True nếu phát hiện pattern nguy hiểm
        """
        response_lower = response.lower()

        # Các pattern nguy hiểm (không bao giờ được phép xuất hiện)
        unsafe_patterns = [
            "chuyển tiền ngay",
            "cung cấp otp",
            "cung cấp mật khẩu",
            "bấm vào link",
            "cài ứng dụng",
        ]

        for pattern in unsafe_patterns:
            if pattern in response_lower:
                # Chỉ đánh dấu nếu đây là lời khuyên (có từ "nên", "hãy", "phải")
                if any(kw in response_lower for kw in ["nên", "hãy", "phải"]):
                    return True
        return False

    def validate(self, context: str, response: str, user_query: str = "") -> Tuple[bool, str, float]:
        """
        Validate response có bị hallucination không.

        --- Args:
        context    : str : Context RAG
        response   : str : Response từ Groq
        user_query : str : Câu hỏi gốc của user (optional, dùng cho logging)

        --- Returns:
        (is_safe : bool, final_response : str, grounding_score : float)
        """
        # Tính grounding score
        score, supported, unsupported = self._calculate_grounding_score(
            context or "", response or ""
        )

        # Kiểm tra unsafe pattern
        has_unsafe = self._check_unsafe_patterns(response)

        # Ghi log
        log_entry = {
            "user_query": user_query,
            "response": response,
            "supported_claims": list(supported)[:10],
            "unsupported_claims": list(unsupported)[:10],
            "grounding_score": score,
            "threshold": self.threshold,
            "has_unsafe_pattern": has_unsafe,
        }
        self.log.append(log_entry)

        # Quyết định: nếu có pattern nguy hiểm → block ngay lập tức
        if has_unsafe:
            return False, "", 0.0

        # Loại bỏ số khẩn cấp toàn quốc & hỗ trợ công cộng khỏi unsupported claims
        unsupported = {c for c in unsupported if c.replace(".", "") not in self.UNIVERSAL_EMERGENCY_NUMBERS}

        # Nếu quá nhiều unsupported claims → hallucination
        if score < self.threshold:
            max_unsupported = 2  # Chỉ cho phép tối đa 2 claim không được support
            if len(unsupported) > max_unsupported:
                return False, "", score

        # Response an toàn
        return True, response, score

    def get_hallucination_rate(self) -> float:
        """
        Tính tỷ lệ hallucination từ lịch sử log.

        --- Returns:
        float : Tỷ lệ hallucination (0.0 → 1.0)
        """
        if not self.log:
            return 0.0
        hallucinated = sum(
            1 for entry in self.log
            if entry.get("grounding_score", 1.0) < entry.get("threshold", 0.25)
        )
        return hallucinated / len(self.log)


# ============================================================
# ╔══════════════════════════════════════════════════════════╗
# ║  PHẦN 4: FASTAPI SERVER (improved_main.py)             ║
# ║  Mục đích: Định nghĩa các API endpoint, khởi tạo hệ    ║
# ║  thống và pipeline xử lý.                              ║
# ╚══════════════════════════════════════════════════════════╝
# ============================================================

# ---------- KHỞI TẠO ----------
load_dotenv()   # Đọc file .env để lấy GROQ_API_KEY

# Tạo ứng dụng FastAPI
app = FastAPI(title="Anti-Scam Chatbot - Improved")

# API Keys
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

# Model config
LLM_MODEL = "llama-3.1-8b-instant"
FALLBACK_MODEL = "meta-llama/llama-3.1-8b-instruct"  # OpenRouter model ID

# Kiểm tra API key từ biến môi trường
if not GROQ_API_KEY:
    print("[WARNING] GROQ_API_KEY not found in .env file")
    client = None  # Không có API key → không thể gọi Groq
else:
    client = Groq(api_key=GROQ_API_KEY)  # Khởi tạo client Groq


def _call_groq_with_retry(messages: list, max_retries: int = 2) -> Optional[str]:
    """Gọi Groq API với retry logic (exponential backoff)."""
    for attempt in range(max_retries + 1):
        try:
            completion = client.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                temperature=0.6,
                max_tokens=150,
                frequency_penalty=1.2,
                presence_penalty=0.8,
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"[GROQ] Attempt {attempt + 1}/{max_retries + 1} failed: {e}")
            if attempt < max_retries:
                wait = 2 ** attempt  # 1s, 2s
                print(f"[GROQ] Retrying in {wait}s...")
                time.sleep(wait)
    return None


def _call_openrouter_fallback(messages: list) -> Optional[str]:
    """Gọi OpenRouter API làm fallback khi Groq không khả dụng."""
    if not OPENROUTER_API_KEY:
        print("[FALLBACK] No OPENROUTER_API_KEY configured")
        return None
    try:
        with httpx.Client(timeout=30.0) as http:
            resp = http.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": FALLBACK_MODEL,
                    "messages": messages,
                    "temperature": 0.6,
                    "max_tokens": 150,
                    "frequency_penalty": 1.2,
                    "presence_penalty": 0.8,
                },
            )
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
        else:
            print(f"[FALLBACK] OpenRouter error {resp.status_code}: {resp.text[:200]}")
            return None
    except Exception as e:
        print(f"[FALLBACK] OpenRouter exception: {e}")
        return None

# Đọc System Prompt (đã hợp nhất từ SystemPrompt.txt và SystemPrompt_updated.txt)
SYSTEM_PROMPT_PATH = "SystemPrompt.txt"

with open(SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()  # Nội dung system prompt

# Khởi tạo RAG Engine (đọc tất cả dữ liệu JSON vào bộ nhớ)
print("[INIT] Loading RAG Engine...")
rag_engine = RAGEngine()

# Khởi tạo Hallucination Guard với ngưỡng 0.2
hallucination_guard = HallucinationGuard(threshold=0.2)


# ---------- MODEL DỮ LIỆU ----------
class ChatInput(BaseModel):
    """Model validation cho dữ liệu đầu vào từ client"""
    messages: List[Dict[str, str]]  # Mảng các tin nhắn [{role, content}, ...]


# ---------- API ENDPOINTS ----------
@app.get("/", response_class=HTMLResponse)
def get_home():
    """
    Endpoint trang chủ.
    Phục vụ file index.html từ thư mục templates/.
    """
    try:
        with open("templates/index.html", "r", encoding="utf-8") as f:
            html = f.read()
            return html
    except FileNotFoundError:
        return HTMLResponse(
            content="<h3>Vui lòng tạo thư mục 'templates' và đặt file 'index.html' vào trong.</h3>",
            status_code=404
        )


@app.get("/health")
def health_check():
    """
    Endpoint kiểm tra sức khỏe hệ thống.
    Trả về trạng thái của các thành phần.
    """
    stats = rag_engine.get_statistics()
    return {
        "status": "ok",
        "model_available": client is not None,    # Groq có khả dụng không?
        "rag_stats": {
            "total_chunks": stats["total_chunks"],        # Tổng số chunks
            "fraud_types": stats["fraud_types"],           # Các loại lừa đảo
        },
        "hallucination_rate": hallucination_guard.get_hallucination_rate(),
        "system_prompt": SYSTEM_PROMPT_PATH,
    }


def _insert_line_breaks(response: str, user_term: str) -> str:
    """Chia response thành nhiều dòng dựa trên cấu trúc chào → giải thích → lời khuyên."""
    if '\n' in response:
        return response  # Đã có xuống dòng (model tự làm)
    sentences = re.split(r'(?<=[.!?])\s+', response.strip())
    if len(sentences) <= 2:
        return response  # Quá ngắn, không cần chia

    # Dòng 1: chào + nhận định (câu đầu)
    line1 = sentences[0]

    # Dòng cuối: lời khuyên (câu bắt đầu bằng từ khuyên hoặc "nên")
    advice_idx = None
    advice_pattern = re.compile(
        rf'^(Tốt nhất|{re.escape(user_term)} nên|Con khuyên|Cháu khuyên|'
        rf'{re.escape(user_term)} hãy|Hãy|Gọi|Liên hệ|Báo|Đến|Nhờ)',
        re.IGNORECASE
    )
    for i in range(len(sentences) - 1, 0, -1):
        if advice_pattern.match(sentences[i]):
            advice_idx = i
            break
    if advice_idx is None:
        advice_idx = len(sentences) - 1  # Mặc định: câu cuối là lời khuyên

    # Dòng giữa: giải thích
    line2 = ' '.join(sentences[1:advice_idx])
    line3 = ' '.join(sentences[advice_idx:])

    parts = [line1]
    if line2:
        parts.append(line2)
    parts.append(line3)
    return '\n'.join(parts)


@app.post("/chat")
def chat(data: ChatInput):
    """
    API CHÍNH - Xử lý tin nhắn từ người dùng.
    
    Pipeline xử lý 7 bước:
      1. Nhận message từ user
      2. Dialect normalization (Bắc-Trung-Nam → phổ thông)
      3. RAG retrieval (chunked + relevance scored)
      4. Build prompt với context
      5. Call Groq LLM (llama-3.1-8b-instant)
      6. Hallucination validation
      7. Trả response an toàn
    """
    if not client:
        raise HTTPException(
            status_code=500,
            detail="API key chưa được cấu hình."
        )

    try:
        # === BƯỚC 1: Lấy message mới nhất từ người dùng ===
        if not data.messages:
            raise HTTPException(status_code=400, detail="Không có tin nhắn.")

        user_message = data.messages[-1].get("content", "")  # Message cuối cùng
        if not user_message.strip():
            raise HTTPException(status_code=400, detail="Tin nhắn trống.")

        # === BƯỚC 2: DIALECT NORMALIZATION + XƯNG HÔ ===
        # Lấy tin nhắn đầu tiên để phát hiện xưng hô (follow-up có thể không có từ xưng hô)
        first_user_raw = ""
        for msg in data.messages:
            if msg.get("role") == "user":
                first_user_raw = msg.get("content", "")
                break
        
        # Phát hiện vùng miền và xưng hô từ tin nhắn đầu tiên
        detected_region = detect_region(first_user_raw or user_message)
        user_term, self_term = detect_xung_ho(first_user_raw or user_message)

        # Chuẩn hóa từ địa phương về phổ thông (cho RAG)
        normalized_message = normalize_dialect(user_message)

        print(f"[CHAT] Region: {detected_region}")
        print(f"[CHAT] Original: {user_message[:100]}...")
        print(f"[CHAT] Normalized: {normalized_message[:100]}...")
        print(f"[CHAT] Xưng hô: gọi user là '{user_term}', AI xưng '{self_term}'")

        # === BƯỚC 3: RAG RETRIEVAL ===
        # Xây dựng query cho RAG: dùng câu hỏi gốc + tin nhắn mới nhất
        # để context luôn liên quan đến chủ đề chính
        first_user_norm = normalize_dialect(first_user_raw) if first_user_raw else ""
        # Nếu là follow-up (có lịch sử hội thoại), chỉ dùng câu hỏi đầu tiên để RAG
        # để context không bị lệch sang chủ đề khác
        has_history = any(msg.get("role") == "assistant" for msg in data.messages)
        if has_history and first_user_norm:
            rag_query = first_user_norm
        elif first_user_norm and first_user_norm != normalized_message:
            rag_query = first_user_norm + " " + normalized_message
        else:
            rag_query = normalized_message
        
        relevant_chunks, context_string = rag_engine.retrieve(
            query=rag_query,
            top_k=1,
            min_score=0.05
        )

        if len(context_string) > 2000:
            context_string = context_string[:2000] + "..."

        print(f"[CHAT] RAG retrieved: {len(relevant_chunks)} chunks")

        # === BƯỚC 4: BUILD PROMPT ===
        # Tạo message chứa RAG context để gửi kèm câu hỏi người dùng
        region_hint = {
            "north": "người dùng nói giọng miền Bắc",
            "central": "người dùng nói giọng miền Trung",
            "south": "người dùng nói giọng miền Nam",
            "unknown": "không xác định được vùng miền",
        }.get(detected_region, "không xác định được vùng miền")
        
        # Loại bỏ từ xưng hô đầu câu khỏi nội dung (vd: "Mạ ơi, ..." → "...")
        # để AI không bị nhiễu bởi từ ngữ trong câu hỏi
        greeting_pattern = rf"^(({XUNG_HO_TERMS})|con|cháu)\s*ơi\s*[,;:.]?\s*"
        # Dùng user_message gốc (giữ nguyên từ địa phương) để AI thấy cách xưng hô tự nhiên
        llm_message = re.sub(greeting_pattern, "", user_message, count=1, flags=re.IGNORECASE).strip()
        # Nếu trong nội dung có "mẹ" (từ chuẩn hóa) mà user_term là từ địa phương,
        # thay thế để xưng hô nhất quán với từ gốc
        if user_term in ("mạ", "má", "u", "bầm"):
            llm_message = llm_message.replace("mẹ", user_term)
        elif user_term in ("ba", "bố", "thầy", "tía", "cha"):
            llm_message = llm_message.replace("bố", user_term)

        print(f"[CHAT] LLM Message (stripped): {llm_message[:100]}...")

        # Kiểm tra nếu người dùng kết thúc hội thoại (chỉ cảm ơn, không hỏi thêm)
        # Biến này được dùng để quyết định nội dung followup_note và bỏ qua LLM
        is_ending = False
        if has_history:
            has_question = any(w in llm_message.lower() for w in ["?", "gì", "sao", "đâu", "nào", "hỏi", "cho hỏi", "hỏi thêm", "nhờ", "làm"])
            is_ending = (
                any(w in llm_message.lower() for w in ["cảm ơn", "cám ơn", "hiểu rồi", "rõ rồi"]) and not has_question
            )
            if not is_ending:
                stripped = llm_message.strip().lower().rstrip(".,! ")
                if stripped in ["ừ", "ừ ạ", "vâng", "vâng ạ", "dạ", "dạ ạ", "ok", "okay", "ồ"] and not has_question:
                    is_ending = True

        # Thêm ghi chú nếu là follow-up: chuyển sang chế độ hội thoại tự do
        followup_note = ""
        if has_history:
            turn_count = sum(1 for m in data.messages if m.get("role") == "assistant") + 1
            if is_ending:
                followup_note = f"[LƯỢT {turn_count} - KẾT THÚC] Người dùng đã xác nhận hiểu rõ. Chào kết thúc, 1-2 câu.\n"
            elif any(w in llm_message.lower() for w in ["bận", "đi làm", "xa", "tội", "không có ai", "một mình", "ở nhà một mình"]):
                suggestions = [
                    "Có thể gợi ý: nhờ hàng xóm tin cậy, gọi 156.",
                    "Có thể gợi ý: gọi tổng đài 156 chống lừa đảo.",
                    "Có thể gợi ý: nhờ hàng xóm hoặc người quen gần nhà.",
                ]
                s = suggestions[turn_count % len(suggestions)]
                followup_note = f"[LƯỢT {turn_count} - HỘI THOẠI TỰ DO] Trả lời tự nhiên, không theo cấu trúc lượt 1. Không cần chào hỏi hay gọi tên đầu câu. {s} Trả lời ngắn.\n"
            else:
                followup_note = f"[LƯỢT {turn_count} - HỘI THOẠI TỰ DO] Trả lời tự nhiên, không theo cấu trúc lượt 1. Không cần chào hỏi hay gọi tên đầu câu. Vào thẳng vấn đề, 1-2 câu.\n"

        if has_history:
            # Follow-up: bỏ qua RAG context, chỉ dùng hội thoại tự do
            rag_system_message = f"""
{followup_note}
Tin nhắn người dùng: {llm_message}

--- XƯNG HÔ ---
Người dùng: "{user_term}"
Bạn: "{self_term}"
"""
        else:
            rag_system_message = f"""
--- KHO DỮ LIỆU TRA CỨU ---
{context_string if context_string else "Không có dữ liệu phù hợp."}
-----------------------------

Câu hỏi của người dùng: {llm_message}
Ghi chú: {region_hint}
{followup_note}

⚠️ QUY TẮC VÀNG (BẮT BUỘC):
Người thân trong gia đình (con, cháu, cháu nội, cháu ngoại, em, anh, chị) nhờ chuyển tiền là việc thường ngày. KHÔNG kết luận lừa đảo chỉ vì người thân nhờ chuyển tiền. Nếu không có dấu hiệu bất thường nào khác (số lạ, giọng lạ, gấp gáp bất thường, yêu cầu giữ bí mật), hãy trả lời bình thường. Nếu người dùng kể có dấu hiệu đáng ngờ (số lạ, giọng không giống, yêu cầu giữ bí mật), thì mới cân nhắc hỏi lại để xác nhận.

--- XƯNG HÔ (BẮT BUỘC TUÂN THEO) ---
Người dùng đã dùng từ xưng hô này với bạn, hãy đáp lại:
- Gọi người dùng là: "{user_term}"
- Tự xưng (AI): "{self_term}"
Ví dụ: nếu gọi người dùng là "mạ", xưng "con" thì nói "Dạ mạ ơi...". Nếu là "u" - "con" thì "Dạ u ơi...". Nếu là "bác" - "cháu" thì "Dạ bác ơi...". Nếu là "ông/bà" - "cháu" thì "Dạ ông/bà ơi...". KHÔNG dùng "cháu thấy" trong câu trả lời, chỉ nói trực tiếp nội dung cần nói.
----------------------------------

Hướng dẫn:
- Trả lời dựa trên thông tin người dùng cung cấp. Dùng dữ liệu TRA CỨU nếu nó khớp với tình huống của người dùng.
- TUYỆT ĐỐI KHÔNG tự thêm tên người, chức vụ, cơ quan, số tài khoản, số tiền.
- QUAN TRỌNG: Chỉ dùng dữ liệu TRA CỨU nếu nó mô tả ĐÚNG tình huống người dùng gặp phải.
- Nếu dữ liệu TRA CỨU không liên quan (kể chuyện khác với người dùng), chỉ dùng thông tin từ câu hỏi của người dùng.
- Nếu người dùng nói về người thân nhờ chuyển tiền, dữ liệu TRA CỨU KHÔNG liên quan, bỏ qua nó.
- Không lặp lại câu hỏi, chỉ trả lời ngắn gọn.
- TUYỆT ĐỐI KHÔNG phân tích cuộc hội thoại. Không nói "cháu thấy đây là...", "cháu nhận thấy...".
- KHÔNG nhắc đến "chuyển tiền", "lừa đảo" hay khái niệm lừa đảo nào nếu người dùng không nhắc đến trước.
"""
        # Xây dựng message history (giữ nguyên lịch sử chat)
        processed_messages = data.messages.copy()

        # Thay thế message cuối cùng bằng message đã normalize + RAG context
        processed_messages[-1]["content"] = rag_system_message

        # Build payload cho Groq (System Prompt đứng đầu)
        groq_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        groq_messages.extend(processed_messages)

        # Nếu người dùng kết thúc hội thoại, trả về lời chào trực tiếp (bỏ qua LLM)
        if is_ending:
            ending_responses = [
                f"Dạ {user_term} ơi, không có gì ạ. Chúc {user_term} luôn mạnh khỏe và bình an!",
                f"Dạ vâng ạ. Chúc {user_term} luôn bình an và tỉnh táo để tránh bị lừa nhé ạ!",
            ]
            bot_response = ending_responses[0]
            print(f"[CHAT] Ending conversation, response: {bot_response}")
            return {
                "status": "success",
                "bot_response": bot_response,
                "debug": {
                    "user_term": user_term,
                    "self_term": self_term,
                    "region": detected_region,
                    "xung_ho": f"user={user_term}, ai={self_term}",
                    "rag_chunks": len(relevant_chunks),
                }
            }

        # === BƯỚC 5: CALL LLM (GROQ → FALLBACK → DEGRADED) ===
        bot_response = _call_groq_with_retry(groq_messages)
        if bot_response is None:
            print("[LLM] Groq failed, trying OpenRouter fallback...")
            bot_response = _call_openrouter_fallback(groq_messages)
        if bot_response is None:
            print("[LLM] All APIs failed, using degraded response")
            raise HTTPException(
                status_code=503,
                detail=f"Dạ hệ thống đang quá tải, {user_term} vui lòng thử lại sau nhé ạ!"
            )

        # === BƯỚC 6: HALLUCINATION VALIDATION ===
        if relevant_chunks:
            # Kiểm tra response có dựa trên context RAG không
            is_safe, validated_response, grounding_score = hallucination_guard.validate(
                context=context_string,
                response=bot_response,
                user_query=normalized_message
            )

            print(f"[CHAT] Grounding score: {grounding_score:.2f}")

            if not is_safe:
                # Hallucination detected - sử dụng fallback response an toàn
                print(f"[HALLUCINATION] Detected! Score: {grounding_score:.2f}")
                print(f"[HALLUCINATION] Original: {bot_response[:100]}...")

                # Fallback responses an toàn (không chứa thông tin sai lệch)
                fallback_responses = [
                    f"Dạ {user_term} ơi, {self_term} đã xem xét câu chuyện của {user_term}. "
                    f"Dựa trên thông tin {user_term} cung cấp, {self_term} thấy có dấu hiệu đáng ngờ. "
                    f"Tốt nhất {user_term} nên trao đổi với người thân trước khi làm theo họ nhé ạ.",

                    f"Dạ {self_term} xin lỗi {user_term}, {self_term} chưa phân tích được tình huống này. "
                    f"{user_term} có thể kể rõ hơn cho {self_term} được không ạ?",
                ]

                if not relevant_chunks:  # Nếu RAG không có dữ liệu liên quan
                    bot_response = fallback_responses[1]
                else:  # Nếu có dữ liệu nhưng response bị hallucination
                    bot_response = fallback_responses[0]
        else:
            # Không có dữ liệu RAG → giữ nguyên response (system prompt đã guard)
            pass

        # === BƯỚC 6.5: FORMAT RESPONSE (ngắt dòng giữa các phần) ===
        bot_response = _insert_line_breaks(bot_response, user_term)

        # === BƯỚC 7: TRẢ RESPONSE VỀ CLIENT ===
        return {
            "status": "success",
            "bot_response": bot_response,
            "debug": {
                "detected_region": detected_region,
                "normalized_message": normalized_message,
                "chunks_found": len(relevant_chunks),
                "xung_ho": {
                    "user_term": user_term,
                    "self_term": self_term,
                },
            }
        }

    except HTTPException:
        raise  # Re-raise HTTP exceptions (không bọc lại)
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Dạ hệ thống của cháu đang bận, ông/bà thử lại sau nhé ạ!"
        )


# ---------- PHỤC VỤ FILE TĨNH ----------
# Mount thư mục templates để phục vụ CSS/JS (nếu có)
if os.path.exists("templates"):
    app.mount("/static", StaticFiles(directory="templates"), name="static")


# ============================================================
# ╔══════════════════════════════════════════════════════════╗
# ║  PHẦN 5: KIỂM TRA (test_improvements.py)               ║
# ║  Mục đích: Chạy kiểm tra toàn bộ module khi gọi        ║
# ║  `python main.py` trực tiếp.                           ║
# ╚══════════════════════════════════════════════════════════╝
# ============================================================

def run_tests():
    """
    Hàm kiểm tra toàn bộ hệ thống.
    Chạy khi gọi `python main.py` trực tiếp (không qua uvicorn).
    """
    print("=" * 70)
    print("TESTING ALL MODULES")
    print("=" * 70)

    # ---------- TEST 1: DIALECT MAP ----------
    print("\n" + "=" * 70)
    print("📝 TEST 1: DIALECT MAP")
    print("=" * 70)

    try:
        test_cases = [
            # (input_text, expected_region)
            ("Mô răng rứa?", "central"),
            ("Chi rứa? Đi mô đó?", "central"),
            ("Mạ ơi, nhà mô đây?", "central"),
            ("Má ơi, hổng có gì đâu", "south"),
            ("Ổng nói vậy đó, tui hổng biết", "south"),
            ("Mẹ ơi, bát cơm đây ạ", "north"),
            ("Tôi thấy cái bát này bự quá", "north"),
        ]

        for text, expected_region in test_cases:
            region = detect_region(text)
            normalized = normalize_dialect(text)
            status = "✅" if region == expected_region else "⚠"
            print(f"\n{status} Gốc: {text}")
            print(f"   Vùng: {region} (expected: {expected_region})")
            print(f"   Chuẩn: {normalized}")

        print("\n✅ Dialect Map: OK")
    except Exception as e:
        print(f"❌ Dialect Map Error: {e}")

    # ---------- TEST 2: RAG ENGINE ----------
    print("\n" + "=" * 70)
    print("📚 TEST 2: RAG ENGINE")
    print("=" * 70)

    try:
        test_engine = RAGEngine()
        stats = test_engine.get_statistics()

        print(f"\n📊 Thống kê:")
        print(f"   Total chunks: {stats['total_chunks']}")
        for ftype, count in stats['fraud_types'].items():
            print(f"   - {ftype}: {count}")

        test_queries = [
            "Có người yêu cầu tôi chuyển tiền đặt cọc nhà hàng",
            "Họ bảo tôi cung cấp mã OTP",
            "Tôi muốn hỏi về thời tiết hôm nay",  # Không liên quan
        ]

        for q in test_queries:
            chunks, ctx = test_engine.retrieve(q, top_k=2)
            print(f"\n🔍 '{q[:50]}...'")
            print(f"   Relevant chunks: {len(chunks)}")
            if chunks:
                print(f"   Context length: {len(ctx)} chars")

        print("\n✅ RAG Engine: OK")
    except Exception as e:
        print(f"❌ RAG Engine Error: {e}")

    # ---------- TEST 3: HALLUCINATION GUARD ----------
    print("\n" + "=" * 70)
    print("🛡️  TEST 3: HALLUCINATION GUARD")
    print("=" * 70)

    try:
        test_guard = HallucinationGuard(threshold=0.25)

        context = """
        [KỊCH BẢN - Lừa đảo đặt bàn ăn]
        [người gọi]: Em là Minh, chị chuyển tiền cọc 2 triệu rưỡi vào tài khoản cá nhân em nhé.
        [người nhận]: Ừ, để tôi chuyển.
        """

        test_responses = [
            # An toàn: dựa trên context
            "Dạ ông/bà ơi, đây có dấu hiệu lừa đảo. Họ yêu cầu chuyển tiền cọc vào tài khoản cá nhân.",
            # Hallucination: số tiền và chi tiết không có trong context
            "Dạ ông/bà ơi, đây là lừa đảo. Họ yêu cầu chuyển 15 triệu và cung cấp mã OTP từ Vietcombank.",
            # An toàn: không kết luận
            "Dạ ông/bà kể cháu nghe rõ hơn nhé, cháu chưa đủ thông tin để kết luận ạ.",
        ]

        for i, resp in enumerate(test_responses):
            is_safe, final, score = test_guard.validate(context, resp, "test query")
            status = "✅" if is_safe else "❌ HALLUCINATION"
            print(f"\n{status} Response {i+1}: {resp[:60]}...")
            print(f"   Grounding score: {score:.2f}")

        print("\n✅ Hallucination Guard: OK")
    except Exception as e:
        print(f"❌ Hallucination Guard Error: {e}")

    # ---------- KẾT THÚC ----------
    print("\n" + "=" * 70)
    print("🏁 ALL TESTS COMPLETE")
    print("=" * 70)


# ============================================================
# ╔══════════════════════════════════════════════════════════╗
# ║  MAIN ENTRY POINT                                       ║
# ║  - Chạy `python main.py` → chạy test                   ║
# ║  - Chạy `uvicorn main:app --reload` → chạy server      ║
# ╚══════════════════════════════════════════════════════════╝
# ============================================================
if __name__ == "__main__":
    """
    Khi chạy trực tiếp: python main.py
      → Chạy test toàn bộ module (không cần API key)
    
    Khi chạy qua uvicorn: uvicorn main:app --reload
      → Chạy FastAPI server
    """
    import uvicorn

    print("=" * 60)
    print("ANTI-SCAM CHATBOT - IMPROVED VERSION")
    print("=" * 60)

    # Hiển thị thông tin hệ thống
    print("\n📊 System Status:")
    stats = rag_engine.get_statistics()
    print(f"   RAG: {stats['total_chunks']} chunks loaded")
    if stats['fraud_types']:
        for ftype, count in stats['fraud_types'].items():
            print(f"     - {ftype}: {count}")
    print(f"   Model: Groq (llama-3.1-8b-instant)")
    print(f"   Hallucination Guard: Active (threshold=0.2)")
    print(f"   Dialect Normalization: Active")
    print(f"\n🚀 Server running at: http://localhost:8000")
    print("=" * 60)

    # Chạy server
    uvicorn.run(app, host="0.0.0.0", port=8000)
