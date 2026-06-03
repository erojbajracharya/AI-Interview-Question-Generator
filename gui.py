import os
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog, simpledialog
from pathlib import Path
import importlib.util

import question_generator as QUESTION_MODULE
import resume_parser as RESUME_MODULE
import final_report as REPORT_MODULE
import db_helper as DB_MODULE

from job_roles import JOB_ROLES


class InterviewQuestionApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AI Interview Simulation Platform")
        
        # Window size designed to support detailed reports and layouts
        self.geometry("860x780")
        self.minimum_size = (840, 720)
        self.minsize(840, 720)
        self.resizable(True, True)

        self.api_key = None
        self.resume_data = None
        self.questions = []
        self.answers = []
        self.current_index = 0

        self._configure_styles()
        self._prompt_api_key()
        self._build_ui()

    def _configure_styles(self):
        # Configure a premium, modern design theme
        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        self.colors = {
            "bg": "#f8fafc",          # slate-50
            "surface": "#ffffff",     # white
            "primary": "#4f46e5",     # indigo-600
            "primary_hover": "#4338ca", # indigo-700
            "secondary": "#64748b",   # slate-500
            "text": "#0f172a",        # slate-900
            "text_muted": "#475569",  # slate-600
            "border": "#e2e8f0"       # slate-200
        }

        self.configure(background=self.colors["bg"])

        self.style.configure(".", background=self.colors["bg"], foreground=self.colors["text"], font=("Segoe UI", 10))
        self.style.configure("TFrame", background=self.colors["bg"])
        self.style.configure("Card.TFrame", background=self.colors["surface"], relief="solid", borderwidth=1)
        self.style.configure("TLabelframe", background=self.colors["bg"], bordercolor=self.colors["border"])
        self.style.configure("TLabelframe.Label", font=("Segoe UI", 10, "bold"), foreground=self.colors["primary"], background=self.colors["bg"])

        self.style.configure("TButton", font=("Segoe UI", 9, "bold"), background=self.colors["primary"], foreground="#ffffff", borderwidth=0, focuscolor="none")
        self.style.map("TButton",
            background=[("active", self.colors["primary_hover"]), ("disabled", self.colors["border"])],
            foreground=[("disabled", self.colors["secondary"])]
        )

        self.style.configure("Secondary.TButton", font=("Segoe UI", 9, "bold"), background=self.colors["secondary"], foreground="#ffffff")
        self.style.map("Secondary.TButton",
            background=[("active", "#475569"), ("disabled", self.colors["border"])],
            foreground=[("disabled", self.colors["secondary"])]
        )

        self.style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), background="#10b981", foreground="#ffffff")  # emerald-500
        self.style.map("Accent.TButton",
            background=[("active", "#059669"), ("disabled", self.colors["border"])],
            foreground=[("disabled", self.colors["secondary"])]
        )

        self.style.configure("TCombobox", arrowcolor=self.colors["primary"])
        self.style.configure("TEntry", fieldbackground=self.colors["surface"], bordercolor=self.colors["border"])

    def _prompt_api_key(self):
        api_key = simpledialog.askstring("API Key", "Enter your Gemini API key for better question generation (optional):", show="*")
        if api_key:
            self.api_key = api_key.strip()
            os.environ["GEMINI_API_KEY"] = self.api_key

    def _build_ui(self):
        # Header panel
        header_frame = ttk.Frame(self)
        header_frame.pack(fill="x", padx=20, pady=(15, 10))

        header = ttk.Label(header_frame, text="AI Interview Simulator", font=("Segoe UI", 20, "bold"), foreground=self.colors["primary"])
        header.pack(anchor="w")

        description = ttk.Label(header_frame, text="Upload your resume, choose a role, and simulate a tailored behavioral and technical interview.", font=("Segoe UI", 10), foreground=self.colors["text_muted"])
        description.pack(anchor="w", pady=(2, 0))

        # Main container
        main_container = ttk.Frame(self)
        main_container.pack(fill="both", expand=True, padx=20, pady=(0, 5))
        
        main_container.columnconfigure(0, weight=1)
        main_container.rowconfigure(0, weight=0) # Setup Frame
        main_container.rowconfigure(1, weight=0) # Profile Frame
        main_container.rowconfigure(2, weight=1) # Interview Simulation Frame

        # 1. Setup/File Import Frame
        setup_frame = ttk.LabelFrame(main_container, text="1. Setup and Preparation")
        setup_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10), ipady=5)
        setup_frame.columnconfigure(1, weight=1)

        ttk.Label(setup_frame, text="Resume PDF:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.resume_path_var = tk.StringVar()
        self.resume_entry = ttk.Entry(setup_frame, textvariable=self.resume_path_var)
        self.resume_entry.grid(row=0, column=1, padx=(5, 5), pady=5, sticky="ew")
        
        browse_button = ttk.Button(setup_frame, text="Browse File", style="Secondary.TButton", command=self._browse_resume)
        browse_button.grid(row=0, column=2, padx=(0, 10), pady=5)

        ttk.Label(setup_frame, text="Job Role:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.role_menu = ttk.Combobox(setup_frame, values=[JOB_ROLES[key]["title"] for key in JOB_ROLES], state="readonly")
        self.role_menu.current(0)
        self.role_menu.grid(row=1, column=1, columnspan=2, padx=(5, 10), pady=5, sticky="ew")

        # Select Number of Questions
        ttk.Label(setup_frame, text="Questions count:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.num_questions_var = tk.IntVar(value=5)
        self.num_questions_spin = ttk.Spinbox(setup_frame, from_=1, to=20, textvariable=self.num_questions_var, width=6)
        self.num_questions_spin.grid(row=2, column=1, columnspan=2, padx=(5, 10), pady=5, sticky="w")

        self.parse_button = ttk.Button(setup_frame, text="Parse Resume & Prepare Interview", style="Accent.TButton", command=self._parse_resume)
        self.parse_button.grid(row=3, column=0, columnspan=3, padx=10, pady=(8, 5), sticky="ew")

        # 2. Candidate Profile Frame
        self.info_frame = ttk.LabelFrame(main_container, text="2. Candidate Profile")
        self.info_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        
        self.profile_text = tk.Text(
            self.info_frame, 
            height=6, 
            wrap="word", 
            state="disabled", 
            background="#ffffff", 
            relief="flat", 
            highlightthickness=1, 
            highlightbackground=self.colors["border"],
            highlightcolor=self.colors["primary"],
            font=("Segoe UI", 9)
        )
        self.profile_text.pack(fill="x", padx=10, pady=10)

        # 3. Interview Simulation Frame
        self.interview_frame = ttk.LabelFrame(main_container, text="3. Interview Simulation")
        self.interview_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 10))
        self.interview_frame.columnconfigure(0, weight=1)
        self.interview_frame.rowconfigure(1, weight=1)

        self.question_label = ttk.Label(
            self.interview_frame, 
            text="No interview started yet.", 
            font=("Segoe UI", 11, "bold"), 
            wraplength=760,
            foreground=self.colors["text"]
        )
        self.question_label.grid(row=0, column=0, sticky="w", padx=12, pady=(12, 8))

        self.answer_text = scrolledtext.ScrolledText(
            self.interview_frame, 
            wrap="word", 
            font=("Segoe UI", 10),
            background="#ffffff",
            relief="flat",
            highlightthickness=1,
            highlightbackground=self.colors["border"],
            highlightcolor=self.colors["primary"]
        )
        self.answer_text.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        
        self.answer_text.bind("<Control-Return>", lambda event: self._submit_answer())

        # Buttons Frame
        button_frame = ttk.Frame(self.interview_frame)
        button_frame.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 12))

        self.start_button = ttk.Button(button_frame, text="Start Interview", command=self._start_interview, state="disabled")
        self.start_button.pack(side="left")

        self.submit_button = ttk.Button(button_frame, text="Submit Answer (Ctrl+Enter)", command=self._submit_answer, state="disabled")
        self.submit_button.pack(side="left", padx=(10, 0))

        self.summary_button = ttk.Button(button_frame, text="Generate Final Summary", command=self._show_summary, state="disabled")
        self.summary_button.pack(side="left", padx=(10, 0))

        self.reset_button = ttk.Button(button_frame, text="Reset", style="Secondary.TButton", command=self._reset_simulation)
        self.reset_button.pack(side="left", padx=(10, 0))

        self.exit_button = ttk.Button(button_frame, text="Exit", style="Secondary.TButton", command=self.destroy)
        self.exit_button.pack(side="right")

        # Status Label
        self.status_var = tk.StringVar(value="API key set." if self.api_key else "Running with built-in fallback questions.")
        self.status_label = ttk.Label(self, textvariable=self.status_var, foreground=self.colors["secondary"], font=("Segoe UI", 9))
        self.status_label.pack(anchor="w", padx=20, pady=(0, 10))

    def _browse_resume(self):
        path = filedialog.askopenfilename(title="Select resume PDF", filetypes=[("PDF files", "*.pdf"), ("All files", "*")])
        if path:
            self.resume_path_var.set(path)

    def _parse_resume(self):
        resume_path = self.resume_path_var.get().strip()
        if not resume_path:
            messagebox.showwarning("Missing resume", "Please choose a resume PDF before parsing.")
            return

        if not Path(resume_path).is_file():
            messagebox.showerror("File error", "The selected resume file does not exist.")
            return

        role_title = self.role_menu.get()
        role_key = self._find_role_key(role_title)
        if not role_key:
            messagebox.showerror("Role error", "Please select a valid role.")
            return

        self.resume_data = RESUME_MODULE.parse_resume(resume_path)
        difficulty = QUESTION_MODULE.determine_difficulty(self.resume_data["experience_years"], role_key)
        self.resume_data["difficulty"] = difficulty
        self.resume_data["role_key"] = role_key
        self.resume_data["role_title"] = role_title

        # --- DB Save: Candidate & Skills ---
        # Try to extract candidate's name from file name or use default
        candidate_name = Path(resume_path).stem.replace("_", " ").replace("Resume", "").strip()
        if not candidate_name:
            candidate_name = "Candidate"
        
        # Save to DB
        candidate_id = DB_MODULE.save_candidate(
            full_name=candidate_name,
            email=f"{candidate_name.lower().replace(' ', '')}@example.com",
            experience_years=self.resume_data["experience_years"]
        )
        self.resume_data["candidate_id"] = candidate_id
        
        if candidate_id:
            DB_MODULE.save_skills(
                candidate_id=candidate_id,
                hard_skills=self.resume_data["hard_skills"],
                soft_skills=self.resume_data["soft_skills"]
            )
        # -----------------------------------

        self._render_profile()
        self.start_button.config(state="normal")
        self.submit_button.config(state="disabled")
        self.summary_button.config(state="disabled")
        self.question_label.config(text="Resume parsed successfully. Click \"Start Interview\" to begin.")
        self.status_var.set("Resume parsing complete & saved to DB. Ready to simulate interview.")

    def _render_profile(self):
        self.profile_text.config(state="normal")
        self.profile_text.delete("1.0", tk.END)
        self.profile_text.insert(tk.END, f"=================== CANDIDATE PROFILE ===================\n")
        self.profile_text.insert(tk.END, f"Role Target  : {self.resume_data['role_title']}\n")
        self.profile_text.insert(tk.END, f"Experience   : {self.resume_data['experience_years']} years\n")
        self.profile_text.insert(tk.END, f"Difficulty   : {self.resume_data['difficulty'].upper()}\n")
        self.profile_text.insert(tk.END, f"Hard Skills  : {', '.join(self.resume_data['hard_skills']) or 'None detected'}\n")
        self.profile_text.insert(tk.END, f"Soft Skills  : {', '.join(self.resume_data['soft_skills']) or 'None detected'}\n")
        self.profile_text.insert(tk.END, f"=========================================================\n")
        self.profile_text.config(state="disabled")

    def _start_interview(self):
        if not self.resume_data:
            messagebox.showwarning("Start error", "Parse a resume first before starting the interview.")
            return

        # Read questions count dynamically from the Spinbox
        try:
            num_questions = int(self.num_questions_var.get())
            if num_questions <= 0:
                num_questions = 5
        except Exception:
            num_questions = 5

        try:
            self.questions = QUESTION_MODULE.generate_questions(
                self.resume_data,
                self.resume_data["role_key"],
                self.resume_data["difficulty"],
                num_questions=num_questions
            )
        except Exception as e:
            messagebox.showerror("Question error", f"Could not generate interview questions: {e}")
            return

        if not self.questions:
            messagebox.showerror("Question error", "Could not generate interview questions.")
            return

        # --- DB Save: Interview Session & Questions ---
        candidate_id = self.resume_data.get("candidate_id")
        self.session_id = None
        self.db_question_ids = []
        if candidate_id:
            self.session_id = DB_MODULE.create_session(
                candidate_id=candidate_id,
                job_role=self.resume_data["role_title"],
                difficulty=self.resume_data["difficulty"]
            )
            self.db_question_ids = DB_MODULE.save_questions(
                question_texts=self.questions,
                difficulty=self.resume_data["difficulty"]
            )
        # -----------------------------------------------

        self.answers = []
        self.current_index = 0
        self.start_button.config(state="disabled")
        self.submit_button.config(state="normal")
        self.summary_button.config(state="disabled")
        self._display_question()
        self.status_var.set("Interview started. Answer each question and click Submit.")

    def _get_question_count(self):
        try:
            return int(self.num_questions_var.get())
        except Exception:
            return 5

    def _display_question(self):
        question = self.questions[self.current_index]
        self.question_label.config(text=f"Question {self.current_index + 1} / {len(self.questions)}:\n{question}")
        self.answer_text.delete("1.0", tk.END)
        self.answer_text.focus()
        self.submit_button.config(state="normal")
        self.summary_button.config(state="disabled")

    def _submit_answer(self):
        if self.submit_button.cget("state") == "disabled":
            return "break"
            
        answer = self.answer_text.get("1.0", tk.END).strip()
        if not answer:
            if not messagebox.askyesno("Skip answer?", "You have not entered a response. Do you want to skip this question?"):
                return "break"
            answer = "[No response]"

        self.answers.append({
            "question": self.questions[self.current_index],
            "answer": answer,
        })

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
        self.status_var.set("Interview complete. Click Generate Final Summary or Exit.")

    def _show_summary(self):
        if not self.answers:
            messagebox.showwarning("No answers", "No interview data to evaluate.")
            return

        self.status_var.set("Evaluating responses and generating final report summary...")
        self.update()

        # Grade responses using the logic from final-report.py
        role_info = JOB_ROLES[self.resume_data["role_key"]]
        difficulty = self.resume_data["difficulty"]
        questions = [entry["question"] for entry in self.answers]
        answers_only = [entry["answer"] for entry in self.answers]
        
        # Invoke grade_answers from final-report.py
        evaluations = REPORT_MODULE.grade_answers(questions, answers_only, role_info, difficulty)

        # Build official interview performance report output
        report = []
        report.append("=========================================================")
        report.append("             OFFICIAL INTERVIEW PERFORMANCE REPORT       ")
        report.append("=========================================================")
        report.append(f"Job Role:             {role_info['title']}")
        report.append(f"Target Level:         {difficulty.upper()}")
        report.append(f"Candidate Experience: {self.resume_data['experience_years']} years")
        report.append("-" * 57)

        total_score = 0
        for idx, (q, a, eval_str) in enumerate(zip(questions, answers_only, evaluations), 1):
            report.append(f"\nQ{idx}: {q}")
            report.append(f"Your Answer: {a}")
            report.append(f"Evaluation:  {eval_str}")
            
            score = 0
            if "Score:" in eval_str:
                try:
                    score = float(eval_str.split("Score:")[1].split("/10")[0].strip())
                except Exception:
                    score = 5
            total_score += score

        avg_score = total_score / len(self.answers)
        report.append("\n" + "=" * 57)
        report.append(f"OVERALL SCORE: {avg_score:.1f}/10")
        
        if avg_score >= 8:
            status = "Highly Recommended for hire!"
        elif avg_score >= 5:
            status = "Recommended with some training."
        else:
            status = "Needs improvement."
        report.append(f"Status:        {status}")
        report.append("=" * 57)

        # --- DB Save: Responses & Summary ---
        if hasattr(self, 'session_id') and self.session_id:
            # Save responses (zip will match up to the shorter list length safely)
            valid_qids = self.db_question_ids[:len(answers_only)]
            valid_answers = answers_only[:len(valid_qids)]
            DB_MODULE.save_responses(
                session_id=self.session_id,
                question_ids=valid_qids,
                answer_texts=valid_answers
            )
            # Save summary evaluation
            strengths = "Tuned to job role skills: " + ", ".join(self.resume_data.get("hard_skills", []))
            weaknesses = "Evaluated on difficulty: " + difficulty
            DB_MODULE.save_summary(
                session_id=self.session_id,
                overall_score=avg_score,
                strengths=strengths,
                weaknesses=weaknesses,
                final_feedback=status
            )
        # ------------------------------------

        # Open a new window and show the report to the user
        report_window = tk.Toplevel(self)
        report_window.title("Interview Performance Report")
        report_window.geometry("700x600")
        report_window.minsize(600, 500)
        report_window.configure(background=self.colors["bg"])

        # Title Label in the new window
        title_lbl = ttk.Label(report_window, text="Performance Evaluation Summary", font=("Segoe UI", 14, "bold"), foreground=self.colors["primary"])
        title_lbl.pack(anchor="w", padx=20, pady=(15, 10))

        # ScrolledText for report content
        report_text = scrolledtext.ScrolledText(
            report_window, 
            wrap="word", 
            font=("Consolas" if os.name == 'nt' else "Courier", 10),
            background="#ffffff",
            relief="flat",
            highlightthickness=1,
            highlightbackground=self.colors["border"],
            highlightcolor=self.colors["primary"]
        )
        report_text.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        
        report_text.insert(tk.END, "\n".join(report))
        report_text.config(state="disabled")

        # Close button
        close_btn = ttk.Button(report_window, text="Close Report", style="Secondary.TButton", command=report_window.destroy)
        close_btn.pack(anchor="e", padx=20, pady=(0, 15))

        # Reset main view inputs and status
        self.question_label.config(text="Interview Evaluation Complete")
        self.answer_text.delete("1.0", tk.END)
        self.answer_text.insert(tk.END, "Thank you for completing the simulation. Your detailed performance evaluation has been opened in a new window.")
        self.status_var.set("Final summary report generated successfully.")

    def _reset_simulation(self):
        self.resume_data = None
        self.questions = []
        self.answers = []
        self.current_index = 0
        self.resume_path_var.set("")
        self.profile_text.config(state="normal")
        self.profile_text.delete("1.0", tk.END)
        self.profile_text.config(state="disabled")
        self.question_label.config(text="No interview started yet.")
        self.answer_text.delete("1.0", tk.END)
        self.start_button.config(state="disabled")
        self.submit_button.config(state="disabled")
        self.summary_button.config(state="disabled")
        self.status_var.set("Reset complete. Upload a resume to begin.")

    def _find_role_key(self, title):
        for key, config in JOB_ROLES.items():
            if config["title"] == title:
                return key
        return None


if __name__ == "__main__":
    app = InterviewQuestionApp()
    app.mainloop()
