# -*- coding: utf-8 -*-
"""
CHAMPIONSHIP ARENA CONFIGURATION MANUAL (coliseum_config.py)
Declares data registries for competitive pacer rivals and global race tracks.
Includes athletic skill unlock thresholds and career mileage criteria barriers.
Supports explicit portrait artwork definitions and character emoji fallback routing.
"""

# =========================================================================
# 🏃‍♂️ PACER RIVALS ROSTER DIRECTORY (boss_catalog)
# Maps competitive opponents onto standard baseline running physics stats.
# Explicitly defines profile picture asset paths and fallback character icons.
# =========================================================================
boss_catalog = {
    'Kilian [GAZELLE]': {
        'fuel': 3, 
        'nitro': 4, 
        'torque': 6, 
        'gold_reward': 30, 
        'desc': '🧗 Kilian the Grade Specialist. Unmatched mountain single-track efficiency and vertical ascent climbing speed.',
        'icon': '🧗',
        'profile_pic': 'images/boss_profile/boss1.png',
        'unlock_criteria': {
            'min_orl_level': 1,
            'min_power_level': 3
        }
    },
    'Usain [CHEETAH]': {
        'fuel': 2, 
        'nitro': 9, 
        'torque': 1, 
        'gold_reward': 50, 
        'desc': '⚡ Usain the Sprint Phenomenon. Absolute maximum explosive power that dominates short stadium ovals.',
        'icon': '⚡',
        'profile_pic': 'images/boss_profile/boss2.png',
        'unlock_criteria': {
            'min_orl_level': 1,
            'min_efficiency_level': 3
        }
    },
    'Eliud [SPRINTER]': {
        'fuel': 5, 
        'nitro': 7, 
        'torque': 3, 
        'gold_reward': 40, 
        'desc': '🏃 Eliud the Cadence Rhythm Master. Maintains mechanical marathon pacelines on flat asphalt roads.',
        'icon': '🏃',
        'profile_pic': 'images/boss_profile/boss3.png',
        'unlock_criteria': {
            'min_orl_level': 3,
            'min_stamina_level': 4
        }
    },
    'Yiannis [STRIDER]': {
        'fuel': 9, 
        'nitro': 3, 
        'torque': 4, 
        'gold_reward': 65, 
        'desc': '🇬🇷 Yiannis the Endurance Beast. Relentless aerobic capacity engine tailored for 100-mile survival bounds.',
        'icon': '🇬🇷',
        'profile_pic': 'images/boss_profile/boss4.png',
        'unlock_criteria': {
            'min_orl_level': 5,
            'min_stamina_level': 6
        }
    },
    'Pre [ROADRUNNER]': {
        'fuel': 4, 
        'nitro': 6, 
        'torque': 2, 
        'gold_reward': 55, 
        'desc': '🌵 Pre the Desert Predator. High-tempo execution strategy focused on mid-distance track segments.',
        'icon': '🌵',
        'profile_pic': 'images/boss_profile/boss5.png', # Left as None to verify fallback to the '🌵' icon inside UI components
        'unlock_criteria': {
            'min_orl_level': 2,
            'min_efficiency_level': 4
        }
    },
    'Haile [FLASH]': {
        'fuel': 6, 
        'nitro': 8, 
        'torque': 4, 
        'gold_reward': 120, 
        'desc': '👑 Haile the Multi-Distance King. Flawless versatility balancing heavy endurance splits with extreme closing speed.',
        'icon': '👑',
        'profile_pic': 'images/boss_profile/boss6.png',
        'unlock_criteria': {
            'min_orl_level': 6,
            'min_stamina_level': 5,
            'min_efficiency_level': 5
        }
    }
}

