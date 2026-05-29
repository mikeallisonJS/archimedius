#!/usr/bin/env python3
"""
Collision prompt dialog for Archimedius organize runs.
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk

import defaults


class CollisionPromptDialog:
    """Modal dialog asking how to handle a path collision."""

    def __init__(
        self,
        parent: tk.Misc,
        *,
        source_path: Path,
        destination_path: Path,
    ) -> None:
        self._result: tuple[str, bool] | None = None
        self._apply_all = tk.BooleanVar(value=False)

        self.window = tk.Toplevel(parent)
        self.window.title("Path Collision")
        self.window.transient(parent)
        self.window.grab_set()
        self.window.resizable(False, False)

        main_frame = ttk.Frame(self.window, padding=12)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            main_frame,
            text="A file already exists at the destination path:",
            wraplength=520,
        ).pack(anchor=tk.W)

        ttk.Label(
            main_frame,
            text=str(destination_path),
            font=("TkDefaultFont", 9, "bold"),
            wraplength=520,
        ).pack(anchor=tk.W, pady=(4, 8))

        ttk.Label(
            main_frame,
            text=f"Source file: {source_path}",
            wraplength=520,
        ).pack(anchor=tk.W, pady=(0, 12))

        ttk.Label(
            main_frame,
            text="How should Archimedius handle this collision?",
            wraplength=520,
        ).pack(anchor=tk.W, pady=(0, 8))

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 8))

        ttk.Button(
            button_frame,
            text="Rename",
            command=lambda: self._choose(defaults.COLLISION_POLICY_RENAME),
        ).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(
            button_frame,
            text="Overwrite",
            command=lambda: self._choose(defaults.COLLISION_POLICY_OVERWRITE),
        ).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(
            button_frame,
            text="Skip",
            command=lambda: self._choose(defaults.COLLISION_POLICY_SKIP),
        ).pack(side=tk.LEFT)

        ttk.Checkbutton(
            main_frame,
            text="Apply to all remaining collisions in this run",
            variable=self._apply_all,
        ).pack(anchor=tk.W, pady=(0, 8))

        self.window.protocol("WM_DELETE_WINDOW", lambda: self._choose(defaults.COLLISION_POLICY_SKIP))
        self.window.bind("<Escape>", lambda _event: self._choose(defaults.COLLISION_POLICY_SKIP))

        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")

    def _choose(self, action: str) -> None:
        self._result = (action, self._apply_all.get())
        self.window.destroy()

    def show(self) -> tuple[str, bool]:
        """Show the dialog and return (action, apply_to_all)."""
        self.window.wait_window()
        if self._result is None:
            return defaults.COLLISION_POLICY_SKIP, False
        return self._result
