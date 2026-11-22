from lib import ext
T = []
def add(*a, **k): T.append(ext(*a, **k))

add("ext-stack-peek-capacity", "easy",
{"BoundedStack.java": r'''
import java.util.*;
public class BoundedStack<T> {
    private final Deque<T> d = new ArrayDeque<>();
    private final int cap;
    public BoundedStack(int cap) { this.cap = cap; }
    public void push(T t) {
        if (d.size() == cap) throw new IllegalStateException("full");
        d.push(t);
    }
    public T pop() { if (d.isEmpty()) throw new NoSuchElementException(); return d.pop(); }
    public int size() { return d.size(); }
}'''},
"Add `T peek()` (returns top without removing; NoSuchElementException when empty), `boolean isFull()`, and `int remaining()` (free slots) to BoundedStack.",
[("BoundedStack.java", "    public int size() { return d.size(); }", "    public int size() { return d.size(); }\n    public T peek() { if (d.isEmpty()) throw new NoSuchElementException(); return d.peek(); }\n    public boolean isFull() { return d.size() == cap; }\n    public int remaining() { return cap - d.size(); }")],
r'''
BoundedStack<Integer> s = new BoundedStack<>(2);
eq(2, s.remaining(), "rem0"); ok(!s.isFull(), "not full"); s.push(1); s.push(2);
ok(s.isFull(), "full"); eq(0, s.remaining(), "rem full"); eq(2, s.peek(), "peek"); eq(2, s.size(), "peek keeps");
thrown(java.util.NoSuchElementException.class, () -> new BoundedStack<String>(1).peek(), "peek empty");
''')

add("ext-person-sort-comparators", "easy",
{"Person.java": r'''
public record Person(String name, int age, String city) {}
''', "People.java": r'''
import java.util.*;
public class People {
    public static List<Person> byName(List<Person> ps) {
        List<Person> c = new ArrayList<>(ps);
        c.sort(Comparator.comparing(Person::name));
        return c;
    }
}'''},
"Add to People: `byAgeThenName(List<Person>)` (age ascending, ties by name) and `oldestPerCity(List<Person>)` returning `Map<String, Person>` (city -> oldest person; first in list wins ties) iterating in alphabetical city order. Inputs must not be modified.",
[("People.java", "        return c;\n    }\n}", "        return c;\n    }\n    public static List<Person> byAgeThenName(List<Person> ps) {\n        List<Person> c = new ArrayList<>(ps);\n        c.sort(Comparator.comparingInt(Person::age).thenComparing(Person::name));\n        return c;\n    }\n    public static Map<String, Person> oldestPerCity(List<Person> ps) {\n        Map<String, Person> m = new TreeMap<>();\n        for (Person p : ps) m.merge(p.city(), p, (a, b) -> b.age() > a.age() ? b : a);\n        return m;\n    }\n}")],
r'''
List<Person> ps = List.of(new Person("zed", 30, "NYC"), new Person("amy", 30, "LA"), new Person("bob", 25, "NYC"), new Person("cat", 30, "NYC"));
eq(List.of("bob", "amy", "cat", "zed"), People.byAgeThenName(ps).stream().map(Person::name).toList(), "age/name");
Map<String, Person> m = People.oldestPerCity(ps);
eq(List.of("LA", "NYC"), new ArrayList<>(m.keySet()), "city order"); eq("zed", m.get("NYC").name(), "first wins ties"); eq("amy", m.get("LA").name(), "LA");
eq(4, ps.size(), "unmodified");
''')

add("ext-calculator-pow-mod", "easy",
{"Calc.java": r'''
public class Calc {
    public static double apply(String op, double a, double b) {
        switch (op) {
            case "+": return a + b;
            case "-": return a - b;
            case "*": return a * b;
            case "/":
                if (b == 0) throw new ArithmeticException("division by zero");
                return a / b;
            default: throw new IllegalArgumentException("unknown op " + op);
        }
    }
}'''},
"Extend Calc.apply with `\"^\"` (power, Math.pow) and `\"%\"` (remainder; division-by-zero ArithmeticException like \"/\"), and add `\"max\"` and `\"min\"`.",
[("Calc.java", '            default: throw', '            case "^": return Math.pow(a, b);\n            case "%":\n                if (b == 0) throw new ArithmeticException("division by zero");\n                return a % b;\n            case "max": return Math.max(a, b);\n            case "min": return Math.min(a, b);\n            default: throw')],
r'''
eq(8.0, Calc.apply("^", 2, 3), "pow"); eq(1.0, Calc.apply("%", 7, 3), "mod"); eq(4.0, Calc.apply("max", 4, -1), "max"); eq(-1.0, Calc.apply("min", 4, -1), "min");
thrown(ArithmeticException.class, () -> Calc.apply("%", 1, 0), "mod zero"); eq(5.0, Calc.apply("+", 2, 3), "still works");
thrown(IllegalArgumentException.class, () -> Calc.apply("??", 1, 1), "unknown");
''')

add("ext-logger-levels", "medium",
{"Level.java": "public enum Level { DEBUG, INFO, WARN, ERROR }\n",
 "Logger.java": r'''
import java.util.*;
public class Logger {
    private final List<String> lines = new ArrayList<>();
    public void log(Level l, String msg) { lines.add("[" + l + "] " + msg); }
    public List<String> lines() { return lines; }
}'''},
"Add a minimum level to Logger: `setMinLevel(Level)` (default DEBUG); messages below the minimum are dropped. Add convenience methods debug/info/warn/error(String) and `int count(Level)` returning how many lines were logged at exactly that level.",
[("Logger.java", "    private final List<String> lines = new ArrayList<>();\n    public void log(Level l, String msg) { lines.add(\"[\" + l + \"] \" + msg); }",
  "    private final List<String> lines = new ArrayList<>();\n    private final Map<Level, Integer> counts = new EnumMap<>(Level.class);\n    private Level min = Level.DEBUG;\n    public void setMinLevel(Level l) { min = l; }\n    public void log(Level l, String msg) {\n        if (l.compareTo(min) < 0) return;\n        lines.add(\"[\" + l + \"] \" + msg);\n        counts.merge(l, 1, Integer::sum);\n    }\n    public void debug(String m) { log(Level.DEBUG, m); }\n    public void info(String m) { log(Level.INFO, m); }\n    public void warn(String m) { log(Level.WARN, m); }\n    public void error(String m) { log(Level.ERROR, m); }\n    public int count(Level l) { return counts.getOrDefault(l, 0); }")],
r'''
Logger lg = new Logger(); lg.debug("d"); lg.setMinLevel(Level.WARN); lg.info("i"); lg.warn("w"); lg.error("e"); lg.error("e2");
eq(List.of("[DEBUG] d", "[WARN] w", "[ERROR] e", "[ERROR] e2"), lg.lines(), "lines"); eq(2, lg.count(Level.ERROR), "errors"); eq(0, lg.count(Level.INFO), "info dropped"); eq(1, lg.count(Level.DEBUG), "debug before min");
''')

add("ext-shapes-add-triangle", "medium",
{"Shape.java": "public interface Shape { double area(); String describe(); }\n",
 "Circle.java": r'''
public class Circle implements Shape {
    private final double r;
    public Circle(double r) { this.r = r; }
    public double area() { return Math.PI * r * r; }
    public String describe() { return "Circle(r=" + r + ")"; }
}''',
 "Rect.java": r'''
public class Rect implements Shape {
    private final double w, h;
    public Rect(double w, double h) { this.w = w; this.h = h; }
    public double area() { return w * h; }
    public String describe() { return "Rect(" + w + "x" + h + ")"; }
}'''},
"Add a `Triangle` class (new file Triangle.java) implementing Shape, constructed from three side lengths (a,b,c). It must throw IllegalArgumentException if the sides violate the triangle inequality or any side <= 0. area() uses Heron's formula; describe() returns \"Triangle(a,b,c)\" with the sides printed as doubles, e.g. \"Triangle(3.0,4.0,5.0)\". Also add `default boolean isLargerThan(Shape o)` to the Shape interface comparing areas.",
[("Shape.java", "String describe(); }", "String describe();\n    default boolean isLargerThan(Shape o) { return area() > o.area(); }\n}")],
r'''
Triangle t = new Triangle(3, 4, 5); eq(6.0, t.area(), "area"); eq("Triangle(3.0,4.0,5.0)", t.describe(), "describe");
thrown(IllegalArgumentException.class, () -> new Triangle(1, 2, 3), "degenerate"); thrown(IllegalArgumentException.class, () -> new Triangle(0, 1, 1), "zero side");
thrown(IllegalArgumentException.class, () -> new Triangle(1, 1, 5), "too long");
ok(new Rect(10, 10).isLargerThan(t), "larger"); ok(!t.isLargerThan(new Circle(5)), "smaller");
Shape s = t; eq(6.0, s.area(), "polymorphic");
''', new_files={"Triangle.java": r'''
public class Triangle implements Shape {
    private final double a, b, c;
    public Triangle(double a, double b, double c) {
        if (a <= 0 || b <= 0 || c <= 0 || a + b <= c || a + c <= b || b + c <= a) throw new IllegalArgumentException("invalid triangle");
        this.a = a; this.b = b; this.c = c;
    }
    public double area() { double s = (a + b + c) / 2; return Math.sqrt(s * (s - a) * (s - b) * (s - c)); }
    public String describe() { return "Triangle(" + a + "," + b + "," + c + ")"; }
}'''})

add("ext-todo-priorities", "medium",
{"Todo.java": r'''
public class Todo {
    private final String title;
    private boolean done;
    public Todo(String title) { this.title = title; }
    public String title() { return title; }
    public boolean isDone() { return done; }
    public void complete() { done = true; }
}''',
 "TodoList.java": r'''
import java.util.*;
public class TodoList {
    private final List<Todo> items = new ArrayList<>();
    public Todo add(String title) { Todo t = new Todo(title); items.add(t); return t; }
    public List<Todo> pending() {
        List<Todo> out = new ArrayList<>();
        for (Todo t : items) if (!t.isDone()) out.add(t);
        return out;
    }
}'''},
"Add priorities: Todo gets `int priority()` (default 0, higher is more urgent) and `setPriority(int)`; TodoList gets `add(String title, int priority)` and `pendingByPriority()` returning pending todos sorted by priority descending, ties in insertion order.",
[("Todo.java", "    private boolean done;", "    private boolean done;\n    private int priority;\n    public int priority() { return priority; }\n    public void setPriority(int p) { priority = p; }"),
 ("TodoList.java", "    public List<Todo> pending() {", "    public Todo add(String title, int priority) { Todo t = add(title); t.setPriority(priority); return t; }\n    public List<Todo> pendingByPriority() {\n        List<Todo> out = pending();\n        out.sort(Comparator.comparingInt(Todo::priority).reversed());\n        return out;\n    }\n    public List<Todo> pending() {")],
r'''
TodoList l = new TodoList(); l.add("a"); l.add("b", 5); l.add("c", 5); Todo d = l.add("d", 9); l.add("e", 1); d.complete();
eq(List.of("b", "c", "e", "a"), l.pendingByPriority().stream().map(Todo::title).toList(), "order");
eq(0, l.add("z").priority(), "default"); eq(4, l.pending().size() - 1, "pending count unaffected");
''')

