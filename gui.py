import os
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog, simpledialog
from pathlib import Path
import importlib.util

import question_generator as QUESTION_MODULE
import resume_parser as RESUME_MODULE
import final_report as REPORT_MODULE
import db_helper as DB_MODULE
import resume_screener as SCREENER_MODULE

from job_roles import JOB_ROLES


class InterviewQuestionApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AI Interview Simulation Platform")
        self.geometry("900x800")
        self.minsize(800, 600)
        self.resizable(True, True)
        
        # Calculate responsive values based on window size
        self.update_idletasks()
        self.wrap_length = max(400, self.winfo_width() - 100)

        self.api_key = None
        self.resume_data = None
        self.questions = []
        self.answers = []
        self.current_index = 0
        
        self._configure_styles()
        self._prompt_api_key()
        self._build_ui()
        self.bind("<Configure>", self._on_window_resize)

    def _configure_styles(self):
        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        self.colors = {
            "bg": "#f8fafc", "surface": "#ffffff", "primary": "#4f46e5", 
            "primary_hover": "#4338ca", "secondary": "#64748b", "text": "#0f172a", 
            "text_muted": "#475569", "border": "#e2e8f0"
        }
        self.configure(background=self.colors["bg"])

        self.style.configure(".", background=self.colors["bg"], foreground=self.colors["text"], font=("Segoe UI", 10))
        self.style.configure("TFrame", background=self.colors["bg"])
        self.style.configure("TLabelframe", background=self.colors["bg"], bordercolor=self.colors["border"])
        self.style.configure("TLabelframe.Label", font=("Segoe UI", 10, "bold"), foreground=self.colors["primary"], background=self.colors["bg"])
        self.style.configure("TButton", font=("Segoe UI", 9, "bold"), background=self.colors["primary"], foreground="#ffffff", borderwidth=0, focuscolor="none")
        self.style.map("TButton", background=[("active", self.colors["primary_hover"]), ("disabled", self.colors["border"])], foreground=[("disabled", self.colors["secondary"])])
        self.style.configure("Secondary.TButton", font=("Segoe UI", 9, "bold"), background=self.colors["secondary"], foreground="#ffffff")
        self.style.map("Secondary.TButton", background=[("active", "#475569"), ("disabled", self.colors["border"])], foreground=[("disabled", self.colors["secondary"])])
        self.style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), background="#10b981", foreground="#ffffff")
        self.style.map("Accent.TButton", background=[("active", "#059669"), ("disabled", self.colors["border"])], foreground=[("disabled", self.colors["secondary"])])
        self.style.configure("TCombobox", arrowcolor=self.colors["primary"])
        self.style.configure("TEntry", fieldbackground=self.colors["surface"], bordercolor=self.colors["border"])

    def _prompt_api_key(self):
        api_key = simpledialog.askstring("API Key", "Enter your Gemini API key (required):", show="*")
        if not api_key:
            messagebox.showerror("Missing API Key", "This application requires a Gemini API key to run.")
            self.destroy()
            return
        self.api_key = api_key.strip()
        os.environ["GEMINI_API_KEY"] = self.api_key

    def _on_window_resize(self, event=None):
        """Update responsive values on window resize."""
        self.wrap_length = max(400, self.winfo_width() - 100)
        if hasattr(self, 'question_label'):
            self.question_label.config(wraplength=self.wrap_length)
    
    def _build_ui(self):
        # Header
        header_frame = ttk.Frame(self)
        header_frame.pack(fill="x", padx=20, pady=(15, 10))
        ttk.Label(header_frame, text="AI Interview Simulator", font=("Segoe UI", 20, "bold"), foreground=self.colors["primary"]).pack(anchor="w")
        ttk.Label(header_frame, text="Upload your resume, choose a role, and simulate a tailored behavioral and technical interview.", font=("Segoe UI", 10), foreground=self.colors["text_muted"]).pack(anchor="w", pady=(2, 0))

        # Main container
        main_container = ttk.Frame(self)
        main_container.pack(fill="both", expand=True, padx=20, pady=(0, 5))
        main_container.columnconfigure(0, weight=1)
        main_container.rowconfigure(2, weight=1)

        # 1. Setup Frame
        setup_frame = ttk.LabelFrame(main_container, text="1. Setup and Preparation")
        setup_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10), ipady=5)
        setup_frame.columnconfigure(1, weight=1)

        ttk.Label(setup_frame, text="Resume PDF:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.resume_path_var = tk.StringVar()
        self.resume_entry = ttk.Entry(setup_frame, textvariable=self.resume_path_var)
        self.resume_entry.grid(row=0, column=1, padx=(5, 5), pady=5, sticky="ew")
        ttk.Button(setup_frame, text="Browse", style="Secondary.TButton", command=self._browse_resume).grid(row=0, column=2, padx=(0, 10), pady=5)

        ttk.Label(setup_frame, text="Job Role:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.role_menu = ttk.Combobox(setup_frame, values=[JOB_ROLES[k]["title"] for k in JOB_ROLES], state="readonly")
        self.role_menu.current(0)
        self.role_menu.grid(row=1, column=1, columnspan=2, padx=(5, 10), pady=5, sticky="ew")

        ttk.Label(setup_frame, text="Questions:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.num_questions_var = tk.IntVar(value=5)
        ttk.Spinbox(setup_frame, from_=1, to=20, textvariable=self.num_questions_var, width=6).grid(row=2, column=1, columnspan=2, padx=(5, 10), pady=5, sticky="w")

        self.parse_button = ttk.Button(setup_frame, text="Parse Resume & Prepare", style="Accent.TButton", command=self._parse_resume)
        self.parse_button.grid(row=3, column=0, columnspan=3, padx=10, pady=(8, 5), sticky="ew")

        # 2. Profile Frame
        self.info_frame = ttk.LabelFrame(main_container, text="2. Candidate Profile")
        self.info_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self.profile_text = tk.Text(self.info_frame, height=6, wrap="word", state="disabled", background="#ffffff", relief="flat", highlightthickness=1, highlightbackground=self.colors["border"], highlightcolor=self.colors["primary"], font=("Segoe UI", 9))
        self.profile_text.pack(fill="x", padx=10, pady=10)

        # 3. Interview Frame
        self.interview_frame = ttk.LabelFrame(main_container, text="3. Interview Simulation")
        self.interview_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 10))
        self.interview_frame.columnconfigure(0, weight=1)
        self.interview_frame.rowconfigure(1, weight=1)

        self.question_label = ttk.Label(self.interview_frame, text="No Interview Started Yet.", font=("Segoe UI", 11, "bold"), foreground=self.colors["text"], wraplength=self.wrap_length, justify="left")
        self.question_label.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 8))

        self.answer_text = scrolledtext.ScrolledText(self.interview_frame, wrap="word", font=("Segoe UI", 10), background="#ffffff", relief="flat", highlightthickness=1, highlightbackground=self.colors["border"], highlightcolor=self.colors["primary"])
        self.answer_text.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self.answer_text.bind("<Control-Return>", lambda e: self._submit_answer())

        # Buttons
        button_frame = ttk.Frame(self.interview_frame)
        button_frame.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 12))
        
        self.start_button = ttk.Button(button_frame, text="Start", command=self._start_interview, state="disabled")
        self.start_button.pack(side="left")
        self.submit_button = ttk.Button(button_frame, text="Submit (Ctrl+Enter)", command=self._submit_answer, state="disabled")
        self.submit_button.pack(side="left", padx=(10, 0))
        self.summary_button = ttk.Button(button_frame, text="Summary", command=self._show_summary, state="disabled")
        self.summary_button.pack(side="left", padx=(10, 0))
        self.reset_button = ttk.Button(button_frame, text="Reset", style="Secondary.TButton", command=self._reset_simulation)
        self.reset_button.pack(side="left", padx=(10, 0))
        self.exit_button = ttk.Button(button_frame, text="Exit", style="Secondary.TButton", command=self.destroy)
        self.exit_button.pack(side="right")

        # Status
        self.status_var = tk.StringVar(value="API key set.")
        self.status_label = ttk.Label(self, textvariable=self.status_var, foreground=self.colors["secondary"], font=("Segoe UI", 9))
        self.status_label.pack(anchor="w", padx=20, pady=(0, 10))

    def _browse_resume(self):
        path = filedialog.askopenfilename(title="Select resume PDF", filetypes=[("PDF files", "*.pdf"), ("All files", "*")])
        if path:
            self.resume_path_var.set(path)

    def _parse_resume(self):
        path = self.resume_path_var.get().strip()
        if not path or not Path(path).is_file():
            messagebox.showerror("Error", "Invalid resume file.")
            return
        
        role_title = self.role_menu.get()
        role_key = self._find_role_key(role_title)
        if not role_key:
            messagebox.showerror("Error", "Invalid role.")
            return

        self.resume_data = RESUME_MODULE.parse_resume(path)
        self.resume_data.update({
            "difficulty": QUESTION_MODULE.determine_difficulty(self.resume_data["experience_years"], role_key),
            "role_key": role_key,
            "role_title": role_title
        })

        # DB: Save candidate & skills
        name = Path(path).stem.replace("_", " ").replace("Resume", "").strip() or "Candidate"
        cid = DB_MODULE.save_candidate(name, f"{name.lower().replace(' ', '')}@example.com", self.resume_data["experience_years"])
        self.resume_data["candidate_id"] = cid
        if cid:
            DB_MODULE.save_skills(cid, self.resume_data["hard_skills"], self.resume_data["soft_skills"])

        # Resume Screening (Linear Regression)
        screening_result = SCREENER_MODULE.screen_resume(self.resume_data, role_key)
        self.resume_data["screening"] = screening_result
        report_text = SCREENER_MODULE.format_screening_report(screening_result, role_title)

        self._render_profile()

        if screening_result["passed"]:
            # Candidate qualifies - allow interview
            self.start_button.config(state="normal")
            self.question_label.config(
                text=f"SCREENING PASSED ({screening_result['match_score']}% Match) - Click Start Interview."
            )
            self.status_var.set(f"Resume screened: {screening_result['match_score']}% match - PASSED.")
            self._show_screening_report(report_text, passed=True)
        else:
            # Candidate does not qualify - block interview
            self.start_button.config(state="disabled")
            self.question_label.config(
                text=f"SCREENING FAILED ({screening_result['match_score']}% match) - You do not qualify for this role."
            )
            self.status_var.set(f"Resume screened: {screening_result['match_score']}% match - REJECTED.")
            self._show_screening_report(report_text, passed=False)
            messagebox.showwarning(
                "Resume Rejected",
                f"Your resume matched only {screening_result['match_score']}% to the {role_title} role.\n"
                f"Minimum required: 60%.\n\n"
                f"You do not qualify for this position.\n"
                f"Please update your resume or select a different role."
            )

    def _show_screening_report(self, report_text, passed=True):
        """Opens a window with the detailed screening report."""
        report_window = tk.Toplevel(self)
        report_window.title("Resume Screening Report")
        report_window.geometry(f"{min(650, self.winfo_width() - 20)}x{min(500, self.winfo_height() - 50)}")
        report_window.minsize(500, 350)
        report_window.configure(background=self.colors["bg"])

        title_color = "#10b981" if passed else "#ef4444"
        title_text = "Screening Result: PASSED" if passed else "Screening Result: REJECTED"
        ttk.Label(
            report_window, text=title_text,
            font=("Segoe UI", 14, "bold"), foreground=title_color
        ).pack(anchor="w", padx=20, pady=(15, 10))

        report_widget = scrolledtext.ScrolledText(
            report_window, wrap="word",
            font=("Consolas" if os.name == 'nt' else "Courier", 10),
            background="#ffffff", relief="flat",
            highlightthickness=1,
            highlightbackground=self.colors["border"],
            highlightcolor=self.colors["primary"]
        )
        report_widget.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        report_widget.insert(tk.END, report_text)
        report_widget.config(state="disabled")

        ttk.Button(
            report_window, text="Close", style="Secondary.TButton",
            command=report_window.destroy
        ).pack(anchor="e", padx=20, pady=(0, 15))

        # Force window rendering and focus
        report_window.update_idletasks()
        report_window.update()
        report_window.lift()
        report_window.focus_force()

    def _render_profile(self):
        self.profile_text.config(state="normal")
        self.profile_text.delete("1.0", tk.END)
        exp = self.resume_data.get('experience_years', 0)
        try:
            exp_str = f"{exp:g}"
        except Exception:
            exp_str = str(exp)

        screening_info = ""
        if self.resume_data and "screening" in self.resume_data:
            scr = self.resume_data.get("screening", {})
            status = "PASSED" if scr.get("passed") else "REJECTED"
            screening_info = f"\nScreening Status: {status} ({scr.get('match_score', 0)}% match)"

        text = (
            f"Role: {self.resume_data.get('role_title', 'N/A')}\n"
            f"Experience: {exp_str} Year/s | Level: {self.resume_data.get('difficulty', '').upper()}\n"
            f"Hard Skills: {', '.join(self.resume_data.get('hard_skills', [])) or 'None'}\n"
            f"Soft Skills: {', '.join(self.resume_data.get('soft_skills', [])) or 'None'}"
            f"{screening_info}"
        )
        self.profile_text.insert(tk.END, text)
        self.profile_text.config(state="disabled")

    def _start_interview(self):
        if not self.resume_data:
            messagebox.showwarning("Error", "Parse a resume first.")
            return
        try:
            num_q = int(self.num_questions_var.get())
            if num_q <= 0:
                num_q = 5
        except:
            num_q = 5
        try:
            self.questions = QUESTION_MODULE.generate_questions(self.resume_data, self.resume_data["role_key"], self.resume_data["difficulty"], num_questions=num_q)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate questions: {e}")
            return
        if not self.questions:
            messagebox.showerror("Error", "No questions generated.")
            return
        
        # DB: Save session
        cid = self.resume_data.get("candidate_id")
        if cid:
            self.session_id = DB_MODULE.create_session(cid, self.resume_data["role_title"], self.resume_data["difficulty"])
            self.db_question_ids = DB_MODULE.save_questions(self.questions, self.resume_data["difficulty"])
        
        self.answers = []
        self.current_index = 0
        self.start_button.config(state="disabled")
        self.submit_button.config(state="normal")
        self.summary_button.config(state="disabled")
        self._display_question()
        self.status_var.set("Interview started. Answer each question.")

    def _display_question(self):
        q = self.questions[self.current_index]
        self.question_label.config(text=f"Q{self.current_index + 1}/{len(self.questions)}: {q}")
        self.answer_text.delete("1.0", tk.END)
        self.answer_text.focus()

    def _submit_answer(self):
        if self.submit_button.cget("state") == "disabled":
            return "break"
        answer = self.answer_text.get("1.0", tk.END).strip()
        if not answer:
            if not messagebox.askyesno("Skip?", "Skip this question?"):
                return "break"
            answer = "[Skipped]"
        self.answers.append({"question": self.questions[self.current_index], "answer": answer})
        self.current_index += 1
        if self.current_index < len(self.questions):
            self._display_question()
        else:
            self._finish_interview()
        return "break"

    def _finish_interview(self):
        self.submit_button.config(state="disabled")
        self.start_button.config(state="normal")
        self.summary_button.config(state="normal")
        self.status_var.set("Complete. Click Summary or Reset.")

    def _show_summary(self):
        if not self.answers:
            messagebox.showwarning("No answers", "No interview data to evaluate.")
            return

        self.status_var.set("Evaluating responses...")
        self.update()

        role_info = JOB_ROLES[self.resume_data["role_key"]]
        difficulty = self.resume_data["difficulty"]
        questions = [e["question"] for e in self.answers]
        answers_only = [e["answer"] for e in self.answers]
        try:
            evaluations = REPORT_MODULE.grade_answers(questions, answers_only, role_info, difficulty)
        except Exception as e:
            messagebox.showerror("Evaluation error", f"Evaluation failed: {e}")
            self.status_var.set("Evaluation failed.")
            return

        # Build report
        report = ["=========================================================", "OFFICIAL INTERVIEW PERFORMANCE REPORT", "=========================================================",
                  f"Job Role: {role_info['title']}", f"Target Level: {difficulty.upper()}", f"Experience: {self.resume_data['experience_years']:g} Year/s", "-" * 57]
        
        total_score = 0
        for idx, (q, a, e) in enumerate(zip(questions, answers_only, evaluations), 1):
            report.extend([f"\nQ{idx}: {q}", f"Answer: {a}", f"Eval: {e}"])
            try:
                score = float(e.split("Score:")[1].split("/10")[0].strip())
                total_score += score
            except:
                total_score += 5

        avg_score = total_score / len(self.answers)
        status = "Highly Recommended!" if avg_score >= 8 else ("Recommended with training" if avg_score >= 5 else "Needs Improvement")
        report.extend(["=" * 57, f"OVERALL SCORE: {avg_score:.1f}/10", f"Status: {status}", "=" * 57])

        # Save to DB
        if hasattr(self, 'session_id') and self.session_id:
            valid_qids = self.db_question_ids[:len(answers_only)]
            DB_MODULE.save_responses(self.session_id, valid_qids, answers_only[:len(valid_qids)])
            DB_MODULE.save_summary(self.session_id, avg_score, "Tuned to skills: " + ", ".join(self.resume_data.get("hard_skills", [])), f"Level: {difficulty}", status)

        # Show report
        report_window = tk.Toplevel(self)
        report_window.title("Performance Report")
        report_window.geometry(f"{min(800, self.winfo_width() - 20)}x{min(700, self.winfo_height() - 50)}")
        report_window.minsize(600, 400)
        report_window.configure(background=self.colors["bg"])

        ttk.Label(report_window, text="Performance Evaluation", font=("Segoe UI", 14, "bold"), foreground=self.colors["primary"]).pack(anchor="w", padx=20, pady=(15, 10))
        
        report_text = scrolledtext.ScrolledText(report_window, wrap="word", font=("Consolas" if os.name == 'nt' else "Courier", 10), background="#ffffff", relief="flat", highlightthickness=1, highlightbackground=self.colors["border"], highlightcolor=self.colors["primary"])
        report_text.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        report_text.insert(tk.END, "\n".join(report))
        report_text.config(state="disabled")

        ttk.Button(report_window, text="Close", style="Secondary.TButton", command=report_window.destroy).pack(anchor="e", padx=20, pady=(0, 15))

        self.question_label.config(text="Interview Complete")
        self.answer_text.delete("1.0", tk.END)
        self.answer_text.insert(tk.END, "Thank you for completing the simulation.")
        self.status_var.set("Report generated successfully.")

    def _reset_simulation(self):
        self.resume_data = self.questions = self.answers = None
        self.current_index = 0
        self.resume_path_var.set("")
        self.profile_text.config(state="normal")
        self.profile_text.delete("1.0", tk.END)
        self.profile_text.config(state="disabled")
        self.question_label.config(text="No interview started.")
        self.answer_text.delete("1.0", tk.END)
        self.start_button.config(state="disabled")
        self.submit_button.config(state="disabled")
        self.summary_button.config(state="disabled")
        self.status_var.set("Reset complete.")

    def _find_role_key(self, title):
        for key, config in JOB_ROLES.items():
            if config["title"] == title:
                return key
        return None


if __name__ == "__main__":
    app = InterviewQuestionApp()
    app.mainloop()
