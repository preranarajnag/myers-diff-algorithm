
import sys
from array import array

def read_lines(path):
    
    with open(path, "rb") as f:         
        data = f.read()
    lines = data.split(b"\n")
    if lines[-1] == b"":
        lines.pop()
    return lines

class TooBig(Exception):
    pass

def read_saved(snapshot, d, k):
    
    return snapshot[(k + d - 1) // 2]

def myers_snakes(a, b, max_cells=None):
    
    n, m = len(a), len(b)

    padding = n + m + 2
    a = a + [-1] * padding
    b = b + [-2] * padding

    x = 0
    while a[x] == b[x]:
        x += 1
    if x == n and x == m:               
        return [(0, 0, n)] if n else []

   
    max_d = n + m
    offset = max_d + 1
    v = [0] * (2 * max_d + 3)
    v[offset + 0] = x                   
    saved_rounds = [None]               
    cells_used = 0
    end_diagonal = n - m                

    d = 0
    while True:
        d += 1        
        snapshot = array("i", v[offset - d + 1: offset + d: 2])
        saved_rounds.append(snapshot)
        if max_cells is not None:
            cells_used += d
            if cells_used > max_cells:
                raise TooBig()

        first = offset - d             
        last = offset + d               
        for idx in range(first, last + 1, 2):       
            
            if idx == first or (idx != last and v[idx - 1] < v[idx + 1]):
                x = v[idx + 1]          
            else:
                x = v[idx - 1] + 1      
            y = x + offset - idx       

            while a[x] == b[y]:         
                x += 1
                y += 1
            v[idx] = x

        if -d <= end_diagonal <= d and (end_diagonal + d) % 2 == 0:
            if v[offset + end_diagonal] >= n:
                break
    return backtrack(saved_rounds, d, n, m)

def backtrack(saved_rounds, total_d, n, m):
    
    snakes = []
    x, y = n, m
    for d in range(total_d, 0, -1):
        snapshot = saved_rounds[d]
        k = x - y

        if k == -d or (k != d and read_saved(snapshot, d, k - 1) < read_saved(snapshot, d, k + 1)):
            prev_k = k + 1                              
            prev_x = read_saved(snapshot, d, prev_k)
            prev_y = prev_x - prev_k
            snake_start_x, snake_start_y = prev_x, prev_y + 1
        else:
            prev_k = k - 1                              
            prev_x = read_saved(snapshot, d, prev_k)
            prev_y = prev_x - prev_k
            snake_start_x, snake_start_y = prev_x + 1, prev_y

        if x > snake_start_x:
            snakes.append((snake_start_x, snake_start_y, x - snake_start_x))
        x, y = prev_x, prev_y

    if x > 0:                                           
        snakes.append((0, 0, x))
    snakes.reverse()                                    
    return snakes

def compute_matches(A, B, max_cells=None):
    
    n, m = len(A), len(B)
    shortest = min(n, m)
    
    start = 0
    while start < shortest and A[start] == B[start]:
        start += 1
    tail = 0
    while tail < shortest - start and A[n - 1 - tail] == B[m - 1 - tail]:
        tail += 1
    end_a = n - tail                    
    end_b = m - tail                    

    match_a = list(range(start))        
    match_b = list(range(start))

    if start < end_a and start < end_b:
        
        set_a = set(A[start:end_a])
        set_b = set(B[start:end_b])
        keep_a = [i for i in range(start, end_a) if A[i] in set_b]   
        keep_b = [j for j in range(start, end_b) if B[j] in set_a]

        if keep_a and keep_b:
            
            number_of = {}
            small_a = [number_of.setdefault(A[i], len(number_of)) for i in keep_a]
            small_b = [number_of.setdefault(B[j], len(number_of)) for j in keep_b]

            for x, y, length in myers_snakes(small_a, small_b, max_cells):
                match_a.extend(keep_a[x: x + length])
                match_b.extend(keep_b[y: y + length])

    match_a.extend(range(end_a, n))     
    match_b.extend(range(end_b, m))
    return match_a, match_b

HIGHLIGHT_MAX_CELLS = 60_000_000        

def format_ranges(matched, length):
    
    parts = []
    next_free = 0                       
    for pos in matched:
        if pos > next_free:             
            parts.append("%d-%d" % (next_free, pos))
        next_free = pos + 1
    if length > next_free:              
        parts.append("%d-%d" % (next_free, length))
    return ",".join(parts) if parts else "."

def highlight_row(old_line, new_line):
    
    old = old_line.decode("utf-8", "surrogateescape")
    new = new_line.decode("utf-8", "surrogateescape")
    try:
        matched_old, matched_new = compute_matches(old, new, HIGHLIGHT_MAX_CELLS)
    except TooBig:
        matched_old, matched_new = [], []       
    text = "? %s | %s\n" % (format_ranges(matched_old, len(old)),
                            format_ranges(matched_new, len(new)))
    return text.encode("ascii")

def render(A, B, match_a, match_b, highlight):
    
    out = []
    len_a, len_b = len(A), len(B)
    next_a = next_b = 0                 
    for ma, mb in zip(match_a + [len_a], match_b + [len_b]):

        if next_a < ma or next_b < mb:              
            deleted = A[next_a:ma]
            inserted = B[next_b:mb]

            for line in deleted:                    
                out.append(b"-" + line + b"\n")

            if highlight:
                pairs = min(len(deleted), len(inserted))
                for t in range(len(inserted)):
                    out.append(b"+" + inserted[t] + b"\n")
                    if t < pairs:                  
                        out.append(highlight_row(deleted[t], inserted[t]))
            else:
                for line in inserted:              
                    out.append(b"+" + line + b"\n")

        if ma < len_a:                             
            out.append(b" " + A[ma] + b"\n")
        next_a, next_b = ma + 1, mb + 1

    return out

def main(argv):
    if len(argv) != 4 or argv[1] not in ("lines", "highlight"):
        sys.stderr.write("usage: main.py lines|highlight FILE_A FILE_B\n")
        return 2

    mode, path_a, path_b = argv[1], argv[2], argv[3]

    try:
        A = read_lines(path_a)
        B = read_lines(path_b)
    except OSError as error:            
        sys.stderr.write("error: cannot read input file: %s\n" % error)
        return 2                        

    match_a, match_b = compute_matches(A, B)
    output = render(A, B, match_a, match_b, mode == "highlight")

    sys.stdout.buffer.write(b"".join(output))   
    sys.stdout.buffer.flush()
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))