"""RBAC — roles, department permissions, demo users."""

ROLES = {
    "admin": {
        "label": "Administrator", "icon": "shield",
        "color": "#818cf8",
        "departments": ["hr","finance","marketing","legal","engineering","general"],
        "features": ["chat","upload","analytics","audit","manage_users"],
    },
    "hr": {
        "label": "HR Manager", "icon": "users",
        "color": "#22d3ee",
        "departments": ["hr","general"],
        "features": ["chat","upload","analytics"],
    },
    "finance": {
        "label": "Finance Analyst", "icon": "trending-up",
        "color": "#34d399",
        "departments": ["finance","general"],
        "features": ["chat","upload","analytics"],
    },
    "marketing": {
        "label": "Marketing Lead", "icon": "bar-chart-2",
        "color": "#fbbf24",
        "departments": ["marketing","general"],
        "features": ["chat","upload"],
    },
    "engineering": {
        "label": "Engineer", "icon": "cpu",
        "color": "#f87171",
        "departments": ["engineering","general"],
        "features": ["chat","upload","analytics"],
    },
    "employee": {
        "label": "Employee", "icon": "user",
        "color": "#94a3b8",
        "departments": ["general"],
        "features": ["chat"],
    },
}

DEPARTMENTS = {
    "hr":          {"label": "Human Resources", "color": "#22d3ee"},
    "finance":     {"label": "Finance",          "color": "#34d399"},
    "marketing":   {"label": "Marketing",        "color": "#fbbf24"},
    "legal":       {"label": "Legal",            "color": "#818cf8"},
    "engineering": {"label": "Engineering",      "color": "#f87171"},
    "general":     {"label": "General",          "color": "#94a3b8"},
}

# Demo users — in production replace with a real DB
DEMO_USERS = {
    "admin@nexus.ai":      {"name": "Alex Chen",      "password": "admin123",      "role": "admin",       "initials": "AC"},
    "hr@nexus.ai":         {"name": "Priya Sharma",   "password": "hr123",         "role": "hr",          "initials": "PS"},
    "finance@nexus.ai":    {"name": "Rahul Gupta",    "password": "finance123",    "role": "finance",     "initials": "RG"},
    "marketing@nexus.ai":  {"name": "Sneha Patel",    "password": "marketing123",  "role": "marketing",   "initials": "SP"},
    "dev@nexus.ai":        {"name": "Arjun Nair",     "password": "dev123",        "role": "engineering", "initials": "AN"},
    "emp@nexus.ai":        {"name": "Meera Iyer",     "password": "emp123",        "role": "employee",    "initials": "MI"},
}

def get_departments(role: str) -> list[str]:
    return ROLES.get(role, {}).get("departments", ["general"])

def has_feature(role: str, feature: str) -> bool:
    return feature in ROLES.get(role, {}).get("features", [])
