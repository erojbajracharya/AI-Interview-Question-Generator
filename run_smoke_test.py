from resume_parser import parse_text

SAMPLE_1 = """
John Doe
Professional Summary
Experienced software engineer with 6 years of experience in backend development.

Technical Skills
Python, Django, PostgreSQL, Docker, REST APIs

Work Experience
Jun 2018 - Present: Senior Software Engineer at Acme Corp
"""

SAMPLE_2 = """
Jane Smith
Summary: 3 yrs experience in data analysis and machine learning.

Skills & Tools
- Python (pandas, scikit-learn)
- SQL; Tableau; AWS

Experience
2017 - 2020 Data Analyst at DataCo
2020 - present Data Scientist at ML Inc
"""


def run():
    for i, s in enumerate([SAMPLE_1, SAMPLE_2], start=1):
        print(f"--- SAMPLE {i} ---")
        out = parse_text(s)
        print(out)

if __name__ == '__main__':
    run()