add("ext-inventory-low-stock", "medium",
{"Product.java": "public record Product(String sku, String name, int qty) {}\n",
 "Inventory.java": r'''
import java.util.*;
public class Inventory {
    private final Map<String, Product> products = new LinkedHashMap<>();
    public void add(Product p) { products.merge(p.sku(), p, (a, b) -> new Product(a.sku(), a.name(), a.qty() + b.qty())); }
    public int qty(String sku) { Product p = products.get(sku); return p == null ? 0 : p.qty(); }
}'''},
"Add `void remove(String sku, int n)` to Inventory (IllegalArgumentException if n <= 0; NoSuchElementException if unknown sku; IllegalStateException if n exceeds stock, leaving stock unchanged), and `List<String> lowStock(int threshold)` returning SKUs with qty strictly below threshold in insertion order.",
[("Inventory.java", "    public int qty(", "    public void remove(String sku, int n) {\n        if (n <= 0) throw new IllegalArgumentException(\"n\");\n        Product p = products.get(sku);\n        if (p == null) throw new NoSuchElementException(sku);\n        if (n > p.qty()) throw new IllegalStateException(\"insufficient stock\");\n        products.put(sku, new Product(sku, p.name(), p.qty() - n));\n    }\n    public List<String> lowStock(int threshold) {\n        List<String> out = new ArrayList<>();\n        for (Product p : products.values()) if (p.qty() < threshold) out.add(p.sku());\n        return out;\n    }\n    public int qty(")],
r'''
Inventory inv = new Inventory(); inv.add(new Product("a", "A", 10)); inv.add(new Product("b", "B", 3)); inv.add(new Product("c", "C", 5)); inv.add(new Product("a", "A", 2));
inv.remove("a", 7); eq(5, inv.qty("a"), "after remove"); eq(List.of("b"), inv.lowStock(5), "strictly below"); eq(List.of("a", "b", "c"), inv.lowStock(100), "insertion order");
thrown(IllegalStateException.class, () -> inv.remove("b", 4), "too many"); eq(3, inv.qty("b"), "unchanged");
thrown(IllegalArgumentException.class, () -> inv.remove("b", 0), "zero"); thrown(java.util.NoSuchElementException.class, () -> inv.remove("zz", 1), "unknown");
''')

add("ext-text-stats-extra", "easy",
{"TextStats.java": r'''
import java.util.*;
public class TextStats {
    private final String text;
    public TextStats(String text) { this.text = text; }
    public int wordCount() {
        String t = text.trim();
        return t.isEmpty() ? 0 : t.split("\\s+").length;
    }
}'''},
"Add `int lineCount()` (number of lines; empty text has 0; a trailing newline does not add a line), `String longestWord()` (first longest, letters/digits/apostrophes only after stripping other punctuation; empty string if no words), and `double averageWordLength()` (0.0 if no words; counts same cleaned words).",
[("TextStats.java", "    public int wordCount() {", r'''    private List<String> words() {
        List<String> out = new ArrayList<>();
        for (String w : text.split("\\s+")) {
            String c = w.replaceAll("[^A-Za-z0-9']", "");
            if (!c.isEmpty()) out.add(c);
        }
        return out;
    }
    public int lineCount() {
        if (text.isEmpty()) return 0;
        String[] ls = text.split("\n", -1);
        return text.endsWith("\n") ? ls.length - 1 : ls.length;
    }
    public String longestWord() {
        String best = "";
        for (String w : words()) if (w.length() > best.length()) best = w;
        return best;
    }
    public double averageWordLength() {
        List<String> ws = words();
        if (ws.isEmpty()) return 0.0;
        int t = 0; for (String w : ws) t += w.length();
        return (double) t / ws.size();
    }
    public int wordCount() {''')],
r'''
TextStats s = new TextStats("Hello, world!\nIt's a beautiful day.\n");
eq(2, s.lineCount(), "lines"); eq("beautiful", s.longestWord(), "longest"); eq((5 + 5 + 4 + 1 + 9 + 3) / 6.0, s.averageWordLength(), "avg");
eq(0, new TextStats("").lineCount(), "empty lines"); eq(3, new TextStats("a\nb\nc").lineCount(), "no trailing nl"); eq("", new TextStats("?! ...").longestWord(), "no words"); eq(0.0, new TextStats(" ").averageWordLength(), "avg none");
eq(6, s.wordCount(), "wordCount still works");
''')

add("ext-matrix-add-determinant", "medium",
{"Matrix.java": r'''
public class Matrix {
    private final double[][] a;
    public Matrix(double[][] a) { this.a = a; }
    public int rows() { return a.length; }
    public int cols() { return a[0].length; }
    public double get(int i, int j) { return a[i][j]; }
    public Matrix transpose() {
        double[][] t = new double[cols()][rows()];
        for (int i = 0; i < rows(); i++) for (int j = 0; j < cols(); j++) t[j][i] = a[i][j];
        return new Matrix(t);
    }
}'''},
"Add `Matrix add(Matrix o)` (IllegalArgumentException if shapes differ), `Matrix scale(double k)`, and `double determinant()` (square matrices only, else IllegalArgumentException; works for any size via cofactor or elimination).",
[("Matrix.java", "    public Matrix transpose() {", r'''    public Matrix add(Matrix o) {
        if (rows() != o.rows() || cols() != o.cols()) throw new IllegalArgumentException("shape");
        double[][] r = new double[rows()][cols()];
        for (int i = 0; i < rows(); i++) for (int j = 0; j < cols(); j++) r[i][j] = a[i][j] + o.a[i][j];
        return new Matrix(r);
    }
    public Matrix scale(double k) {
        double[][] r = new double[rows()][cols()];
        for (int i = 0; i < rows(); i++) for (int j = 0; j < cols(); j++) r[i][j] = a[i][j] * k;
        return new Matrix(r);
    }
    public double determinant() {
        if (rows() != cols()) throw new IllegalArgumentException("not square");
        int n = rows(); double[][] m = new double[n][];
        for (int i = 0; i < n; i++) m[i] = a[i].clone();
        double det = 1;
        for (int c = 0; c < n; c++) {
            int p = c;
            for (int r = c + 1; r < n; r++) if (Math.abs(m[r][c]) > Math.abs(m[p][c])) p = r;
            if (Math.abs(m[p][c]) < 1e-12) return 0;
            if (p != c) { double[] t = m[p]; m[p] = m[c]; m[c] = t; det = -det; }
            det *= m[c][c];
            for (int r = c + 1; r < n; r++) { double f = m[r][c] / m[c][c]; for (int k = c; k < n; k++) m[r][k] -= f * m[c][k]; }
        }
        return det;
    }
    public Matrix transpose() {''')],
r'''
Matrix a = new Matrix(new double[][]{{1,2},{3,4}}), b = new Matrix(new double[][]{{10,20},{30,40}});
eq(44.0, a.add(b).get(1, 1), "add"); eq(4.0, a.scale(2).get(0, 1), "scale"); eq(-2.0, a.determinant(), "det2");
eq(-306.0, new Matrix(new double[][]{{6,1,1},{4,-2,5},{2,8,7}}).determinant(), "det3"); eq(1.0, new Matrix(new double[][]{{1}}).determinant() , "det1");
eq(0.0, new Matrix(new double[][]{{1,2},{2,4}}).determinant(), "singular"); eq(-1.0, new Matrix(new double[][]{{0,1},{1,0}}).determinant(), "needs pivot");
thrown(IllegalArgumentException.class, () -> a.add(new Matrix(new double[][]{{1,2,3}})), "shape"); thrown(IllegalArgumentException.class, () -> new Matrix(new double[][]{{1,2,3}}).determinant(), "non square");
''')

add("ext-event-bus-priority-once", "hard",
{"Handler.java": "public interface Handler { void handle(String payload); }\n",
 "Bus.java": r'''
import java.util.*;
public class Bus {
    private final Map<String, List<Handler>> handlers = new HashMap<>();
    public void on(String topic, Handler h) {
        handlers.computeIfAbsent(topic, k -> new ArrayList<>()).add(h);
    }
    public void emit(String topic, String payload) {
        for (Handler h : new ArrayList<>(handlers.getOrDefault(topic, List.of()))) h.handle(payload);
    }
}'''},
"Add `once(String topic, Handler h)` (handler runs for the first emit only, then is removed) and `on(String topic, int priority, Handler h)` (higher priority runs first; same priority keeps registration order; plain on() is priority 0). `once` handlers also participate in ordering with priority 0. Add `int listenerCount(String topic)`.",
[("Bus.java", r'''    private final Map<String, List<Handler>> handlers = new HashMap<>();
    public void on(String topic, Handler h) {
        handlers.computeIfAbsent(topic, k -> new ArrayList<>()).add(h);
    }
    public void emit(String topic, String payload) {
        for (Handler h : new ArrayList<>(handlers.getOrDefault(topic, List.of()))) h.handle(payload);
    }''', r'''    private static class Reg { final Handler h; final int prio; final boolean once; Reg(Handler h, int p, boolean o) { this.h = h; prio = p; once = o; } }
    private final Map<String, List<Reg>> handlers = new HashMap<>();
    private void add(String topic, Reg r) {
        List<Reg> l = handlers.computeIfAbsent(topic, k -> new ArrayList<>());
        int i = l.size();
        while (i > 0 && l.get(i - 1).prio < r.prio) i--;
        l.add(i, r);
    }
    public void on(String topic, Handler h) { add(topic, new Reg(h, 0, false)); }
    public void on(String topic, int priority, Handler h) { add(topic, new Reg(h, priority, false)); }
    public void once(String topic, Handler h) { add(topic, new Reg(h, 0, true)); }
    public int listenerCount(String topic) { return handlers.getOrDefault(topic, List.of()).size(); }
    public void emit(String topic, String payload) {
        List<Reg> snapshot = new ArrayList<>(handlers.getOrDefault(topic, List.of()));
        for (Reg r : snapshot) {
            if (r.once) handlers.get(topic).remove(r);
            r.h.handle(payload);
        }
    }''')],
r'''
Bus b = new Bus(); List<String> log = new ArrayList<>();
b.on("t", e -> log.add("n1:" + e)); b.on("t", 10, e -> log.add("hi:" + e)); b.once("t", e -> log.add("once:" + e)); b.on("t", -1, e -> log.add("lo:" + e)); b.on("t", e -> log.add("n2:" + e));
eq(5, b.listenerCount("t"), "count");
b.emit("t", "1"); eq(List.of("hi:1", "n1:1", "once:1", "n2:1", "lo:1"), log, "first emit"); eq(4, b.listenerCount("t"), "once removed");
log.clear(); b.emit("t", "2"); eq(List.of("hi:2", "n1:2", "n2:2", "lo:2"), log, "second emit"); eq(0, b.listenerCount("none"), "no topic"); b.emit("none", "x");
''')

