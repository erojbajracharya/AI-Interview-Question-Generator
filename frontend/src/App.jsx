import React, { useState, useEffect, useRef } from 'react';
import {
  Upload,
  Briefcase,
  Star,
  FileText,
  CheckCircle2,
  XCircle,
  ArrowRight,
  Play,
  RefreshCw,
  Clock,
  Award,
  AlertCircle,
  ChevronRight,
  User,
  ExternalLink,
  ChevronLeft,
  Mic,
  MicOff,
  Send,
  Volume2,
  Cpu,
  Sun,
  Moon
} from 'lucide-react';

const API_BASE = 'http://localhost:5000/api';

export default function App() {
  // Navigation
  const [activeTab, setActiveTab] = useState('setup'); // 'setup', 'screening', 'interview', 'evaluation', 'history'
  
  // Theme state
  const [theme, setTheme] = useState('dark');
  const toggleTheme = () => {
    setTheme(prev => (prev === 'dark' ? 'light' : 'dark'));
  };
  
  // Settings & Configuration state
  const [roles, setRoles] = useState([]);
  const [selectedRoleKey, setSelectedRoleKey] = useState('');
  const [customRoleTitle, setCustomRoleTitle] = useState('');
  const [numQuestions, setNumQuestions] = useState(5);
  const [questionSource, setQuestionSource] = useState('ai'); // 'ai' or 'db'
  const [saveToDb, setSaveToDb] = useState(true);
  
  // File Uploader state
  const [selectedFile, setSelectedFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isParsing, setIsParsing] = useState(false);
  
  // Assessment Results state (Candidate & Screening)
  const [candidateId, setCandidateId] = useState(null);
  const [candidateName, setCandidateName] = useState('');
  const [resumeData, setResumeData] = useState(null);
  const [screeningResult, setScreeningResult] = useState(null);
  
  // Interview Simulation state
  const [sessionData, setSessionData] = useState(null); // { session_id, questions, difficulty }
  const [currentQuestionIdx, setCurrentQuestionIdx] = useState(0);
  const [candidateAnswers, setCandidateAnswers] = useState([]);
  const [activeAnswerText, setActiveAnswerText] = useState('');
  
  // Custom states for messaging platform feel & speech recognition
  const [isTyping, setIsTyping] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(true);
  const recognitionRef = useRef(null);
  const isListeningRef = useRef(false);
  const startTextRef = useRef('');
  const activeAnswerTextRef = useRef('');
  
  // Timer state
  const [recordingTime, setRecordingTime] = useState(0);
  const timerRef = useRef(null);

  // Sync activeAnswerText to ref to avoid stale closures in event listeners
  useEffect(() => {
    activeAnswerTextRef.current = activeAnswerText;
  }, [activeAnswerText]);

  // Check speech support on mount
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setSpeechSupported(false);
    }
  }, []);

  const startTimer = () => {
    setRecordingTime(0);
    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = setInterval(() => {
      setRecordingTime((prev) => prev + 1);
    }, 1000);
  };

  const stopTimer = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  };

  // simulated typing effect for question loading
  useEffect(() => {
    if (activeTab === 'interview' && sessionData) {
      setIsTyping(true);
      const timer = setTimeout(() => {
        setIsTyping(false);
      }, 1200);
      return () => clearTimeout(timer);
    }
  }, [currentQuestionIdx, activeTab, sessionData]);

  const toggleListening = () => {
    if (!speechSupported) {
      alert('Speech Recognition is not supported by your browser. Please use Chrome, Safari, or Edge.');
      return;
    }

    if (isListening) {
      // Stop listening manually
      isListeningRef.current = false;
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      setIsListening(false);
      stopTimer();
    } else {
      // Start listening
      try {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';

        startTextRef.current = activeAnswerTextRef.current; // set baseline text

        recognition.onresult = (event) => {
          if (!isListeningRef.current) return;
          let transcript = '';
          for (let i = 0; i < event.results.length; ++i) {
            transcript += event.results[i][0].transcript;
          }
          const base = startTextRef.current;
          const separator = base && !base.endsWith(' ') ? ' ' : '';
          setActiveAnswerText(base + separator + transcript);
        };

        recognition.onerror = (event) => {
          console.error('Speech recognition error', event.error);
          if (event.error !== 'no-speech' && event.error !== 'aborted') {
            setIsListening(false);
            isListeningRef.current = false;
            stopTimer();
          }
        };

        recognition.onend = () => {
          if (isListeningRef.current) {
            // Restart automatically if user hasn't stopped it
            try {
              startTextRef.current = activeAnswerTextRef.current;
              recognition.start();
            } catch (err) {
              console.error('Failed to restart speech recognition:', err);
            }
          } else {
            setIsListening(false);
            stopTimer();
          }
        };

        recognitionRef.current = recognition;
        isListeningRef.current = true;
        recognition.start();
        setIsListening(true);
        startTimer();
      } catch (err) {
        console.error('Failed to start speech recognition:', err);
      }
    }
  };

  const formatTime = (seconds) => {
    const m = Math.floor(seconds / 60).toString().padStart(2, '0');
    const s = (seconds % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  const formatExperienceYears = (years) => {
    if (years === null || years === undefined || isNaN(years)) return 'N/A';
    const y = Number(years);
    if (y <= 0) return '0 months';
    if (y < 1) {
      const months = Math.max(1, Math.floor(y * 12 + 1e-8));
      return `${months} month${months === 1 ? '' : 's'}`;
    }
    // show integer years if whole number, otherwise one decimal
    if (Number.isInteger(y)) return `${y} Year${y === 1 ? '' : 's'}`;
    return `${y.toFixed(1)} Years`;
  };

  const speakQuestion = (text) => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      const voices = window.speechSynthesis.getVoices();
      const englishVoice = voices.find(v => v.lang.startsWith('en'));
      if (englishVoice) {
        utterance.voice = englishVoice;
      }
      window.speechSynthesis.speak(utterance);
    } else {
      alert('Text-to-speech is not supported in this browser.');
    }
  };
  
  // Evaluation Report state
  const [evaluationReport, setEvaluationReport] = useState(null); // { evaluations, overall_score, status }
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [gradingProgressMsg, setGradingProgressMsg] = useState('');
  
  // History tab state
  const [historyList, setHistoryList] = useState([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [selectedHistoryId, setSelectedHistoryId] = useState(null);
  const [historyDetail, setHistoryDetail] = useState(null);
  const [isLoadingHistoryDetail, setIsLoadingHistoryDetail] = useState(false);

  // References
  const fileInputRef = useRef(null);
  const chatBottomRef = useRef(null);

  // Fetch job roles from Flask API on mount
  useEffect(() => {
    fetch(`${API_BASE}/roles`)
      .then((res) => res.json())
      .then((data) => {
        if (data.success && data.roles.length > 0) {
          setRoles(data.roles);
          setSelectedRoleKey(data.roles[0].key);
        }
      })
      .catch((err) => console.error('Error fetching job roles:', err));
  }, []);



  // Scroll to bottom of chat whenever questions/answers change
  useEffect(() => {
    if (chatBottomRef.current) {
      chatBottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [currentQuestionIdx, activeTab]);

  // Drag and Drop File Handlers
  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      if (file.type === 'application/pdf' || file.name.endsWith('.pdf')) {
        setSelectedFile(file);
      } else {
        alert('Please select a PDF file.');
      }
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0]);
    }
  };

  // Parse Resume (POST /api/screen)
  const handleParseAndScreen = async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      alert('Please upload a resume PDF.');
      return;
    }
    if (!selectedRoleKey) {
      alert('Please select a job role.');
      return;
    }

    setIsParsing(true);
    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('role_key', selectedRoleKey);

    try {
      const response = await fetch(`${API_BASE}/screen`, {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      if (data.success) {
        setCandidateId(data.candidate_id);
        setCandidateName(data.candidate_name);
        setResumeData(data.resume_data);
        setScreeningResult(data.screening);
        setActiveTab('screening');
      } else {
        alert(`Assessment Failed: ${data.error}`);
      }
    } catch (err) {
      console.error('Screening API error:', err);
      alert('Server error while parsing resume. Please check if Flask server is running.');
    } finally {
      setIsParsing(false);
    }
  };

  // Start Interview Simulation (POST /api/interview/start)
  const handleStartInterview = async () => {
    if (!candidateId) {
      alert("Database Connection Error: MySQL database is not connected. Please make sure MySQL is running and properly configured in db_helper.py.");
      return;
    }
    if (!resumeData) return;

    setIsParsing(true); // show loader
    try {
      const response = await fetch(`${API_BASE}/interview/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          candidate_id: candidateId,
          role_key: resumeData.role_key !== 'custom' ? resumeData.role_key : undefined,
          role_title: resumeData.role_title,
          difficulty: resumeData.difficulty,
          num_questions: numQuestions,
          source: questionSource,
          save_to_db: saveToDb,
          experience_years: resumeData.experience_years,
          hard_skills: resumeData.hard_skills,
          soft_skills: resumeData.soft_skills
        })
      });

      const data = await response.json();
      if (data.success) {
        setSessionData(data);
        setCurrentQuestionIdx(0);
        setCandidateAnswers([]);
        setActiveAnswerText('');
        setActiveTab('interview');
      } else {
        alert(`Failed to start interview: ${data.error}`);
      }
    } catch (err) {
      console.error('Start Interview error:', err);
      alert('Failed to connect to the interview server.');
    } finally {
      setIsParsing(false);
    }
  };

  // Handle Answer Submission (automatic evaluation on last question)
  const handleSubmitAnswer = async (e) => {
    if (e) e.preventDefault();
    
    // Stop speech recognition if listening
    if (isListening && recognitionRef.current) {
      isListeningRef.current = false;
      recognitionRef.current.stop();
      setIsListening(false);
    }
    
    const answer = activeAnswerText.trim() || '[Skipped]';
    
    // Add answer to list
    const updatedAnswers = [...candidateAnswers, answer];
    setCandidateAnswers(updatedAnswers);
    setActiveAnswerText('');

    // Check if there are more questions
    if (currentQuestionIdx + 1 < sessionData.questions.length) {
      setCurrentQuestionIdx(currentQuestionIdx + 1);
    } else {
      // Last answer submitted! Trigger automatic grading
      await handleAutoEvaluation(updatedAnswers);
    }
  };

  // Submit and grade answers (POST /api/interview/submit)
  const handleAutoEvaluation = async (finalAnswers) => {
    setIsSubmitting(true);
    setGradingProgressMsg('Evaluating responses using Gemini AI...');
    
    try {
      // Small visual delay effect to make evaluation feel thorough and premium
      setTimeout(() => setGradingProgressMsg('Running scoring comparisons...'), 1500);
      setTimeout(() => setGradingProgressMsg('Saving interview summary to MySQL Database...'), 3000);

      const response = await fetch(`${API_BASE}/interview/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionData.session_id,
          questions: sessionData.questions,
          answers: finalAnswers,
          role_key: resumeData.role_key !== 'custom' ? resumeData.role_key : undefined,
          role_title: resumeData.role_title,
          difficulty: sessionData.difficulty,
          hard_skills: resumeData.hard_skills
        })
      });

      const data = await response.json();
      if (data.success) {
        setEvaluationReport(data);
        // Wait briefly for smooth transition
        setTimeout(() => {
          setIsSubmitting(false);
          setActiveTab('evaluation');
        }, 4000);
      } else {
        setIsSubmitting(false);
        alert(`Grading failed: ${data.error}`);
      }
    } catch (err) {
      setIsSubmitting(false);
      console.error('Submit Interview error:', err);
      alert('Error connecting to the grading server.');
    }
  };

  // Fetch History Logs from Database
  const handleLoadHistory = async () => {
    setIsLoadingHistory(true);
    setSelectedHistoryId(null);
    setHistoryDetail(null);
    try {
      const response = await fetch(`${API_BASE}/history`);
      const data = await response.json();
      if (data.success) {
        setHistoryList(data.history);
        setActiveTab('history');
      }
    } catch (err) {
      console.error('History load error:', err);
      alert('Could not fetch history list from server.');
    } finally {
      setIsLoadingHistory(false);
    }
  };

  // Fetch Session details
  const handleViewSessionDetail = async (sessionId) => {
    setSelectedHistoryId(sessionId);
    setIsLoadingHistoryDetail(true);
    try {
      const response = await fetch(`${API_BASE}/history/${sessionId}`);
      const data = await response.json();
      if (data.success) {
        setHistoryDetail(data.details);
      } else {
        alert('Could not find session details.');
      }
    } catch (err) {
      console.error('Error fetching session details:', err);
    } finally {
      setIsLoadingHistoryDetail(false);
    }
  };

  // Reset Simulation
  const handleReset = () => {
    setSelectedFile(null);
    setCandidateId(null);
    setCandidateName('');
    setResumeData(null);
    setScreeningResult(null);
    setSessionData(null);
    setCurrentQuestionIdx(0);
    setCandidateAnswers([]);
    setActiveAnswerText('');
    setEvaluationReport(null);
    setCustomRoleTitle('');
    setActiveTab('setup');
  };

  // Parse structured evaluations helper
  const parseEvaluationString = (text) => {
    let score = 'N/A';
    let feedback = 'No feedback available.';
    let improve = 'No recommendations.';
    
    if (text) {
      const scoreMatch = text.match(/Score:\s*(\d+(\.\d+)?)\/10/i);
      const feedbackMatch = text.match(/Feedback:\s*([^|]+)/i);
      const improveMatch = text.match(/Improve:\s*(.+)/i);
      
      if (scoreMatch) score = `${scoreMatch[1]}/10`;
      if (feedbackMatch) feedback = feedbackMatch[1].trim();
      if (improveMatch) improve = improveMatch[1].trim();
    }
    
    return { score, feedback, improve };
  };

  return (
    <div className={`app-container ${theme}-mode`}>
      {/* Background neon meshes */}
      <div className="mesh-bg">
        <div className="glow-1"></div>
        <div className="glow-2"></div>
      </div>

      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <img src="/company-logo-trans.png" alt="EPSSN Logo" style={{ height: '32px', width: 'auto', objectFit: 'contain' }} />
          <h1>EPSSN</h1>
        </div>

        <ul className="nav-menu">
          <li className="nav-item">
            <button
              onClick={() => setActiveTab('setup')}
              className={`nav-link ${activeTab === 'setup' ? 'active' : ''}`}
            >
              <Briefcase size={20} className="nav-link-icon" />
              Interview Setup
            </button>
          </li>
          <li className="nav-item">
            <button
              disabled={!screeningResult}
              onClick={() => setActiveTab('screening')}
              className={`nav-link ${activeTab === 'screening' ? 'active' : ''}`}
            >
              <FileText size={20} className="nav-link-icon" />
              Resume Screening
            </button>
          </li>
          <li className="nav-item">
            <button
              disabled={!sessionData}
              onClick={() => setActiveTab('interview')}
              className={`nav-link ${activeTab === 'interview' ? 'active' : ''}`}
            >
              <Play size={20} className="nav-link-icon" />
              Live Simulation
            </button>
          </li>
          <li className="nav-item">
            <button
              disabled={!evaluationReport}
              onClick={() => setActiveTab('evaluation')}
              className={`nav-link ${activeTab === 'evaluation' ? 'active' : ''}`}
            >
              <Award size={20} className="nav-link-icon" />
              Performance Report
            </button>
          </li>
          <li className="nav-item" style={{ marginTop: '20px', paddingTop: '20px', borderTop: '1px solid var(--glass-border)' }}>
            <button
              onClick={handleLoadHistory}
              className={`nav-link ${activeTab === 'history' ? 'active' : ''}`}
            >
              <Clock size={20} className="nav-link-icon" />
              MySQL Logs history
            </button>
          </li>
        </ul>

        <div className="sidebar-footer">
          <button
            onClick={toggleTheme}
            type="button"
            className="btn btn-secondary"
            style={{
              width: '100%',
              marginBottom: '12px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              padding: '10px'
            }}
          >
            {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
            {theme === 'dark' ? 'Light Mode' : 'Dark Mode'}
          </button>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Status: Database Ready</p>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="main-content">
        
        {/* VIEW 1: INTERVIEW SETUP */}
        {activeTab === 'setup' && (
          <>
            <div className="content-header">
              <div>
                <h2>Preparation & Setup</h2>
                <p>Upload a candidate resume, specify targets, and configure the interview generation system.</p>
              </div>
            </div>

            <form onSubmit={handleParseAndScreen} className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              <div className="form-group">
                <label><FileText size={18} /> Candidate Resume (PDF)</label>
                <div
                  className={`file-drop-container ${isDragging ? 'active' : ''}`}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  onClick={() => fileInputRef.current.click()}
                >
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileChange}
                    accept="application/pdf"
                    style={{ display: 'none' }}
                  />
                  <Upload size={40} className="file-drop-icon" />
                  <div className="file-drop-text">
                    <h4>Drag & Drop resume file here</h4>
                    <p>Or click to browse from files (PDF format only)</p>
                  </div>
                  {selectedFile && (
                    <div className="file-selected-badge" onClick={(e) => e.stopPropagation()}>
                      <CheckCircle2 size={16} /> {selectedFile.name} ({(selectedFile.size / 1024).toFixed(0)} KB)
                    </div>
                  )}
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label><Briefcase size={18} /> Job Target Profile</label>
                  <select
                    className="select-box"
                    value={selectedRoleKey}
                    onChange={(e) => { setSelectedRoleKey(e.target.value); setCustomRoleTitle(''); }}
                  >
                    {roles.map((r) => (
                      <option key={r.key} value={r.key}>{r.title}</option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label><Star size={18} /> Questions Count</label>
                  <input
                    type="number"
                    min="1"
                    max="20"
                    className="input-text"
                    value={numQuestions}
                    onChange={(e) => setNumQuestions(e.target.value)}
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label><Play size={18} /> Question Source</label>
                  <select
                    className="select-box"
                    value={questionSource}
                    onChange={(e) => setQuestionSource(e.target.value)}
                  >
                    <option value="ai">Generate New Questions (Gemini AI)</option>
                    <option value="db">Use Seeded Question Pool (Database)</option>
                  </select>
                </div>

                <div className="form-group" style={{ justifyContent: 'center', paddingTop: '20px' }}>
                  <label style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <input
                      type="checkbox"
                      checked={saveToDb}
                      disabled={questionSource === 'db'}
                      onChange={(e) => setSaveToDb(e.target.checked)}
                      style={{ width: '18px', height: '18px', cursor: 'pointer' }}
                    />
                    Save AI-generated questions to DB pool
                  </label>
                </div>
              </div>



              <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '10px' }}>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={isParsing || !selectedFile}
                >
                  {isParsing ? (
                    <>
                      <RefreshCw className="spinner" size={18} />
                      Parsing Resume & Run Assessment...
                    </>
                  ) : (
                    <>
                      Run Resume Screening & Assessment
                      <ArrowRight size={18} />
                    </>
                  )}
                </button>
              </div>
            </form>
          </>
        )}

        {/* VIEW 2: RESUME SCREENING */}
        {activeTab === 'screening' && screeningResult && (
          <>
            <div className="content-header">
              <div>
                <h2>Resume Screening Assessment</h2>
                <p>Predictive match score computed using a Simple Linear Regression model based on skills and experience matches.</p>
              </div>
              <button onClick={handleReset} className="btn btn-secondary">
                <RefreshCw size={18} /> Re-Upload
              </button>
            </div>

            {!candidateId && (
              <div className="glass-card" style={{ borderColor: 'var(--danger)', background: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)', marginBottom: '20px', padding: '16px', display: 'flex', alignItems: 'center', gap: '12px' }}>
                <AlertCircle size={20} />
                <div>
                  <strong>Database Offline:</strong> Connection to MySQL database failed. You will not be able to start or save the interview. Please ensure your MySQL server is running and configured correctly in <code>db_helper.py</code>.
                </div>
              </div>
            )}

            <div className="screening-container">
              {/* Profile Card */}
              <div className="glass-card">
                <div className="profile-section">
                  <h3><User size={20} style={{ verticalAlign: 'middle', marginRight: '8px' }} /> Candidate Profile Data</h3>
                  <div className="info-row">
                    <span>Name</span>
                    <span>{candidateName}</span>
                  </div>
                  <div className="info-row">
                    <span>Target Role</span>
                    <span>{screeningResult.details ? resumeData.role_title : 'N/A'}</span>
                  </div>
                  <div className="info-row">
                    <span>Experience Years</span>
                    <span>{formatExperienceYears(resumeData.experience_years)}</span>
                  </div>
                  <div className="info-row">
                    <span>Assessed Level</span>
                    <span>{resumeData.difficulty.toUpperCase()}</span>
                  </div>
                </div>

                <div style={{ marginTop: '24px' }}>
                  <h4 style={{ fontSize: '14px', fontWeight: '700', color: 'var(--text-muted)', marginBottom: '10px' }}>Matched Hard Skills</h4>
                  <div className="skills-list">
                    {screeningResult.details.hard_matched.map((s) => (
                      <span key={s} className="skill-tag" style={{ borderColor: 'rgba(20, 184, 166, 0.4)', color: 'var(--secondary)' }}>{s}</span>
                    ))}
                    {screeningResult.details.hard_matched.length === 0 && <span style={{ color: 'var(--text-muted)' }}>None matched</span>}
                  </div>
                </div>

                <div style={{ marginTop: '20px' }}>
                  <h4 style={{ fontSize: '14px', fontWeight: '700', color: 'var(--text-muted)', marginBottom: '10px' }}>Matched Soft Skills</h4>
                  <div className="skills-list">
                    {screeningResult.details.soft_matched.map((s) => (
                      <span key={s} className="skill-tag" style={{ borderColor: 'rgba(16, 185, 129, 0.4)', color: 'var(--success)' }}>{s}</span>
                    ))}
                    {screeningResult.details.soft_matched.length === 0 && <span style={{ color: 'var(--text-muted)' }}>None matched</span>}
                  </div>
                </div>
              </div>

              {/* Match Score Regression Breakdown */}
              <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                <div className="score-section">
                  <h3>Linear Regression Prediction</h3>
                  
                  <div className="score-percentage">
                    {screeningResult.match_score}% <span>Match Score</span>
                  </div>

                  <div style={{ marginBottom: '16px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '4px' }}>
                      <span style={{ color: 'var(--text-muted)' }}>Decision Outcome</span>
                      <span style={{ fontWeight: '700' }}>
                        {screeningResult.passed ? (
                          <span className="badge badge-pass">PASSED</span>
                        ) : (
                          <span className="badge badge-fail">REJECTED</span>
                        )}
                      </span>
                    </div>
                  </div>

                  <div className="score-metric">
                    <div className="score-header">
                      <span>Hard Skills match (50% weight)</span>
                      <span>{(screeningResult.details.hard_ratio * 100).toFixed(0)}%</span>
                    </div>
                    <div className="progress-bar-container">
                      <div className="progress-bar-fill" style={{ width: `${screeningResult.details.hard_ratio * 100}%` }}></div>
                    </div>
                  </div>

                  <div className="score-metric">
                    <div className="score-header">
                      <span>Experience match (30% weight)</span>
                      <span>{(screeningResult.details.exp_ratio * 100).toFixed(0)}%</span>
                    </div>
                    <div className="progress-bar-container">
                      <div className="progress-bar-fill" style={{ width: `${screeningResult.details.exp_ratio * 100}%` }}></div>
                    </div>
                  </div>

                  <div className="score-metric">
                    <div className="score-header">
                      <span>Soft Skills match (20% weight)</span>
                      <span>{(screeningResult.details.soft_ratio * 100).toFixed(0)}%</span>
                    </div>
                    <div className="progress-bar-container">
                      <div className="progress-bar-fill" style={{ width: `${screeningResult.details.soft_ratio * 100}%` }}></div>
                    </div>
                  </div>
                </div>

                <div style={{ borderTop: '1px solid var(--glass-border)', paddingTop: '20px', display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
                  {!screeningResult.passed ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--danger)', fontSize: '13px' }}>
                      <AlertCircle size={16} /> Minimum score required to unlock interview is 40%.
                    </div>
                  ) : (
                    <button onClick={handleStartInterview} className="btn btn-success">
                      Unlock & Start Interview Simulator
                      <Play size={16} />
                    </button>
                  )}
                </div>
              </div>
            </div>

            {/* Screening Text Output */}
            <div className="glass-card">
              <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '16px' }}>Detailed Screening Report</h3>
              <pre className="screening-raw-report">
                {screeningResult.report_text}
              </pre>
            </div>
          </>
        )}

        {/* VIEW 3: LIVE INTERVIEW SIMULATION */}
        {activeTab === 'interview' && sessionData && (
          <>
            <div className="content-header">
              <div>
                <h2>Interview Simulation</h2>
                <p>Simulating role-based behavioral and technical questions for <strong>{resumeData.role_title} ({sessionData.difficulty.toUpperCase()} level)</strong>.</p>
              </div>
              <button onClick={handleReset} className="btn btn-danger">
                End Simulation
              </button>
            </div>

            <div className="chat-window">
              <div className="chat-header">
                <div className="chat-title-info">
                  <div className="chat-indicator"></div>
                  <span style={{ fontWeight: '700' }}>Active Interview Simulator</span>
                </div>
                <span style={{ color: 'var(--text-muted)', fontSize: '14px' }}>
                  Question {currentQuestionIdx + 1} of {sessionData.questions.length}
                </span>
              </div>

              <div className="chat-messages">
                {/* Simulated conversation history */}
                {sessionData.questions.slice(0, isTyping ? currentQuestionIdx : currentQuestionIdx + 1).map((q, idx) => {
                  const hasAnswer = idx < candidateAnswers.length;
                  
                  return (
                    <React.Fragment key={idx}>
                      {/* Question bubble */}
                      <div className="message-bubble message-system">
                        <div className="message-meta-container">
                          <div className="avatar avatar-system"><Cpu size={16} /></div>
                          <div className="message-meta">INTERVIEWER (AI)</div>
                          <button 
                            type="button" 
                            className="btn-tts" 
                            onClick={() => speakQuestion(q.question_text)} 
                            title="Read Question Aloud"
                          >
                            <Volume2 size={14} />
                          </button>
                        </div>
                        <div className="message-text-content">
                          {q.question_text}
                        </div>
                        {q.reference_answer && (
                          <div style={{ marginTop: '8px', fontSize: '12px', borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '4px', color: 'var(--secondary)' }}>
                            [Database Reference Answer Enabled]
                          </div>
                        )}
                      </div>

                      {/* Candidate Answer bubble */}
                      {hasAnswer && (
                        <div className="message-bubble message-candidate">
                          <div className="message-meta-container">
                            <div className="message-meta">CANDIDATE (YOU)</div>
                            <div className="avatar avatar-candidate"><User size={16} /></div>
                          </div>
                          <div className="message-text-content">
                            {candidateAnswers[idx]}
                          </div>
                        </div>
                      )}
                    </React.Fragment>
                  );
                })}

                {isTyping && (
                  <div className="message-bubble message-system">
                    <div className="message-meta-container">
                      <div className="avatar avatar-system"><Cpu size={16} /></div>
                      <div className="message-meta">INTERVIEWER (AI) is thinking...</div>
                    </div>
                    <div className="typing-indicator">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                )}
                <div ref={chatBottomRef}></div>
              </div>

              {/* Sound Wave Animation when recording */}
              {isListening && (
                <div className="voice-status-container">
                  <div className="soundwave">
                    <div className="bar"></div>
                    <div className="bar"></div>
                    <div className="bar"></div>
                    <div className="bar"></div>
                    <div className="bar"></div>
                    <div className="bar"></div>
                    <div className="bar"></div>
                    <div className="bar"></div>
                  </div>
                  <span className="voice-status-text">Recording... {formatTime(recordingTime)}</span>
                </div>
              )}

              {/* Input section */}
              <form onSubmit={handleSubmitAnswer} className="chat-input-area">
                <div className="chat-input-row">
                  <button
                    type="button"
                    onClick={toggleListening}
                    className={`btn-voice ${isListening ? 'active' : ''}`}
                    title={isListening ? "Stop Listening" : "Speak Response (Voice Mode)"}
                    disabled={isTyping}
                  >
                    {isListening ? <MicOff size={20} /> : <Mic size={20} />}
                  </button>

                  <textarea
                    className="chat-input-box"
                    placeholder={isListening ? "Listening... speak into your mic." : "Type your answer or click the microphone to speak..."}
                    value={activeAnswerText}
                    onChange={(e) => setActiveAnswerText(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && e.ctrlKey) {
                        e.preventDefault();
                        handleSubmitAnswer();
                      }
                    }}
                    style={{ height: '80px' }}
                    disabled={isTyping}
                  />

                  <button 
                    type="submit" 
                    className="btn btn-primary btn-chat-submit" 
                    style={{ padding: '0 28px', height: '80px' }}
                    disabled={isTyping}
                  >
                    {currentQuestionIdx + 1 === sessionData.questions.length ? 'Submit' : 'Next'}
                    <Send size={18} />
                  </button>
                </div>
                <div className="chat-shortcuts">
                  <span>Press <kbd style={{ padding: '2px 4px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px' }}>Ctrl + Enter</kbd> to submit response.</span>
                  <span style={{ color: 'var(--warning)', cursor: 'pointer' }} onClick={handleSubmitAnswer}>
                    Skip Question
                  </span>
                </div>
              </form>
            </div>
          </>
        )}

        {/* VIEW 4: PERFORMANCE EVALUATION */}
        {activeTab === 'evaluation' && evaluationReport && (
          <>
            <div className="content-header">
              <div>
                <h2>Interview Performance Report</h2>
                <p>Evaluation completed successfully. Scores and feedback logged to local MySQL DB.</p>
              </div>
              <div style={{ display: 'flex', gap: '12px' }}>
                <button onClick={handleLoadHistory} className="btn btn-secondary">
                  <Clock size={16} /> History logs
                </button>
                <button onClick={handleReset} className="btn btn-primary">
                  Start New Interview
                </button>
              </div>
            </div>

            <div className="glass-card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '20px' }}>
              <div style={{ display: 'flex', gap: '24px', alignItems: 'center' }}>
                <div style={{
                  width: '90px',
                  height: '90px',
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '24px',
                  fontWeight: '800',
                  boxShadow: '0 5px 15px var(--primary-glow)'
                }}>
                  {evaluationReport.overall_score}
                </div>
                <div>
                  <h3 style={{ fontSize: '20px', fontWeight: '700' }}>Overall Grading Score</h3>
                  <p style={{ color: 'var(--text-muted)', fontSize: '14px', marginTop: '4px' }}>Average score graded out of 10 across all responses.</p>
                </div>
              </div>

              <div>
                <span className="badge badge-info" style={{ fontSize: '14px', padding: '10px 20px' }}>
                  {evaluationReport.status}
                </span>
              </div>
            </div>

            <div className="eval-grid">
              <h3 style={{ fontSize: '18px', fontWeight: '700', borderBottom: '1px solid var(--glass-border)', paddingBottom: '12px' }}>Response Breakdown</h3>
              {sessionData && sessionData.questions.map((q, idx) => {
                const rawEval = evaluationReport.evaluations[idx];
                const parsed = parseEvaluationString(rawEval);
                return (
                  <div key={idx} className="glass-card eval-card">
                    <div className="eval-card-header">
                      <div className="eval-question">Q{idx + 1}: {q.question_text}</div>
                      <div className="eval-score-badge">{parsed.score}</div>
                    </div>

                    <div className="eval-answer-block">
                      <div style={{ color: 'var(--text-muted)', fontSize: '12px', marginBottom: '4px', fontWeight: '600' }}>YOUR ANSWER:</div>
                      {candidateAnswers[idx] || '[Skipped]'}
                    </div>

                    {q.reference_answer && (
                      <div className="eval-answer-block" style={{ borderLeftColor: 'var(--secondary)', background: 'rgba(20,184,166,0.03)', marginTop: '-8px', marginBottom: '14px' }}>
                        <div style={{ color: 'var(--secondary)', fontSize: '12px', marginBottom: '4px', fontWeight: '600' }}>STANDARD REFERENCE ANSWER:</div>
                        {q.reference_answer}
                      </div>
                    )}

                    <div className="eval-details-row">
                      <div>
                        <div className="eval-feedback-label">
                          <CheckCircle2 size={15} /> Feedback
                        </div>
                        <p style={{ color: 'var(--text-muted)' }}>{parsed.feedback}</p>
                      </div>
                      <div>
                        <div className="eval-improve-label">
                          <AlertCircle size={15} /> Key Improvements
                        </div>
                        <p style={{ color: 'var(--text-muted)' }}>{parsed.improve}</p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </>
        )}

        {/* VIEW 5: MYSQL SESSION LOGS HISTORY */}
        {activeTab === 'history' && (
          <>
            <div className="content-header">
              <div>
                <h2>MySQL Logs History</h2>
                <p>Database transaction records. Read directly from local database tables.</p>
              </div>
              <button onClick={handleLoadHistory} className="btn btn-secondary">
                <RefreshCw size={16} /> Refresh logs
              </button>
            </div>

            {selectedHistoryId === null ? (
              <div className="history-table-container">
                {isLoadingHistory ? (
                  <div style={{ padding: '60px', textAlign: 'center', color: 'var(--text-muted)' }}>
                    <RefreshCw className="spinner" size={24} style={{ marginBottom: '12px' }} />
                    <p>Fetching logs from MySQL db...</p>
                  </div>
                ) : historyList.length === 0 ? (
                  <div style={{ padding: '60px', textAlign: 'center', color: 'var(--text-muted)' }}>
                    <AlertCircle size={32} style={{ marginBottom: '12px', color: 'var(--warning)' }} />
                    <p>No logged sessions found in database.</p>
                  </div>
                ) : (
                  <table className="history-table">
                    <thead>
                      <tr>
                        <th>Session ID</th>
                        <th>Candidate</th>
                        <th>Job Role</th>
                        <th>Difficulty</th>
                        <th>Score</th>
                        <th>Date</th>
                        <th>Final Status</th>
                        <th></th>
                      </tr>
                    </thead>
                    <tbody>
                      {historyList.map((row) => (
                        <tr key={row.session_id} onClick={() => handleViewSessionDetail(row.session_id)}>
                          <td>#{row.session_id}</td>
                          <td>
                            <div style={{ fontWeight: '600' }}>{row.full_name}</div>
                            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{formatExperienceYears(row.experience_years)} Experience</div>
                          </td>
                          <td>{row.job_role}</td>
                          <td><span className="badge badge-info">{row.difficulty}</span></td>
                          <td>
                            <span style={{ fontWeight: '800', color: 'var(--primary)' }}>
                              {row.overall_score !== null ? `${row.overall_score}/10` : 'N/A'}
                            </span>
                          </td>
                          <td>{row.interview_date ? new Date(row.interview_date).toLocaleString() : 'N/A'}</td>
                          <td>
                            {row.final_feedback ? (
                              <span className={`badge ${row.final_feedback.includes('Highly') ? 'badge-pass' : row.final_feedback.includes('Needs') ? 'badge-fail' : 'badge-info'}`}>
                                {row.final_feedback}
                              </span>
                            ) : (
                              <span style={{ color: 'var(--text-muted)' }}>Draft / Skipped</span>
                            )}
                          </td>
                          <td>
                            <ChevronRight size={18} style={{ color: 'var(--text-muted)' }} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            ) : (
              // Details of history log session
              <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                <div style={{ display: 'flex', gap: '12px' }}>
                  <button onClick={() => setSelectedHistoryId(null)} className="btn btn-secondary">
                    <ChevronLeft size={16} /> Back to logs list
                  </button>
                </div>

                {isLoadingHistoryDetail ? (
                  <div className="glass-card" style={{ padding: '60px', textAlign: 'center', color: 'var(--text-muted)' }}>
                    <RefreshCw className="spinner" size={24} style={{ marginBottom: '12px' }} />
                    <p>Loading database records...</p>
                  </div>
                ) : historyDetail === null ? (
                  <div className="glass-card" style={{ padding: '40px', textAlign: 'center', color: 'var(--danger)' }}>
                    <AlertCircle size={32} style={{ marginBottom: '12px' }} />
                    <p>Session records not found.</p>
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
                    {/* Session overview */}
                    <div className="glass-card" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px' }}>
                      <div>
                        <div style={{ fontSize: '12px', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '4px' }}>Candidate Name</div>
                        <div style={{ fontSize: '18px', fontWeight: '700' }}>{historyDetail.session.full_name}</div>
                        <div style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '2px' }}>{historyDetail.session.email}</div>
                      </div>
                      <div>
                        <div style={{ fontSize: '12px', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '4px' }}>Target Job Role</div>
                        <div style={{ fontSize: '18px', fontWeight: '700' }}>{historyDetail.session.job_role}</div>
                        <div style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '2px' }}>Difficulty: {historyDetail.session.difficulty}</div>
                      </div>
                      <div>
                        <div style={{ fontSize: '12px', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '4px' }}>Score Summary</div>
                        <div style={{ fontSize: '18px', fontWeight: '700', color: 'var(--primary)' }}>
                          {historyDetail.summary ? `${historyDetail.summary.overall_score}/10` : 'N/A'}
                        </div>
                        <div style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '2px' }}>
                          Status: {historyDetail.summary ? historyDetail.summary.final_feedback : 'N/A'}
                        </div>
                      </div>
                      <div>
                        <div style={{ fontSize: '12px', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '4px' }}>Interview Date</div>
                        <div style={{ fontSize: '15px', fontWeight: '600' }}>
                          {new Date(historyDetail.session.interview_date).toLocaleString()}
                        </div>
                      </div>
                    </div>

                    {/* Candidate Skills */}
                    <div className="glass-card">
                      <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '14px' }}>Skills Registered in Session</h3>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                        {historyDetail.skills.map((s, i) => (
                          <span key={i} className={`skill-tag ${s.skill_type === 'Hard Skill' ? 'badge-info' : 'badge-pass'}`} style={{ border: '1px solid transparent' }}>
                            {s.skill_name} ({s.skill_type})
                          </span>
                        ))}
                        {historyDetail.skills.length === 0 && <span style={{ color: 'var(--text-muted)' }}>No skills found.</span>}
                      </div>
                    </div>

                    {/* Question Answers Details */}
                    <div className="eval-grid">
                      <h3 style={{ fontSize: '16px', fontWeight: '700', borderBottom: '1px solid var(--glass-border)', paddingBottom: '10px' }}>Q&A Responses</h3>
                      {historyDetail.qa.map((qa, i) => (
                        <div key={i} className="glass-card eval-card">
                          <div className="eval-card-header">
                            <div className="eval-question">Q{i + 1}: {qa.question_text}</div>
                          </div>
                          <div className="eval-answer-block">
                            <div style={{ color: 'var(--text-muted)', fontSize: '12px', marginBottom: '4px', fontWeight: '600' }}>SUBMITTED RESPONSE:</div>
                            {qa.answer_text}
                          </div>
                        </div>
                      ))}
                      {historyDetail.qa.length === 0 && (
                        <div className="glass-card" style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>
                          No responses captured. The session may have been aborted.
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}
          </>
        )}

      </main>

      {/* FULLSCREEN AUTOMATIC EVALUATION GRADING LOADER OVERLAY */}
      {isSubmitting && (
        <div className="loading-overlay">
          <div className="spinner"></div>
          <div className="loading-text">
            <h3>Analyzing Interview Performance</h3>
            <p>{gradingProgressMsg}</p>
          </div>
        </div>
      )}
    </div>
  );
}
