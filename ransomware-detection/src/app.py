"""Simple Windows GUI for training and using the ransomware classifier."""

from __future__ import annotations

import queue
import json
import os
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

COLORS = {
    "background": "#17191f",
    "surface": "#22252e",
    "surface_hover": "#303440",
    "text": "#e6e8ef",
    "muted": "#aeb4c2",
    "accent": "#6ea8fe",
    "border": "#3b404d",
    "selection": "#355f9c",
}


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
        self.geometry("980x680")
        self.minsize(760, 560)
        self.configure(background=COLORS["background"])
        self.project_root = find_project_root()
        self.dataset_path = self.project_root / "ransom.csv"
        self.output_queue: queue.Queue[str] = queue.Queue()
        self.process: subprocess.Popen[str] | None = None
        self.cv_folds = tk.IntVar(value=3)
        self.include_xgboost = tk.BooleanVar(value=False)
        self._configure_dark_theme()
        self._build_ui()
        self.after(100, self._drain_output)

    def _configure_dark_theme(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            ".",
            background=COLORS["background"],
            foreground=COLORS["text"],
            fieldbackground=COLORS["surface"],
            bordercolor=COLORS["border"],
            troughcolor=COLORS["surface"],
            focuscolor=COLORS["accent"],
            font=("Segoe UI", 9),
        )
        style.configure("TFrame", background=COLORS["background"])
        style.configure(
            "TLabel",
            background=COLORS["background"],
            foreground=COLORS["text"],
        )
        style.configure(
            "TButton",
            background=COLORS["surface"],
            foreground=COLORS["text"],
            borderwidth=1,
            padding=(10, 7),
            relief="flat",
        )
        style.map(
            "TButton",
            background=[
                ("disabled", COLORS["surface"]),
                ("pressed", COLORS["selection"]),
                ("active", COLORS["surface_hover"]),
            ],
            foreground=[("disabled", COLORS["muted"]), ("!disabled", COLORS["text"])],
            bordercolor=[("focus", COLORS["accent"])],
        )
        style.configure(
            "TScrollbar",
            background=COLORS["surface_hover"],
            troughcolor=COLORS["background"],
            bordercolor=COLORS["background"],
            arrowcolor=COLORS["text"],
        )
        style.configure(
            "TCheckbutton",
            background=COLORS["background"],
            foreground=COLORS["text"],
        )
        style.map(
            "TCheckbutton",
            background=[("active", COLORS["background"])],
            foreground=[("disabled", COLORS["muted"])],
        )

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

        dataset_frame = ttk.Frame(frame)
        dataset_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(dataset_frame, text="Dataset:").pack(side=tk.LEFT, padx=(0, 6))
        self.dataset_label = ttk.Label(
            dataset_frame, text=str(self.dataset_path), wraplength=700
        )
        self.dataset_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(
            dataset_frame, text="Escolher CSV", command=self.select_dataset
        ).pack(side=tk.RIGHT)

        actions = ttk.Frame(frame)
        actions.pack(fill=tk.X, pady=(0, 12))
        self.install_button = ttk.Button(
            actions,
            text="Instalar dependências",
            command=self.install_dependencies,
        )
        self.install_button.pack(side=tk.LEFT, padx=(0, 8))
        self.train_button = ttk.Button(
            actions, text="Treinar e avaliar modelos", command=self.train
        )
        self.train_button.pack(side=tk.LEFT, padx=(0, 8))
        self.predict_button = ttk.Button(
            actions, text="Fazer previsão", command=self.predict
        )
        self.predict_button.pack(side=tk.LEFT, padx=(0, 8))
        self.extract_button = ttk.Button(
            actions,
            text="Extrair .exe/.zip",
            command=self.extract_features,
        )
        self.extract_button.pack(side=tk.LEFT, padx=(0, 8))
        self.api_button = ttk.Button(
            actions, text="Iniciar API", command=self.start_api
        )
        self.api_button.pack(side=tk.LEFT)

        roadmap_actions = ttk.Frame(frame)
        roadmap_actions.pack(fill=tk.X, pady=(0, 10))
        self.eda_button = ttk.Button(
            roadmap_actions, text="Gerar EDA", command=self.run_eda
        )
        self.eda_button.pack(side=tk.LEFT, padx=(0, 8))
        self.preparation_button = ttk.Button(
            roadmap_actions,
            text="Relatório de preparação",
            command=self.run_preparation_report,
        )
        self.preparation_button.pack(side=tk.LEFT, padx=(0, 8))
        self.evaluation_button = ttk.Button(
            roadmap_actions,
            text="Ver avaliação e gráficos",
            command=self.show_evaluation,
        )
        self.evaluation_button.pack(side=tk.LEFT, padx=(0, 8))
        ttk.Label(roadmap_actions, text="Folds CV:").pack(side=tk.LEFT, padx=(8, 4))
        self.cv_spinbox = ttk.Spinbox(
            roadmap_actions,
            from_=2,
            to=10,
            width=4,
            textvariable=self.cv_folds,
        )
        self.cv_spinbox.pack(side=tk.LEFT)
        self.xgboost_checkbox = ttk.Checkbutton(
            roadmap_actions,
            text="Incluir XGBoost (opcional)",
            variable=self.include_xgboost,
        )
        self.xgboost_checkbox.pack(side=tk.LEFT, padx=(12, 0))

        artifact_actions = ttk.Frame(frame)
        artifact_actions.pack(fill=tk.X, pady=(0, 10))
        self.eda_folder_button = ttk.Button(
            artifact_actions,
            text="Abrir resultados EDA",
            command=lambda: self._open_path(
                self.project_root / "results" / "roadmap" / "eda"
            ),
        )
        self.eda_folder_button.pack(side=tk.LEFT, padx=(0, 8))
        self.preparation_report_button = ttk.Button(
            artifact_actions,
            text="Abrir relatório de preparação",
            command=lambda: self._open_path(
                self.project_root
                / "results"
                / "roadmap"
                / "preparation"
                / "data_preparation_report.json"
            ),
        )
        self.preparation_report_button.pack(side=tk.LEFT)

        ttk.Label(
            frame,
            text=(
                "A análise de EXE/ZIP é estática: não executa o ficheiro. "
                "Features comportamentais (rede/processos/registo) não podem "
                "ser extraídas estaticamente e a previsão pode ser menos fiável. "
                "EDA, preparação e treino guardam relatórios em results/roadmap "
                "ou results."
            ),
            wraplength=920,
        ).pack(anchor=tk.W, pady=(0, 8))

        self.log = tk.Text(
            frame,
            height=20,
            state=tk.DISABLED,
            wrap=tk.WORD,
            background=COLORS["surface"],
            foreground=COLORS["text"],
            insertbackground=COLORS["text"],
            selectbackground=COLORS["selection"],
            selectforeground=COLORS["text"],
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=1,
            highlightbackground=COLORS["border"],
            highlightcolor=COLORS["accent"],
            padx=10,
            pady=8,
            font=("Cascadia Mono", 9),
        )
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
        self._run_sequence_async(title, [command])

    def _run_sequence_async(
        self, title: str, commands: list[list[str]]
    ) -> None:
        if self.process is not None and self.process.poll() is None:
            messagebox.showwarning("Operação em curso", "Aguarda a operação atual terminar.")
            return

        self._set_buttons(False)
        self._write(f"\n> {title}")

        def worker() -> None:
            try:
                for command in commands:
                    self.output_queue.put(f"$ {' '.join(command)}\n")
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
                    if return_code != 0:
                        self.output_queue.put(
                            f"\nFalha: comando terminou com código {return_code}.\n"
                        )
                        return
                self.output_queue.put("\nConcluído: sucesso\n")
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
            self.extract_button,
            self.api_button,
            self.eda_button,
            self.preparation_button,
            self.evaluation_button,
            self.eda_folder_button,
            self.preparation_report_button,
            self.cv_spinbox,
            self.xgboost_checkbox,
        ):
            button.configure(state=state)

    def _python_command(self) -> list[str]:
        venv_python = self.project_root / ".venv" / "Scripts" / "python.exe"
        if venv_python.is_file():
            return [str(venv_python)]
        if getattr(sys, "frozen", False):
            launcher = shutil.which("py")
            if launcher:
                return [launcher, "-3.13"]
            python = shutil.which("python")
            if python:
                return [python]
            raise FileNotFoundError(
                "Python 3.13 não foi encontrado. Instala Python ou cria "
                "ransomware-detection\\.venv antes de usar o executável."
            )
        return [sys.executable]

    def select_dataset(self) -> None:
        path = filedialog.askopenfilename(
            title="Selecionar dataset CSV",
            initialdir=self.project_root,
            filetypes=[("Ficheiros CSV", "*.csv")],
        )
        if path:
            self.dataset_path = Path(path)
            self.dataset_label.configure(text=str(self.dataset_path))

    def install_dependencies(self) -> None:
        try:
            python_command = self._python_command()
        except FileNotFoundError as exc:
            messagebox.showerror("Python necessário", str(exc))
            return
        venv_python = self.project_root / ".venv" / "Scripts" / "python.exe"
        commands = []
        if getattr(sys, "frozen", False) and not venv_python.is_file():
            commands.append(python_command + ["-m", "venv", ".venv"])
            python_command = [str(venv_python)]
        commands.append(
            python_command + ["-m", "pip", "install", "-r", "requirements.txt"]
        )
        self._run_sequence_async("Instalar dependências", commands)

    def train(self) -> None:
        try:
            folds = self.cv_folds.get()
            if not 2 <= folds <= 10:
                raise ValueError
            python_command = self._python_command()
        except (tk.TclError, ValueError):
            messagebox.showerror(
                "Validação inválida",
                "O número de folds deve ser um inteiro entre 2 e 10.",
            )
            return
        except FileNotFoundError as exc:
            messagebox.showerror("Python necessário", str(exc))
            return
        command = python_command + [
            "-u",
            "src/supervised_learning.py",
            "--data",
            str(self.dataset_path),
            "--output",
            "results",
            "--model-dir",
            "models/ransomware",
            "--cv-folds",
            str(folds),
        ]
        if self.include_xgboost.get():
            command.append("--include-xgboost")
        self._run_async("Treinar e avaliar modelos", command)

    def run_eda(self) -> None:
        try:
            python_command = self._python_command()
        except FileNotFoundError as exc:
            messagebox.showerror("Python necessário", str(exc))
            return
        self._run_async(
            "Gerar análise exploratória (EDA)",
            python_command
            + [
                "-u",
                "src/roadmap_eda.py",
                "--data",
                str(self.dataset_path),
                "--output",
                "results/roadmap/eda",
            ],
        )

    def run_preparation_report(self) -> None:
        try:
            python_command = self._python_command()
        except FileNotFoundError as exc:
            messagebox.showerror("Python necessário", str(exc))
            return
        self._run_async(
            "Gerar relatório de preparação",
            python_command
            + [
                "-u",
                "src/data_preparation_report.py",
                "--data",
                str(self.dataset_path),
                "--output",
                "results/roadmap/preparation",
            ],
        )

    def show_evaluation(self) -> None:
        report_path = self.project_root / "results" / "supervised_learning_report.json"
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
            metrics = report["final_test_metrics"]
            cv = report["cross_validation"]
            selected_model = report["selected_model"]
            model_results = report.get("models", [])
        except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
            messagebox.showwarning(
                "Avaliação indisponível",
                "Não foi possível ler um relatório de treino válido. "
                "Executa primeiro «Treinar e avaliar modelos».\n\n"
                f"Detalhe: {exc}",
            )
            return

        details = [
            f"Modelo selecionado: {selected_model}",
            "",
            "Métricas no conjunto de teste reservado:",
        ]
        details.extend(
            f"  {name}: {value:.4f}"
            for name, value in metrics.items()
            if isinstance(value, (int, float))
        )
        details.extend(
            [
                "",
                f"Validação cruzada: {cv.get('folds', '—')} folds",
                f"Recall treino-CV: {cv.get('mean_train_recall_malware', float('nan')):.4f}",
                f"Recall validação-CV: {cv.get('mean_validation_recall_malware', float('nan')):.4f}",
                f"Gap de generalização: {cv.get('recall_generalization_gap', float('nan')):.4f}",
                f"Diagnóstico: {cv.get('fit_diagnostic', '—')}",
                f"Parâmetros afinados: {cv.get('best_parameters', {})}",
            ]
        )
        if model_results:
            details.extend(["", "Comparação dos modelos na validação:"])
            details.extend(
                (
                    f"  {result['model']}: recall={result['recall_malware']:.4f}, "
                    f"precision={result['precision_malware']:.4f}, "
                    f"F1={result['f1_malware']:.4f}, "
                    f"ROC-AUC={result['roc_auc']:.4f}"
                )
                for result in model_results
            )
        details.extend(["", "Os gráficos e o relatório completo estão na pasta results."])

        window = tk.Toplevel(self)
        window.title("Avaliação do modelo")
        window.configure(background=COLORS["background"])
        window.geometry("760x560")
        text = tk.Text(
            window,
            wrap=tk.WORD,
            background=COLORS["surface"],
            foreground=COLORS["text"],
            insertbackground=COLORS["text"],
            relief=tk.FLAT,
            padx=12,
            pady=10,
        )
        text.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        text.insert("1.0", "\n".join(details))
        text.configure(state=tk.DISABLED)
        buttons = ttk.Frame(window, padding=(12, 0, 12, 12))
        buttons.pack(fill=tk.X)
        ttk.Button(
            buttons,
            text="Abrir pasta de resultados",
            command=lambda: self._open_path(self.project_root / "results"),
        ).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(
            buttons,
            text="Abrir learning curve",
            command=lambda: self._open_path(
                self.project_root / "results" / "learning_curve.png"
            ),
        ).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(
            buttons,
            text="Abrir curva ROC",
            command=lambda: self._open_path(
                self.project_root / "results" / "supervised_roc_curve.png"
            ),
        ).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(
            buttons,
            text="Abrir matriz de confusão",
            command=lambda: self._open_path(
                self.project_root / "results" / "supervised_confusion_matrix.png"
            ),
        ).pack(side=tk.LEFT)

    def _open_path(self, path: Path) -> None:
        if not path.exists():
            messagebox.showwarning(
                "Ficheiro não encontrado",
                f"O artefacto ainda não existe:\n{path}",
            )
            return
        try:
            os.startfile(str(path))
        except OSError as exc:
            messagebox.showerror(
                "Não foi possível abrir",
                f"Falha ao abrir {path}:\n{exc}",
            )

    def predict(self) -> None:
        try:
            python_command = self._python_command()
        except FileNotFoundError as exc:
            messagebox.showerror("Python necessário", str(exc))
            return
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
            python_command
            + [
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

    def extract_features(self) -> None:
        try:
            python_command = self._python_command()
        except FileNotFoundError as exc:
            messagebox.showerror("Python necessário", str(exc))
            return
        input_path = filedialog.askopenfilename(
            title="Selecionar executável ou arquivo ZIP",
            initialdir=self.project_root,
            filetypes=[
                ("Executável ou ZIP", "*.exe *.zip"),
                ("Executável Windows", "*.exe"),
                ("Arquivo ZIP", "*.zip"),
            ],
        )
        if not input_path:
            return
        default_name = f"{Path(input_path).stem}_features.csv"
        output_path = filedialog.asksaveasfilename(
            title="Guardar features extraídas",
            initialdir=self.project_root / "results",
            initialfile=default_name,
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
        )
        if not output_path:
            return
        self._run_async(
            "Extrair features estáticas",
            python_command
            + [
                "-u",
                "src/extract_features.py",
                "--input",
                input_path,
                "--output",
                output_path,
                "--schema",
                "models/ransomware/feature_schema.json",
            ],
        )
        self._write(
            "Depois da extração terminar, usa «Fazer previsão» e seleciona o CSV gerado."
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
                self._python_command() + ["-u", "src/serve.py"],
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