add("ext-parser-add-modulo-vars", "hard",
{"Parser.java": r'''
public class Parser {
    private final String s; private int p;
    private Parser(String s) { this.s = s; }
    public static long eval(String s) {
        Parser q = new Parser(s); long v = q.expr(); q.ws();
        if (q.p != s.length()) throw new IllegalArgumentException("unexpected input at " + q.p);
        return v;
    }
    private void ws() { while (p < s.length() && s.charAt(p) == ' ') p++; }
    private long expr() {
        long v = term();
        while (true) {
            ws();
            if (p < s.length() && s.charAt(p) == '+') { p++; v += term(); }
            else if (p < s.length() && s.charAt(p) == '-') { p++; v -= term(); }
            else return v;
        }
    }
    private long term() {
        long v = atom();
        while (true) {
            ws();
            if (p < s.length() && s.charAt(p) == '*') { p++; v *= atom(); }
            else if (p < s.length() && s.charAt(p) == '/') { p++; long d = atom(); if (d == 0) throw new ArithmeticException("/ by zero"); v /= d; }
            else return v;
        }
    }
    private long atom() {
        ws();
        if (p >= s.length()) throw new IllegalArgumentException("unexpected end");
        char c = s.charAt(p);
        if (c == '(') { p++; long v = expr(); ws(); if (p >= s.length() || s.charAt(p) != ')') throw new IllegalArgumentException("missing )"); p++; return v; }
        if (!Character.isDigit(c)) throw new IllegalArgumentException("unexpected " + c);
        long v = 0; while (p < s.length() && Character.isDigit(s.charAt(p))) v = v * 10 + (s.charAt(p++) - '0');
        return v;
    }
}'''},
"Extend Parser: add the `%` operator (same precedence as * and /, ArithmeticException on zero), and variables: add `static long eval(String s, java.util.Map<String, Long> vars)` where identifiers (letters/underscore, then letters/digits/underscore) are looked up in vars (IllegalArgumentException naming the variable if unbound). The existing one-argument eval must keep working (it behaves as an empty map).",
[("Parser.java", "    private final String s; private int p;\n    private Parser(String s) { this.s = s; }\n    public static long eval(String s) {\n        Parser q = new Parser(s);", "    private final String s; private int p; private final java.util.Map<String, Long> vars;\n    private Parser(String s, java.util.Map<String, Long> vars) { this.s = s; this.vars = vars; }\n    public static long eval(String s) { return eval(s, java.util.Map.of()); }\n    public static long eval(String s, java.util.Map<String, Long> vars) {\n        Parser q = new Parser(s, vars);"),
 ("Parser.java", "            else if (p < s.length() && s.charAt(p) == '/')", "            else if (p < s.length() && s.charAt(p) == '%') { p++; long d = atom(); if (d == 0) throw new ArithmeticException(\"% by zero\"); v %= d; }\n            else if (p < s.length() && s.charAt(p) == '/')"),
 ("Parser.java", "        if (!Character.isDigit(c)) throw", "        if (Character.isLetter(c) || c == '_') {\n            int st = p; while (p < s.length() && (Character.isLetterOrDigit(s.charAt(p)) || s.charAt(p) == '_')) p++;\n            String name = s.substring(st, p); Long val = vars.get(name);\n            if (val == null) throw new IllegalArgumentException(\"unbound variable \" + name);\n            return val;\n        }\n        if (!Character.isDigit(c)) throw")],
r'''
eq(1L, Parser.eval("7 % 3"), "mod"); eq(7L, Parser.eval("1 + 10 % 4 * 3"), "mod prec"); eq(14L, Parser.eval("2 + 3 * 4"), "old");
Map<String, Long> v = new HashMap<>(); v.put("x", 5L); v.put("long_name2", 10L);
eq(25L, Parser.eval("x * x", v), "var"); eq(12L, Parser.eval("(long_name2 + 2) % 100", v), "named var"); eq(8L, Parser.eval("x + 3", v), "x+3");
try { Parser.eval("y + 1", v); fail("expected exception"); } catch (IllegalArgumentException e) { ok(e.getMessage().contains("y"), "message names y"); }
thrown(ArithmeticException.class, () -> Parser.eval("5 % 0"), "mod zero"); thrown(IllegalArgumentException.class, () -> Parser.eval("x"), "no vars");
''')

add("ext-queue-to-deque", "medium",
{"IntQueue.java": r'''
import java.util.*;
public class IntQueue {
    private int[] buf = new int[2];
    private int head, size;
    public void addLast(int x) {
        if (size == buf.length) grow();
        buf[(head + size) % buf.length] = x; size++;
    }
    public int removeFirst() {
        if (size == 0) throw new NoSuchElementException();
        int x = buf[head]; head = (head + 1) % buf.length; size--; return x;
    }
    public int size() { return size; }
    private void grow() {
        int[] nb = new int[buf.length * 2];
        for (int i = 0; i < size; i++) nb[i] = buf[(head + i) % buf.length];
        buf = nb; head = 0;
    }
}'''},
"Turn IntQueue into a deque: add `addFirst(int)`, `removeLast()` and `peekFirst()`/`peekLast()` (all NoSuchElementException when empty on remove/peek). Must stay O(1) amortized and correct across wrap-around and growth.",
[("IntQueue.java", "    public int size() { return size; }", r'''    public void addFirst(int x) {
        if (size == buf.length) grow();
        head = (head - 1 + buf.length) % buf.length; buf[head] = x; size++;
    }
    public int removeLast() {
        if (size == 0) throw new NoSuchElementException();
        int i = (head + size - 1) % buf.length; size--; return buf[i];
    }
    public int peekFirst() { if (size == 0) throw new NoSuchElementException(); return buf[head]; }
    public int peekLast() { if (size == 0) throw new NoSuchElementException(); return buf[(head + size - 1) % buf.length]; }
    public int size() { return size; }''')],
r'''
IntQueue q = new IntQueue(); q.addFirst(2); q.addFirst(1); q.addLast(3); q.addLast(4); q.addFirst(0);
eq(0, q.peekFirst(), "pf"); eq(4, q.peekLast(), "pl"); eq(5, q.size(), "size");
eq(4, q.removeLast(), "rl"); eq(0, q.removeFirst(), "rf"); eq(3, q.removeLast(), "rl2"); eq(1, q.removeFirst(), "rf2"); eq(2, q.removeLast(), "last one");
thrown(java.util.NoSuchElementException.class, () -> q.removeLast(), "empty rl"); thrown(java.util.NoSuchElementException.class, () -> q.peekFirst(), "empty pf"); thrown(java.util.NoSuchElementException.class, () -> q.peekLast(), "empty pl");
java.util.ArrayDeque<Integer> ref = new java.util.ArrayDeque<>(); java.util.Random rnd = new java.util.Random(7);
for (int i = 0; i < 5000; i++) {
    int op = rnd.nextInt(4);
    if (op == 0) { q.addFirst(i); ref.addFirst(i); } else if (op == 1) { q.addLast(i); ref.addLast(i); }
    else if (op == 2 && !ref.isEmpty()) eq((int) ref.removeFirst(), q.removeFirst(), "rnd rf " + i);
    else if (op == 3 && !ref.isEmpty()) eq((int) ref.removeLast(), q.removeLast(), "rnd rl " + i);
    eq(ref.size(), q.size(), "rnd size " + i);
}
''')

add("ext-user-validation-errors", "medium",
{"User.java": r'''
public record User(String name, String email, int age) {}
''', "UserValidator.java": r'''
public class UserValidator {
    public static void validate(User u) {
        if (u.name() == null || u.name().isBlank()) throw new IllegalArgumentException("name required");
        if (u.email() == null || !u.email().contains("@")) throw new IllegalArgumentException("invalid email");
        if (u.age() < 0) throw new IllegalArgumentException("invalid age");
    }
}'''},
"Add `static List<String> errors(User u)` to UserValidator returning all problems (in the order name, email, age) using exactly the same messages as validate; empty list if valid. Make `validate` throw a new `ValidationException extends RuntimeException` (new file; `List<String> errors()` accessor; message = errors joined by \"; \") when errors are present. ValidationException extends RuntimeException.",
[("UserValidator.java", r'''    public static void validate(User u) {
        if (u.name() == null || u.name().isBlank()) throw new IllegalArgumentException("name required");
        if (u.email() == null || !u.email().contains("@")) throw new IllegalArgumentException("invalid email");
        if (u.age() < 0) throw new IllegalArgumentException("invalid age");
    }''', r'''    public static java.util.List<String> errors(User u) {
        java.util.List<String> e = new java.util.ArrayList<>();
        if (u.name() == null || u.name().isBlank()) e.add("name required");
        if (u.email() == null || !u.email().contains("@")) e.add("invalid email");
        if (u.age() < 0) e.add("invalid age");
        return e;
    }
    public static void validate(User u) {
        java.util.List<String> e = errors(u);
        if (!e.isEmpty()) throw new ValidationException(e);
    }''')],
r'''
eq(List.of(), UserValidator.errors(new User("a", "a@b", 1)), "valid"); UserValidator.validate(new User("a", "a@b", 1));
eq(List.of("name required", "invalid email", "invalid age"), UserValidator.errors(new User(" ", "x", -1)), "all bad"); eq(List.of("invalid age"), UserValidator.errors(new User("a", "a@b", -5)), "one bad");
try { UserValidator.validate(new User("", null, 3)); fail("expected"); } catch (ValidationException e) { eq(List.of("name required", "invalid email"), e.errors(), "exception errors"); eq("name required; invalid email", e.getMessage(), "message"); }
''', new_files={"ValidationException.java": r'''
import java.util.List;
public class ValidationException extends RuntimeException {
    private final List<String> errors;
    public ValidationException(List<String> errors) { super(String.join("; ", errors)); this.errors = List.copyOf(errors); }
    public List<String> errors() { return errors; }
}'''})

