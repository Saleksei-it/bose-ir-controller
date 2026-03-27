#!/usr/bin/env python3
"""GUI controller for a Bose 3-2-1 media center over infrared."""

from __future__ import annotations

import json
import subprocess
import threading
import tkinter as tk
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from tkinter import messagebox
from typing import Any


CONFIG_PATH = Path(__file__).with_name("bose_ir_config.json")


@dataclass(frozen=True)
class IRCommand:
    protocol: str
    scancode: str | None = None
    raw: list[int] | None = None


@dataclass(frozen=True)
class AppConfig:
    window_title: str
    ir_device: str
    test_mode: bool
    buttons: dict[str, IRCommand]


def load_config(path: Path) -> AppConfig:
    with path.open("r", encoding="utf-8") as config_file:
        data: dict[str, Any] = json.load(config_file)

    buttons: dict[str, IRCommand] = {}
    for name, command_data in data["buttons"].items():
        buttons[name] = IRCommand(
            protocol=command_data["protocol"],
            scancode=command_data.get("scancode"),
            raw=command_data.get("raw"),
        )

    return AppConfig(
        window_title=data["window_title"],
        ir_device=data["ir_device"],
        test_mode=data.get("test_mode", False),
        buttons=buttons,
    )


class IrCtlTransmitter:
    def __init__(self, ir_device: str) -> None:
        self.ir_device = ir_device

    def send(self, command: IRCommand) -> None:
        if command.protocol == "raw":
            if not command.raw:
                raise ValueError("Raw command is empty.")
            with NamedTemporaryFile("w", encoding="utf-8", delete=True) as temp_file:
                temp_file.write("\n".join(self._format_raw(command.raw)))
                temp_file.write("\n")
                temp_file.flush()
                args = ["ir-ctl", "--device", self.ir_device, "--send", temp_file.name]
                subprocess.run(args, check=True, capture_output=True, text=True)
        else:
            if not command.scancode:
                raise ValueError("Scancode is empty.")
            args = [
                "ir-ctl",
                "--device",
                self.ir_device,
                "--scancode",
                f"{command.protocol}:{command.scancode}",
            ]
            subprocess.run(args, check=True, capture_output=True, text=True)

    @staticmethod
    def _format_raw(raw: list[int]) -> list[str]:
        formatted: list[str] = []
        for index, value in enumerate(raw):
            prefix = "+" if index % 2 == 0 else "-"
            formatted.append(f"{prefix}{value}")
        return formatted


class MockTransmitter:
    def __init__(self, ir_device: str) -> None:
        self.ir_device = ir_device

    def send(self, command: IRCommand) -> None:
        return None


