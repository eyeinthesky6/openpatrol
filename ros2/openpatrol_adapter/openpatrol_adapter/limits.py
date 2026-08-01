import math

def clamp_command(linear: float, angular: float, max_linear: float, max_angular: float) -> tuple[float,float]:
    values=(linear,angular,max_linear,max_angular)
    if not all(math.isfinite(value) for value in values): raise ValueError("velocity values must be finite")
    if max_linear <= 0 or max_angular <= 0: raise ValueError("velocity limits must be positive")
    return max(-max_linear,min(max_linear,linear)),max(-max_angular,min(max_angular,angular))