add("ext-cache-stats-and-evict", "medium",
{"SimpleCache.java": r'''
import java.util.*;
public class SimpleCache<K, V> {
    private final Map<K, V> m = new HashMap<>();
    public V get(K k) { return m.get(k); }
    public void put(K k, V v) { m.put(k, v); }
    public int size() { return m.size(); }
}'''},
"Track statistics in SimpleCache: `hits()` and `misses()` counts for get() (a key mapped to a value counts as a hit; absent counts as miss), `double hitRate()` (0.0 when there were no lookups), `V getOrCompute(K k, java.util.function.Function<K,V> f)` (computes and stores on miss, counted as a miss; hit otherwise; f is called at most once per absent key), and `boolean evict(K k)` (true if the key was present).",
[("SimpleCache.java", "    public V get(K k) { return m.get(k); }", r'''    private int hits, misses;
    public V get(K k) { V v = m.get(k); if (v == null) misses++; else hits++; return v; }
    public int hits() { return hits; }
    public int misses() { return misses; }
    public double hitRate() { int t = hits + misses; return t == 0 ? 0.0 : (double) hits / t; }
    public V getOrCompute(K k, java.util.function.Function<K, V> f) {
        V v = m.get(k);
        if (v != null) { hits++; return v; }
        misses++; v = f.apply(k); m.put(k, v); return v;
    }
    public boolean evict(K k) { return m.remove(k) != null; }''')],
r'''
SimpleCache<String,Integer> c = new SimpleCache<>(); eq(0.0, c.hitRate(), "no lookups");
c.put("a", 1); c.get("a"); c.get("b"); c.get("a"); eq(2, c.hits(), "hits"); eq(1, c.misses(), "misses"); eq(2.0 / 3, c.hitRate(), "rate");
int[] calls = {0}; eq(5, c.getOrCompute("x", k -> { calls[0]++; return 5; }), "compute"); eq(5, c.getOrCompute("x", k -> { calls[0]++; return 6; }), "cached"); eq(1, calls[0], "called once");
eq(3, c.hits(), "hits after"); eq(2, c.misses(), "misses after"); ok(c.evict("x") && !c.evict("x"), "evict"); eq(1, c.size(), "size");
''')

add("ext-string-builder-fluent-table", "medium",
{"Table.java": r'''
import java.util.*;
public class Table {
    private final List<String> headers;
    private final List<List<String>> rows = new ArrayList<>();
    public Table(String... headers) { this.headers = List.of(headers); }
    public Table addRow(String... cells) {
        if (cells.length != headers.size()) throw new IllegalArgumentException("expected " + headers.size() + " cells");
        rows.add(List.of(cells));
        return this;
    }
    public int rowCount() { return rows.size(); }
}'''},
"Add `String render()`: a plain-text table. Each column is as wide as its widest cell (header included); cells are left-aligned and padded with spaces; columns are joined by \" | \"; after the header line comes a separator line of dashes joined by \"-+-\"; lines have no trailing spaces; lines are joined by \"\\n\" with no trailing newline. Example for headers (name, qty) and row (apple, 3): \"name  | qty\\n------+----\\napple | 3\".",
[("Table.java", "    public int rowCount()", r'''    public String render() {
        int n = headers.size(); int[] w = new int[n];
        for (int i = 0; i < n; i++) w[i] = headers.get(i).length();
        for (List<String> r : rows) for (int i = 0; i < n; i++) w[i] = Math.max(w[i], r.get(i).length());
        StringBuilder sb = new StringBuilder();
        line(sb, headers, w); sb.append('\n');
        for (int i = 0; i < n; i++) { if (i > 0) sb.append("-+-"); sb.append("-".repeat(w[i])); }
        for (List<String> r : rows) { sb.append('\n'); line(sb, r, w); }
        return sb.toString();
    }
    private void line(StringBuilder sb, List<String> cells, int[] w) {
        StringBuilder l = new StringBuilder();
        for (int i = 0; i < cells.size(); i++) { if (i > 0) l.append(" | "); l.append(String.format("%-" + w[i] + "s", cells.get(i))); }
        int e = l.length(); while (e > 0 && l.charAt(e - 1) == ' ') e--;
        sb.append(l, 0, e);
    }
    public int rowCount()''')],
r'''
eq("name  | qty\n------+----\napple | 3", new Table("name", "qty").addRow("apple", "3").render(), "example");
eq("a | b\n--+--", new Table("a", "b").render(), "no rows");
eq("id | name\n---+-----\n1  | x\n22 | yyyy", new Table("id", "name").addRow("1", "x").addRow("22", "yyyy").render(), "widths");
eq("h1 | h2\n---+---\nv  |", new Table("h1", "h2").addRow("v", "").render(), "empty cell trailing trimmed");
''')

add("ext-bank-statement-history", "hard",
{"Tx.java": "public record Tx(String type, long amount, long balanceAfter) {}\n",
 "Account.java": r'''
public class Account {
    private long balance;
    public void deposit(long amt) {
        if (amt <= 0) throw new IllegalArgumentException("amount");
        balance += amt;
    }
    public void withdraw(long amt) {
        if (amt <= 0) throw new IllegalArgumentException("amount");
        if (amt > balance) throw new IllegalStateException("insufficient funds");
        balance -= amt;
    }
    public long balance() { return balance; }
}'''},
"Record a transaction history in Account: each successful deposit/withdraw appends `Tx(\"DEPOSIT\"|\"WITHDRAW\", amount, balanceAfter)`. Failed operations record nothing. Add `List<Tx> history()` (unmodifiable copy), `List<Tx> history(String type)` filtered by type, and `long totalDeposited()`.",
[("Account.java", "    private long balance;", "    private long balance;\n    private final java.util.List<Tx> txs = new java.util.ArrayList<>();"),
 ("Account.java", "        balance += amt;\n", "        balance += amt;\n        txs.add(new Tx(\"DEPOSIT\", amt, balance));\n"),
 ("Account.java", "        balance -= amt;\n", "        balance -= amt;\n        txs.add(new Tx(\"WITHDRAW\", amt, balance));\n"),
 ("Account.java", "    public long balance() { return balance; }", "    public long balance() { return balance; }\n    public java.util.List<Tx> history() { return java.util.List.copyOf(txs); }\n    public java.util.List<Tx> history(String type) { return txs.stream().filter(t -> t.type().equals(type)).toList(); }\n    public long totalDeposited() { return txs.stream().filter(t -> t.type().equals(\"DEPOSIT\")).mapToLong(Tx::amount).sum(); }")],
r'''
Account a = new Account(); a.deposit(100); a.withdraw(30); a.deposit(5);
eq(List.of(new Tx("DEPOSIT", 100, 100), new Tx("WITHDRAW", 30, 70), new Tx("DEPOSIT", 5, 75)), a.history(), "history");
thrown(IllegalStateException.class, () -> a.withdraw(1000), "fail"); thrown(IllegalArgumentException.class, () -> a.deposit(-1), "fail2"); eq(3, a.history().size(), "failures not recorded");
eq(1, a.history("WITHDRAW").size(), "filtered"); eq(105L, a.totalDeposited(), "total");
thrown(UnsupportedOperationException.class, () -> a.history().add(new Tx("X", 1, 1)), "unmodifiable");
List<Tx> snap = a.history(); a.deposit(1); eq(3, snap.size(), "snapshot is a copy");
''')

add("ext-graph-weighted", "hard",
{"Graph.java": r'''
import java.util.*;
public class Graph {
    private final Map<String, Set<String>> adj = new TreeMap<>();
    public void addEdge(String a, String b) {
        adj.computeIfAbsent(a, k -> new TreeSet<>()).add(b);
        adj.computeIfAbsent(b, k -> new TreeSet<>()).add(a);
    }
    public Set<String> neighbors(String n) { return adj.getOrDefault(n, Set.of()); }
    public boolean hasNode(String n) { return adj.containsKey(n); }
}'''},
"Add weights: `addEdge(String a, String b, int weight)` (weight > 0 else IllegalArgumentException; re-adding an edge updates its weight; the 2-arg addEdge keeps working and means weight 1), `int weight(String a, String b)` (NoSuchElementException if no edge), and `int shortestDistance(String from, String to)` (Dijkstra; -1 if unreachable; NoSuchElementException if either node is unknown).",
[("Graph.java", "    private final Map<String, Set<String>> adj = new TreeMap<>();\n    public void addEdge(String a, String b) {\n        adj.computeIfAbsent(a, k -> new TreeSet<>()).add(b);\n        adj.computeIfAbsent(b, k -> new TreeSet<>()).add(a);\n    }",
 r'''    private final Map<String, Set<String>> adj = new TreeMap<>();
    private final Map<String, Integer> w = new HashMap<>();
    private static String key(String a, String b) { return a.compareTo(b) <= 0 ? a + "\0" + b : b + "\0" + a; }
    public void addEdge(String a, String b) { addEdge(a, b, 1); }
    public void addEdge(String a, String b, int weight) {
        if (weight <= 0) throw new IllegalArgumentException("weight");
        adj.computeIfAbsent(a, k -> new TreeSet<>()).add(b);
        adj.computeIfAbsent(b, k -> new TreeSet<>()).add(a);
        w.put(key(a, b), weight);
    }
    public int weight(String a, String b) {
        Integer x = w.get(key(a, b));
        if (x == null) throw new NoSuchElementException("no edge");
        return x;
    }
    public int shortestDistance(String from, String to) {
        if (!hasNode(from) || !hasNode(to)) throw new NoSuchElementException("unknown node");
        Map<String, Integer> d = new HashMap<>();
        PriorityQueue<Map.Entry<String, Integer>> pq = new PriorityQueue<>(Map.Entry.comparingByValue());
        d.put(from, 0); pq.add(Map.entry(from, 0));
        while (!pq.isEmpty()) {
            var e = pq.poll();
            if (e.getValue() > d.get(e.getKey())) continue;
            if (e.getKey().equals(to)) return e.getValue();
            for (String n : neighbors(e.getKey())) {
                int nd = e.getValue() + weight(e.getKey(), n);
                if (nd < d.getOrDefault(n, Integer.MAX_VALUE)) { d.put(n, nd); pq.add(Map.entry(n, nd)); }
            }
        }
        return -1;
    }''')],
r'''
Graph g = new Graph(); g.addEdge("a", "b", 10); g.addEdge("a", "c", 3); g.addEdge("c", "b", 4); g.addEdge("b", "d", 2); g.addEdge("x", "y");
eq(7, g.shortestDistance("a", "b"), "via c"); eq(9, g.shortestDistance("a", "d"), "a to d"); eq(0, g.shortestDistance("a", "a"), "self"); eq(-1, g.shortestDistance("a", "x"), "unreachable");
eq(1, g.weight("x", "y"), "default weight"); eq(10, g.weight("b", "a"), "undirected"); g.addEdge("a", "b", 1); eq(1, g.weight("a", "b"), "updated"); eq(1, g.shortestDistance("a", "b"), "after update");
thrown(java.util.NoSuchElementException.class, () -> g.weight("a", "d"), "no edge"); thrown(java.util.NoSuchElementException.class, () -> g.shortestDistance("a", "zz"), "unknown");
thrown(IllegalArgumentException.class, () -> g.addEdge("p", "q", 0), "zero weight");
''')