class BoseRemoteApp:
    def __init__(self, root: tk.Tk, config: AppConfig) -> None:
        self.root = root
        self.config = config
        self.test_mode_var = tk.BooleanVar(value=config.test_mode)
        self.transmitter = self._build_transmitter()
        self.status_var = tk.StringVar(value="Готово к отправке ИК-команды.")
        self.device_var = tk.StringVar(value=self._device_label())

        self.root.title(config.window_title)
        self.root.geometry("420x560")
        self.root.minsize(380, 520)
        self.root.configure(bg="#000000")

        self._build_ui()

    def _build_transmitter(self) -> IrCtlTransmitter | MockTransmitter:
        if self.test_mode_var.get():
            return MockTransmitter(self.config.ir_device)
        return IrCtlTransmitter(self.config.ir_device)

    def _device_label(self) -> str:
        mode = "TEST MODE" if self.test_mode_var.get() else "LIVE MODE"
        return f"{mode}  |  {self.config.ir_device}"

    def _build_ui(self) -> None:
        title = tk.Label(
            self.root,
            text="Bose 3-2-1 IR Control",
            font=("Helvetica", 18, "bold"),
            bg="#000000",
            fg="#ffffff",
        )
        title.pack(pady=(24, 8))

        subtitle = tk.Label(
            self.root,
            textvariable=self.device_var,
            font=("Helvetica", 10),
            bg="#000000",
            fg="#ffffff",
        )
        subtitle.pack(pady=(0, 18))

        mode_frame = tk.Frame(self.root, bg="#000000")
        mode_frame.pack(fill="x", padx=24, pady=(0, 16))

        mode_toggle = tk.Checkbutton(
            mode_frame,
            text="Тестовый режим без отправки ИК",
            variable=self.test_mode_var,
            command=self._toggle_test_mode,
            font=("Helvetica", 10, "bold"),
            bg="#000000",
            fg="#ffffff",
            activebackground="#000000",
            activeforeground="#ffffff",
            selectcolor="#000000",
        )
        mode_toggle.pack(anchor="w")

        buttons_frame = tk.Frame(self.root, bg="#000000")
        buttons_frame.pack(fill="both", expand=False, padx=24, pady=(8, 0))

        volume_frame = tk.Frame(buttons_frame, bg="#000000")
        volume_frame.pack(fill="x", pady=(0, 18))
        volume_frame.grid_columnconfigure(0, weight=1)
        volume_frame.grid_columnconfigure(1, weight=1)

        self._add_button(volume_frame, "volume_down", "Volume -").grid(
            row=0, column=0, padx=(0, 8), sticky="nsew"
        )
        self._add_button(volume_frame, "volume_up", "Volume +").grid(
            row=0, column=1, padx=(8, 0), sticky="nsew"
        )
        self._add_button(buttons_frame, "power_on", "Power On").pack(fill="x")

        self.log_text = tk.Text(
            self.root,
            height=8,
            font=("Courier", 10),
            bg="#000000",
            fg="#ffffff",
            insertbackground="#ffffff",
            relief="solid",
            borderwidth=1,
        )
        self.log_text.pack(fill="both", expand=True, padx=24, pady=(20, 16))
        self.log_text.insert("end", "Приложение запущено.\n")
        self.log_text.configure(state="disabled")

    def _add_button(self, parent: tk.Frame, command_name: str, label: str) -> tk.Button:
        button = tk.Button(
            parent,
            text=label,
            font=("Helvetica", 14, "bold"),
            bg="#000000",
            fg="#ffffff",
            activebackground="#111111",
            activeforeground="#ffffff",
            relief="solid",
            borderwidth=2,
            highlightthickness=1,
            highlightbackground="#ffffff",
            highlightcolor="#ffffff",
            padx=12,
            pady=18,
            command=lambda: self._send_async(command_name),
        )
        return button

    def _send_async(self, command_name: str) -> None:
        thread = threading.Thread(target=self._send_command, args=(command_name,), daemon=True)
        thread.start()

    def _send_command(self, command_name: str) -> None:
        command = self.config.buttons[command_name]
        try:
            self._set_status(f"Отправка команды: {command_name}")
            self.transmitter.send(command)
        except FileNotFoundError:
            self._show_error(
                "Команда ir-ctl не найдена. Установите пакет v4l-utils: sudo apt install v4l-utils"
            )
            return
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.strip() or exc.stdout.strip() or str(exc)
            self._show_error(f"Не удалось отправить ИК-команду.\n\n{stderr}")
            return
        except Exception as exc:  # pragma: no cover - GUI fallback
            self._show_error(str(exc))
            return

        self._append_log(command_name, command)
        self._set_status(f"Команда {command_name} отправлена.")

    def _toggle_test_mode(self) -> None:
        self.transmitter = self._build_transmitter()
        self.device_var.set(self._device_label())
        state = "включен" if self.test_mode_var.get() else "выключен"
        self._set_status(f"Тестовый режим {state}.")
        self._append_log("mode", IRCommand(protocol="mock", scancode=state))

    def _set_status(self, text: str) -> None:
        self.root.after(0, lambda: self.status_var.set(text))

    def _show_error(self, text: str) -> None:
        self.root.after(0, lambda: messagebox.showerror("Ошибка", text))
        self._set_status("Ошибка отправки ИК-команды.")

    def _append_log(self, command_name: str, command: IRCommand) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        details = command.scancode if command.scancode else f"raw[{len(command.raw or [])}]"
        line = f"[{timestamp}] {command_name}: {command.protocol} {details}\n"

        def append() -> None:
            self.log_text.configure(state="normal")
            self.log_text.insert("end", line)
            self.log_text.see("end")
            self.log_text.configure(state="disabled")

        self.root.after(0, append)


def main() -> None:
    config = load_config(CONFIG_PATH)
    root = tk.Tk()
    BoseRemoteApp(root, config)
    root.mainloop()


if __name__ == "__main__":
    main()
