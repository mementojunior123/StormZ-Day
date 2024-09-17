"""Module that contains multiple lerp related utility functions."""
def compatibilty_lerp(a, b, t : float):
    try: return a + (b-a) * t 
    except: pass
        
    try : return a.lerp(b, t) 
    except: pass
        
    try: size_a, size_b = len(a), len(b)
    except: raise ValueError("Compatibilty checks failed")
    else: 
        if size_a != size_b: raise ValueError("Size mismatch")
        
    try: return [a[i] + (b[i] - a[i]) * t for i in range(size_a)]
    except: pass
        
    raise ValueError(f"Compatibilty checks failed ({a} does not match {b})")

def lerp(a, b, t : float):
    try:
        return a + (b-a) * t
    except:
        pass

    return [a[i] + (b[i] - a[i]) * t for i in range(2)]

    


def flip(t : float) -> float:
    return 1 - t


def quad_ease_out(t : float) -> float:
    return 1 - (1 - t) * (1 - t)


def quad_ease_in(t : float) -> float:
    return t * t

def cubic_ease_in(t : float) -> float:
    return t * t * t

def cubic_ease_out(t : float) -> float:
    return flip(cubic_ease_in(flip(t)))



def smoothstep(t : float) -> float:
    return lerp(quad_ease_in(t), quad_ease_out(t), t)


def linear(t : float) -> float:
    return t

def mirror(t : float) -> float:
    if t < 0.5: return t * 2
    else: return flip(t) * 2