add("ext-tokenizer-strings-comments", "hard",
{"Lexer.java": r'''
import java.util.*;
public class Lexer {
    public static List<String> tokens(String src) {
        List<String> out = new ArrayList<>();
        int i = 0;
        while (i < src.length()) {
            char c = src.charAt(i);
            if (Character.isWhitespace(c)) { i++; }
            else if (Character.isLetter(c) || c == '_') {
                int j = i; while (j < src.length() && (Character.isLetterOrDigit(src.charAt(j)) || src.charAt(j) == '_')) j++;
                out.add("ID:" + src.substring(i, j)); i = j;
            } else if (Character.isDigit(c)) {
                int j = i; while (j < src.length() && Character.isDigit(src.charAt(j))) j++;
                out.add("NUM:" + src.substring(i, j)); i = j;
            } else { out.add("SYM:" + c); i++; }
        }
        return out;
    }
}'''},
"Extend the lexer: (1) double-quoted string literals become `STR:<contents>` with backslash escapes \\\" and \\\\ unescaped (an unterminated string throws IllegalArgumentException); (2) `//` line comments and `/* ... */` block comments are skipped (an unterminated block comment throws IllegalArgumentException); (3) the two-character operators `==`, `!=`, `<=`, `>=`, `&&`, `||` become a single `SYM:<op>` token.",
[("Lexer.java", "            } else { out.add(\"SYM:\" + c); i++; }", r'''            } else if (c == '"') {
                StringBuilder sb = new StringBuilder(); int j = i + 1; boolean closed = false;
                while (j < src.length()) {
                    char d = src.charAt(j);
                    if (d == '\\' && j + 1 < src.length()) { sb.append(src.charAt(j + 1)); j += 2; }
                    else if (d == '"') { closed = true; j++; break; }
                    else { sb.append(d); j++; }
                }
                if (!closed) throw new IllegalArgumentException("unterminated string");
                out.add("STR:" + sb); i = j;
            } else if (src.startsWith("//", i)) {
                while (i < src.length() && src.charAt(i) != '\n') i++;
            } else if (src.startsWith("/*", i)) {
                int e = src.indexOf("*/", i + 2);
                if (e < 0) throw new IllegalArgumentException("unterminated comment");
                i = e + 2;
            } else if (i + 1 < src.length() && List.of("==", "!=", "<=", ">=", "&&", "||").contains(src.substring(i, i + 2))) {
                out.add("SYM:" + src.substring(i, i + 2)); i += 2;
            } else { out.add("SYM:" + c); i++; }''')],
r'''
eq(List.of("ID:x", "SYM:==", "NUM:10"), Lexer.tokens("x == 10"), "eqeq"); eq(List.of("ID:a", "SYM:=", "ID:b"), Lexer.tokens("a = b"), "single eq");
eq(List.of("STR:hi there", "SYM:;"), Lexer.tokens("\"hi there\";"), "string"); eq(List.of("STR:a\"b\\c"), Lexer.tokens("\"a\\\"b\\\\c\""), "escapes");
eq(List.of("ID:a", "ID:b"), Lexer.tokens("a // comment == \"x\n b"), "line comment"); eq(List.of("ID:a", "ID:b"), Lexer.tokens("a /* x\n y */ b"), "block comment");
eq(List.of("SYM:<=", "SYM:>=", "SYM:!=", "SYM:&&", "SYM:||", "SYM:<", "SYM:!"), Lexer.tokens("<= >= != && || < !"), "ops"); eq(List.of("NUM:1", "SYM:/", "NUM:2"), Lexer.tokens("1 / 2"), "slash alone");
thrown(IllegalArgumentException.class, () -> Lexer.tokens("\"abc"), "unterminated string"); thrown(IllegalArgumentException.class, () -> Lexer.tokens("/* nope"), "unterminated comment");
''')

add("ext-employee-hierarchy-reports", "medium",
{"Employee.java": r'''
import java.util.*;
public class Employee {
    private final String name;
    private final List<Employee> reports = new ArrayList<>();
    public Employee(String name) { this.name = name; }
    public String name() { return name; }
    public Employee addReport(Employee e) { reports.add(e); return this; }
    public List<Employee> directReports() { return reports; }
}'''},
"Add `int totalReports()` (all direct and indirect reports, not counting self), `int depth()` (0 for an employee with no reports, else 1 + max depth of reports), and `List<String> chainTo(String name)` returning names from this employee down to the one with that name (inclusive, depth-first), or an empty list if not found.",
[("Employee.java", "    public Employee addReport", r'''    public int totalReports() { int t = 0; for (Employee e : reports) t += 1 + e.totalReports(); return t; }
    public int depth() { int d = -1; for (Employee e : reports) d = Math.max(d, e.depth()); return d + 1; }
    public List<String> chainTo(String target) {
        if (name.equals(target)) return new ArrayList<>(List.of(name));
        for (Employee e : reports) { List<String> c = e.chainTo(target); if (!c.isEmpty()) { c.add(0, name); return c; } }
        return new ArrayList<>();
    }
    public Employee addReport''')],
r'''
Employee ceo = new Employee("ceo"), vp = new Employee("vp"), dev = new Employee("dev"), qa = new Employee("qa"), cfo = new Employee("cfo");
vp.addReport(dev).addReport(qa); ceo.addReport(vp).addReport(cfo);
eq(4, ceo.totalReports(), "total"); eq(2, vp.totalReports(), "vp total"); eq(0, dev.totalReports(), "leaf"); eq(2, ceo.depth(), "depth"); eq(0, dev.depth(), "leaf depth"); eq(1, vp.depth(), "vp depth");
eq(List.of("ceo", "vp", "qa"), ceo.chainTo("qa"), "chain"); eq(List.of("ceo"), ceo.chainTo("ceo"), "self"); eq(List.of(), ceo.chainTo("nobody"), "missing"); eq(List.of(), vp.chainTo("cfo"), "not below");
''')

add("ext-generic-repository-query", "hard",
{"Entity.java": "public interface Entity { int id(); }\n",
 "Repo.java": r'''
import java.util.*;
public class Repo<T extends Entity> {
    private final Map<Integer, T> store = new TreeMap<>();
    public void save(T t) { store.put(t.id(), t); }
    public Optional<T> find(int id) { return Optional.ofNullable(store.get(id)); }
    public int count() { return store.size(); }
}'''},
"Extend Repo with `List<T> findAll(java.util.function.Predicate<? super T> p)` (in id order), `boolean delete(int id)`, `<R extends Comparable<? super R>> Optional<T> maxBy(java.util.function.Function<? super T, ? extends R> key)` (the entity with the greatest key; first by id on ties; empty if repo empty), and `<K> Map<K, List<T>> groupBy(Function<? super T, ? extends K> f)` preserving id order within groups.",
[("Repo.java", "    public int count()", r'''    public List<T> findAll(java.util.function.Predicate<? super T> p) {
        List<T> out = new ArrayList<>();
        for (T t : store.values()) if (p.test(t)) out.add(t);
        return out;
    }
    public boolean delete(int id) { return store.remove(id) != null; }
    public <R extends Comparable<? super R>> Optional<T> maxBy(java.util.function.Function<? super T, ? extends R> key) {
        T best = null; R bk = null;
        for (T t : store.values()) { R k = key.apply(t); if (best == null || k.compareTo(bk) > 0) { best = t; bk = k; } }
        return Optional.ofNullable(best);
    }
    public <K> Map<K, List<T>> groupBy(java.util.function.Function<? super T, ? extends K> f) {
        Map<K, List<T>> m = new LinkedHashMap<>();
        for (T t : store.values()) m.computeIfAbsent(f.apply(t), k -> new ArrayList<>()).add(t);
        return m;
    }
    public int count()''')],
r'''
Repo<Pet> r = new Repo<>(); r.save(new Pet(3, "cat", 4)); r.save(new Pet(1, "dog", 7)); r.save(new Pet(2, "cat", 7));
eq(List.of(1, 3), r.findAll(p -> p.id() != 2).stream().map(Pet::id).toList(), "findAll ordered"); eq(1, r.maxBy(Pet::age).get().id(), "maxBy tie -> lowest id");
eq(Optional.empty(), new Repo<Pet>().maxBy(Pet::age), "maxBy empty");
Map<String, List<Pet>> g = r.groupBy(Pet::kind); eq(List.of("dog", "cat"), new ArrayList<>(g.keySet()), "group key order"); eq(List.of(2, 3), g.get("cat").stream().map(Pet::id).toList(), "group members");
ok(r.delete(2) && !r.delete(2), "delete"); eq(2, r.count(), "count");
''', helpers=r'''
    record Pet(int id, String kind, int age) implements Entity {}
''')

