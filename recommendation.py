from models import Policy

def get_recommendations(user, insurance_type='all', max_budget=1000):
    policies = Policy.query.filter(Policy.premium <= max_budget)
    if insurance_type != 'all':
        policies = policies.filter_by(type=insurance_type)
    policies = policies.all()

    if not policies:
        return []

    user_risk = {"non-smoker": "low", "smoker": "high"}.get(user.health_status, "medium")
    user_lifestyle = {"active": "low", "sedentary": "medium"}.get(user.lifestyle, "medium")
    occupation_risk = {"office": "low", "construction": "high"}.get(user.occupation, "medium")

    recommendations = []
    for policy in policies:
        score = 0
        if policy.min_age <= user.age <= policy.max_age:
            score += 50
        if policy.risk_level == user_risk:
            score += 30
        if policy.risk_level == user_lifestyle:
            score += 10
        if policy.risk_level == occupation_risk:
            score += 10
        if score > 20:  # Only include policies with a decent score
            recommendations.append({
                "id": policy.id,
                "name": policy.name,
                "type": policy.type,
                "premium": policy.premium,
                "coverage": policy.coverage,
                "score": score,
                "recommendation": f"Recommended {policy.name} for your {user.age}-year-old {user.occupation} profile with {user.lifestyle} lifestyle and {user.health_status} health status."
            })

    return sorted(recommendations, key=lambda x: x['score'], reverse=True)[:3]  # Top 3 recommendations