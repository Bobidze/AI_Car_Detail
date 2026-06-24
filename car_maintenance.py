"""
АвтоСервис — Рекомендации по техническому обслуживанию автомобиля
Настольное приложение на Python + tkinter + DeepSeek AI
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import tkinter.font as tkfont
from datetime import datetime
import threading
import urllib.request
import urllib.error
import json
import os

# ============================================================
# КОНФИГУРАЦИЯ (сохранение API ключа)
# ============================================================

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

def load_config() -> dict:
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def save_config(cfg: dict):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# ============================================================
# КОНСТАНТЫ
# ============================================================

CURRENT_YEAR = datetime.now().year

COLORS = {
    "bg_main":      "#F0F4F8",
    "bg_card":      "#FFFFFF",
    "bg_input":     "#F8FAFC",
    "accent":       "#2563EB",
    "accent_hover": "#1D4ED8",
    "purple":       "#7C3AED",
    "purple_hover": "#6D28D9",
    "green":        "#059669",
    "green_hover":  "#047857",
    "high_bg":      "#FEE2E2",
    "high_border":  "#EF4444",
    "high_text":    "#B91C1C",
    "med_bg":       "#FFF7ED",
    "med_border":   "#F97316",
    "med_text":     "#C2410C",
    "low_bg":       "#EFF6FF",
    "low_border":   "#3B82F6",
    "low_text":     "#1D4ED8",
    "text_primary": "#1E293B",
    "text_sec":     "#64748B",
    "text_muted":   "#94A3B8",
    "border":       "#E2E8F0",
    "header_bg":    "#1E293B",
    "header_text":  "#FFFFFF",
    "success":      "#059669",
    "warn_bg":      "#FFFBEB",
    "warn_text":    "#92400E",
    "ai_bg":        "#F0FDF4",
    "ai_border":    "#10B981",
    "ai_header":    "#065F46",
    "ai_text_bg":   "#F8FFFE",
}

ENGINE_TYPES = ["Бензин", "Дизель", "Гибрид", "Электро"]
DEEPSEEK_URL  = "https://api.deepseek.com/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"

# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def fmt(n: int) -> str:
    return f"{n:,}".replace(",", " ")

def brand_category(bm: str) -> str:
    b = bm.lower().split()[0] if bm.strip() else ""
    if any(x in b for x in ["toyota","honda","mazda","subaru","mitsubishi","nissan","lexus","infiniti"]):
        return "japanese"
    if any(x in b for x in ["vw","volkswagen","audi","skoda","bmw","mercedes","opel","porsche"]):
        return "german"
    if any(x in b for x in ["lada","ваз","газ","уаз"]):
        return "russian"
    if any(x in b for x in ["renault","peugeot","citroen","dacia"]):
        return "french"
    if any(x in b for x in ["kia","hyundai","genesis"]):
        return "korean"
    return "other"

def has_chain(bm: str) -> bool:
    b = bm.lower()
    return any(x in b for x in ["bmw","mercedes","benz"])

# ============================================================
# ЛОГИКА РЕКОМЕНДАЦИЙ
# ============================================================

def generate_recommendations(brand, year, engine, total_km):
    age  = CURRENT_YEAR - year
    km   = total_km
    cat  = brand_category(brand)
    diesel = (engine == "Дизель")
    chain  = has_chain(brand)
    recs   = []

    # 1. Моторное масло
    oil_int = 15000 if cat == "german" else (8000 if diesel else 10000)
    last_oil = km % oil_int if oil_int else 0
    r = last_oil / oil_int
    recs.append({"priority": "high" if r > .90 else ("medium" if r > .70 else "low"),
                 "name": "Моторное масло + масляный фильтр",
                 "interval": f"Каждые {fmt(oil_int)} км или 1 год",
                 "status": "ЗАМЕНИТЬ СРОЧНО" if r > .90 else ("ЗАМЕНИТЬ" if r > .70 else "РЕГУЛЯРНО МЕНЯТЬ"),
                 "reason": f"~{fmt(last_oil)} км от расч. последней замены (интервал {fmt(oil_int)} км)."})

    # 2. Воздушный фильтр
    af = 10000 if cat == "russian" else 15000
    r  = (km % af) / af if af else 0
    recs.append({"priority": "medium" if r > .80 else "low",
                 "name": "Воздушный фильтр",
                 "interval": f"Каждые {fmt(af)} км или 1 год",
                 "status": "ЗАМЕНИТЬ" if r > .80 else "ПРОВЕРИТЬ",
                 "reason": f"Расч. пробег от замены: ~{fmt(int(km % af))} км. Загрязнённый фильтр = перерасход топлива."})

    # 3. Салонный фильтр
    cf = 15000
    r  = (km % cf) / cf if cf else 0
    recs.append({"priority": "medium" if r > .80 or age >= 1 else "low",
                 "name": "Салонный фильтр",
                 "interval": "Каждые 15 000 км или 1 год",
                 "status": "ЗАМЕНИТЬ" if r > .80 else "ПРОВЕРИТЬ",
                 "reason": "Влияет на качество воздуха в салоне и КПД климатики."})

    # 4. Свечи
    if not diesel:
        si = {"german": 60000, "japanese": 40000}.get(cat, 30000)
        r  = (km % si) / si if si else 0
        recs.append({"priority": "high" if r > .90 else ("medium" if r > .70 else "low"),
                     "name": "Свечи зажигания",
                     "interval": f"Каждые {fmt(si)} км",
                     "status": "ЗАМЕНИТЬ" if r > .70 else "ПРОВЕРИТЬ ЗАЗОР",
                     "reason": f"Расч. пробег: ~{fmt(int(km % si))} км. Изношенные свечи — нестабильный ХХ, перерасход."})
    else:
        r = (km % 80000) / 80000 if km else 0
        recs.append({"priority": "medium" if r > .80 or age > 5 else "low",
                     "name": "Свечи накаливания (дизель)",
                     "interval": "Каждые 80 000 км / 5–7 лет",
                     "status": "ПРОВЕРИТЬ / ЗАМЕНИТЬ" if r > .80 else "ПРОВЕРИТЬ",
                     "reason": "Критичны для холодного запуска дизеля."})

    # 5. ГРМ
    if chain:
        recs.append({"priority": "high" if (km > 120000 or age > 10) else ("medium" if km > 80000 else "low"),
                     "name": "Цепь ГРМ + натяжители",
                     "interval": "Диагностика каждые 60 000 км",
                     "status": "ДИАГНОСТИКА ОБЯЗАТЕЛЬНА" if age > 8 else "ПРОСЛУШАТЬ",
                     "reason": "Стук при запуске = признак износа. Обрыв → капитальный ремонт."})
    else:
        bk  = {"german": 90000, "japanese": 90000, "korean": 80000}.get(cat, 60000)
        by_ = {"german": 6,     "japanese": 7,      "korean": 6    }.get(cat, 5)
        r   = max((km % bk) / bk, (age % by_) / by_) if (bk and by_) else 0
        recs.append({"priority": "high" if r > .90 else ("medium" if r > .65 else "low"),
                     "name": "Ремень ГРМ + ролики + помпа",
                     "interval": f"Каждые {fmt(bk)} км или {by_} лет",
                     "status": "СРОЧНО ЗАМЕНИТЬ" if r > .90 else ("ЗАМЕНИТЬ СКОРО" if r > .65 else "ПЛАНОВАЯ ЗАМЕНА"),
                     "reason": f"КРИТИЧНО: обрыв ремня = капремонт двигателя. Ресурс использован ~{int(r*100)}%."})

    # 6. Приводной ремень
    db = {"german": 80000}.get(cat, 60000)
    r  = (km % db) / db if db else 0
    recs.append({"priority": "high" if r > .90 else ("medium" if r > .70 or age > 7 else "low"),
                 "name": "Приводной ремень + натяжной ролик",
                 "interval": f"Каждые {fmt(db)} км / 5–7 лет",
                 "status": "ЗАМЕНИТЬ" if r > .70 else "ОСМОТРЕТЬ НА ТРЕЩИНЫ",
                 "reason": "Обрыв → нет зарядки АКБ, нет кондиционера/ГУР."})

    # 7. Антифриз
    ck = 100000 if cat in ("japanese","german") else 60000
    cy = 5 if cat in ("japanese","german") else 2
    r  = max((km % ck) / ck, (age % cy) / cy) if (ck and cy) else 0
    recs.append({"priority": "medium" if r > .80 else "low",
                 "name": "Охлаждающая жидкость (антифриз)",
                 "interval": f"Каждые {fmt(ck)} км / {cy} года",
                 "status": "ЗАМЕНИТЬ" if r > .80 else "ПРОВЕРИТЬ УРОВЕНЬ",
                 "reason": "Деградация → коррозия радиатора и блока. Признак: коричневый цвет."})

    # 8. Тормозная жидкость
    r = (age % 2) / 2 if age > 0 else 0
    recs.append({"priority": "high" if r > .90 else ("medium" if r > .70 else "low"),
                 "name": "Тормозная жидкость",
                 "interval": "Каждые 2 года / 40 000 км",
                 "status": "ЗАМЕНИТЬ" if r > .70 else "ПРОВЕРИТЬ",
                 "reason": "Гигроскопична — увлажнение снижает т° кипения. Риск отказа тормозов."})

    # 9. Тормозные колодки
    fp = 35000
    r  = (km % fp) / fp if fp else 0
    recs.append({"priority": "high" if r > .85 else ("medium" if r > .65 else "low"),
                 "name": "Тормозные колодки (перед. / зад.)",
                 "interval": f"Передние ~{fmt(fp)} км, задние ~60 000 км",
                 "status": "ЗАМЕНИТЬ" if r > .85 else ("ИЗМЕРИТЬ ТОЛЩИНУ" if r > .65 else "ПРОВЕРИТЬ"),
                 "reason": f"Расч. износ передних: ~{int(r*100)}%. Минимум: 3 мм. Скрип = замена немедленно."})

    # 10. Тормозные диски
    r = (km % 120000) / 120000 if km else 0
    recs.append({"priority": "medium" if r > .85 or age > 8 else "low",
                 "name": "Тормозные диски",
                 "interval": "80 000–150 000 км",
                 "status": "ПРОВЕРИТЬ ТОЛЩИНУ" if r > .70 else "ОСМОТРЕТЬ",
                 "reason": "Мин. толщина выбита на диске. Борозды и биение — признаки износа."})

    # 11. АКБ
    bl = 3 if cat == "russian" else 4
    r  = age / bl if bl else 0
    if age >= 2:
        recs.append({"priority": "high" if r >= 1.1 else ("medium" if r >= 0.80 else "low"),
                     "name": "Аккумуляторная батарея",
                     "interval": f"Средний ресурс: {bl}–5 лет",
                     "status": "ДИАГНОСТИКА / ЗАМЕНИТЬ" if r >= 1.1 else ("ПРОВЕРИТЬ ТОК ХП" if r >= .80 else "МОНИТОРИНГ"),
                     "reason": f"Расч. возраст: ~{age} лет. Проверить ток хол. пуска, особенно перед зимой."})

    # 12. Шины
    if age >= 7:
        recs.append({"priority": "high", "name": "Шины",
                     "interval": "Замена каждые 5–7 лет", "status": "ЗАМЕНИТЬ",
                     "reason": f"Расч. возраст ~{age} лет. Резина трескается — проверить DOT-маркировку."})
    elif age >= 4:
        recs.append({"priority": "medium", "name": "Шины",
                     "interval": "Замена каждые 5–7 лет", "status": "ПРОВЕРИТЬ СОСТОЯНИЕ",
                     "reason": f"Возраст ~{age} лет. Осмотр боковин. Протектор: мин. 1.6 мм (реком. 3 мм)."})
    else:
        recs.append({"priority": "low", "name": "Шины",
                     "interval": "Замена каждые 5–7 лет", "status": "ПЛАНОВЫЙ ОСМОТР",
                     "reason": "Давление ежемесячно. Ротация каждые 10 000–15 000 км."})

    # 13. АКПП
    if km > 40000:
        r = (km % 60000) / 60000
        recs.append({"priority": "medium" if r > .80 or age > 6 else "low",
                     "name": "Масло АКПП / вариатора (при наличии)",
                     "interval": "Каждые 40 000–60 000 км",
                     "status": "ЗАМЕНИТЬ" if r > .80 else "УТОЧНИТЬ У МАСТЕРА",
                     "reason": "«Залито навсегда» — миф. Замена масла дешевле ремонта АКПП в 15–20 раз."})

    order = {"high": 0, "medium": 1, "low": 2}
    recs.sort(key=lambda x: order.get(x["priority"], 9))
    return recs

# ============================================================
# DEEPSEEK AI КЛИЕНТ
# ============================================================

def deepseek_stream(api_key: str, prompt: str):
    """
    Генератор: отдаёт чанки текста из DeepSeek streaming API.
    Вызывать в отдельном потоке.
    """
    payload = json.dumps({
        "model": DEEPSEEK_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": True,
        "temperature": 0.7,
        "max_tokens": 3000,
    }).encode("utf-8")

    req = urllib.request.Request(
        DEEPSEEK_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=60) as resp:
        for raw_line in resp:
            line = raw_line.decode("utf-8").strip()
            if not line.startswith("data:"):
                continue
            body = line[5:].strip()
            if body == "[DONE]":
                return
            try:
                delta = json.loads(body)["choices"][0]["delta"]
                chunk = delta.get("content", "")
                if chunk:
                    yield chunk
            except (KeyError, json.JSONDecodeError):
                pass

def build_ai_prompt(brand, year, engine, avg_km, total_km):
    age = CURRENT_YEAR - year
    return (
        f"Ты — опытный автомеханик с 20-летним стажем. Дай детальные рекомендации по ТО.\n\n"
        f"**Автомобиль:** {brand}, {year} г. ({age} лет), {engine}\n"
        f"**Пробег:** {fmt(total_km)} км (ср. {fmt(avg_km)} км/год)\n\n"
        f"Проанализируй и дай рекомендации по каждому пункту:\n"
        f"1. ГРМ (ремень/цепь) — статус и когда менять\n"
        f"2. Моторное масло — марка, вязкость, интервал\n"
        f"3. Охлаждающая жидкость\n"
        f"4. Тормозная система (колодки, диски, жидкость)\n"
        f"5. Свечи {'накаливания' if engine=='Дизель' else 'зажигания'}\n"
        f"6. Аккумулятор\n"
        f"7. Подвеска и рулевое — типичные слабые места модели\n"
        f"8. Приводные ремни\n"
        f"9. Шины\n"
        f"10. АКПП/МКПП\n"
        f"11. Топливная система\n\n"
        f"**Для каждого пункта укажи:**\n"
        f"- Статус: [СРОЧНО] / [СКОРО] / [ПЛАНОВОЕ] / [OK]\n"
        f"- Конкретный интервал для данной модели\n"
        f"- Типичные проблемы {brand}\n"
        f"- Ориентировочная стоимость (запчасть + работа, руб., средний регион РФ)\n\n"
        f"В конце: **итоговая сумма** для приведения авто в порядок."
    )

# ============================================================
# ГЛАВНЫЙ КЛАСС ПРИЛОЖЕНИЯ
# ============================================================

class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("АвтоСервис — ТО + DeepSeek AI")
        self.root.geometry("980x820")
        self.root.minsize(840, 640)
        self.root.configure(bg=COLORS["bg_main"])
        self._cfg = load_config()
        self._ai_thread: threading.Thread | None = None
        self._ai_stop = threading.Event()
        self._dpi_fix()
        self._init_fonts()
        self._build_ui()

    def _dpi_fix(self):
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

    def _init_fonts(self):
        self.F = {
            "h1":    tkfont.Font(family="Segoe UI", size=20, weight="bold"),
            "h2":    tkfont.Font(family="Segoe UI", size=13, weight="bold"),
            "lbl":   tkfont.Font(family="Segoe UI", size=11),
            "lblb":  tkfont.Font(family="Segoe UI", size=11, weight="bold"),
            "small": tkfont.Font(family="Segoe UI", size=9),
            "btn":   tkfont.Font(family="Segoe UI", size=12, weight="bold"),
            "ct":    tkfont.Font(family="Segoe UI", size=11, weight="bold"),
            "cb":    tkfont.Font(family="Segoe UI", size=10),
            "badge": tkfont.Font(family="Segoe UI", size=9,  weight="bold"),
            "mono":  tkfont.Font(family="Consolas",  size=10),
        }

    # ------------------------------------------------------------------
    # ПОСТРОЕНИЕ UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        self._build_header()
        body = tk.Frame(self.root, bg=COLORS["bg_main"])
        body.pack(fill="both", expand=True)
        self._build_input(body)
        self._build_api_row(body)
        self._build_results(body)

    def _build_header(self):
        hdr = tk.Frame(self.root, bg=COLORS["header_bg"], height=64)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        inner = tk.Frame(hdr, bg=COLORS["header_bg"])
        inner.pack(fill="both", expand=True, padx=24)
        tk.Label(inner, text="АвтоСервис", font=self.F["h1"],
                 bg=COLORS["header_bg"], fg=COLORS["header_text"]).pack(side="left", pady=14)
        tk.Label(inner, text="  Рекомендации по ТО  +  DeepSeek AI",
                 font=self.F["lbl"], bg=COLORS["header_bg"], fg="#94A3B8").pack(side="left", pady=(20,14))

    def _build_input(self, parent):
        card = tk.Frame(parent, bg=COLORS["bg_card"])
        card.pack(fill="x", padx=16, pady=(12, 0))
        tk.Frame(parent, bg="#CBD5E1", height=2).pack(fill="x", padx=18, pady=(0, 0))

        inp = tk.Frame(card, bg=COLORS["bg_card"])
        inp.pack(fill="x", padx=20, pady=16)

        tk.Label(inp, text="Данные автомобиля", font=self.F["h2"],
                 bg=COLORS["bg_card"], fg=COLORS["text_primary"]).pack(anchor="w", pady=(0,10))

        # Строка 1
        r1 = tk.Frame(inp, bg=COLORS["bg_card"])
        r1.pack(fill="x", pady=(0,8))

        bf = tk.Frame(r1, bg=COLORS["bg_card"])
        bf.pack(side="left", fill="x", expand=True, padx=(0,10))
        tk.Label(bf, text="Марка и модель *", font=self.F["lblb"],
                 bg=COLORS["bg_card"], fg=COLORS["text_primary"]).pack(anchor="w")
        self.v_brand = tk.StringVar()
        self._entry(bf, self.v_brand).pack(fill="x", ipady=7, pady=(3,0))
        tk.Label(bf, text="Пример: Toyota Camry, Lada Vesta, VW Passat",
                 font=self.F["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(anchor="w")

        yf = tk.Frame(r1, bg=COLORS["bg_card"])
        yf.pack(side="left", padx=(0,10))
        tk.Label(yf, text="Год выпуска *", font=self.F["lblb"],
                 bg=COLORS["bg_card"], fg=COLORS["text_primary"]).pack(anchor="w")
        self.v_year = tk.StringVar()
        self._entry(yf, self.v_year, w=10).pack(fill="x", ipady=7, pady=(3,0))
        tk.Label(yf, text=f"1990–{CURRENT_YEAR}",
                 font=self.F["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(anchor="w")

        ef = tk.Frame(r1, bg=COLORS["bg_card"])
        ef.pack(side="left")
        tk.Label(ef, text="Тип двигателя *", font=self.F["lblb"],
                 bg=COLORS["bg_card"], fg=COLORS["text_primary"]).pack(anchor="w")
        self.v_engine = tk.StringVar(value="Бензин")
        ttk.Combobox(ef, textvariable=self.v_engine, values=ENGINE_TYPES,
                     state="readonly", font=self.F["lbl"], width=12).pack(pady=(3,0))
        tk.Label(ef, text=" ", font=self.F["small"], bg=COLORS["bg_card"]).pack()

        # Строка 2
        r2 = tk.Frame(inp, bg=COLORS["bg_card"])
        r2.pack(fill="x", pady=(0,8))

        af = tk.Frame(r2, bg=COLORS["bg_card"])
        af.pack(side="left", fill="x", expand=True, padx=(0,10))
        tk.Label(af, text="Среднегодовой пробег (км/год) *", font=self.F["lblb"],
                 bg=COLORS["bg_card"], fg=COLORS["text_primary"]).pack(anchor="w")
        self.v_avg = tk.StringVar()
        self._entry(af, self.v_avg).pack(fill="x", ipady=7, pady=(3,0))
        tk.Label(af, text="Пример: 15000",
                 font=self.F["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(anchor="w")

        cf = tk.Frame(r2, bg=COLORS["bg_card"])
        cf.pack(side="left", fill="x", expand=True)
        tk.Label(cf, text="Текущий пробег по одометру (км)", font=self.F["lblb"],
                 bg=COLORS["bg_card"], fg=COLORS["text_primary"]).pack(anchor="w")
        self.v_cur = tk.StringVar()
        self._entry(cf, self.v_cur).pack(fill="x", ipady=7, pady=(3,0))
        tk.Label(cf, text="Необязательно — рассчитывается автоматически",
                 font=self.F["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(anchor="w")

        # Кнопка
        br = tk.Frame(inp, bg=COLORS["bg_card"])
        br.pack(fill="x", pady=(10,0))
        self.btn_calc = self._btn(br, "  РАССЧИТАТЬ РЕКОМЕНДАЦИИ  ",
                                  COLORS["accent"], COLORS["accent_hover"],
                                  self._on_calc, pad=(20, 10))
        self.btn_calc.pack(side="left")
        self.lbl_status = tk.Label(br, text="", font=self.F["lbl"],
                                   bg=COLORS["bg_card"], fg=COLORS["text_sec"])
        self.lbl_status.pack(side="left", padx=(14,0))

    def _build_api_row(self, parent):
        """Панель настройки DeepSeek API ключа"""
        arow = tk.Frame(parent, bg="#ECFDF5")
        arow.pack(fill="x", padx=16, pady=(6, 0))
        tk.Frame(parent, bg=COLORS["ai_border"], height=2).pack(fill="x", padx=18, pady=(0,0))

        inner = tk.Frame(arow, bg="#ECFDF5")
        inner.pack(fill="x", padx=20, pady=10)

        tk.Label(inner, text="DeepSeek AI", font=self.F["lblb"],
                 bg="#ECFDF5", fg=COLORS["ai_header"]).pack(side="left")

        tk.Label(inner, text="  API ключ:",
                 font=self.F["lbl"], bg="#ECFDF5", fg=COLORS["text_sec"]).pack(side="left")

        self.v_apikey = tk.StringVar(value=self._cfg.get("deepseek_key", ""))
        key_entry = tk.Entry(inner, textvariable=self.v_apikey,
                             font=self.F["lbl"], show="•", width=38,
                             relief="flat", bg=COLORS["bg_input"],
                             fg=COLORS["text_primary"],
                             insertbackground=COLORS["ai_border"],
                             bd=1, highlightthickness=1,
                             highlightcolor=COLORS["ai_border"],
                             highlightbackground=COLORS["border"])
        key_entry.pack(side="left", padx=(6,6), ipady=5)

        # Показать/скрыть ключ
        self._show_key = False
        self.btn_eye = tk.Button(inner, text="👁", font=self.F["lbl"],
                                 bg="#ECFDF5", fg=COLORS["text_sec"],
                                 relief="flat", cursor="hand2", bd=0,
                                 command=lambda: self._toggle_key_vis(key_entry))
        self.btn_eye.pack(side="left", padx=(0,8))

        self._btn(inner, "Сохранить ключ", "#0D9488", "#0F766E",
                  self._save_key, pad=(10,5)).pack(side="left")

        self.lbl_key_status = tk.Label(inner, text="", font=self.F["small"],
                                       bg="#ECFDF5", fg=COLORS["success"])
        self.lbl_key_status.pack(side="left", padx=(8,0))

        # Показать статус если ключ уже сохранён
        if self._cfg.get("deepseek_key"):
            self.lbl_key_status.config(text="✓ Ключ сохранён")

    def _toggle_key_vis(self, entry: tk.Entry):
        self._show_key = not self._show_key
        entry.config(show="" if self._show_key else "•")

    def _save_key(self):
        key = self.v_apikey.get().strip()
        if not key:
            messagebox.showwarning("Внимание", "Введите API ключ DeepSeek")
            return
        if not key.startswith("sk-"):
            messagebox.showwarning("Внимание", "API ключ DeepSeek должен начинаться с sk-")
            return
        self._cfg["deepseek_key"] = key
        save_config(self._cfg)
        self.lbl_key_status.config(text="✓ Ключ сохранён", fg=COLORS["success"])

    def _build_results(self, parent):
        outer = tk.Frame(parent, bg=COLORS["bg_main"])
        outer.pack(fill="both", expand=True, padx=16, pady=(6,12))

        self.canvas = tk.Canvas(outer, bg=COLORS["bg_main"], highlightthickness=0)
        sb = ttk.Scrollbar(outer, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.rf = tk.Frame(self.canvas, bg=COLORS["bg_main"])
        self._cw = self.canvas.create_window((0,0), window=self.rf, anchor="nw")
        self.rf.bind("<Configure>",
                     lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>",
                         lambda e: self.canvas.itemconfig(self._cw, width=e.width))

        # Глобальный скролл: привязка ко всему окну, а не только к canvas
        self.root.bind_all("<MouseWheel>", self._on_mousewheel)
        self._show_placeholder()

    # ------------------------------------------------------------------
    # СКРОЛЛ
    # ------------------------------------------------------------------

    def _on_mousewheel(self, event):
        # Не перехватывать скролл у ScrolledText (AI-ответ) — у него свой
        w = event.widget
        try:
            if isinstance(w, tk.Text) or w.master and isinstance(w.master, scrolledtext.ScrolledText):
                return
        except (AttributeError, tk.TclError):
            pass
        self.canvas.yview_scroll(-int(event.delta / 120), "units")

    # ------------------------------------------------------------------
    # ВСПОМОГАТЕЛЬНЫЕ ВИДЖЕТЫ
    # ------------------------------------------------------------------

    def _entry(self, parent, var, w=None):
        kw = dict(textvariable=var, font=self.F["lbl"], relief="flat",
                  bg=COLORS["bg_input"], fg=COLORS["text_primary"],
                  insertbackground=COLORS["accent"], bd=1,
                  highlightthickness=1, highlightcolor=COLORS["accent"],
                  highlightbackground=COLORS["border"])
        if w:
            kw["width"] = w
        return tk.Entry(parent, **kw)

    def _btn(self, parent, text, bg, hover, cmd, pad=(14,8)):
        b = tk.Button(parent, text=text, font=self.F["btn"],
                      bg=bg, fg="white", relief="flat", cursor="hand2",
                      padx=pad[0], pady=pad[1], command=cmd,
                      activebackground=hover, activeforeground="white")
        b.bind("<Enter>", lambda _: b.config(bg=hover))
        b.bind("<Leave>", lambda _: b.config(bg=bg))
        return b

    # ------------------------------------------------------------------
    # ПЛЕЙСХОЛДЕР
    # ------------------------------------------------------------------

    def _show_placeholder(self):
        for w in self.rf.winfo_children():
            w.destroy()
        ph = tk.Frame(self.rf, bg=COLORS["bg_main"])
        ph.pack(expand=True, pady=50)
        tk.Label(ph, text="🚗", font=tkfont.Font(size=52), bg=COLORS["bg_main"]).pack()
        tk.Label(ph, text="Введите данные и нажмите «РАССЧИТАТЬ РЕКОМЕНДАЦИИ»",
                 font=self.F["lbl"], bg=COLORS["bg_main"], fg=COLORS["text_sec"]).pack(pady=(8,0))

    # ------------------------------------------------------------------
    # ВАЛИДАЦИЯ
    # ------------------------------------------------------------------

    def _validate(self):
        brand = self.v_brand.get().strip()
        if not brand:
            return None, "Введите марку и модель автомобиля"
        try:
            year = int(self.v_year.get().strip())
            if not (1990 <= year <= CURRENT_YEAR):
                raise ValueError
        except ValueError:
            return None, f"Год выпуска: от 1990 до {CURRENT_YEAR}"
        try:
            avg = int(self.v_avg.get().strip().replace(" ","").replace(",",""))
            if not (500 <= avg <= 150000):
                raise ValueError
        except ValueError:
            return None, "Среднегодовой пробег: от 500 до 150 000 км"
        cs = self.v_cur.get().strip().replace(" ","").replace(",","")
        if cs:
            try:
                cur = int(cs)
                if not (0 <= cur <= 2000000):
                    raise ValueError
            except ValueError:
                return None, "Пробег по одометру: 0 – 2 000 000 км"
        else:
            cur = (CURRENT_YEAR - year) * avg
        return {"brand": brand, "year": year, "engine": self.v_engine.get(),
                "avg": avg, "cur": cur}, None

    # ------------------------------------------------------------------
    # РАСЧЁТ
    # ------------------------------------------------------------------

    def _on_calc(self):
        data, err = self._validate()
        if err:
            messagebox.showerror("Ошибка ввода", err)
            return
        self.lbl_status.config(text="Анализирую...", fg=COLORS["text_sec"])
        self.root.update_idletasks()
        recs = generate_recommendations(data["brand"], data["year"],
                                        data["engine"], data["cur"])
        self._display(data, recs)
        self.lbl_status.config(text=f"✓ Готово — {len(recs)} рекомендаций", fg=COLORS["success"])

    # ------------------------------------------------------------------
    # ОТОБРАЖЕНИЕ РЕЗУЛЬТАТОВ
    # ------------------------------------------------------------------

    def _display(self, data, recs):
        for w in self.rf.winfo_children():
            w.destroy()

        age = CURRENT_YEAR - data["year"]

        # ── Сводка ──────────────────────────────────────────────────
        sc = tk.Frame(self.rf, bg=COLORS["bg_card"])
        sc.pack(fill="x", pady=(8,4))
        si = tk.Frame(sc, bg=COLORS["bg_card"])
        si.pack(fill="x", padx=20, pady=14)

        tk.Label(si, text=f"{data['brand']}  ·  {data['engine']}",
                 font=self.F["h2"], bg=COLORS["bg_card"], fg=COLORS["text_primary"]).pack(anchor="w", pady=(0,8))

        sr = tk.Frame(si, bg=COLORS["bg_card"])
        sr.pack(anchor="w")
        for lbl, val in [("Возраст", f"{age} лет"), ("Пробег", f"{fmt(data['cur'])} км"),
                          ("Ср. пробег/год", f"{fmt(data['avg'])} км"), ("Год выпуска", str(data["year"]))]:
            sf = tk.Frame(sr, bg="#F1F5F9", padx=12, pady=6)
            sf.pack(side="left", padx=(0,8))
            tk.Label(sf, text=lbl, font=self.F["small"], bg="#F1F5F9", fg=COLORS["text_sec"]).pack()
            tk.Label(sf, text=val, font=self.F["lblb"], bg="#F1F5F9", fg=COLORS["text_primary"]).pack()

        # ── Карточки рекомендаций ────────────────────────────────────
        groups = {"high": [], "medium": [], "low": []}
        for r in recs:
            groups[r["priority"]].append(r)

        cfg_map = {
            "high":   ("🔴  Высокий приоритет — срочное внимание",
                       COLORS["high_bg"], COLORS["high_border"], COLORS["high_text"]),
            "medium": ("🟠  Средний приоритет — плановое обслуживание",
                       COLORS["med_bg"],  COLORS["med_border"],  COLORS["med_text"]),
            "low":    ("🔵  Рутинное обслуживание — регулярный мониторинг",
                       COLORS["low_bg"],  COLORS["low_border"],  COLORS["low_text"]),
        }

        for key in ("high","medium","low"):
            items = groups[key]
            if not items:
                continue
            title, bg, border, tc = cfg_map[key]
            gh = tk.Frame(self.rf, bg=COLORS["bg_main"])
            gh.pack(fill="x", pady=(12,3))
            tk.Label(gh, text=title, font=self.F["h2"],
                     bg=COLORS["bg_main"], fg=tc).pack(anchor="w")
            for rec in items:
                self._rec_card(rec, bg, border)

        # ── Секция AI анализа ────────────────────────────────────────
        self._build_ai_section(data)

        # ── Дисклеймер ───────────────────────────────────────────────
        df = tk.Frame(self.rf, bg=COLORS["warn_bg"])
        df.pack(fill="x", pady=(14,10))
        di = tk.Frame(df, bg=COLORS["warn_bg"])
        di.pack(fill="x", padx=16, pady=10)
        tk.Label(di, text="⚠️  Важное предупреждение", font=self.F["lblb"],
                 bg=COLORS["warn_bg"], fg=COLORS["warn_text"]).pack(anchor="w")
        tk.Label(di,
                 text=("Рекомендации носят справочный характер и основаны на усреднённых данных.\n"
                       "Точные интервалы замены указаны в руководстве по эксплуатации.\n"
                       "Для профессиональной диагностики обратитесь к квалифицированному механику."),
                 font=self.F["cb"], bg=COLORS["warn_bg"], fg="#78350F", justify="left").pack(anchor="w", pady=(4,0))

        self.canvas.yview_moveto(0)

    def _rec_card(self, rec, bg, border):
        outer = tk.Frame(self.rf, bg=border, padx=1, pady=1)
        outer.pack(fill="x", pady=3)
        inner = tk.Frame(outer, bg=bg)
        inner.pack(fill="x")
        ct = tk.Frame(inner, bg=bg)
        ct.pack(fill="x", padx=14, pady=10)
        tr = tk.Frame(ct, bg=bg)
        tr.pack(fill="x")
        tk.Label(tr, text=rec["name"], font=self.F["ct"], bg=bg, fg=COLORS["text_primary"]).pack(side="left")
        tk.Label(tr, text=f"  {rec['status']}  ", font=self.F["badge"],
                 bg=border, fg="white", padx=4, pady=2).pack(side="right")
        tk.Label(ct, text=f"Интервал: {rec['interval']}",
                 font=self.F["cb"], bg=bg, fg=COLORS["text_sec"]).pack(anchor="w", pady=(4,2))
        tk.Label(ct, text=rec["reason"], font=self.F["cb"], bg=bg, fg=COLORS["text_primary"],
                 wraplength=840, justify="left").pack(anchor="w")

    # ------------------------------------------------------------------
    # СЕКЦИЯ DEEPSEEK AI
    # ------------------------------------------------------------------

    def _build_ai_section(self, data: dict):
        """Строит блок «Анализ DeepSeek AI» внутри результатов"""
        ai_card = tk.Frame(self.rf, bg=COLORS["bg_card"])
        ai_card.pack(fill="x", pady=(16, 4))

        # Заголовок с зелёной полосой
        hf = tk.Frame(ai_card, bg=COLORS["ai_border"], height=4)
        hf.pack(fill="x")

        hi = tk.Frame(ai_card, bg=COLORS["bg_card"])
        hi.pack(fill="x", padx=20, pady=(12, 8))

        tk.Label(hi, text="🤖  Глубокий анализ DeepSeek AI",
                 font=self.F["h2"], bg=COLORS["bg_card"], fg=COLORS["ai_header"]).pack(side="left")

        tk.Label(hi,
                 text="  Нейросеть даст персональные рекомендации с учётом модели и региона",
                 font=self.F["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(side="left", pady=(4,0))

        # Кнопки
        bf = tk.Frame(ai_card, bg=COLORS["bg_card"])
        bf.pack(fill="x", padx=20, pady=(0,12))

        self.btn_ai = self._btn(bf, "  Получить анализ от ИИ  ",
                                COLORS["green"], COLORS["green_hover"],
                                lambda: self._start_ai(data), pad=(18, 10))
        self.btn_ai.pack(side="left")

        self.btn_stop_ai = tk.Button(bf, text="Остановить", font=self.F["lbl"],
                                     bg="#94A3B8", fg="white", relief="flat",
                                     cursor="hand2", padx=12, pady=10,
                                     command=self._stop_ai,
                                     activebackground="#64748B", activeforeground="white",
                                     state="disabled")
        self.btn_stop_ai.pack(side="left", padx=(8,0))

        self.lbl_ai_status = tk.Label(bf, text="", font=self.F["small"],
                                      bg=COLORS["bg_card"], fg=COLORS["text_sec"])
        self.lbl_ai_status.pack(side="left", padx=(12,0))

        # Текстовое поле для ответа
        tf = tk.Frame(ai_card, bg=COLORS["bg_card"])
        tf.pack(fill="x", padx=20, pady=(0,16))

        self.ai_text = scrolledtext.ScrolledText(
            tf, font=self.F["mono"], wrap="word",
            bg=COLORS["ai_text_bg"], fg=COLORS["text_primary"],
            relief="flat", bd=1, height=18,
            highlightthickness=1,
            highlightbackground=COLORS["ai_border"],
            highlightcolor=COLORS["ai_border"],
            state="disabled",
            spacing3=3,
        )
        self.ai_text.pack(fill="x")

        # Тег для форматирования жирного текста (Markdown **text**)
        self.ai_text.tag_configure("bold", font=tkfont.Font(family="Consolas", size=10, weight="bold"))
        self.ai_text.tag_configure("placeholder", foreground=COLORS["text_muted"],
                                   font=tkfont.Font(family="Segoe UI", size=10))

        self._ai_text_placeholder()

    def _ai_text_placeholder(self):
        self.ai_text.config(state="normal")
        self.ai_text.delete("1.0", "end")
        self.ai_text.insert("end",
            "Нажмите «Получить анализ от ИИ» — DeepSeek изучит марку, пробег и двигатель\n"
            "и выдаст детальные рекомендации с типичными проблемами модели и стоимостью работ.",
            "placeholder")
        self.ai_text.config(state="disabled")

    def _start_ai(self, data: dict):
        api_key = self.v_apikey.get().strip()
        if not api_key:
            messagebox.showwarning("API ключ не задан",
                                   "Введите и сохраните API ключ DeepSeek\n"
                                   "в строке выше (поле с зелёным фоном).")
            return
        if not api_key.startswith("sk-"):
            messagebox.showwarning("Неверный ключ",
                                   "API ключ DeepSeek должен начинаться с sk-")
            return

        # Остановить предыдущий поток если он ещё работает
        self._stop_ai()
        self._ai_stop.clear()

        # Очистить поле
        self.ai_text.config(state="normal")
        self.ai_text.delete("1.0", "end")
        self.ai_text.config(state="disabled")

        self.btn_ai.config(state="disabled")
        self.btn_stop_ai.config(state="normal")
        self.lbl_ai_status.config(text="⏳ Запрос к DeepSeek...", fg=COLORS["text_sec"])

        prompt = build_ai_prompt(data["brand"], data["year"], data["engine"],
                                 data["avg"], data["cur"])

        self._ai_thread = threading.Thread(
            target=self._ai_worker, args=(api_key, prompt), daemon=True)
        self._ai_thread.start()

    def _stop_ai(self):
        self._ai_stop.set()
        if self._ai_thread and self._ai_thread.is_alive():
            self._ai_thread.join(timeout=2)
        self._ai_reset_buttons()

    def _ai_worker(self, api_key: str, prompt: str):
        """Поток: потоковый вызов DeepSeek API"""
        try:
            char_count = 0
            for chunk in deepseek_stream(api_key, prompt):
                if self._ai_stop.is_set():
                    break
                self.root.after(0, self._ai_append, chunk)
                char_count += len(chunk)
                if char_count % 200 == 0:
                    self.root.after(0, lambda: self.lbl_ai_status.config(
                        text=f"⏳ Генерирую... {char_count} символов"))
            if not self._ai_stop.is_set():
                self.root.after(0, self._ai_done, char_count)
            else:
                self.root.after(0, self._ai_stopped)

        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="ignore")
            msg = f"HTTP {e.code}: {e.reason}"
            try:
                detail = json.loads(body).get("error", {}).get("message", "")
                if detail:
                    msg += f"\n{detail}"
            except Exception:
                pass
            self.root.after(0, self._ai_error, msg)
        except urllib.error.URLError as e:
            self.root.after(0, self._ai_error, f"Нет соединения с DeepSeek:\n{e.reason}")
        except Exception as e:
            self.root.after(0, self._ai_error, str(e))

    def _ai_append(self, text: str):
        """Добавить текст в поле ответа (вызывается из главного потока)"""
        self.ai_text.config(state="normal")
        self.ai_text.insert("end", text)
        self.ai_text.see("end")
        self.ai_text.config(state="disabled")

    def _ai_done(self, n: int):
        self.lbl_ai_status.config(text=f"✓ Готово — {n} символов", fg=COLORS["success"])
        self._ai_reset_buttons()

    def _ai_stopped(self):
        self.lbl_ai_status.config(text="Остановлено", fg=COLORS["text_muted"])
        self._ai_reset_buttons()

    def _ai_error(self, msg: str):
        self.ai_text.config(state="normal")
        self.ai_text.delete("1.0", "end")
        self.ai_text.insert("end", f"Ошибка при обращении к DeepSeek API:\n\n{msg}")
        self.ai_text.config(state="disabled")
        self.lbl_ai_status.config(text="Ошибка запроса", fg=COLORS["high_text"])
        self._ai_reset_buttons()

    def _ai_reset_buttons(self):
        try:
            self.btn_ai.config(state="normal")
            self.btn_stop_ai.config(state="disabled")
        except tk.TclError:
            pass  # виджет мог быть уничтожен при пересчёте


# ============================================================
# ТОЧКА ВХОДА
# ============================================================

def main():
    root = tk.Tk()
    App(root)
    root.mainloop()

if __name__ == "__main__":
    main()