add("ext-state-machine-guards", "hard",
{"Order.java": r'''
public class Order {
    public enum State { NEW, PAID, SHIPPED, DELIVERED }
    private State state = State.NEW;
    public State state() { return state; }
    public void pay() {
        if (state != State.NEW) throw new IllegalStateException("cannot pay in " + state);
        state = State.PAID;
    }
    public void ship() {
        if (state != State.PAID) throw new IllegalStateException("cannot ship in " + state);
        state = State.SHIPPED;
    }
    public void deliver() {
        if (state != State.SHIPPED) throw new IllegalStateException("cannot deliver in " + state);
        state = State.DELIVERED;
    }
}'''},
"Add cancellation and history. `cancel()` is allowed in NEW and PAID (new state CANCELLED, add it to the enum after DELIVERED) and throws IllegalStateException otherwise. Keep `List<State> history()` — an unmodifiable list of every state the order has been in, starting with NEW, appended on each successful transition. A failed transition changes nothing.",
[("Order.java", "NEW, PAID, SHIPPED, DELIVERED }", "NEW, PAID, SHIPPED, DELIVERED, CANCELLED }"),
 ("Order.java", "    private State state = State.NEW;", "    private State state = State.NEW;\n    private final java.util.List<State> hist = new java.util.ArrayList<>(java.util.List.of(State.NEW));\n    private void to(State s) { state = s; hist.add(s); }\n    public java.util.List<State> history() { return java.util.Collections.unmodifiableList(hist); }\n    public void cancel() {\n        if (state != State.NEW && state != State.PAID) throw new IllegalStateException(\"cannot cancel in \" + state);\n        to(State.CANCELLED);\n    }"),
 ("Order.java", "        state = State.PAID;", "        to(State.PAID);"), ("Order.java", "        state = State.SHIPPED;", "        to(State.SHIPPED);"), ("Order.java", "        state = State.DELIVERED;", "        to(State.DELIVERED);")],
r'''
Order o = new Order(); eq(List.of(Order.State.NEW), o.history(), "initial"); o.pay(); o.ship();
thrown(IllegalStateException.class, () -> o.cancel(), "cannot cancel shipped"); eq(Order.State.SHIPPED, o.state(), "unchanged"); o.deliver();
eq(List.of(Order.State.NEW, Order.State.PAID, Order.State.SHIPPED, Order.State.DELIVERED), o.history(), "full history");
Order p = new Order(); p.cancel(); eq(Order.State.CANCELLED, p.state(), "cancel new"); thrown(IllegalStateException.class, () -> p.pay(), "pay cancelled"); thrown(IllegalStateException.class, () -> p.cancel(), "double cancel");
Order q = new Order(); q.pay(); q.cancel(); eq(List.of(Order.State.NEW, Order.State.PAID, Order.State.CANCELLED), q.history(), "cancel paid");
thrown(UnsupportedOperationException.class, () -> q.history().add(Order.State.NEW), "unmodifiable");
''')

add("ext-tictactoe-winner-draw", "medium",
{"Board.java": r'''
public class Board {
    private final char[][] g = new char[3][3];
    private char turn = 'X';
    public Board() { for (char[] r : g) java.util.Arrays.fill(r, '.'); }
    public char turn() { return turn; }
    public void play(int r, int c) {
        if (r < 0 || r > 2 || c < 0 || c > 2) throw new IllegalArgumentException("off board");
        if (g[r][c] != '.') throw new IllegalStateException("occupied");
        g[r][c] = turn;
        turn = turn == 'X' ? 'O' : 'X';
    }
    public char at(int r, int c) { return g[r][c]; }
}'''},
"Add `char winner()` returning 'X' or 'O' if that player has three in a row/column/diagonal, else '.'; `boolean isDraw()` (board full and no winner); `boolean isOver()`; and make `play` throw IllegalStateException(\"game over\") once the game is over.",
[("Board.java", "    public void play(int r, int c) {", r'''    public char winner() {
        for (int i = 0; i < 3; i++) {
            if (g[i][0] != '.' && g[i][0] == g[i][1] && g[i][1] == g[i][2]) return g[i][0];
            if (g[0][i] != '.' && g[0][i] == g[1][i] && g[1][i] == g[2][i]) return g[0][i];
        }
        if (g[1][1] != '.' && ((g[0][0] == g[1][1] && g[1][1] == g[2][2]) || (g[0][2] == g[1][1] && g[1][1] == g[2][0]))) return g[1][1];
        return '.';
    }
    public boolean isDraw() {
        if (winner() != '.') return false;
        for (char[] r : g) for (char c : r) if (c == '.') return false;
        return true;
    }
    public boolean isOver() { return winner() != '.' || isDraw(); }
    public void play(int r, int c) {
        if (isOver()) throw new IllegalStateException("game over");''')],
r'''
Board b = new Board(); ok(!b.isOver() && b.winner() == '.', "start");
int[][] moves = {{0,0},{1,0},{0,1},{1,1}}; for (int[] m : moves) b.play(m[0], m[1]); b.play(0, 2);
eq('X', b.winner(), "row win"); ok(b.isOver() && !b.isDraw(), "over"); thrown(IllegalStateException.class, () -> b.play(2, 2), "game over");
Board d = new Board(); int[][] dm = {{0,0},{0,1},{0,2},{1,1},{1,0},{1,2},{2,1},{2,0},{2,2}}; for (int[] m : dm) d.play(m[0], m[1]);
eq('.', d.winner(), "no winner"); ok(d.isDraw() && d.isOver(), "draw");
Board e = new Board(); int[][] em = {{0,2},{0,0},{1,1},{0,1},{2,0}}; for (int[] m : em) e.play(m[0], m[1]); eq('X', e.winner(), "anti-diagonal");
Board f = new Board(); int[][] fm = {{0,0},{0,1},{1,0},{1,1},{2,0}}; for (int[] m : fm) f.play(m[0], m[1]); eq('X', f.winner(), "column");
Board h = new Board(); h.play(1, 1); h.play(0, 0); h.play(0, 2); h.play(2, 2); h.play(2, 0); eq('X', h.winner(), "other diag");
''')

add("ext-priority-queue-comparator", "medium",
{"TaskQueue.java": r'''
import java.util.*;
public class TaskQueue {
    public record Task(String name, int priority) {}
    private final PriorityQueue<Task> pq = new PriorityQueue<>(Comparator.comparingInt(Task::priority));
    public void add(String name, int priority) { pq.add(new Task(name, priority)); }
    public Task next() { return pq.poll(); }
    public int size() { return pq.size(); }
}'''},
"Fix ordering semantics and extend: lower priority number should still run first, but tasks with equal priority must come out in insertion (FIFO) order (PriorityQueue alone is not stable). `next()` on an empty queue must throw NoSuchElementException instead of returning null. Add `Task peek()` (same empty behaviour) and `List<String> drainNames()` that removes and returns all names in order.",
[("TaskQueue.java", "    private final PriorityQueue<Task> pq = new PriorityQueue<>(Comparator.comparingInt(Task::priority));\n    public void add(String name, int priority) { pq.add(new Task(name, priority)); }\n    public Task next() { return pq.poll(); }",
 r'''    private record Entry(Task t, long seq) {}
    private long seq;
    private final PriorityQueue<Entry> pq = new PriorityQueue<>(Comparator.comparingInt((Entry e) -> e.t().priority()).thenComparingLong(Entry::seq));
    public void add(String name, int priority) { pq.add(new Entry(new Task(name, priority), seq++)); }
    public Task next() { Entry e = pq.poll(); if (e == null) throw new NoSuchElementException("empty"); return e.t(); }
    public Task peek() { Entry e = pq.peek(); if (e == null) throw new NoSuchElementException("empty"); return e.t(); }
    public List<String> drainNames() { List<String> out = new ArrayList<>(); while (!pq.isEmpty()) out.add(next().name()); return out; }''')],
r'''
TaskQueue q = new TaskQueue(); q.add("c", 2); q.add("a", 1); q.add("b", 1); q.add("d", 2); q.add("e", 1);
eq("a", q.peek().name(), "peek"); eq(5, q.size(), "peek keeps"); eq("a", q.next().name(), "first"); eq(List.of("b", "e", "c", "d"), q.drainNames(), "stable order"); eq(0, q.size(), "drained");
thrown(java.util.NoSuchElementException.class, () -> q.next(), "empty next"); thrown(java.util.NoSuchElementException.class, () -> q.peek(), "empty peek"); eq(List.of(), q.drainNames(), "drain empty");
for (int i = 0; i < 100; i++) q.add("n" + i, 0); for (int i = 0; i < 100; i++) eq("n" + i, q.next().name(), "fifo " + i);
''')

add("ext-string-utils-more", "easy",
{"Strs.java": r'''
public class Strs {
    public static String repeat(String s, int n) {
        if (n < 0) throw new IllegalArgumentException("n < 0");
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < n; i++) sb.append(s);
        return sb.toString();
    }
    public static boolean isBlank(String s) { return s == null || s.trim().isEmpty(); }
}'''},
"Add `String padLeft(String s, int width, char fill)` (no truncation if longer), `String center(String s, int width)` (pad with spaces; if the extra padding is odd, the extra space goes on the right), `int countOccurrences(String s, String sub)` (non-overlapping; empty `sub` throws IllegalArgumentException), and `String capitalize(String s)` (null stays null, empty stays empty).",
[("Strs.java", "    public static boolean isBlank", r'''    public static String padLeft(String s, int width, char fill) { return repeat(String.valueOf(fill), Math.max(0, width - s.length())) + s; }
    public static String center(String s, int width) {
        int extra = Math.max(0, width - s.length()), left = extra / 2;
        return " ".repeat(left) + s + " ".repeat(extra - left);
    }
    public static int countOccurrences(String s, String sub) {
        if (sub.isEmpty()) throw new IllegalArgumentException("empty sub");
        int c = 0, i = 0;
        while ((i = s.indexOf(sub, i)) >= 0) { c++; i += sub.length(); }
        return c;
    }
    public static String capitalize(String s) { return s == null || s.isEmpty() ? s : Character.toUpperCase(s.charAt(0)) + s.substring(1); }
    public static boolean isBlank''')],
r'''
eq("007", Strs.padLeft("7", 3, '0'), "pad"); eq("long", Strs.padLeft("long", 2, '*'), "pad no trunc"); eq(" ab  ", Strs.center("ab", 5), "center odd");
eq("  ab  ", Strs.center("ab", 6), "center even"); eq("abc", Strs.center("abc", 2), "center narrow");
eq(2, Strs.countOccurrences("aaaa", "aa"), "non overlapping"); eq(0, Strs.countOccurrences("abc", "x"), "none"); thrown(IllegalArgumentException.class, () -> Strs.countOccurrences("a", ""), "empty sub");
eq("Hello", Strs.capitalize("hello"), "cap"); eq("", Strs.capitalize(""), "cap empty"); ok(Strs.capitalize(null) == null, "cap null"); eq("xxx", Strs.repeat("x", 3), "old still works");
''')