# =========================================================================
# 🗺️ GLOBAL CIRCUIT CATALOG DIRECTORY (course_catalog)
# Details distance, vertical feet climbs, climate tags, and unlock metrics.
# Includes dedicated disk file path definitions for track illustration images.
# =========================================================================
course_catalog = {
    'Berlin Olympiastadion Track': {
        'dist': 0.25, 'elev': 0, 'bias': 'Speed', 'climate_tag': 'Neutral',
        'desc': '🇩🇪 The historic, lightning-fast 400m track in Germany.', 
        'strat': 'Pure anaerobic sprint power. Max out your stride parameters to slice lap splits.',
        'course_img': 'images/course_profile/berlin_olympiastadion.png',
        'unlock_criteria': {'min_orl_level': 1}
    },
    'Monaco Diamond League 1500m': {
        'dist': 0.93, 'elev': 2, 'bias': 'Speed', 'climate_tag': 'Neutral',
        'desc': '🇲🇨 Premium middle-distance stadium circuit on the Mediterranean coast.', 
        'strat': 'Aggressive threshold velocity test. Requires high Stride Efficiency rankings.',
        'course_img': 'images/course_profile/monaco_1500m.png',
        'unlock_criteria': {'min_orl_level': 2, 'min_efficiency_level': 3}
    },
    'Monza F1 Breaking2 Grid': {
        'dist': 1.50, 'elev': 0, 'bias': 'Speed', 'climate_tag': 'Neutral',
        'desc': '🇮🇹 The legendary flat Formula 1 tarmac in Italy used for elite marathon barriers.', 
        'strat': 'Dead flat, hyper-optimized racing lines. Keeps cadence velocity locked at high efficiency output.',
        'course_img': 'images/course_profile/monza_f1.png',
        'unlock_criteria': {'min_orl_level': 3, 'min_efficiency_level': 4}
    },
    'Boston Marathon (Hopkinton to Copley)': {
        'dist': 26.22, 'elev': 850, 'bias': 'Balanced', 'climate_tag': 'Neutral',
        'desc': '🇺🇸 World’s oldest annual marathon course, featuring Newton’s notorious Heartbreak Hill.', 
        'strat': 'Pushes both pacing endurance and descending muscle durability. Requires deep mileage foundations.',
        'course_img': 'images/course_profile/boston_marathon.png',
        'unlock_criteria': {'min_orl_level': 4, 'min_stamina_level': 4}
    },
    'London Marathon Highway Grid': {
        'dist': 26.22, 'elev': 120, 'bias': 'Speed', 'climate_tag': 'Neutral',
        'desc': '🇬🇧 Flat, fast road course tracing the River Thames alongside millions of roaring spectators.', 
        'strat': 'Elite pace execution circuit. Leverages high carbon-plated footwear and baseline speed turnover.',
        'course_img': 'images/course_profile/london_marathon.png',
        'unlock_criteria': {'min_orl_level': 4, 'min_stamina_level': 5}
    },
    'Berlin Speedway (World Record Flat)': {
        'dist': 26.22, 'elev': 45, 'bias': 'Speed', 'climate_tag': 'Neutral',
        'desc': '🇩🇪 The absolute flattest major marathon course on Earth. Home of human pacing limits.', 
        'strat': 'Shifts scoring weights heavily toward Stride Efficiency and split consistency metrics.',
        'course_img': 'images/course_profile/berlin_speedway.png',
        'unlock_criteria': {'min_orl_level': 5, 'min_stamina_level': 5, 'min_efficiency_level': 5}
    },
    'Zegama-Aizkorri Mountain Skyrun': {
        'dist': 26.10, 'elev': 8970, 'bias': 'Torque', 'climate_tag': 'Cold',
        'desc': '🇪🇸 Legendary technical alpine marathon in the Basque Country under heavy downpours.', 
        'strat': 'Absolute mountain torture. Shifts major physics weight to Climbing Power. Trail shoes are required.',
        'course_img': 'images/course_profile/zegama_skyrun.png',
        'unlock_criteria': {'min_orl_level': 5, 'min_power_level': 6}
    },
    'UTMB Mont-Blanc Core Loop': {
        'dist': 106.00, 'elev': 32800, 'bias': 'Fuel', 'climate_tag': 'Cold',
        'desc': '🇫🇷 The pinnacle of global trail running. Encircles the Mont-Blanc massif across France, Italy, and Switzerland.', 
        'strat': 'Extreme high-altitude ultramarathon. Pushes your Aerobic Stamina to absolute limits.',
        'course_img': 'images/course_profile/utmb_mont_blanc.png',
        'unlock_criteria': {'min_orl_level': 7, 'min_stamina_level': 7, 'min_power_level': 7}
    },
    'Western States 100 Canyons': {
        'dist': 100.00, 'elev': 18000, 'bias': 'Fuel', 'climate_tag': 'Hot',
        'desc': '🇺🇸 World’s oldest 100-mile trail race, tracing hot, rugged singletracks in California Sierra Nevada.', 
        'strat': 'Severe canyon heat endurance test. Maximizes Aerobic Capacity. Requires heat acclimatization history.',
        'course_img': 'images/course_profile/western_states_100.png',
        'unlock_criteria': {'min_orl_level': 7, 'min_stamina_level': 8, 'min_power_level': 6}
    },
    'Comrades Ultra Marathon (Up-Run)': {
        'dist': 54.00, 'elev': 5900, 'bias': 'Fuel', 'climate_tag': 'Hot',
        'desc': '🇿🇦 Legendary paved ultra between Durban and Pietermaritzburg in South Africa.', 
        'strat': 'Relentless highway climbing and muscle fatigue. Demands maximum long-run history boundaries.',
        'course_img': 'images/course_profile/comrades_ultra.png',
        'unlock_criteria': {'min_orl_level': 6, 'min_stamina_level': 6}
    },
    'UNM 400-Meter Olympic Track': {
        'dist': 0.25, 'elev': 0, 'bias': 'Speed', 'climate_tag': 'Neutral',
        'desc': '🏟️ Pure 400-meter oval track speedway at UNM in Albuquerque.', 
        'strat': 'Pure, absolute maximum velocity test. Focuses heavily on Stride Efficiency traits.',
        'course_img': 'images/course_profile/unm_400m_track.png',
        'unlock_criteria': {'min_orl_level': 1}
    },
    'UNM 800-Meter Tactical Oval': {
        'dist': 0.50, 'elev': 5, 'bias': 'Speed', 'climate_tag': 'Neutral',
        'desc': '⚡ Two-lap tactical middle-distance oval.', 
        'strat': 'Demands explosive initial acceleration balanced with high tempo focus.',
        'course_img': 'images/course_profile/unm_800m_oval.png',
        'unlock_criteria': {'min_orl_level': 1, 'min_efficiency_level': 2}
    },
    'Santa Fe 1600-Meter Milestoning Grid': {
        'dist': 1.00, 'elev': 25, 'bias': 'Speed', 'climate_tag': 'Neutral',
        'desc': '🏃 Classic 1-Mile premium high-altitude asphalt circuit.', 
        'strat': 'Tests anaerobic stride execution and efficiency markers.',
        'course_img': 'images/course_profile/santa_fe_1600m.png',
        'unlock_criteria': {'min_orl_level': 2}
    },
    'White Sands 5K Desert Horizon': {
        'dist': 3.11, 'elev': 40, 'bias': 'Speed', 'climate_tag': 'Hot',
        'desc': '☀️ Flat 5-Kilometer speedway loop across gypsum sands.', 
        'strat': 'Dead flat sands require high cadence. Favors elevated Stride Efficiency values.',
        'course_img': 'images/course_profile/white_sands_5k.png',
        'unlock_criteria': {'min_orl_level': 2}
    },
    'White Sands Desert Speedway': {
        'dist': 4.00, 'elev': 50, 'bias': 'Speed', 'climate_tag': 'Hot',
        'desc': '☀️ Extended dead-flat white gypsum dunes trail profile.', 
        'strat': 'Max out your sprint properties and heat resilience background.',
        'course_img': 'images/course_profile/white_sands_speedway.png',
        'unlock_criteria': {'min_orl_level': 2, 'min_efficiency_level': 3}
    },
    'Los Alamos Canyon Trail Loop': {
        'dist': 5.20, 'elev': 450, 'bias': 'Balanced', 'climate_tag': 'Neutral',
        'desc': '🏜️ Balanced canyon loop right in Los Alamos.', 
        'strat': 'Evenly distributes criteria weights across all physical fitness components.',
        'course_img': 'images/course_profile/los_alamos_canyon.png',
        'unlock_criteria': {'min_orl_level': 3}
    },
    'Bayo Canyon Track Circuit': {
        'dist': 6.00, 'elev': 180, 'bias': 'Speed', 'climate_tag': 'Neutral',
        'desc': '⚡ Flat, high-speed volcanic flats.', 
        'strat': 'Shifts substantial scoring advantages to your Stride Efficiency level.',
        'course_img': 'images/course_profile/bayo_canyon_circuit.png',
        'unlock_criteria': {'min_orl_level': 3, 'min_efficiency_level': 4}
    },
    'Acoma Pueblo Horizon Dash': {
        'dist': 6.20, 'elev': 300, 'bias': 'Speed', 'climate_tag': 'Hot',
        'desc': '🏜️ Fast, historic 10K high-desert dirt roads circling the Sky City mesa.', 
        'strat': 'Elite high-tempo acceleration course. Requires basic heat exposure metrics.',
        'course_img': 'images/course_profile/acoma_pueblo.png',
        'unlock_criteria': {'min_orl_level': 3, 'min_efficiency_level': 3}
    },
    'The Perimeter Mountain Loop': {
        'dist': 7.50, 'elev': 1250, 'bias': 'Torque', 'climate_tag': 'Neutral',
        'desc': '⛰️ Severe technical single-track mesa rim.', 
        'strat': 'Shifts structural scoring advantages heavily onto your active Climbing Power value.',
        'course_img': 'images/course_profile/perimeter_mountain.png',
        'unlock_criteria': {'min_orl_level': 4, 'min_power_level': 4}
    },
    'Taos Ski Valley Ridge Run': {
        'dist': 8.50, 'elev': 3100, 'bias': 'Torque', 'climate_tag': 'Cold',
        'desc': '❄️ Extreme technical sky-running circuit across high alpine scree fields.', 
        'strat': 'Hardcore mountain climbing test with cold environmental hazards.',
        'course_img': 'images/course_profile/taos_ski_valley.png',
        'unlock_criteria': {'min_orl_level': 4, 'min_power_level': 5}
    },
    'La Luz Trail (Sandia Peak)': {
        'dist': 9.00, 'elev': 3775, 'bias': 'Torque', 'climate_tag': 'Neutral',
        'desc': '🧗 Legendary vertical climbing beast in Albuquerque.', 
        'strat': 'Severe vertical torture test. Amplifies your Climbing Power demands to absolute levels.',
        'course_img': 'images/course_profile/la_luz_trail.png',
        'unlock_criteria': {'min_orl_level': 5, 'min_power_level': 5}
    },
    'Santa Fe Crest Trail Pipeline': {
        'dist': 12.00, 'elev': 2100, 'bias': 'Balanced', 'climate_tag': 'Cold',
        'desc': '🌲 Alpine single-track navigating high elevation heights from Ski Santa Fe.', 
        'strat': 'High-altitude lungs test. Evenly balanced criteria parameters.',
        'course_img': 'images/course_profile/santa_fe_crest.png',
        'unlock_criteria': {'min_orl_level': 4, 'min_stamina_level': 4}
    },
    'Gila Wilderness River Canyon': {
        'dist': 15.00, 'elev': 1100, 'bias': 'Fuel', 'climate_tag': 'Neutral',
        'desc': '🌲 Deep wilderness track with multiple rugged river crossings.', 
        'strat': 'Demands heavy endurance durability buffers and high apparel equipment stats.',
        'course_img': 'images/course_profile/gila_wilderness.png',
        'unlock_criteria': {'min_orl_level': 5, 'min_stamina_level': 5}
    },
    'Albuquerque Half-Marathon Highway': {
        'dist': 13.11, 'elev': 250, 'bias': 'Fuel', 'climate_tag': 'Neutral',
        'desc': '🇲🇽 Flat, paved continuous road thoroughfare tracing the Rio Grande.', 
        'strat': 'Shifts scoring formulas heavily into Aerobic Stamina (Endurance stability).',
        'course_img': 'images/course_profile/albuquerque_half.png',
        'unlock_criteria': {'min_orl_level': 4, 'min_stamina_level': 5}
    },
    'Jemez Mountain 25K Technical Loop': {
        'dist': 15.53, 'elev': 2800, 'bias': 'Torque', 'climate_tag': 'Neutral',
        'desc': '🌲 Punishing technical single-track loop circling ancient volcanic rims.', 
        'strat': 'Severe trail test. Demands high Climbing Power and pacing resilience.',
        'course_img': 'images/course_profile/jemez_mountain_25k.png',
        'unlock_criteria': {'min_orl_level': 5, 'min_power_level': 5}
    },
    'Sandia Crest 50K Skymarathon': {
        'dist': 31.07, 'elev': 6200, 'bias': 'Torque', 'climate_tag': 'Cold',
        'desc': '🧗 Brutal 50-Kilometer skyrunning loop climbing continuously from base to peak.', 
        'strat': 'Ultramarathon endurance combined with severe vertical grade challenges.',
        'course_img': 'images/course_profile/sandia_crest_50k.png',
        'unlock_criteria': {'min_orl_level': 6, 'min_stamina_level': 6, 'min_power_level': 6}
    },
    'Shiprock Ultra Desert Horizon': {
        'dist': 31.00, 'elev': 850, 'bias': 'Fuel', 'climate_tag': 'Hot',
        'desc': '🦅 Brutal, high-mileage volcanic desert flats in the Navajo Nation.', 
        'strat': 'Pushes your Aerobic Stamina capacity and high heat acclimatization modifiers.',
        'course_img': 'images/course_profile/shiprock_ultra.png',
        'unlock_criteria': {'min_orl_level': 6, 'min_stamina_level': 6}
    }
}

# =========================================================================
# 🔄 BACKWARD-COMPATIBLE ALIASES
# Direct structural pointers to maintain sync coverage across all scripts.
# =========================================================================
PACER_RIVALS_ROSTER = boss_catalog
COURSE_CATALOG = course_catalog

