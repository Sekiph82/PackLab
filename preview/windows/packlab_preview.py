from __future__ import annotations

import tkinter as tk
from tkinter import ttk


APP_TITLE = "PackLab Studio Preview"
APP_VERSION = "0.1-preview"


class PackLabPreview(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1180x760")
        self.minsize(980, 640)

        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main()
        self.show_page("Library")

    def _build_sidebar(self) -> None:
        sidebar = tk.Frame(self, bg="#171a1f", width=220)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        tk.Label(
            sidebar,
            text="PACKLAB",
            fg="white",
            bg="#171a1f",
            font=("Segoe UI", 22, "bold"),
            anchor="w",
        ).pack(fill="x", padx=20, pady=(24, 4))

        tk.Label(
            sidebar,
            text="Studio Preview",
            fg="#9da7b3",
            bg="#171a1f",
            font=("Segoe UI", 10),
            anchor="w",
        ).pack(fill="x", padx=20, pady=(0, 22))

        for name in ["Library", "Capture Inbox", "Reconstruction", "Editor", "Settings"]:
            tk.Button(
                sidebar,
                text=name,
                command=lambda n=name: self.show_page(n),
                bg="#222831",
                fg="white",
                activebackground="#303844",
                activeforeground="white",
                relief="flat",
                bd=0,
                anchor="w",
                padx=18,
                pady=12,
                font=("Segoe UI", 10),
            ).pack(fill="x", padx=12, pady=4)

        spacer = tk.Frame(sidebar, bg="#171a1f")
        spacer.pack(fill="both", expand=True)

        tk.Label(
            sidebar,
            text=f"{APP_VERSION}\nPreview shell only",
            fg="#77818d",
            bg="#171a1f",
            font=("Segoe UI", 8),
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=20, pady=18)

    def _build_main(self) -> None:
        self.main = tk.Frame(self, bg="#f3f5f7")
        self.main.grid(row=0, column=1, sticky="nsew")
        self.main.columnconfigure(0, weight=1)
        self.main.rowconfigure(1, weight=1)

        header = tk.Frame(self.main, bg="white", height=72)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)

        self.header_title = tk.Label(
            header,
            text="",
            bg="white",
            fg="#1b1f24",
            font=("Segoe UI", 18, "bold"),
            anchor="w",
        )
        self.header_title.pack(side="left", padx=28)

        tk.Label(
            header,
            text="Windows Preview",
            bg="white",
            fg="#6b7280",
            font=("Segoe UI", 9),
        ).pack(side="right", padx=28)

        self.content = tk.Frame(self.main, bg="#f3f5f7")
        self.content.grid(row=1, column=0, sticky="nsew", padx=28, pady=28)
        self.content.columnconfigure(0, weight=1)
        self.content.rowconfigure(0, weight=1)

    def _clear_content(self) -> None:
        for child in self.content.winfo_children():
            child.destroy()

    def show_page(self, name: str) -> None:
        self.header_title.configure(text=name)
        self._clear_content()

        if name == "Library":
            self._library_page()
        elif name == "Capture Inbox":
            self._simple_page(
                "Capture Inbox",
                "Incoming PackScan packages will appear here.",
                ["Import .packscan", "Validate package", "Review diagnostics"],
            )
        elif name == "Reconstruction":
            self._simple_page(
                "Reconstruction",
                "COLMAP/OpenMVS orchestration is planned for a later milestone.",
                ["New reconstruction", "Job queue", "Logs"],
            )
        elif name == "Editor":
            self._simple_page(
                "Editor",
                "The future 3D/CAD workspace will live here.",
                ["3D viewport", "Design model", "Measurements"],
            )
        else:
            self._simple_page(
                "Settings",
                "Preview settings panel.",
                ["General", "Engines", "Paths", "Diagnostics"],
            )

    def _library_page(self) -> None:
        wrapper = tk.Frame(self.content, bg="#f3f5f7")
        wrapper.grid(sticky="nsew")
        wrapper.columnconfigure((0, 1, 2), weight=1)

        intro = tk.Frame(wrapper, bg="white", bd=0, highlightthickness=1, highlightbackground="#e2e7ec")
        intro.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 22))
        tk.Label(
            intro,
            text="PackLab Studio is alive.",
            bg="white",
            fg="#1b1f24",
            font=("Segoe UI", 20, "bold"),
            anchor="w",
        ).pack(fill="x", padx=24, pady=(24, 6))
        tk.Label(
            intro,
            text=(
                "This is a preview Windows shell, not the production application. "
                "It exists so you can double-click PackLab and see the planned Studio structure."
            ),
            bg="white",
            fg="#59636e",
            font=("Segoe UI", 10),
            wraplength=780,
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=24, pady=(0, 24))

        cards = [
            ("0", "Packaging assets", "Library content arrives in M15."),
            ("0", "Capture packages", "Capture/transfer milestones are still ahead."),
            ("Preview", "Application state", "UI shell only, no production claims."),
        ]
        for i, (value, title, subtitle) in enumerate(cards):
            card = tk.Frame(wrapper, bg="white", highlightthickness=1, highlightbackground="#e2e7ec")
            card.grid(row=1, column=i, sticky="nsew", padx=(0 if i == 0 else 9, 0 if i == 2 else 9))
            tk.Label(card, text=value, bg="white", fg="#20262d", font=("Segoe UI", 24, "bold")).pack(
                anchor="w", padx=20, pady=(20, 4)
            )
            tk.Label(card, text=title, bg="white", fg="#20262d", font=("Segoe UI", 11, "bold")).pack(
                anchor="w", padx=20
            )
            tk.Label(
                card,
                text=subtitle,
                bg="white",
                fg="#6b7280",
                font=("Segoe UI", 9),
                wraplength=230,
                justify="left",
            ).pack(anchor="w", padx=20, pady=(4, 20))

    def _simple_page(self, title: str, description: str, items: list[str]) -> None:
        panel = tk.Frame(self.content, bg="white", highlightthickness=1, highlightbackground="#e2e7ec")
        panel.grid(sticky="nsew")
        tk.Label(
            panel,
            text=title,
            bg="white",
            fg="#1b1f24",
            font=("Segoe UI", 20, "bold"),
            anchor="w",
        ).pack(fill="x", padx=24, pady=(24, 6))
        tk.Label(
            panel,
            text=description,
            bg="white",
            fg="#59636e",
            font=("Segoe UI", 10),
            anchor="w",
        ).pack(fill="x", padx=24, pady=(0, 20))

        for item in items:
            row = tk.Frame(panel, bg="#f7f8fa")
            row.pack(fill="x", padx=24, pady=5)
            tk.Label(
                row,
                text=item,
                bg="#f7f8fa",
                fg="#303842",
                font=("Segoe UI", 10),
                anchor="w",
                padx=14,
                pady=12,
            ).pack(fill="x")


if __name__ == "__main__":
    app = PackLabPreview()
    app.mainloop()