add("ext-interval-set", "hard",
{"IntervalSet.java": r'''
import java.util.*;
public class IntervalSet {
    private final TreeMap<Integer, Integer> m = new TreeMap<>(); // start -> end (inclusive), disjoint, non-adjacent
    public void add(int lo, int hi) {
        if (lo > hi) throw new IllegalArgumentException("lo > hi");
        Map.Entry<Integer, Integer> e = m.floorEntry(lo);
        if (e != null && e.getValue() >= lo - 1) { lo = e.getKey(); hi = Math.max(hi, e.getValue()); }
        Map.Entry<Integer, Integer> n;
        while ((n = m.ceilingEntry(lo)) != null && n.getKey() <= hi + 1) { hi = Math.max(hi, n.getValue()); m.remove(n.getKey()); }
        m.put(lo, hi);
    }
    public boolean contains(int x) { Map.Entry<Integer, Integer> e = m.floorEntry(x); return e != null && e.getValue() >= x; }
    public List<int[]> intervals() { List<int[]> out = new ArrayList<>(); m.forEach((k, v) -> out.add(new int[]{k, v})); return out; }
}'''},
"Add `void remove(int lo, int hi)` which deletes every integer in [lo, hi] (inclusive), splitting intervals as necessary (lo > hi throws IllegalArgumentException), and `long totalLength()` (count of integers covered).",
[("IntervalSet.java", "    public boolean contains", r'''    public void remove(int lo, int hi) {
        if (lo > hi) throw new IllegalArgumentException("lo > hi");
        List<int[]> keep = new ArrayList<>();
        for (int[] iv : intervals()) {
            if (iv[1] < lo || iv[0] > hi) continue;
            m.remove(iv[0]);
            if (iv[0] < lo) keep.add(new int[]{iv[0], lo - 1});
            if (iv[1] > hi) keep.add(new int[]{hi + 1, iv[1]});
        }
        for (int[] k : keep) m.put(k[0], k[1]);
    }
    public long totalLength() { long t = 0; for (var e : m.entrySet()) t += (long) e.getValue() - e.getKey() + 1; return t; }
    public boolean contains''')],
r'''
IntervalSet s = new IntervalSet(); s.add(1, 10); s.add(20, 30); eq(21L, s.totalLength(), "total");
s.remove(4, 6); eq(List.of(List.of(1,3), List.of(7,10), List.of(20,30)), s.intervals().stream().map(a -> List.of(a[0], a[1])).toList(), "split");
ok(!s.contains(5) && s.contains(3) && s.contains(7), "contains after split"); eq(18L, s.totalLength(), "total after");
s.remove(0, 100); eq(0, s.intervals().size(), "remove all"); eq(0L, s.totalLength(), "zero");
s.add(5, 5); s.remove(6, 9); eq(1L, s.totalLength(), "no effect"); s.remove(5, 5); eq(0L, s.totalLength(), "single removed");
s.add(1, 5); s.add(10, 15); s.remove(3, 12); eq(List.of(List.of(1,2), List.of(13,15)), s.intervals().stream().map(a -> List.of(a[0], a[1])).toList(), "span two"); thrown(IllegalArgumentException.class, () -> s.remove(5, 1), "bad range");
''')

add("ext-visitor-ast-simplify", "hard",
{"Expr.java": r'''
public sealed interface Expr permits Expr.Num, Expr.Add, Expr.Mul {
    record Num(int v) implements Expr {}
    record Add(Expr l, Expr r) implements Expr {}
    record Mul(Expr l, Expr r) implements Expr {}
    static int eval(Expr e) {
        if (e instanceof Num n) return n.v();
        if (e instanceof Add a) return eval(a.l()) + eval(a.r());
        if (e instanceof Mul m) return eval(m.l()) * eval(m.r());
        throw new AssertionError();
    }
}'''},
"Add `static String show(Expr e)` (fully parenthesised infix: Num -> \"3\", Add -> \"(l + r)\", Mul -> \"(l * r)\") and `static Expr simplify(Expr e)` which recursively applies: x+0 -> x, 0+x -> x, x*1 -> x, 1*x -> x, x*0 -> 0, 0*x -> 0, and folds Num op Num into a Num. Simplification must be applied bottom-up so that results of simplification can enable further simplification.",
[("Expr.java", "    static int eval(Expr e) {", r'''    static String show(Expr e) {
        if (e instanceof Num n) return String.valueOf(n.v());
        if (e instanceof Add a) return "(" + show(a.l()) + " + " + show(a.r()) + ")";
        if (e instanceof Mul m) return "(" + show(m.l()) + " * " + show(m.r()) + ")";
        throw new AssertionError();
    }
    static Expr simplify(Expr e) {
        if (e instanceof Add a) {
            Expr l = simplify(a.l()), r = simplify(a.r());
            if (l instanceof Num x && r instanceof Num y) return new Num(x.v() + y.v());
            if (l instanceof Num x && x.v() == 0) return r;
            if (r instanceof Num y && y.v() == 0) return l;
            return new Add(l, r);
        }
        if (e instanceof Mul m) {
            Expr l = simplify(m.l()), r = simplify(m.r());
            if (l instanceof Num x && r instanceof Num y) return new Num(x.v() * y.v());
            if ((l instanceof Num x && x.v() == 0) || (r instanceof Num y && y.v() == 0)) return new Num(0);
            if (l instanceof Num x && x.v() == 1) return r;
            if (r instanceof Num y && y.v() == 1) return l;
            return new Mul(l, r);
        }
        return e;
    }
    static int eval(Expr e) {''')],
r'''
Expr x = new Expr.Num(7);
eq("((1 + 2) * 3)", Expr.show(new Expr.Mul(new Expr.Add(new Expr.Num(1), new Expr.Num(2)), new Expr.Num(3))), "show");
eq(x, Expr.simplify(new Expr.Add(x, new Expr.Num(0))), "x+0"); eq(x, Expr.simplify(new Expr.Mul(new Expr.Num(1), x)), "1*x"); eq(new Expr.Num(0), Expr.simplify(new Expr.Mul(x, new Expr.Num(0))), "x*0");
eq(new Expr.Num(9), Expr.simplify(new Expr.Mul(new Expr.Add(new Expr.Num(1), new Expr.Num(2)), new Expr.Num(3))), "fold");
Expr nested = new Expr.Add(new Expr.Mul(new Expr.Add(new Expr.Num(0), new Expr.Num(0)), x), x);
eq(x, Expr.simplify(nested), "enables further simplification (0+0)*x + x");
Expr y = new Expr.Add(new Expr.Num(1), x); eq(new Expr.Num(8), Expr.simplify(y), "fold with consts"); eq(5, Expr.eval(new Expr.Add(new Expr.Num(2), new Expr.Num(3))), "eval still works");
''')

add("ext-csv-writer-quoting", "medium",
{"CsvReader.java": r'''
import java.util.*;
public class CsvReader {
    public static List<String> parseLine(String line) {
        List<String> out = new ArrayList<>(); StringBuilder cur = new StringBuilder(); boolean inQ = false;
        for (int i = 0; i < line.length(); i++) {
            char c = line.charAt(i);
            if (inQ) {
                if (c == '"') { if (i + 1 < line.length() && line.charAt(i + 1) == '"') { cur.append('"'); i++; } else inQ = false; }
                else cur.append(c);
            } else if (c == '"') inQ = true;
            else if (c == ',') { out.add(cur.toString()); cur.setLength(0); }
            else cur.append(c);
        }
        out.add(cur.toString());
        return out;
    }
}'''},
"Add a `CsvWriter` class (new file) with `static String formatLine(List<String> fields)` that quotes a field only if it contains a comma, double quote, or newline (doubling inner quotes), joining with commas; null fields become empty. Also add `static String formatAll(List<List<String>> rows)` (lines joined with \"\\n\", no trailing newline) and, in CsvReader, `static List<List<String>> parseAll(String text)` splitting on \"\\n\" (ignoring a final empty line) and parsing each line. Round trip formatLine -> parseLine must be lossless for fields without newlines.",
[("CsvReader.java", "    public static List<String> parseLine", "    public static List<List<String>> parseAll(String text) {\n        List<List<String>> rows = new ArrayList<>();\n        for (String l : text.split(\"\\n\", -1)) rows.add(parseLine(l));\n        if (!rows.isEmpty() && text.endsWith(\"\\n\")) rows.remove(rows.size() - 1);\n        return rows;\n    }\n    public static List<String> parseLine")],
r'''
eq("a,b,c", CsvWriter.formatLine(List.of("a", "b", "c")), "plain"); eq("a,\"b,c\",d", CsvWriter.formatLine(List.of("a", "b,c", "d")), "comma"); eq("\"say \"\"hi\"\"\"", CsvWriter.formatLine(List.of("say \"hi\"")), "quote");
eq("a,,c", CsvWriter.formatLine(java.util.Arrays.asList("a", null, "c")), "null"); eq("\"l1\nl2\"", CsvWriter.formatLine(List.of("l1\nl2")), "newline");
List<String> tricky = List.of("x", "y,z", "q\"r", "", " lead");
eq(tricky, CsvReader.parseLine(CsvWriter.formatLine(tricky)), "round trip");
eq("a,b\nc,d", CsvWriter.formatAll(List.of(List.of("a", "b"), List.of("c", "d"))), "formatAll"); eq(List.of(List.of("a", "b"), List.of("c", "d")), CsvReader.parseAll("a,b\nc,d\n"), "parseAll trailing nl");
eq(List.of(List.of("a")), CsvReader.parseAll("a"), "parseAll single");
''', new_files={"CsvWriter.java": r'''
import java.util.*;
public class CsvWriter {
    private static String q(String f) {
        if (f == null) return "";
        if (f.contains(",") || f.contains("\"") || f.contains("\n")) return "\"" + f.replace("\"", "\"\"") + "\"";
        return f;
    }
    public static String formatLine(List<String> fields) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < fields.size(); i++) { if (i > 0) sb.append(','); sb.append(q(fields.get(i))); }
        return sb.toString();
    }
    public static String formatAll(List<List<String>> rows) {
        StringJoiner j = new StringJoiner("\n");
        for (List<String> r : rows) j.add(formatLine(r));
        return j.toString();
    }
}'''})

