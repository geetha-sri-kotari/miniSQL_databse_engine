--------------------------------------------------------------------Mini SQL Engine-----------------------------------------------------------------------

A tiny in-memory SQL engine built in Python that lets you run simple SQL queries on CSV files without installing a full database.
It's perfect for learning how databases work internally and experimenting with real data quickly.

Features:
- SELECT columns or all columns. Examples: SELECT * FROM people; SELECT name, age FROM people;
- WHERE clause with conditions. Single condition: WHERE age > 30. Multiple conditions using AND / OR: 
                                                  WHERE occupation = "Chef" AND city = "Chennai", 
                                                  WHERE city = "Bengaluru" OR city = "Chennai".
- COUNT aggregation. Count all rows: COUNT(*). Count non-empty values in a column: COUNT(occupation).
- Case-insensitive comparisons. "Bengaluru" matches "bengaluru" or "BENGALURU" in the CSV.
- Trims spaces automatically. Leading/trailing spaces in CSV values are ignored.
- Interactive command-line interface (REPL). Type queries, see results instantly. Type EXIT or QUIT to leave.

How to Use:
1. Install Python 3.6 or higher.
2. Place your CSV file in the same folder as mini_sql.py (for example: people.csv).
3. Run the engine using the terminal: python mini_sql.py
4. At the sql> prompt, type queries such as: 
                       SELECT * FROM people; 
                       SELECT name, age FROM people WHERE city = "Chennai"; 
                       SELECT COUNT(*) FROM people WHERE occupation = "Data Analyst"; 
                       SELECT name FROM people WHERE occupation = "Chef" AND city = "Hyderabad"; 
                       SELECT name FROM people WHERE city = "Bengaluru" OR city = "Chennai";

CSV Format:
The engine expects a standard CSV file with headers. Example people.csv:
name, age, city, occupation, salary
Rohith, 28, Hyderabad, Chef, 30000
Divya, 27, Bengaluru, Data Analyst, 40000
Harish, 30, Chennai, Software Engineer, 50000
Column names are case-insensitive. Values are automatically trimmed of spaces.

Limitations:
Only supports single-level conditions in WHERE (AND/OR allowed, but no parentheses). 
Only basic SQL features are supported: SELECT, FROM, WHERE, COUNT(). 
No JOINs, GROUP BY, or nested queries.

Error Handling:
Invalid column name → "Column 'xyz' not found." 
Invalid CSV file → "CSV file 'xyz.csv' not found." 
Malformed SQL → "Parse error: ...". 
Friendly error messages guide you to fix mistakes.

Why This Project helps:
Learn how SQL works internally. 
Understand data filtering, projection, and aggregation. 
Experiment with real CSV data without setting up a full database.
