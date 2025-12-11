import csv
import shlex
import os
from typing import List, Dict, Any, Tuple

# ------------------------ Helpers ------------------------

def try_parse_number(s: str):
    if s is None:
        return None
    s = s.strip()
    if s == "":
        return s
    try:
        if '.' in s:
            return float(s)
        else:
            return int(s)
    except:
        return s

def normalize_colname(c: str) -> str:
    return c.strip().lower()

def unquote_value(token: str) -> str:
    token = token.strip()
    if len(token) >= 2 and token[0] == "'" and token[-1] == "'":
        return token[1:-1]
    return token

# ------------------------ Data Loading ------------------------

def load_csv_table(table_name: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    candidates = [table_name] if table_name.lower().endswith('.csv') else [table_name, table_name + '.csv']
    filepath = None
    for c in candidates:
        if os.path.exists(c):
            filepath = c
            break
    if filepath is None:
        raise FileNotFoundError(f"CSV file '{table_name}' not found.")
    
    with open(filepath, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = []
        columns = reader.fieldnames or []
        for raw_row in reader:
            row = {normalize_colname(k): v.strip() if v is not None else "" for k, v in raw_row.items()}
            rows.append(row)
    return rows, [normalize_colname(c) for c in columns]

# ------------------------ Parsing ------------------------

class ParseError(Exception):
    pass

def parse_select_list(token: str) -> List[str]:
    token = token.strip()
    if token == '*':
        return ['*']
    return [p.strip() for p in token.split(',') if p.strip() != '']

def parse_where_clause(where_part: str):
    """
    Parse WHERE clause into a list of conditions and operators (AND/OR)
    Returns: [{'col':..., 'op':..., 'val':...}, 'AND', {...}, ...]
    """
    tokens = shlex.split(where_part)
    conditions = []
    i = 0
    while i < len(tokens):
        # detect AND / OR
        if tokens[i].upper() in ('AND', 'OR'):
            conditions.append(tokens[i].upper())
            i += 1
            continue
        # find operator in token[i..i+2]
        if i + 2 >= len(tokens):
            raise ParseError("Malformed WHERE condition.")
        col = tokens[i]
        op = tokens[i+1]
        val = tokens[i+2]
        if op not in ['=', '!=', '<', '>', '<=', '>=']:
            raise ParseError(f"Invalid operator '{op}' in WHERE.")
        conditions.append({'col': col, 'op': op, 'raw_val': val})
        i += 3
    return conditions

def parse_query(sql: str) -> Dict[str, Any]:
    original = sql.strip()
    if original.endswith(';'):
        original = original[:-1].strip()
    low = original.lower()
    if 'select' not in low or ' from ' not in low:
        raise ParseError("Query must contain SELECT and FROM clauses.")
    
    sel_pos = low.find('select')
    from_pos = low.find(' from ')
    select_part = original[sel_pos + len('select'):from_pos].strip()
    remaining = original[from_pos + len(' from '):].strip()

    where_clause = None
    where_index = remaining.lower().find(' where ')
    if where_index != -1:
        table_part = remaining[:where_index].strip()
        where_part = remaining[where_index + len(' where '):].strip()
        where_clause = parse_where_clause(where_part)
    else:
        table_part = remaining.strip()

    select_list = parse_select_list(select_part)
    return {'select': select_list, 'from': table_part, 'where': where_clause, 'raw_sql': sql}

# ------------------------ WHERE Evaluation ------------------------

def compare_values(left_raw: str, op: str, right_raw: str) -> bool:
    left = try_parse_number(left_raw)
    right = try_parse_number(right_raw)
    numeric_types = (int, float)
    if isinstance(left, numeric_types) and isinstance(right, numeric_types):
        if op == '=': return left == right
        if op == '!=': return left != right
        if op == '<': return left < right
        if op == '>': return left > right
        if op == '<=': return left <= right
        if op == '>=': return left >= right
    else:
        left_s = str(left).strip().lower()
        right_s = str(right).strip().lower()
        if op == '=': return left_s == right_s
        if op == '!=': return left_s != right_s
        if op == '<': return left_s < right_s
        if op == '>': return left_s > right_s
        if op == '<=': return left_s <= right_s
        if op == '>=': return left_s >= right_s
    return False

def evaluate_conditions(row: Dict[str, Any], conditions: list) -> bool:
    """
    Evaluate a list of conditions with AND/OR
    conditions = [cond1, 'AND', cond2, 'OR', cond3, ...]
    """
    if not conditions:
        return True
    result = None
    i = 0
    while i < len(conditions):
        cond = conditions[i]
        if isinstance(cond, dict):
            res = compare_values(row[normalize_colname(cond['col'])], cond['op'], unquote_value(cond['raw_val']))
            if result is None:
                result = res
            else:
                # last operator is stored in prev_op
                if prev_op == 'AND':
                    result = result and res
                elif prev_op == 'OR':
                    result = result or res
        else:
            # it's 'AND' or 'OR'
            prev_op = cond
        i += 1
    return result

# ------------------------ Execution ------------------------

def execute_query(parsed: Dict[str, Any]) -> List[Dict[str, Any]]:
    table_name = parsed['from']
    rows, columns = load_csv_table(table_name)
    filtered = [r for r in rows if evaluate_conditions(r, parsed['where'])]

    sel = parsed['select']
    if sel == ['*']:
        return filtered

    # Check COUNT
    if any(s.lower().startswith('count(') for s in sel):
        results = []
        for s in sel:
            inner = s[s.find('(')+1:s.find(')')].strip()
            if inner == '*':
                results.append({'expr': 'COUNT(*)', 'count': len(filtered)})
            else:
                c = sum(1 for r in filtered if r.get(normalize_colname(inner), '').strip() != '')
                results.append({'expr': f'COUNT({inner})', 'count': c})
        return results

    # Project selected columns
    projected = []
    for r in filtered:
        row_out = {}
        for col in sel:
            norm_col = normalize_colname(col)
            if norm_col not in r:
                raise KeyError(f"Column '{col}' not found.")
            row_out[col] = r[norm_col]
        projected.append(row_out)
    return projected

# ------------------------ Pretty Print ------------------------

def print_results(rows: List[Dict[str, Any]]):
    if not rows:
        print("(no rows)")
        return
    if all('expr' in r and 'count' in r for r in rows):
        for r in rows:
            print(f"{r['expr']}: {r['count']}")
        return
    cols = list(rows[0].keys())
    widths = {c: max(len(str(c)), max(len(str(r.get(c,''))) for r in rows)) for c in cols}
    print(" | ".join(c.ljust(widths[c]) for c in cols))
    print("-+-".join('-'*widths[c] for c in cols))
    for r in rows:
        print(" | ".join(str(r.get(c,'')).ljust(widths[c]) for c in cols))

# ------------------------ CLI ------------------------

def mini_engine():
    print("mini-SQL REPL. Supports AND/OR in WHERE. Type EXIT or QUIT to leave.")
    while True:
        try:
            sql = input("sql> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye.")
            return
        if not sql: continue
        if sql.lower() in ('exit', 'quit'):
            print("Bye.")
            return
        try:
            parsed = parse_query(sql)
            results = execute_query(parsed)
            print_results(results)
        except Exception as e:
            print("Error:", e)

if __name__ == '__main__':
    mini_engine()
