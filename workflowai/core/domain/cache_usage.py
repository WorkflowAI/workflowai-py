from typing import Literal

# Cache usage configuration for agent runs
# - "auto": Use cached results only when temperature is 0
# - "always": Always use cached results if available, regardless of model temperature
# - "never": Never use cached results, always execute a new run
CacheUsage = Literal["auto", "always", "never"]
