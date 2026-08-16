# ==============================================================================
# 🏟️ BIOMETRIC COLISEUM TOURNAMENTS & CHAMPIONSHIP MATRIX
# ==============================================================================
# Define your cross-network training battles and competitive ladder brackets.
# The calculation engine cross-references this matrix to scan your data for arena medals.

ARENA_TOURNAMENTS_REGISTRY = {
    "coliseum_sprint_clash": {
        "title": "Coliseum Speed Clash",
        "arena_icon": "🔱",
        "target_distance": 3.11,          # 5K tournament match line
        "pace_gold_seconds": 380,         # Sub-6:20 /mi pace rule
        "xp_reward": 500,
        "desc": "Compete on a verified 5K split distance matrix to secure arena rank."
    },
    "alpine_vert_challenge": {
        "title": "Alpine Peak Vert Challenge",
        "arena_icon": "🏔️",
        "target_elevation_ft": 2500,      # Single workout ascent goal
        "xp_reward": 750,
        "desc": "Accumulate maximum vertical elevation feet inside an isolated training run."
    }
}

