# db_helper.py
"""
MySQL Database Helper for the AI Interview Question Generator.
Provides functions to save and retrieve data for each stage of the
interview workflow: candidate -> skills -> session -> questions -> responses -> summary.

Requirements:
    pip install mysql-connector-python
"""

import mysql.connector
from mysql.connector import Error
from datetime import datetime


# ── Database connection settings ─────────────────────────────────────────────
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "afno mysql password hala",        # ← Set your MySQL root password here
    "database": "ai_interview_db"
}

_db_initialized = False  # Track whether we've already checked/created the DB


def initialize_database():
    """Create the database and all tables if they do not already exist."""
    global _db_initialized
    if _db_initialized:
        return True

    try:
        # Step 1 – Connect to MySQL server (no database selected)
        conn = mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"]
        )
        cursor = conn.cursor()

        # Step 2 – Create the database
        cursor.execute("CREATE DATABASE IF NOT EXISTS ai_interview_db")
        cursor.execute("USE ai_interview_db")

        # Step 3 – Create all tables
        table_statements = [
            """
            CREATE TABLE IF NOT EXISTS Candidates (
                candidate_id    INT AUTO_INCREMENT PRIMARY KEY,
                full_name       VARCHAR(100)  NOT NULL,
                email           VARCHAR(100)  UNIQUE,
                phone           VARCHAR(20),
                education       VARCHAR(255),
                experience_years DECIMAL(4,1) DEFAULT 0.0
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS Skills (
                skill_id      INT AUTO_INCREMENT PRIMARY KEY,
                candidate_id  INT NOT NULL,
                skill_name    VARCHAR(100) NOT NULL,
                skill_type    ENUM('Hard Skill', 'Soft Skill') NOT NULL,
                FOREIGN KEY (candidate_id) REFERENCES Candidates(candidate_id)
                    ON DELETE CASCADE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS InterviewSessions (
                session_id      INT AUTO_INCREMENT PRIMARY KEY,
                candidate_id    INT NOT NULL,
                job_role        VARCHAR(100) NOT NULL,
                difficulty      ENUM('Easy', 'Medium', 'Hard') NOT NULL,
                interview_date  DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (candidate_id) REFERENCES Candidates(candidate_id)
                    ON DELETE CASCADE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS Questions (
                question_id     INT AUTO_INCREMENT PRIMARY KEY,
                question_text   TEXT NOT NULL,
                difficulty      ENUM('Easy', 'Medium', 'Hard') NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS Responses (
                response_id   INT AUTO_INCREMENT PRIMARY KEY,
                session_id    INT NOT NULL,
                question_id   INT NOT NULL,
                answer_text   TEXT NOT NULL,
                FOREIGN KEY (session_id)  REFERENCES InterviewSessions(session_id)
                    ON DELETE CASCADE,
                FOREIGN KEY (question_id) REFERENCES Questions(question_id)
                    ON DELETE CASCADE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS InterviewSummary (
                summary_id      INT AUTO_INCREMENT PRIMARY KEY,
                session_id      INT NOT NULL UNIQUE,
                overall_score   DECIMAL(5,2),
                strengths       TEXT,
                weaknesses      TEXT,
                final_feedback  TEXT,
                FOREIGN KEY (session_id) REFERENCES InterviewSessions(session_id)
                    ON DELETE CASCADE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS StoredQuestions (
                id             INT AUTO_INCREMENT PRIMARY KEY,
                job_role       VARCHAR(100) NOT NULL,
                difficulty     ENUM('Easy', 'Medium', 'Hard') NOT NULL,
                topic          VARCHAR(100),
                question       TEXT NOT NULL,
                answer         TEXT,
                created_at     DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        ]

        for stmt in table_statements:
            cursor.execute(stmt)

        # Seed default questions if StoredQuestions table is empty
        seed_default_questions(conn)

        conn.commit()
        cursor.close()
        conn.close()

        _db_initialized = True
        print("[DB] Database 'ai_interview_db' is ready (created if it did not exist).")
        return True

    except Error as e:
        print(f"[DB ERROR] Could not initialize database: {e}")
        return False


def get_connection():
    """Create and return a MySQL database connection, auto-creating the DB if needed."""
    initialize_database()
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"[DB ERROR] Could not connect to MySQL: {e}")
        return None


# ── 1. Candidates ────────────────────────────────────────────────────────────

def save_candidate(full_name, email=None, phone=None, education=None, experience_years=0.0):
    """Insert a new candidate or retrieve existing one if email duplicates, and return candidate_id."""
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        sql = """
            INSERT INTO Candidates (full_name, email, phone, education, experience_years)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (full_name, email, phone, education, experience_years))
        conn.commit()
        candidate_id = cursor.lastrowid
        print(f"[DB] Candidate saved  ->  candidate_id = {candidate_id}")
        return candidate_id
    except Error as e:
        if e.errno == 1062 and email:  # Duplicate entry error code
            try:
                sql_select = "SELECT candidate_id FROM Candidates WHERE email = %s"
                cursor.execute(sql_select, (email,))
                result = cursor.fetchone()
                if result:
                    candidate_id = result[0]
                    print(f"[DB] Existing candidate found with email '{email}'  ->  candidate_id = {candidate_id}")
                    return candidate_id
            except Error as select_error:
                print(f"[DB ERROR] Failed to fetch existing candidate: {select_error}")
        print(f"[DB ERROR] save_candidate: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def get_candidate(candidate_id):
    """Retrieve a candidate record by ID."""
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Candidates WHERE candidate_id = %s", (candidate_id,))
        return cursor.fetchone()
    except Error as e:
        print(f"[DB ERROR] get_candidate: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


# ── 2. Skills ────────────────────────────────────────────────────────────────

def save_skills(candidate_id, hard_skills, soft_skills):
    """
    Bulk-insert extracted skills for a candidate. Deletes old skills first to avoid duplication.

    Parameters:
        candidate_id : int
        hard_skills  : list[str]  – e.g. ["python", "sql", "docker"]
        soft_skills  : list[str]  – e.g. ["teamwork", "communication"]
    """
    conn = get_connection()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        # Delete existing skills for candidate to clean up duplicates
        cursor.execute("DELETE FROM Skills WHERE candidate_id = %s", (candidate_id,))
        
        sql = "INSERT INTO Skills (candidate_id, skill_name, skill_type) VALUES (%s, %s, %s)"

        rows = []
        for skill in hard_skills:
            rows.append((candidate_id, skill, "Hard Skill"))
        for skill in soft_skills:
            rows.append((candidate_id, skill, "Soft Skill"))

        if rows:
            cursor.executemany(sql, rows)
        conn.commit()
        print(f"[DB] {len(rows)} skills saved for candidate_id = {candidate_id}")
    except Error as e:
        print(f"[DB ERROR] save_skills: {e}")
    finally:
        cursor.close()
        conn.close()


def get_skills(candidate_id):
    """Retrieve all skills for a candidate."""
    conn = get_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Skills WHERE candidate_id = %s", (candidate_id,))
        return cursor.fetchall()
    except Error as e:
        print(f"[DB ERROR] get_skills: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


# ── 3. Interview Sessions ───────────────────────────────────────────────────

def create_session(candidate_id, job_role, difficulty):
    """Start a new interview session and return the session_id."""
    # Map project difficulty levels to the ENUM values in the DB
    difficulty_map = {
        "beginner": "Easy",
        "intermediate": "Medium",
        "expert": "Hard",
        "easy": "Easy",
        "medium": "Medium",
        "hard": "Hard",
    }
    db_difficulty = difficulty_map.get(difficulty.lower(), "Medium")

    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        sql = """
            INSERT INTO InterviewSessions (candidate_id, job_role, difficulty, interview_date)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql, (candidate_id, job_role, db_difficulty, datetime.now()))
        conn.commit()
        session_id = cursor.lastrowid
        print(f"[DB] Interview session created  ->  session_id = {session_id}")
        return session_id
    except Error as e:
        print(f"[DB ERROR] create_session: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def get_session(session_id):
    """Retrieve a session record by ID."""
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM InterviewSessions WHERE session_id = %s", (session_id,))
        return cursor.fetchone()
    except Error as e:
        print(f"[DB ERROR] get_session: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


# ── 4. Questions ─────────────────────────────────────────────────────────────

def save_questions(question_texts, difficulty):
    """
    Bulk-insert generated questions and return a list of question_ids.

    Parameters:
        question_texts : list[str]  – the generated question strings
        difficulty     : str        – "Easy", "Medium", or "Hard"
    Returns:
        list[int] – corresponding question_ids
    """
    # Map project difficulty levels to the ENUM values in the DB
    difficulty_map = {
        "beginner": "Easy",
        "intermediate": "Medium",
        "expert": "Hard",
        "easy": "Easy",
        "medium": "Medium",
        "hard": "Hard",
    }
    db_difficulty = difficulty_map.get(difficulty.lower(), "Medium")

    conn = get_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        sql = "INSERT INTO Questions (question_text, difficulty) VALUES (%s, %s)"

        question_ids = []
        for text in question_texts:
            cursor.execute(sql, (text, db_difficulty))
            question_ids.append(cursor.lastrowid)

        conn.commit()
        print(f"[DB] {len(question_ids)} questions saved")
        return question_ids
    except Error as e:
        print(f"[DB ERROR] save_questions: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


# ── 5. Responses ─────────────────────────────────────────────────────────────

def save_responses(session_id, question_ids, answer_texts):
    """
    Bulk-insert candidate responses for a session.

    Parameters:
        session_id   : int
        question_ids : list[int]
        answer_texts : list[str]
    """
    conn = get_connection()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        sql = """
            INSERT INTO Responses (session_id, question_id, answer_text)
            VALUES (%s, %s, %s)
        """
        rows = [(session_id, qid, ans) for qid, ans in zip(question_ids, answer_texts)]
        cursor.executemany(sql, rows)
        conn.commit()
        print(f"[DB] {len(rows)} responses saved for session_id = {session_id}")
    except Error as e:
        print(f"[DB ERROR] save_responses: {e}")
    finally:
        cursor.close()
        conn.close()


# ── 6. Interview Summary ────────────────────────────────────────────────────

def save_summary(session_id, overall_score, strengths, weaknesses, final_feedback):
    """Insert the final interview evaluation summary for a session."""
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        sql = """
            INSERT INTO InterviewSummary (session_id, overall_score, strengths, weaknesses, final_feedback)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (session_id, overall_score, strengths, weaknesses, final_feedback))
        conn.commit()
        summary_id = cursor.lastrowid
        print(f"[DB] Summary saved  ->  summary_id = {summary_id}")
        return summary_id
    except Error as e:
        print(f"[DB ERROR] save_summary: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def get_summary(session_id):
    """Retrieve the interview summary for a given session."""
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM InterviewSummary WHERE session_id = %s", (session_id,))
        return cursor.fetchone()
    except Error as e:
        print(f"[DB ERROR] get_summary: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


# ── 7. Stored Questions Pool ─────────────────────────────────────────────────

def seed_default_questions(conn):
    """Seed the StoredQuestions table with high-quality default questions if empty."""
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM StoredQuestions")
        count = cursor.fetchone()[0]
        if count > 0:
            return
    except Error as e:
        # If the table doesn't exist yet, we can't seed it.
        print(f"[DB ERROR] Checking table count failed: {e}")
        return

    print("[DB] Seeding default questions...")
    # List of tuples: (job_role, difficulty, topic, question, answer)
    seed_data = [
        # Software Engineer - Easy
        ("Software Engineer", "Easy", "Python", "Explain the difference between a list and a tuple in Python.", "Lists are mutable, meaning their elements can be modified. Tuples are immutable. Lists use square brackets [], and tuples use parentheses ()."),
        ("Software Engineer", "Easy", "Git", "What is version control, and why is Git important in software development?", "Version control systems track code modifications over time. Git is a distributed VCS that allows developers to work concurrently, manage branching/merging, and maintain history."),
        ("Software Engineer", "Easy", "Databases", "What is the purpose of an index in a database, and how does it speed up queries?", "An index is a data structure (often a B-Tree) that allows database engines to find rows quickly without performing a full table scan, significantly improving read query performance."),
        
        # Software Engineer - Medium
        ("Software Engineer", "Medium", "Code Quality", "How do you ensure code quality and prevent bugs in a collaborative codebase?", "By using code reviews, writing automated tests (unit, integration), following style guides, and integrating CI/CD pipelines that check for lints and test failures before merging."),
        ("Software Engineer", "Medium", "Databases", "Describe the difference between SQL and NoSQL databases. When would you choose one over the other?", "SQL databases are relational, table-based, and have strict schemas (good for ACID compliance). NoSQL databases are non-relational, document/key-value/graph-based, and flexible (good for rapid development and scale)."),
        ("Software Engineer", "Medium", "Web Services", "What are RESTful APIs, and what are the key HTTP methods used in them?", "Representational State Transfer APIs use standard HTTP protocols. Key methods are GET (retrieve), POST (create), PUT/PATCH (update), and DELETE (remove)."),

        # Software Engineer - Hard
        ("Software Engineer", "Hard", "System Design", "Explain how you would design a highly scalable and fault-tolerant system for a chat application.", "I would use a microservices architecture, WebSockets for real-time bi-directional messaging, a message broker like Kafka, a distributed cache like Redis, and partitioned databases with replication."),
        ("Software Engineer", "Hard", "Optimization", "Describe a scenario where you had to optimize a slow database query or application logic. What was the bottleneck?", "Identified a slow query via EXPLAIN; added missing composite indexes and eliminated N+1 query patterns in the ORM, reducing execution time from 5s to 50ms."),
        ("Software Engineer", "Hard", "Concurrency", "How do you handle memory leaks or concurrency issues in multi-threaded applications?", "By using thread-safe data structures, synchronization locks (e.g. mutexes), thread pools, and profiling tools (like memory profilers) to detect dangling references and deadlocks."),

        # Data Scientist - Easy
        ("Data Scientist", "Easy", "Machine Learning", "What is the difference between supervised and unsupervised learning?", "Supervised learning uses labeled training data to learn mappings. Unsupervised learning models unlabeled data to find hidden patterns or structures."),
        ("Data Scientist", "Easy", "Model Evaluation", "Explain what overfitting is and how you can prevent it.", "Overfitting occurs when a model learns noise in the training data rather than the signal. Prevent by using regularization, cross-validation, and pruning."),
        ("Data Scientist", "Easy", "Data Structures", "What is the difference between pandas series and pandas dataframe?", "A Series is a one-dimensional array-like object with labels. A DataFrame is a two-dimensional tabular structure with rows and columns (effectively a collection of Series)."),

        # Data Scientist - Medium
        ("Data Scientist", "Medium", "Machine Learning", "Explain the bias-variance tradeoff in machine learning.", "Bias is error from erroneous assumptions (underfitting). Variance is error from sensitivity to training data fluctuations (overfitting). We seek a balance that minimizes total error."),
        ("Data Scientist", "Medium", "Data Processing", "How do you handle missing or noisy data in a dataset before modeling?", "By using imputation (mean, median, mode, or predictive imputation), dropping rows/columns with excessive missing values, or using models robust to missing data."),
        ("Data Scientist", "Medium", "Model Validation", "What is the purpose of cross-validation, and how does k-fold cross-validation work?", "It assesses how well a model generalizes. K-fold splits data into k subsets; the model is trained on k-1 subsets and evaluated on the remaining subset, repeating k times."),

        # Data Scientist - Hard
        ("Data Scientist", "Hard", "Deployment", "Describe how you would design and deploy an end-to-end machine learning pipeline in production.", "By writing clean pipeline modules for extraction, preprocessing, training, and inference; containerizing with Docker; and exposing endpoints via FastAPI deployed on Kubernetes."),
        ("Data Scientist", "Hard", "Imbalanced Data", "How do you evaluate the performance of a classification model when the dataset is highly imbalanced?", "Avoid accuracy. Use Precision, Recall, F1-Score, ROC-AUC, and PR-AUC. Use techniques like SMOTE (oversampling), undersampling, or class weights during training."),
        ("Data Scientist", "Hard", "Deep Learning", "Explain the architecture and use cases of Transformer models compared to LSTMs.", "Transformers use self-attention mechanisms to process sequences in parallel, resolving vanishing gradients. LSTMs process sequentially, making them slower but good for smaller datasets."),

        # Frontend Engineer - Easy
        ("Frontend Engineer", "Easy", "DOM", "What is the DOM, and how does JavaScript interact with it?", "The Document Object Model is a programming interface representing HTML documents as a tree. JS accesses and manipulates nodes to update content/styles dynamically."),
        ("Frontend Engineer", "Easy", "CSS", "Explain the difference between 'margin' and 'padding' in CSS.", "Margin is space outside the element's border, separating it from others. Padding is space inside the border, separating the content from the border."),
        ("Frontend Engineer", "Easy", "HTML/SEO", "What are semantic HTML tags, and why are they important for SEO and accessibility?", "Tags like <article>, <section>, and <nav> define content meaning rather than appearance. They help screen readers navigate and search engines index content effectively."),

        # Frontend Engineer - Medium
        ("Frontend Engineer", "Medium", "React", "What is the virtual DOM in React, and how does it improve rendering performance?", "A lightweight in-memory representation of the real DOM. React updates the virtual DOM first, diffs it against the old one, and batches minimal updates to the real DOM."),
        ("Frontend Engineer", "Medium", "Performance", "How do you optimize a website's loading performance and minimize assets?", "By using image compression, minification, tree-shaking, caching, lazy loading, and CDN delivery for static assets."),
        ("Frontend Engineer", "Medium", "Web Storage", "Explain the difference between localStorage, sessionStorage, and cookies.", "localStorage persists indefinitely. sessionStorage expires when the tab/session ends. Cookies store small data sent with HTTP requests, supporting expirations."),

        # Frontend Engineer - Hard
        ("Frontend Engineer", "Hard", "State Management", "How would you architect a state management system for a large-scale single-page application (SPA)?", "By separating global, local, and server states. Use Redux or Zustand for global UI state, React Query/SWR for server state, and React context/useState for local component state."),
        ("Frontend Engineer", "Hard", "Code Optimization", "Describe how you would implement code-splitting and lazy-loading in a modern web framework.", "Using dynamic imports (e.g., React.lazy and Suspense) to split the bundle into smaller chunks loaded on-demand, improving initial page load time."),
        ("Frontend Engineer", "Hard", "Security", "How do you address security concerns on the frontend, such as Cross-Site Scripting (XSS) and CSRF?", "For XSS: sanitize inputs, use frameworks that auto-escape (like React), set Content Security Policy (CSP) headers. For CSRF: use anti-CSRF tokens and SameSite cookie attribute."),

        # DevOps Engineer - Easy
        ("DevOps Engineer", "Easy", "CI/CD", "What is CI/CD, and why is it important in a DevOps pipeline?", "Continuous Integration merges developer code frequently, running tests automatically. Continuous Delivery/Deployment automates releasing that code to production safely."),
        ("DevOps Engineer", "Easy", "Containers", "Explain the difference between a container and a virtual machine.", "Containers share the host OS kernel and are lightweight. VMs run complete guest OSs on virtualized hardware, consuming more resources and taking longer to boot."),
        ("DevOps Engineer", "Easy", "Config Management", "What is the purpose of a configuration management tool like Ansible or Puppet?", "To automate server provisioning, configuration, and application deployment, ensuring consistency across environments and preventing configuration drift."),

        # DevOps Engineer - Medium
        ("DevOps Engineer", "Medium", "Kubernetes", "How does Kubernetes manage container deployment, scaling, and load balancing?", "Via Pods, Deployments, and Services. Deployments declare the desired state, replica counts scale containers up/down, and Services load-balance traffic across pods."),
        ("DevOps Engineer", "Medium", "IaC", "What is Infrastructure as Code (IaC), and how does Terraform help implement it?", "Writing code to define, provision, and manage infrastructure. Terraform uses declarative configuration files to provision resources across multiple cloud providers."),
        ("DevOps Engineer", "Medium", "Monitoring", "Explain how you would set up central logging and monitoring for a microservices application.", "By using Prometheus and Grafana for metrics collection and visualization, and the EFK stack (Elasticsearch, Fluentd, Kibana) for centralized log aggregation."),

        # DevOps Engineer - Hard
        ("DevOps Engineer", "Hard", "Deployment", "Describe how you would design a zero-downtime deployment strategy for a high-traffic production application.", "By using blue-green deployments (routing traffic from old environment to new) or rolling updates with readiness/liveness probes, supported by automated rollbacks."),
        ("DevOps Engineer", "Hard", "Security", "How do you secure a CI/CD pipeline against secret leaks and dependency vulnerabilities?", "By using secret management tools (Vault), scanning tools (SonarQube, Snyk), pinning dependency versions, and running pipelines on isolated, temporary agents."),
        ("DevOps Engineer", "Hard", "Disaster Recovery", "Explain how you would handle disaster recovery and multi-region failover in a cloud environment.", "By setting up active-active or active-passive multi-region deployments, replicating databases asynchronously, and using Route 53 DNS routing policies to failover."),

        # Project Manager - Easy
        ("Project Manager", "Easy", "Methodologies", "What is the Agile methodology, and how does it differ from Waterfall?", "Agile is iterative, focusing on collaboration and adaptability. Waterfall is linear and sequential, where each phase must finish before the next begins."),
        ("Project Manager", "Easy", "Planning", "What are the main responsibilities of a Project Manager during the planning phase?", "Defining project scope, identifying stakeholders, estimating timelines and budgets, assigning resources, and establishing risk management plans."),
        ("Project Manager", "Easy", "Scope", "How do you define a project's Scope, and what is scope creep?", "Scope is the detailed set of deliverables and boundaries of a project. Scope creep is the uncontrolled growth of requirements without adjustments to time, cost, or resources."),

        # Project Manager - Medium
        ("Project Manager", "Medium", "Stakeholder Management", "How do you manage conflicting priorities between product stakeholders and the engineering team?", "By facilitating alignment meetings, prioritizing based on business value and technical feasibility, using data-driven roadmaps, and setting clear expectations."),
        ("Project Manager", "Medium", "Scrum", "Describe the Scrum framework. What are the key ceremonies and roles?", "Scrum is an Agile framework with Sprints. Key roles are Product Owner, Scrum Master, and Developers. Ceremonies include Sprint Planning, Daily Standup, Review, and Retrospective."),
        ("Project Manager", "Medium", "Risk Management", "How do you perform risk assessment and mitigation planning for a new project?", "Identify potential risks, evaluate their likelihood and impact, assign owners, and create action plans for avoidance, mitigation, transference, or acceptance."),

        # Project Manager - Hard
        ("Project Manager", "Hard", "Crisis Management", "Describe a time when a critical project was falling behind schedule. How did you get it back on track?", "I re-evaluated the scope, cut non-essential features, optimized task distribution among engineers, and increased communication frequency to remove blockers daily."),
        ("Project Manager", "Hard", "Portfolio Management", "How do you manage budget allocation, resource constraints, and scope adjustments for a multi-million dollar portfolio?", "Using portfolio management tools, balancing resources across projects based on strategic alignment, and reviewing financial status monthly with stakeholders."),
        ("Project Manager", "Hard", "KPIs", "What metrics or KPIs do you use to measure project success and team velocity?", "Sprint velocity, burndown/burnup charts, cycle time, defect escape rate, budget variance (CPI/SPI), and client satisfaction scores."),

        # QA Engineer - Easy
        ("QA Engineer", "Easy", "Testing Types", "What is the difference between manual testing and automated testing?", "Manual testing involves human execution of test cases without tools. Automated testing uses software tools to run tests, compare outcomes, and generate reports automatically."),
        ("QA Engineer", "Easy", "Test Planning", "What is a test plan, and what key components should it contain?", "A document outlining the testing scope, strategy, resources, schedule, deliverables, and environment requirements for a project."),
        ("QA Engineer", "Easy", "Regression/Smoke", "Explain the difference between regression testing and smoke testing.", "Smoke testing checks basic functionality to ensure the build is stable enough for deeper testing. Regression testing verifies that recent changes haven't broken existing features."),

        # QA Engineer - Medium
        ("QA Engineer", "Medium", "Automation", "How do you design an automated test suite that is maintainable and not flaky?", "By using design patterns like Page Object Model (POM), avoiding hard-coded sleep times, using dynamic waits, cleaning test data, and running tests in isolation."),
        ("QA Engineer", "Medium", "Defect Management", "Describe the bug lifecycle from discovery to resolution.", "New → Assigned → Open → Fixed → Pending Retest → Retest/Verify → Closed. If retest fails, it is Reopened."),
        ("QA Engineer", "Medium", "API Testing", "How do you perform API testing, and what response status codes do you check?", "By sending HTTP requests (GET, POST, etc.) and checking status codes (e.g. 200 OK, 201 Created, 400 Bad Request, 401 Unauthorized, 500 Server Error) and payload JSON schema."),

        # QA Engineer - Hard
        ("QA Engineer", "Hard", "CI/CD Integration", "Describe how you would integrate automated testing into a CI/CD pipeline.", "By triggers (e.g. pull requests), running fast unit/lint tests first, then integration tests in containerized test environments, and outputting reports to dashboards."),
        ("QA Engineer", "Hard", "Performance", "How do you perform performance and load testing, and what bottlenecks do you look for?", "Using tools like JMeter or Locust to simulate concurrent users. Look for high CPU/memory utilization, slow database queries, connection pooling limits, or network latency."),
        ("QA Engineer", "Hard", "Microservices", "What is your strategy for testing a complex microservices architecture where dependencies are constantly changing?", "Using contract testing (e.g. Pact) to ensure services agree on API schemas, service virtualization/mocking for dependent services, and end-to-end smoke testing."),

        # UX/UI Designer - Easy
        ("UX/UI Designer", "Easy", "UX vs UI", "What is the difference between UX and UI design?", "UX (User Experience) focuses on how a product feels and the overall user journey. UI (User Interface) focuses on how the product looks, including visual design elements like typography, colors, and buttons."),
        ("UX/UI Designer", "Easy", "Hierarchy", "What are the basic principles of visual hierarchy in UI design?", "Size, color contrast, spacing/margins, alignment, and typography hierarchy (e.g., H1, H2, body) to guide the user's eye to important elements first."),
        ("UX/UI Designer", "Easy", "User Research", "Why is user research important before beginning the design process?", "To understand the target audience's pain points, behaviors, and goals, ensuring the design solves actual problems rather than relying on designer assumptions."),

        # UX/UI Designer - Medium
        ("UX/UI Designer", "Medium", "Design Systems", "How do you create and maintain a consistent design system across a product?", "By defining reusable components (buttons, forms), typography scales, color palettes, and spacing variables in tools like Figma, and aligning them with frontend developers."),
        ("UX/UI Designer", "Medium", "Usability Testing", "Describe your process for conducting usability testing and how you iterate on feedback.", "Create interactive prototypes, define user tasks, observe users performing tasks while thinking aloud, record pain points, and prioritize redesigning elements with the highest failure rates."),
        ("UX/UI Designer", "Medium", "Mobile-First", "What is mobile-first design, and how does it affect layout decisions?", "Designing for the smallest screen first and scaling up. It forces prioritization of essential content and features, avoiding cluttered desktop layouts."),

        # UX/UI Designer - Hard
        ("UX/UI Designer", "Hard", "Complexity", "Describe how you would design an interface for an extremely complex data dashboard with accessibility (WCAG) compliance.", "By using progressive disclosure, clear grouping/hierarchy, keyboard navigability, high color contrast, screen reader aria-labels, and tooltips for data explanations."),
        ("UX/UI Designer", "Hard", "Balancing constraints", "How do you balance user needs, technical constraints, and business goals in a design project?", "By collaborating early with engineers and product managers, defining MVP designs, and planning iterative design improvements post-launch based on user data."),
        ("UX/UI Designer", "Hard", "Metrics", "Explain how you measure the success of UX improvements post-launch.", "Through quantitative metrics (conversion rates, task completion time, drop-off rates, system usability scale) and qualitative feedback (user interviews, support tickets)."),

        # Business Analyst - Easy
        ("Business Analyst", "Easy", "Role", "What is a Business Analyst, and what is their role in software development?", "A BA acts as a bridge between business stakeholders and the technical team, analyzing business needs, defining requirements, and ensuring the project delivers value."),
        ("Business Analyst", "Easy", "Requirements", "What are functional vs. non-functional requirements?", "Functional requirements describe what the system should do (e.g., 'User can log in'). Non-functional requirements describe how the system behaves (e.g., 'System must load within 2 seconds')."),
        ("Business Analyst", "Easy", "User Stories", "What is a user story, and what format does it typically follow?", "A simple explanation of a feature from the user's perspective. Format: 'As a [user type], I want to [action], so that [benefit/goal].'"),

        # Business Analyst - Medium
        ("Business Analyst", "Medium", "Stakeholder Mgmt", "How do you gather requirements from stakeholders who have conflicting visions?", "By conducting workshops, using prioritization frameworks (like MoSCoW), aligning requirements with core business goals, and seeking executive sponsorship for final decisions."),
        ("Business Analyst", "Medium", "Data Usage", "Describe how you use SQL or data visualization tools to support business decisions.", "I query databases to extract key performance metrics, clean the data, and build Tableau dashboards to visualize trends and back business cases with quantitative data."),
        ("Business Analyst", "Medium", "Gap Analysis", "What is Gap Analysis, and when is it used?", "Comparing current performance or process state ('As-Is') with the desired future state ('To-Be') to identify missing capabilities and steps required to achieve goals."),

        # Business Analyst - Hard
        ("Business Analyst", "Hard", "Process Optimization", "Describe a time when you identified a critical business process bottleneck. How did you propose and implement a solution?", "Mapped the current process, identified manual steps that could be automated, drafted a business case showing ROI, worked with developers to deploy, and trained users, reducing processing time by 40%."),
        ("Business Analyst", "Hard", "Technical Translation", "How do you translate highly complex technical constraints into business-friendly terms for executives?", "By avoiding jargon and focusing on business outcomes like risk, cost, timeline, and impact on customer experience, using diagrams or metaphors where helpful."),
        ("Business Analyst", "Hard", "Cost-Benefit", "What methodology do you use to perform cost-benefit analysis for a proposed major system overhaul?", "Calculate Total Cost of Ownership (TCO), estimated cost savings, revenue increases, Net Present Value (NPV), ROI, and Payback Period to present a clear financial comparison.")
    ]

    sql = """
        INSERT INTO StoredQuestions (job_role, difficulty, topic, question, answer)
        VALUES (%s, %s, %s, %s, %s)
    """
    cursor.executemany(sql, seed_data)
    conn.commit()
    print(f"[DB] Successfully seeded {len(seed_data)} default questions.")
    cursor.close()


def save_stored_question(job_role, difficulty, topic, question, answer=None):
    """Save a question to the reusable StoredQuestions pool."""
    difficulty_map = {
        "beginner": "Easy",
        "intermediate": "Medium",
        "expert": "Hard",
        "easy": "Easy",
        "medium": "Medium",
        "hard": "Hard",
    }
    db_difficulty = difficulty_map.get(difficulty.lower(), "Medium")

    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        sql = """
            INSERT INTO StoredQuestions (job_role, difficulty, topic, question, answer)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (job_role, db_difficulty, topic, question, answer))
        conn.commit()
        qid = cursor.lastrowid
        print(f"[DB] Question saved to reusable pool -> id = {qid}")
        return qid
    except Error as e:
        print(f"[DB ERROR] save_stored_question: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def get_stored_questions(job_role, difficulty, limit=5):
    """Retrieve questions from the StoredQuestions pool, filtered by role and difficulty."""
    difficulty_map = {
        "beginner": "Easy",
        "intermediate": "Medium",
        "expert": "Hard",
        "easy": "Easy",
        "medium": "Medium",
        "hard": "Hard",
    }
    db_difficulty = difficulty_map.get(difficulty.lower(), "Medium")

    conn = get_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        # Randomly sample the questions to provide variety
        sql = """
            SELECT question, answer, topic FROM StoredQuestions
            WHERE job_role = %s AND difficulty = %s
            ORDER BY RAND()
            LIMIT %s
        """
        cursor.execute(sql, (job_role, db_difficulty, limit))
        results = cursor.fetchall()
        
        # Fallback if no questions are found for specific role/difficulty:
        # e.g., if we select another role, try pulling any questions for that difficulty.
        if not results:
            sql_fallback = """
                SELECT question, answer, topic FROM StoredQuestions
                WHERE difficulty = %s
                ORDER BY RAND()
                LIMIT %s
            """
            cursor.execute(sql_fallback, (db_difficulty, limit))
            results = cursor.fetchall()
            
        return results
    except Error as e:
        print(f"[DB ERROR] get_stored_questions: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def get_all_sessions():
    """Retrieve all interview sessions with candidate name, score, feedback, and date."""
    conn = get_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        sql = """
            SELECT 
                s.session_id,
                c.full_name,
                c.experience_years,
                s.job_role,
                s.difficulty,
                s.interview_date,
                sumy.overall_score,
                sumy.final_feedback
            FROM InterviewSessions s
            JOIN Candidates c ON s.candidate_id = c.candidate_id
            LEFT JOIN InterviewSummary sumy ON s.session_id = sumy.session_id
            ORDER BY s.interview_date DESC
        """
        cursor.execute(sql)
        results = cursor.fetchall()
        # Convert interview_date to string for JSON serialization
        for r in results:
            if r.get("interview_date"):
                r["interview_date"] = r["interview_date"].isoformat()
            if r.get("overall_score"):
                r["overall_score"] = float(r["overall_score"])
        return results
    except Error as e:
        print(f"[DB ERROR] get_all_sessions: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def get_session_details(session_id):
    """Retrieve detailed reports for a given session: candidate, skills, questions, answers, and summary."""
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 1. Get session info
        cursor.execute("""
            SELECT s.*, c.full_name, c.email, c.phone, c.education, c.experience_years
            FROM InterviewSessions s
            JOIN Candidates c ON s.candidate_id = c.candidate_id
            WHERE s.session_id = %s
        """, (session_id,))
        session = cursor.fetchone()
        if not session:
            return None
            
        if session.get("interview_date"):
            session["interview_date"] = session["interview_date"].isoformat()
        if session.get("experience_years"):
            session["experience_years"] = float(session["experience_years"])
            
        # 2. Get skills
        cursor.execute("SELECT skill_name, skill_type FROM Skills WHERE candidate_id = %s", (session["candidate_id"],))
        skills = cursor.fetchall()
        
        # 3. Get questions and responses
        cursor.execute("""
            SELECT q.question_text, r.answer_text
            FROM Responses r
            JOIN Questions q ON r.question_id = q.question_id
            WHERE r.session_id = %s
            ORDER BY r.response_id ASC
        """, (session_id,))
        qa_pairs = cursor.fetchall()
        
        # 4. Get summary
        cursor.execute("SELECT * FROM InterviewSummary WHERE session_id = %s", (session_id,))
        summary = cursor.fetchone()
        if summary:
            if summary.get("overall_score"):
                summary["overall_score"] = float(summary["overall_score"])
        
        return {
            "session": session,
            "skills": skills,
            "qa": qa_pairs,
            "summary": summary
        }
    except Error as e:
        print(f"[DB ERROR] get_session_details: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


# ── Full Workflow Demo ───────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  DB Helper – Quick Integration Test")
    print("=" * 60)

    # 1. Save a test candidate
    cid = save_candidate(
        full_name="Navaraj Thapa",
        email="navaraj@example.com",
        phone="9841000000",
        education="Bachelor in Computer Science",
        experience_years=3.0
    )

    if cid:
        # 2. Save skills
        save_skills(cid, ["python", "sql", "docker"], ["teamwork", "communication"])

        # 3. Create session
        sid = create_session(cid, "Software Engineer", "Intermediate")

        if sid:
            # 4. Save questions
            sample_qs = [
                "Explain the difference between a list and a tuple in Python.",
                "How do you handle version control in a team environment?"
            ]
            qids = save_questions(sample_qs, "intermediate")

            # 5. Save responses
            sample_answers = [
                "A list is mutable while a tuple is immutable.",
                "We use Git with feature branches and pull requests."
            ]
            save_responses(sid, qids, sample_answers)

            # 6. Save summary
            save_summary(
                session_id=sid,
                overall_score=7.5,
                strengths="Good grasp of Python fundamentals",
                weaknesses="Needs deeper understanding of CI/CD pipelines",
                final_feedback="Recommended with additional training on DevOps."
            )

    print("\n✓ Integration test complete.")
