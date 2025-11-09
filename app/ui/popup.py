from __future__ import annotations

import os
import platform
import subprocess
from typing import List, Tuple

import tkinter as tk
from tkinter import messagebox

try:
    from PIL import Image, ImageTk  # type: ignore
    _PIL_AVAILABLE = True
except Exception:
    _PIL_AVAILABLE = False

# Use runtime-aware base for packaged data
from app.core.paths import drawings_path


class SectionPopup:
    """Modal popup that shows 4 info cards + file/image shortcuts."""

    def __init__(self, parent, section_name: str, section_info: dict):
        self.popup = tk.Toplevel(parent)
        self.popup.title(f"Site Equipment - {section_name}")

        self._site_id = section_info.get("site")
        self._img_cache: List[tk.PhotoImage] = []  # keep references

        # --- size/position ---
        parent.update_idletasks()
        win_width = parent.winfo_width()
        win_height = parent.winfo_height()
        W, H = 700, 600
        x = parent.winfo_x() + (win_width // 2) - (W // 2)
        y = parent.winfo_y() + (win_height // 2) - (H // 2)
        self.popup.geometry(f"{W}x{H}+{x}+{y}")
        self.popup.resizable(True, True)
        self.popup.configure(bg="#f0f0f0")
        self.popup.transient(parent)
        self.popup.grab_set()

        # --- scroll container ---
        canvas = tk.Canvas(self.popup, bg="#f0f0f0", highlightthickness=0)
        scrollbar = tk.Scrollbar(self.popup, orient="vertical", command=canvas.yview)
        holder = tk.Frame(canvas, bg="#f0f0f0")
        holder.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=holder, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # header
        header = tk.Frame(holder, bg="#2c3e50", pady=8)
        header.pack(fill="x", padx=5, pady=(5, 3))
        tk.Label(header, text=f"📡 {section_name}", font=("Arial", 16, "bold"), fg="white", bg="#2c3e50").pack()

        # data to render
        data = self.parse_display_data(section_info)

        # grid
        grid = tk.Frame(holder, bg="#f0f0f0")
        grid.pack(fill="both", expand=True, padx=5, pady=5)
        for r in (0, 1):
            grid.rowconfigure(r, weight=1)
        for c in (0, 1):
            grid.columnconfigure(c, weight=1)

        self.create_info_card(grid, "🏢 Site Information", data.get("site", {}), "#3498db", 0, 0)
        self.create_info_card(grid, "⚙️ Equipment Details", data.get("equipment", {}), "#e74c3c", 0, 1)
        self.create_info_card(grid, "📍 Location", data.get("location", {}), "#27ae60", 1, 0)
        self.create_info_card(grid, "🔧 Technical Specs", data.get("technical", {}), "#f39c12", 1, 1)

        # close button
        footer = tk.Frame(holder, bg="#f0f0f0", pady=5)
        footer.pack(fill="x")
        btn_wrap = tk.Frame(footer, bg="#e74c3c", relief=tk.FLAT, bd=0, cursor="hand2")
        btn_wrap.pack(pady=5)
        btn_lbl = tk.Label(btn_wrap, text="✕ Close", bg="#e74c3c", fg="white",
                           font=("Arial", 11, "bold"), padx=20, pady=5, cursor="hand2")
        btn_lbl.pack()
        for w in (btn_wrap, btn_lbl):
            w.bind("<Button-1>", lambda _e: self.close())
        def on_enter(_e): btn_wrap.configure(bg="#c0392b"); btn_lbl.configure(bg="#c0392b")
        def on_leave(_e): btn_wrap.configure(bg="#e74c3c"); btn_lbl.configure(bg="#e74c3c")
        for w in (btn_wrap, btn_lbl):
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)

        canvas.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side="right", fill="y", pady=10, padx=(0, 10))

        self.popup.bind("<Escape>", lambda e: self.close())
        self.popup.focus_set()

    # ---- card ----
    def create_info_card(self, parent, title: str, data: dict, color: str, row: int, col: int) -> None:
        card = tk.Frame(parent, bg="white", relief=tk.RAISED, bd=2)
        card.grid(row=row, column=col, sticky="nsew", padx=3, pady=3)
        card.rowconfigure(1, weight=1)
        card.columnconfigure(0, weight=1)

        header = tk.Frame(card, bg=color, height=28)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        tk.Label(header, text=title, font=("Arial", 12, "bold"), fg="white", bg=color).pack(expand=True)

        content_frame = tk.Frame(card, bg="white")
        content_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=5)

        canvas = tk.Canvas(content_frame, bg="white", highlightthickness=0)
        scrollbar = tk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        content = tk.Frame(canvas, bg="white")
        content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # key/value rendering
        for key, value in data.items():
            if not value:
                continue
            rowf = tk.Frame(content, bg="white"); rowf.pack(fill="x", pady=0)
            tk.Label(rowf, text=f"{key}:", font=("Arial", 11, "bold"), bg="white", fg="#2c3e50",
                     width=12, anchor="w").pack(side="left")
            if isinstance(value, list):
                bullets = tk.Frame(rowf, bg="white"); bullets.pack(side="left", padx=(3,0), fill="x", expand=True)
                for item in value:
                    line = tk.Frame(bullets, bg="white"); line.pack(anchor="w")
                    tk.Label(line, text="•", font=("Arial", 10, "bold"), bg="white", fg="#34495e").pack(side="left", padx=(0,4))
                    tk.Label(line, text=str(item), font=("Arial", 10), bg="white", fg="#34495e",
                             anchor="w", wraplength=160).pack(side="left")
            else:
                tk.Label(rowf, text=str(value), font=("Arial", 10), bg="white", fg="#34495e",
                         anchor="w", wraplength=160).pack(side="left", padx=(3,0), fill="x", expand=True)

        # attach sections
        if title == "🏢 Site Information":
            self._add_pdf_button(content, "Site Drawing",
                                 self.get_site_drawing_path(data.get("Site ID", "Unknown")), icon="📄")
        if title == "⚙️ Equipment Details":
            sid = (getattr(self, "_site_id", None)
                   or data.get("Site ID") or data.get("Site") or data.get("site") or "Unknown")
            self._add_pdf_button(content, "Equipment Drawing",
                                 self.get_equipment_drawing_path(sid), icon="🔌")
        if title == "📍 Location":
            self._add_frequency_gallery(content,
                                        getattr(self, "_site_id", None) or data.get("Site") or data.get("site") or "Unknown")

    # ---- helpers: buttons & files ----
    def _add_pdf_button(self, parent, label: str, path: str, icon: str = "📄") -> None:
        sep = tk.Frame(parent, bg="#ecf0f1", height=1); sep.pack(fill="x", pady=(10,5))
        card = tk.Frame(parent, bg="#f8f9fa", relief=tk.RAISED, bd=2, cursor="hand2"); card.pack(anchor="w", padx=10, pady=2)
        thumb = tk.Frame(card, bg="white", width=30, height=30, relief=tk.SUNKEN, bd=1); thumb.pack(side="left", padx=8, pady=8); thumb.pack_propagate(False)
        tk.Label(thumb, text=icon, font=("Arial", 18), bg="white", fg="#3498db", cursor="hand2").pack(expand=True)
        box = tk.Frame(card, bg="#f8f9fa"); box.pack(side="left", padx=8, pady=8, fill="x")
        tk.Label(box, text=label, font=("Arial", 10, "bold"), bg="#f8f9fa", fg="#2c3e50", anchor="w", cursor="hand2").pack(anchor="w")
        tk.Label(box, text="Click to view", font=("Arial", 9), bg="#f8f9fa", fg="#7f8c8d", anchor="w", cursor="hand2").pack(anchor="w")

        def open_external(_evt=None, p=path):
            abs_path = os.path.abspath(p) if p else ""
            if not abs_path or not os.path.exists(abs_path):
                messagebox.showerror("File not found", f"File not found:\n{p}"); return
            try:
                sys = platform.system()
                if sys == "Darwin": subprocess.run(["open", abs_path], check=False)
                elif sys == "Windows": os.startfile(abs_path)  # nosec
                else: subprocess.run(["xdg-open", abs_path], check=False)
            except Exception as e:
                messagebox.showerror("Error", f"Could not open file:\n{e}")

        for w in (card, thumb, box):
            w.bind("<Button-1>", open_external)

        def on_enter(_e): card.configure(bg="#e9ecef")
        def on_leave(_e): card.configure(bg="#f8f9fa")
        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)

    def _add_frequency_gallery(self, parent, site_id: str) -> None:
        sep = tk.Frame(parent, bg="#ecf0f1", height=1); sep.pack(fill="x", pady=(10,5))
        wrap = tk.Frame(parent, bg="#f8f9fa", relief=tk.RAISED, bd=2); wrap.pack(anchor="w", fill="x", padx=10, pady=2)
        head = tk.Frame(wrap, bg="#f8f9fa"); head.pack(fill="x", padx=8, pady=(8,0))
        tk.Label(head, text="📶 Frequency Images", font=("Arial", 10, "bold"), bg="#f8f9fa", fg="#2c3e50").pack(side="left")
        gal = tk.Frame(wrap, bg="#f8f9fa"); gal.pack(fill="x", padx=8, pady=8)

        paths = self.find_frequency_images(site_id)
        if not paths:
            tk.Label(gal, text="No images found", font=("Arial", 9), bg="#f8f9fa", fg="#7f8c8d").pack(anchor="w")
            return

        max_w, max_h, cols = 140, 100, 3
        for idx, p in enumerate(paths[:6]):
            thumb = self._load_thumbnail(p, max_w, max_h)
            self._img_cache.append(thumb)  # keep ref
            cell = tk.Frame(gal, bg="#ffffff", relief=tk.SOLID, bd=1, cursor="hand2")
            r, c = divmod(idx, cols); cell.grid(row=r, column=c, padx=6, pady=6, sticky="w")
            lbl = tk.Label(cell, image=thumb, bg="#ffffff", cursor="hand2"); lbl.pack()
            cap = tk.Label(cell, text=os.path.basename(p), font=("Arial", 8), bg="#ffffff", fg="#7f8c8d", wraplength=max_w); cap.pack(padx=2, pady=(2,4))

            def _open(_evt=None, path=p):
                abs_path = os.path.abspath(path)
                if not os.path.exists(abs_path):
                    messagebox.showerror("Image not found", f"File not found:\n{path}"); return
                try:
                    sys = platform.system()
                    if sys == "Darwin": subprocess.run(["open", abs_path], check=False)
                    elif sys == "Windows": os.startfile(abs_path)  # nosec
                    else: subprocess.run(["xdg-open", abs_path], check=False)
                except Exception as e:
                    messagebox.showerror("Error", f"Could not open image:\n{e}")
            for w in (cell, lbl, cap):
                w.bind("<Button-1>", _open)

    # ---- search helpers ----
    def _normalize(self, s: str) -> str:
        s = s.lower()
        out = [(ch if (ch.isalnum() or ch.isspace()) else " ") for ch in s]
        return " ".join("".join(out).split())

    def get_site_drawing_path(self, site_id: str) -> str:
        base_dir = os.fspath(drawings_path())
        if not site_id or site_id == "Unknown" or not os.path.isdir(base_dir):
            return os.fspath(drawings_path("unknown.pdf"))
        site_tokens = [t for t in self._normalize(str(site_id)).split() if t not in {"al", "el"}] or [site_id]
        room_kw = ["equipment room", "rack room", "room layout", "shelter layout", "layout"]
        exclude_kw = ["radio", "radios", "front", "back", "r&s", "rack front", "elevation"]
        best, best_score = None, -1.0
        for root, _dirs, files in os.walk(base_dir):
            for fn in files:
                if not fn.lower().endswith(".pdf"): continue
                norm = self._normalize(fn)
                if any(ex in norm for ex in exclude_kw): continue
                token_hits = sum(1 for t in site_tokens if t and t in norm)
                if token_hits == 0: continue
                kw_bonus = sum(2 for kw in room_kw if kw in norm)
                score = token_hits * 3 + kw_bonus - (len(norm) / 200.0)
                if score > best_score:
                    best_score = score; best = os.path.join(root, fn)
        if best:
            try: return os.path.relpath(best, os.path.abspath("."))
            except Exception: return best
        for root, _dirs, files in os.walk(base_dir):
            for fn in files:
                if fn.lower().endswith(".pdf") and all(t in self._normalize(fn) for t in site_tokens):
                    try: return os.path.relpath(os.path.join(root, fn), os.path.abspath("."))
                    except Exception: return os.path.join(root, fn)
        return os.fspath(drawings_path("unknown.pdf"))

    def get_equipment_drawing_path(self, site_id: str) -> str:
        base_dir = os.fspath(drawings_path())
        if not site_id or site_id == "Unknown" or not os.path.isdir(base_dir):
            return os.fspath(drawings_path("unknown.pdf"))
        site_tokens = [t for t in self._normalize(str(site_id)).split() if t not in {"al", "el"}] or [site_id]
        include_kw = ["radio", "radios", "elevation", "front", "back", "rack front", "rcag", "equipment"]
        exclude_kw = ["room layout", "equipment room", "rack room", "shelter layout", "layout"]
        best, best_score = None, -1.0
        for root, _dirs, files in os.walk(base_dir):
            for fn in files:
                if not fn.lower().endswith(".pdf"): continue
                norm = self._normalize(fn)
                if any(ex in norm for ex in exclude_kw): continue
                token_hits = sum(1 for t in site_tokens if t and t in norm)
                if token_hits == 0: continue
                kw_bonus = sum(2 for kw in include_kw if kw in norm)
                score = token_hits * 3 + kw_bonus - (len(norm) / 200.0)
                if score > best_score:
                    best_score = score; best = os.path.join(root, fn)
        if best:
            try: return os.path.relpath(best, os.path.abspath("."))
            except Exception: return best
        for root, _dirs, files in os.walk(base_dir):
            for fn in files:
                if fn.lower().endswith(".pdf") and all(t in self._normalize(fn) for t in site_tokens):
                    try: return os.path.relpath(os.path.join(root, fn), os.path.abspath("."))
                    except Exception: return os.path.join(root, fn)
        return os.fspath(drawings_path("unknown.pdf"))

    def find_frequency_images(self, site_id: str) -> List[str]:
        pref = os.fspath(drawings_path("freq"))
        fb = os.fspath(drawings_path())
        base_candidates = []
        if os.path.isdir(pref): base_candidates.append(pref)
        if os.path.isdir(fb) and fb not in base_candidates: base_candidates.append(fb)
        if not site_id or site_id == "Unknown" or not base_candidates: return []
        site_tokens = [t for t in self._normalize(site_id).split() if t]
        freq_kw = [site_id]
        scored: List[Tuple[float, str]] = []
        seen = set()
        for base in base_candidates:
            for root, _dirs, files in os.walk(base):
                for fn in files:
                    if not fn.lower().endswith((".png", ".jpg", ".jpeg")): continue
                    fpath = os.path.join(root, fn)
                    if fpath in seen: continue
                    seen.add(fpath)
                    norm = self._normalize(fn)
                    site_hits = sum(1 for t in site_tokens if t in norm)
                    kw_hits = sum(1 for k in freq_kw if k in norm)
                    score = site_hits * 3 + kw_hits * 2 - (len(norm) / 300.0)
                    if score <= 0 and base == pref: score = 0.1
                    scored.append((score, fpath))
        if not scored: return []
        scored.sort(key=lambda x: (-x[0], os.path.basename(x[1])))
        return [p for _s, p in scored[:1]]

    def _load_thumbnail(self, path: str, max_w: int, max_h: int) -> tk.PhotoImage:
        try:
            if _PIL_AVAILABLE:
                img = Image.open(path)
                img.thumbnail((max_w, max_h))
                return ImageTk.PhotoImage(img)
            else:
                img = tk.PhotoImage(file=path)
                w, h = img.width(), img.height()
                fx = max(1, int((w + max_w - 1) // max_w))
                fy = max(1, int((h + max_h - 1) // max_h))
                f = max(fx, fy)
                if f > 1: img = img.subsample(f, f)
                return img
        except Exception:
            return tk.PhotoImage(width=max_w, height=max_h)

    # ---- data mapping ----
    def parse_display_data(self, section_info: dict) -> dict:
        """
        Normalize the raw point dict into four display sections.
        Expected keys in section_info: site, lon, lat, sectorId, freq (dict), power (dict)
        """
        site = section_info.get("site")
        lon = section_info.get("lon")
        lat = section_info.get("lat")
        sector_id = section_info.get("sectorId")
        freq = section_info.get("freq") or {}
        power = section_info.get("power") or {}

        def dict_to_list(d):
            if isinstance(d, dict):
                return [f"{k}: {v}" for k, v in d.items()] or ["Unknown"]
            return [str(d or "Unknown")]

        return {
            "site": {
                "Site ID": site or "Unknown",
                "Sector ID": sector_id or "Unknown",
                "System Type": "RCAG SITE",
                "Environment": "MPS",
                "Criticality": "Non Critical",
            },
            "equipment": {
                "Description": "SITE RCAG - EQUIPMENT SUPPORT SYSTEM",
                "Equipment Type": "Site Infrastructure",
                "Brand": "—",
                "Model": "—",
            },
            "location": {
                "Latitude": f"{lat:.5f}" if isinstance(lat, (int, float)) else str(lat or "—"),
                "Longitude": f"{lon:.5f}" if isinstance(lon, (int, float)) else str(lon or "—"),
                "Frequencies": dict_to_list(freq),
            },
            "technical": {
                "Power": dict_to_list(power),
                "Certification": "Active",
            },
        }

    def close(self) -> None:
        self.popup.grab_release()
        self.popup.destroy()
