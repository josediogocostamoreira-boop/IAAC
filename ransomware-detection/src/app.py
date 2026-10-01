"""Simple Windows GUI for training and using the ransomware classifier."""

from __future__ import annotations

import queue
import json
import os
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


def find_project_root() -> Path:
    candidates = [
        Path.cwd(),
        Path(__file__).resolve().parents[1],
        Path(sys.executable).resolve().parent,
        Path(sys.executable).resolve().parent.parent,
    ]
    for candidate in candidates:
        if (candidate / "ransom.csv").is_file() and (candidate / "src").is_dir():
            return candidate
    raise FileNotFoundError(
        "Não foi possível localizar a pasta do projeto. "
        "Execute a aplicação a partir de ransomware-detection."
    )


class RansomwareApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Deteção de ransomware")
        self.geometry("780x520")
        self.minsize(650, 420)
        self.project_root = find_project_root()
        self.output_queue: queue.Queue[str] = queue.Queue()
        self.process: subprocess.Popen[str] | None = None
        self._build_ui()
        self.after(100, self._drain_output)

    def _build_ui(self) -> None:
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            frame,
            text="Deteção de ransomware",
            font=("Segoe UI", 16, "bold"),
        ).pack(anchor=tk.W)
        ttk.Label(
            frame,
            text=f"Projeto: {self.project_root}",
        ).pack(anchor=tk.W, pady=(2, 12))

        actions = ttk.Frame(frame)
        actions.pack(fill=tk.X, pady=(0, 12))
        self.install_button = ttk.Button(
            actions, text="1. Instalar dependências", command=self.install_dependencies
        )
        self.install_button.pack(side=tk.LEFT, padx=(0, 8))
        self.train_button = ttk.Button(
            actions, text="2. Treinar modelo", command=self.train
        )
        self.train_button.pack(side=tk.LEFT, padx=(0, 8))
        self.predict_button = ttk.Button(
            actions, text="3. Fazer previsão", command=self.predict
        )
        self.predict_button.pack(side=tk.LEFT, padx=(0, 8))
        self.api_button = ttk.Button(
            actions, text="Iniciar API", command=self.start_api
        )
        self.api_button.pack(side=tk.LEFT)

        self.log = tk.Text(frame, height=20, state=tk.DISABLED, wrap=tk.WORD)
        self.log.pack(fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(frame, command=self.log.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log.configure(yscrollcommand=scrollbar.set)
        self._write("Pronto. Começa por instalar as dependências.")

    def _write(self, text: str) -> None:
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, text)
        if not text.endswith("\n"):
            self.log.insert(tk.END, "\n")
        self.log.see(tk.END)
        self.log.configure(state=tk.DISABLED)

    def _run_async(self, title: str, command: list[str]) -> None:
        if self.process is not None and self.process.poll() is None:
            messagebox.showwarning("Operação em curso", "Aguarda a operação atual terminar.")
            return

        self._set_buttons(False)
        self._write(f"\n> {title}")

        def worker() -> None:
            try:
                self.process = subprocess.Popen(
                    command,
                    cwd=self.project_root,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    env={**os.environ, "PYTHONUNBUFFERED": "1"},
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
                assert self.process.stdout is not None
                for line in self.process.stdout:
                    self.output_queue.put(line)
                return_code = self.process.wait()
                self.output_queue.put(
                    f"\nConcluído: {'sucesso' if return_code == 0 else f'erro ({return_code})'}\n"
                )
            except OSError as exc:
                self.output_queue.put(f"\nErro ao executar a operação: {exc}\n")
            finally:
                self.output_queue.put("__ENABLE_BUTTONS__")

        threading.Thread(target=worker, daemon=True).start()

    def _drain_output(self) -> None:
        try:
            while True:
                message = self.output_queue.get_nowait()
                if message == "__ENABLE_BUTTONS__":
                    self._set_buttons(True)
                else:
                    self._write(message)
        except queue.Empty:
            pass
        self.after(100, self._drain_output)

    def _set_buttons(self, enabled: bool) -> None:
        state = tk.NORMAL if enabled else tk.DISABLED
        for button in (
            self.install_button,
            self.train_button,
            self.predict_button,
            self.api_button,
        ):
            button.configure(state=state)

    def _python(self) -> str:
        venv_python = self.project_root / ".venv" / "Scripts" / "python.exe"
        return str(venv_python if venv_python.is_file() else sys.executable)

    def install_dependencies(self) -> None:
        self._run_async(
            "Instalar dependências",
            [self._python(), "-m", "pip", "install", "-r", "requirements.txt"],
        )

    def train(self) -> None:
        self._run_async(
            "Treinar modelos",
            [
                self._python(),
                "-u",
                "src/supervised_learning.py",
                "--data",
                "ransom.csv",
                "--output",
                "results",
                "--model-dir",
                "models/ransomware",
            ],
        )

    def predict(self) -> None:
        report_path = self.project_root / "results" / "supervised_learning_report.json"
        models_dir = self.project_root / "models" / "ransomware"
        if not report_path.is_file():
            messagebox.showwarning(
                "Treino necessário",
                "Treina o modelo primeiro. O relatório do treino não existe.",
            )
            return
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
            selected_model = report["selected_model"]
            model_path = models_dir / f"{selected_model}.joblib"
        except (OSError, json.JSONDecodeError, KeyError, TypeError):
            messagebox.showerror(
                "Treino inválido",
                "O relatório do treino está inválido. Executa o treino novamente.",
            )
            return
        if not model_path.is_file():
            messagebox.showwarning(
                "Treino incompleto",
                f"O modelo selecionado ({selected_model}) não foi criado.\n"
                "Deixa o treino terminar e tenta novamente.",
            )
            return
        input_path = filedialog.askopenfilename(
            title="Selecionar CSV de entrada",
            initialdir=self.project_root,
            filetypes=[("CSV", "*.csv"), ("Todos os ficheiros", "*.*")],
        )
        if not input_path:
            return
        output_path = filedialog.asksaveasfilename(
            title="Guardar previsões",
            initialdir=self.project_root / "results",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
        )
        if not output_path:
            return
        self._run_async(
            "Fazer previsão",
            [
                self._python(),
                "-u",
                "src/predict.py",
                "--input",
                input_path,
                "--report",
                "results/supervised_learning_report.json",
                "--models-dir",
                "models/ransomware",
                "--output",
                output_path,
            ],
        )

    def start_api(self) -> None:
        if self.process is not None and self.process.poll() is None:
            messagebox.showinfo("API", "A API já está em execução.")
            return
        report_path = self.project_root / "results" / "supervised_learning_report.json"
        models_dir = self.project_root / "models" / "ransomware"
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
            selected_model = report["selected_model"]
            model_path = models_dir / f"{selected_model}.joblib"
        except (OSError, json.JSONDecodeError, KeyError, TypeError):
            messagebox.showwarning(
                "Treino necessário",
                "A API precisa de um relatório de treino válido. "
                "Executa o treino primeiro.",
            )
            return
        if not model_path.is_file():
            messagebox.showwarning(
                "Treino incompleto",
                f"O modelo selecionado ({selected_model}) não existe.\n"
                "Deixa o treino terminar com sucesso antes de iniciar a API.",
            )
            return
        try:
            self.process = subprocess.Popen(
                [self._python(), "-u", "src/serve.py"],
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env={**os.environ, "PYTHONUNBUFFERED": "1"},
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except OSError as exc:
            messagebox.showerror("Erro", f"Não foi possível iniciar a API:\n{exc}")
            return
        self._write("A iniciar API em http://127.0.0.1:8000...")

        def read_api_output() -> None:
            assert self.process is not None
            if self.process.stdout is not None:
                for line in self.process.stdout:
                    self.output_queue.put(line)
            return_code = self.process.wait()
            self.output_queue.put(
                f"API terminada: código {return_code}. "
                "Verifica o log acima.\n"
            )

        threading.Thread(target=read_api_output, daemon=True).start()


if __name__ == "__main__":
    RansomwareApp().mainloop()
