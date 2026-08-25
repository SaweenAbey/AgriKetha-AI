import re
from typing import Tuple

# Define regex patterns for security checks

# 1. Prompt Injection Patterns
PROMPT_INJECTION_PATTERNS = [
    # Ignore instructions
    re.compile(r"ignore\s+(?:all\s+)?(?:previous\s+)?instructions", re.IGNORECASE),
    re.compile(r"disregard\s+(?:all\s+)?(?:previous\s+)?instructions", re.IGNORECASE),
    re.compile(r"forget\s+(?:all\s+)?(?:previous\s+)?instructions", re.IGNORECASE),
    re.compile(r"forget\s+(?:what\s+)?i\s+said\s+before", re.IGNORECASE),
    re.compile(r"bypass\s+safety", re.IGNORECASE),
    re.compile(r"override\s+system", re.IGNORECASE),
    re.compile(r"system\s+override", re.IGNORECASE),
    # System role prompt injection
    re.compile(r"you\s+are\s+now\s+(?:a|an)", re.IGNORECASE),
    re.compile(r"act\s+as\s+(?:a|an)", re.IGNORECASE),
    re.compile(r"new\s+system\s+prompt", re.IGNORECASE),
    re.compile(r"developer\s+mode", re.IGNORECASE),
    re.compile(r"jailbreak", re.IGNORECASE),
    re.compile(r"do\s+anything\s+now", re.IGNORECASE),
    # Sinhala/Tamil overrides (transliterated or raw scripts)
    re.compile(r"පෙර\s+උපදෙස්\s+අමතක\s+කරන්න", re.IGNORECASE),  # forget previous instructions
    re.compile(r"උපදෙස්\s+අමතක\s+කරන්න", re.IGNORECASE),       # forget instructions
    re.compile(r"முந்தைய\s+அறிவுறுத்தல்களை\s+புறக்கணிக்கவும்", re.IGNORECASE),  # ignore previous instructions
]

# 2. Code/SQL/Command Injection Patterns
CODE_INJECTION_PATTERNS = [
    # Script / HTML tags
    re.compile(r"<script[^>]*>", re.IGNORECASE),
    re.compile(r"javascript\s*:", re.IGNORECASE),
    re.compile(r"onerror\s*=", re.IGNORECASE),
    re.compile(r"onload\s*=", re.IGNORECASE),
    # SQL Injection common patterns
    re.compile(r"union\s+select", re.IGNORECASE),
    re.compile(r"drop\s+table", re.IGNORECASE),
    re.compile(r"insert\s+into", re.IGNORECASE),
    re.compile(r"delete\s+from", re.IGNORECASE),
    re.compile(r"select\s+.*\s+from", re.IGNORECASE),
    re.compile(r"'\s+or\s+'\d+'\s*=\s*'\d+", re.IGNORECASE),
    re.compile(r"admin'\s+or\s+'1'='1", re.IGNORECASE),
    re.compile(r"or\s+1\s*=\s*1", re.IGNORECASE),
    # Command Injection
    re.compile(r"os\.system\s*\(", re.IGNORECASE),
    re.compile(r"subprocess\.", re.IGNORECASE),
    re.compile(r"eval\s*\(", re.IGNORECASE),
    re.compile(r"exec\s*\(", re.IGNORECASE),
    re.compile(r"sh\s+-c", re.IGNORECASE),
    re.compile(r"bash\s+-c", re.IGNORECASE),
]

# 3. Restricted/Unauthorized Features and Policy Violations
# Agricultural context: we allow pesticides, fertilizers, weedicides, but restrict explosives, weapons, hacking, administrative overrides
RESTRICTED_KEYWORDS = [
    # Weapons / Explosives
    "bomb", "explosive", "dynamite", "gun", "rifle", "weapon", "grenade", "c4", "terrorist",
    # Illegal drugs (excluding regular farm chemicals/fertilizers/pesticides)
    "heroin", "cocaine", "methamphetamine", "ecstasy", "illegal drug", "manufacture drug",
    # Self-harm / Violence
    "suicide", "kill myself", "self-harm", "hurt myself",
    # System administrator commands/files
    "sudo rm", "config_env", "db_dump", "env_variables", "api_keys", "secret_key", "system_reboot",
    "sudo shutdown", "sudo reboot", "/etc/passwd", "/etc/shadow"
]

def check_query_safety(query: str, translated_query: str = None) -> Tuple[bool, str]:
    """
    Checks user query and its translation for security issues:
    - Prompt Injection
    - Code / SQL Injection
    - Restricted Topics/Features
    
    Returns:
        (is_secure: bool, error_message: str)
    """
    if not query:
        return True, ""
        
    texts_to_check = [query]
    if translated_query and translated_query != query:
        texts_to_check.append(translated_query)
        
    for text in texts_to_check:
        text_lower = text.lower().strip()
        
        # 1. Check for prompt injection patterns
        for pattern in PROMPT_INJECTION_PATTERNS:
            if pattern.search(text):
                return False, "Security violation: Prompt injection detected."
                
        # 2. Check for code/SQL/command injection patterns
        for pattern in CODE_INJECTION_PATTERNS:
            if pattern.search(text):
                return False, "Security violation: Code or script injection attempt detected."
                
        # 3. Check for restricted keywords/features
        for keyword in RESTRICTED_KEYWORDS:
            # Match whole words or phrase to avoid substring false positives (e.g. "bomb" shouldn't block "bombay onion")
            # We can use regex with word boundaries for keywords
            keyword_pattern = re.compile(rf"\b{re.escape(keyword)}\b", re.IGNORECASE)
            if keyword_pattern.search(text_lower):
                return False, f"Security violation: Access to restricted feature or topic '{keyword}' is blocked."
                
    return True, ""