add("ext-counter-thread-safe", "hard",
{"Hits.java": r'''
import java.util.*;
public class Hits {
    private final Map<String, Integer> counts = new HashMap<>();
    public void hit(String page) { counts.merge(page, 1, Integer::sum); }
    public int get(String page) { return counts.getOrDefault(page, 0); }
    public int total() { int t = 0; for (int v : counts.values()) t += v; return t; }
}'''},
"Make Hits safe to use from many threads (no lost updates, no ConcurrentModificationException while total() is called concurrently with hit()). Keep the same public API and add `Map<String,Integer> snapshot()` returning a consistent copy.",
[("Hits.java", "    private final Map<String, Integer> counts = new HashMap<>();\n    public void hit(String page) { counts.merge(page, 1, Integer::sum); }\n    public int get(String page) { return counts.getOrDefault(page, 0); }\n    public int total() { int t = 0; for (int v : counts.values()) t += v; return t; }",
 "    private final Map<String, Integer> counts = new HashMap<>();\n    public synchronized void hit(String page) { counts.merge(page, 1, Integer::sum); }\n    public synchronized int get(String page) { return counts.getOrDefault(page, 0); }\n    public synchronized int total() { int t = 0; for (int v : counts.values()) t += v; return t; }\n    public synchronized Map<String, Integer> snapshot() { return new HashMap<>(counts); }")],
r'''
Hits h = new Hits(); Thread[] ts = new Thread[6]; boolean[] err = {false};
for (int i = 0; i < ts.length; i++) { final int id = i; ts[i] = new Thread(() -> { try { for (int k = 0; k < 50000; k++) { h.hit("p" + (k % 5)); if (k % 1000 == 0) { h.total(); h.snapshot(); } } } catch (Throwable t) { err[0] = true; } }); ts[i].start(); }
for (Thread t : ts) t.join();
ok(!err[0], "no exceptions in threads"); eq(300000, h.total(), "total"); eq(60000, h.get("p3"), "per page"); eq(5, h.snapshot().size(), "snapshot size");
Map<String,Integer> s = h.snapshot(); h.hit("new"); ok(!s.containsKey("new"), "snapshot is a copy");
''')

add("ext-tree-traversals", "medium",
{"BinTree.java": r'''
import java.util.*;
public class BinTree {
    public static class Node {
        public final int val; public Node left, right;
        public Node(int val, Node left, Node right) { this.val = val; this.left = left; this.right = right; }
    }
    public static List<Integer> inorder(Node n) {
        List<Integer> out = new ArrayList<>();
        walk(n, out);
        return out;
    }
    private static void walk(Node n, List<Integer> out) {
        if (n == null) return;
        walk(n.left, out); out.add(n.val); walk(n.right, out);
    }
}'''},
"Add to BinTree: `preorder(Node)`, `postorder(Node)`, `levelOrder(Node)` returning `List<List<Integer>>` (one list per depth), `maxDepth(Node)` (nodes on longest root-to-leaf path; null tree = 0), and `boolean isSymmetric(Node)` (mirror image of itself).",
[("BinTree.java", "    private static void walk", r'''    public static List<Integer> preorder(Node n) { List<Integer> o = new ArrayList<>(); pre(n, o); return o; }
    private static void pre(Node n, List<Integer> o) { if (n == null) return; o.add(n.val); pre(n.left, o); pre(n.right, o); }
    public static List<Integer> postorder(Node n) { List<Integer> o = new ArrayList<>(); post(n, o); return o; }
    private static void post(Node n, List<Integer> o) { if (n == null) return; post(n.left, o); post(n.right, o); o.add(n.val); }
    public static List<List<Integer>> levelOrder(Node root) {
        List<List<Integer>> out = new ArrayList<>();
        if (root == null) return out;
        Deque<Node> q = new ArrayDeque<>(); q.add(root);
        while (!q.isEmpty()) {
            int sz = q.size(); List<Integer> lvl = new ArrayList<>();
            for (int i = 0; i < sz; i++) { Node n = q.poll(); lvl.add(n.val); if (n.left != null) q.add(n.left); if (n.right != null) q.add(n.right); }
            out.add(lvl);
        }
        return out;
    }
    public static int maxDepth(Node n) { return n == null ? 0 : 1 + Math.max(maxDepth(n.left), maxDepth(n.right)); }
    public static boolean isSymmetric(Node n) { return n == null || mirror(n.left, n.right); }
    private static boolean mirror(Node a, Node b) {
        if (a == null || b == null) return a == b;
        return a.val == b.val && mirror(a.left, b.right) && mirror(a.right, b.left);
    }
    private static void walk''')],
r'''
BinTree.Node t = new BinTree.Node(1, new BinTree.Node(2, new BinTree.Node(4, null, null), new BinTree.Node(5, null, null)), new BinTree.Node(3, null, null));
eq(List.of(1,2,4,5,3), BinTree.preorder(t), "pre"); eq(List.of(4,5,2,3,1), BinTree.postorder(t), "post"); eq(List.of(4,2,5,1,3), BinTree.inorder(t), "in");
eq(List.of(List.of(1), List.of(2,3), List.of(4,5)), BinTree.levelOrder(t), "levels"); eq(3, BinTree.maxDepth(t), "depth"); eq(0, BinTree.maxDepth(null), "depth null"); eq(List.of(), BinTree.levelOrder(null), "levels null");
BinTree.Node s = new BinTree.Node(1, new BinTree.Node(2, new BinTree.Node(3, null, null), null), new BinTree.Node(2, null, new BinTree.Node(3, null, null)));
ok(BinTree.isSymmetric(s), "symmetric"); ok(!BinTree.isSymmetric(t), "asymmetric"); ok(BinTree.isSymmetric(null), "null symmetric");
BinTree.Node bad = new BinTree.Node(1, new BinTree.Node(2, null, new BinTree.Node(3, null, null)), new BinTree.Node(2, null, new BinTree.Node(3, null, null))); ok(!BinTree.isSymmetric(bad), "same side");
''')

add("ext-id-generator-prefix-width", "easy",
{"IdGen.java": r'''
public class IdGen {
    private int next = 1;
    public String nextId() { return "ID" + next++; }
}'''},
"Make the id format configurable: add a constructor `IdGen(String prefix, int width)` producing ids like prefix + zero-padded counter (IdGen(\"INV-\", 4) gives INV-0001, INV-0002, ...; a counter wider than width is not truncated). Keep the no-arg constructor producing \"ID1\", \"ID2\"... as before. Add `void reset(int start)` (next id uses start; start < 1 throws IllegalArgumentException) and `String peek()` returning the id that nextId would return, without advancing.",
[("IdGen.java", "    private int next = 1;\n    public String nextId() { return \"ID\" + next++; }",
 "    private int next = 1;\n    private final String prefix; private final int width;\n    public IdGen() { this(\"ID\", 0); }\n    public IdGen(String prefix, int width) { this.prefix = prefix; this.width = width; }\n    public String peek() { return prefix + String.format(\"%0\" + Math.max(width, 1) + \"d\", next); }\n    public String nextId() { String s = peek(); next++; return s; }\n    public void reset(int start) { if (start < 1) throw new IllegalArgumentException(\"start\"); next = start; }")],
r'''
IdGen g = new IdGen(); eq("ID1", g.nextId(), "default 1"); eq("ID2", g.nextId(), "default 2"); eq("ID3", g.peek(), "peek"); eq("ID3", g.nextId(), "peek does not advance");
IdGen h = new IdGen("INV-", 4); eq("INV-0001", h.nextId(), "padded"); h.reset(9998); eq("INV-9998", h.nextId(), "reset"); eq("INV-9999", h.nextId(), "9999"); eq("INV-10000", h.nextId(), "wider");
IdGen d = new IdGen(); d.reset(10); eq("ID10", d.nextId(), "default reset"); thrown(IllegalArgumentException.class, () -> d.reset(0), "bad reset");
''')

add("ext-money-allocation", "hard",
{"Splitter.java": r'''
import java.util.*;
public class Splitter {
    /** Split total cents evenly among n people; any remainder is ignored (bug-compatible v1). */
    public static long[] splitEven(long total, int n) {
        if (n <= 0) throw new IllegalArgumentException("n");
        long[] out = new long[n];
        Arrays.fill(out, total / n);
        return out;
    }
}'''},
"Extend Splitter: `splitEven` must now distribute the remainder one cent at a time to the first people so that the parts always sum exactly to total (works for non-negative totals; negative total throws IllegalArgumentException). Add `long[] splitWeighted(long total, int[] weights)` giving each person total*weight/sumWeights rounded down, then distributing leftover cents one each in order of largest fractional remainder (ties: lower index first). Weights must be positive and non-empty else IllegalArgumentException.",
[("Splitter.java", "        long[] out = new long[n];\n        Arrays.fill(out, total / n);\n        return out;\n    }", r'''        if (total < 0) throw new IllegalArgumentException("total");
        long[] out = new long[n];
        Arrays.fill(out, total / n);
        for (int i = 0; i < total % n; i++) out[i]++;
        return out;
    }
    public static long[] splitWeighted(long total, int[] weights) {
        if (total < 0 || weights.length == 0) throw new IllegalArgumentException("args");
        long sum = 0; for (int w : weights) { if (w <= 0) throw new IllegalArgumentException("weight"); sum += w; }
        long[] out = new long[weights.length]; long[] rem = new long[weights.length]; long given = 0;
        for (int i = 0; i < weights.length; i++) { out[i] = total * weights[i] / sum; rem[i] = total * weights[i] % sum; given += out[i]; }
        Integer[] idx = new Integer[weights.length]; for (int i = 0; i < idx.length; i++) idx[i] = i;
        Arrays.sort(idx, (a, b) -> rem[a] != rem[b] ? Long.compare(rem[b], rem[a]) : Integer.compare(a, b));
        for (int k = 0; k < total - given; k++) out[idx[k]]++;
        return out;
    }''')],
r'''
long[] a = Splitter.splitEven(100, 3); eq(new int[]{34, 33, 33}, new int[]{(int) a[0], (int) a[1], (int) a[2]}, "100/3");
long[] b = Splitter.splitEven(5, 7); long s = 0; for (long x : b) s += x; eq(5L, s, "sum"); eq(1L, b[4], "fifth gets cent"); eq(0L, b[5], "sixth none");
thrown(IllegalArgumentException.class, () -> Splitter.splitEven(-1, 2), "neg total"); thrown(IllegalArgumentException.class, () -> Splitter.splitEven(1, 0), "zero people");
long[] w = Splitter.splitWeighted(100, new int[]{1, 1, 1}); eq(new int[]{34, 33, 33}, new int[]{(int) w[0], (int) w[1], (int) w[2]}, "equal weights");
long[] w2 = Splitter.splitWeighted(10, new int[]{1, 2}); eq(3L, w2[0], "w2[0]"); eq(7L, w2[1], "w2[1]");
long[] w3 = Splitter.splitWeighted(10, new int[]{5, 3, 2}); eq(5L, w3[0], "w3[0]"); eq(3L, w3[1], "w3[1]"); eq(2L, w3[2], "w3[2]");
long[] w4 = Splitter.splitWeighted(7, new int[]{1, 1, 5}); long t = 0; for (long x : w4) t += x; eq(7L, t, "w4 sum"); eq(5L, w4[2], "w4 big share");
thrown(IllegalArgumentException.class, () -> Splitter.splitWeighted(1, new int[]{}), "no weights"); thrown(IllegalArgumentException.class, () -> Splitter.splitWeighted(1, new int[]{1, 0}), "zero weight");
''')
