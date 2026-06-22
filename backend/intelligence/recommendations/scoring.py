from backend.intelligence.recommendations.recommendation_types import RecommendationSeverity

def calculate_priority(
    base_risk_score: int, 
    is_exposed: bool, 
    criticality_score: int, 
    sensitivity_level: str, 
    blast_radius_size: int
) -> RecommendationSeverity:
    """
    Deterministic priority calculation for recommendations.
    Max practical score ~100.
    """
    score = 0
    
    # 1. Base Risk (0-100)
    # If the base node already has a high risk score from the RiskAnalyzer
    score += (base_risk_score * 0.3)
    
    # 2. Exposure
    if is_exposed:
        score += 40
        
    # 3. Criticality (0-100+)
    score += (criticality_score * 0.2)
    
    # 4. Sensitivity
    if sensitivity_level == "Restricted":
        score += 30
    elif sensitivity_level == "Confidential":
        score += 15
        
    # 5. Blast Radius Size
    if blast_radius_size > 10:
        score += 20
    elif blast_radius_size > 3:
        score += 10
        
    if score >= 80:
        return RecommendationSeverity.CRITICAL
    elif score >= 50:
        return RecommendationSeverity.HIGH
    elif score >= 25:
        return RecommendationSeverity.MEDIUM
    else:
        return RecommendationSeverity.LOW
