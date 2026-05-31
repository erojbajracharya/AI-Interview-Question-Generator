def generate_overall_assessment(evaluations: list) -> dict:
    """
    Receives multiple interview evaluations and aggregates them into a final assessment.

    Parameters:
        evaluations (list): List of dictionaries, each containing evaluation details:
                            [
                                {
                                    "score": int,
                                    "strengths": list of str,
                                    "weaknesses": list of str,
                                    "suggestions": list of str
                                },
                                ...
                            ]

    Returns:
        dict: The consolidated final assessment:
              {
                  "overall_score": int,
                  "performance_level": str,
                  "summary": str,
                  "strengths": list of str,
                  "improvements": list of str
              }
    """
    # Handle empty list of evaluations gracefully
    if not evaluations:
        return {
            "overall_score": 0,
            "performance_level": "Needs Improvement",
            "summary": "No evaluations were provided.",
            "strengths": [],
            "improvements": []
        }

    # Extract score from each evaluation and compute average (scaled to 100)
    scores = [item.get("score", 0) for item in evaluations]
    avg_score = sum(scores) / len(evaluations)
    overall_score = round(avg_score * 10)

    # Determine performance level based on rules
    if 90 <= overall_score <= 100:
        performance_level = "Excellent"
    elif 75 <= overall_score <= 89:
        performance_level = "Good"
    elif 60 <= overall_score <= 74:
        performance_level = "Average"
    else:
        performance_level = "Needs Improvement"

    # Consolidate strengths and improvements across all questions (removing duplicates)
    strengths = []
    improvements = []

    for item in evaluations:
        # Accumulate unique strengths
        for strength in item.get("strengths", []):
            if strength and strength not in strengths:
                strengths.append(strength)
        
        # Accumulate unique improvements (from both suggestions and weaknesses)
        for suggestion in item.get("suggestions", []):
            if suggestion and suggestion not in improvements:
                improvements.append(suggestion)
        for weakness in item.get("weaknesses", []):
            if weakness and weakness not in improvements:
                improvements.append(weakness)

    # Construct overall summary text
    summary = (
        f"The candidate achieved an overall score of {overall_score}/100, "
        f"placing them in the '{performance_level}' performance tier. "
        f"This is based on an average evaluation of {len(evaluations)} question(s)."
    )

    return {
        "overall_score": overall_score,
        "performance_level": performance_level,
        "summary": summary,
        "strengths": strengths,
        "improvements": improvements
    }

if __name__ == "__main__":
    # Test example
    print("--- Running Assessment Aggregator Test ---")
    
    test_evaluations = [
        {
            "score": 8,
            "strengths": ["Demonstrated strong logic", "Explained mutable/immutable well"],
            "suggestions": ["Could mention key-value pair characteristics"],
            "weaknesses": ["Missed explaining garbage collection differences"]
        },
        {
            "score": 7,
            "strengths": ["Good verbal communication"],
            "suggestions": ["Practice structured answering methods"],
            "weaknesses": ["Slightly disorganized structure"]
        },
        {
            "score": 9,
            "strengths": ["Perfect technical explanation", "Demonstrated strong logic"],
            "suggestions": ["Keep up the good work"],
            "weaknesses": []
        }
    ]

    result = generate_overall_assessment(test_evaluations)
    
    import json
    print("\nConsolidated Final Assessment:")
    print(json.dumps(result, indent=4))
