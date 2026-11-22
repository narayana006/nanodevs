from lib import impl
T = []
def add(*a, **k): T.append(impl(*a, **k))
U = "throw new UnsupportedOperationException();"

add("impl-fibonacci-memo", "easy", "Implement `Fib.fib(int n)` returning the n-th Fibonacci number as long (fib(0)=0, fib(1)=1). It must be fast for n up to 90 and throw IllegalArgumentException for negative n.",
{"Fib.java": f"public class Fib {{ public static long fib(int n) {{ {U} }} }}"},
{"Fib.java": r'''
public class Fib {
    public static long fib(int n) {
        if (n < 0) throw new IllegalArgumentException("n < 0");
        long a = 0, b = 1;
        for (int i = 0; i < n; i++) { long t = a + b; a = b; b = t; }
        return a;
    }
}'''}, r'''
eq(0L, Fib.fib(0), "0"); eq(1L, Fib.fib(1), "1"); eq(55L, Fib.fib(10), "10"); eq(2880067194370816120L, Fib.fib(90), "90");
thrown(IllegalArgumentException.class, () -> Fib.fib(-1), "neg");
''', visible="Fib.fib(10) == 55")

add("impl-count-chars", "easy", "Implement `Chars.frequencies(String s)` returning a `Map<Character,Integer>` with the count of each character; the map iterates in order of first appearance.",
{"Chars.java": f"import java.util.*;\npublic class Chars {{ public static Map<Character,Integer> frequencies(String s) {{ {U} }} }}"},
{"Chars.java": r'''
import java.util.*;
public class Chars {
    public static Map<Character,Integer> frequencies(String s) {
        Map<Character,Integer> m = new LinkedHashMap<>();
        for (char c : s.toCharArray()) m.merge(c, 1, Integer::sum);
        return m;
    }
}'''}, r'''
Map<Character,Integer> m = Chars.frequencies("banana");
eq(List.of('b','a','n'), new ArrayList<>(m.keySet()), "order");
eq(3, m.get('a'), "a"); eq(2, m.get('n'), "n");
eq(0, Chars.frequencies("").size(), "empty");
''', visible='Chars.frequencies("banana") -> {b=1, a=3, n=2}')

add("impl-is-balanced-brackets", "easy", "Implement `Brackets.isBalanced(String s)`: true if all (), [], {} in s are properly nested and matched; other characters are ignored.",
{"Brackets.java": f"public class Brackets {{ public static boolean isBalanced(String s) {{ {U} }} }}"},
{"Brackets.java": r'''
import java.util.*;
public class Brackets {
    public static boolean isBalanced(String s) {
        Deque<Character> st = new ArrayDeque<>();
        for (char c : s.toCharArray()) {
            if (c == '(' || c == '[' || c == '{') st.push(c);
            else if (c == ')' || c == ']' || c == '}') {
                if (st.isEmpty()) return false;
                char o = st.pop();
                if ((c == ')' && o != '(') || (c == ']' && o != '[') || (c == '}' && o != '{')) return false;
            }
        }
        return st.isEmpty();
    }
}'''}, r'''
ok(Brackets.isBalanced("{[()]}"), "nested"); ok(Brackets.isBalanced("a(b)c"), "text"); ok(Brackets.isBalanced(""), "empty");
ok(!Brackets.isBalanced("(]"), "mismatch"); ok(!Brackets.isBalanced("(("), "open"); ok(!Brackets.isBalanced(")("), "order"); ok(!Brackets.isBalanced("}"), "close only");
''')

add("impl-run-length", "easy", "Implement `Rle.encode(String)` and `Rle.decode(String)`. Encoding writes each run as count followed by the character (\"aaabcc\" -> \"3a1b2c\"). decode is the inverse (counts may have several digits; input never contains digits as payload). Empty string maps to empty string.",
{"Rle.java": f"public class Rle {{ public static String encode(String s) {{ {U} }} public static String decode(String s) {{ {U} }} }}"},
{"Rle.java": r'''
public class Rle {
    public static String encode(String s) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < s.length(); ) {
            int j = i;
            while (j < s.length() && s.charAt(j) == s.charAt(i)) j++;
            sb.append(j - i).append(s.charAt(i));
            i = j;
        }
        return sb.toString();
    }
    public static String decode(String s) {
        StringBuilder sb = new StringBuilder();
        int n = 0;
        for (char c : s.toCharArray()) {
            if (Character.isDigit(c)) n = n * 10 + (c - '0');
            else { sb.append(String.valueOf(c).repeat(n)); n = 0; }
        }
        return sb.toString();
    }
}'''}, r'''
eq("3a1b2c", Rle.encode("aaabcc"), "enc"); eq("", Rle.encode(""), "enc empty"); eq("12x", Rle.encode("xxxxxxxxxxxx"), "enc 12");
eq("aaabcc", Rle.decode("3a1b2c"), "dec"); eq("xxxxxxxxxxxx", Rle.decode("12x"), "dec 12"); eq("", Rle.decode(""), "dec empty");
''', visible='Rle.encode("aaabcc") -> "3a1b2c"')

add("impl-title-case", "easy", "Implement `Text.titleCase(String s)`: capitalize the first letter of each whitespace-separated word and lowercase the rest; collapse runs of whitespace to a single space and trim.",
{"Text.java": f"public class Text {{ public static String titleCase(String s) {{ {U} }} }}"},
{"Text.java": r'''
public class Text {
    public static String titleCase(String s) {
        StringBuilder sb = new StringBuilder();
        for (String w : s.trim().split("\\s+")) {
            if (w.isEmpty()) continue;
            if (sb.length() > 0) sb.append(' ');
            sb.append(Character.toUpperCase(w.charAt(0))).append(w.substring(1).toLowerCase());
        }
        return sb.toString();
    }
}'''}, r'''
eq("Hello World", Text.titleCase("hELLO   wORLD"), "basic"); eq("A", Text.titleCase(" a "), "single"); eq("", Text.titleCase("  "), "blank");
''')

add("impl-snake-to-camel", "easy", "Implement `Names.snakeToCamel(String)` (\"user_account_id\" -> \"userAccountId\"; repeated/leading/trailing underscores ignored) and `Names.camelToSnake(String)` (\"userAccountID\" -> \"user_account_id\": insert '_' before every uppercase letter that is not first, then lowercase).",
{"Names.java": f"public class Names {{ public static String snakeToCamel(String s) {{ {U} }} public static String camelToSnake(String s) {{ {U} }} }}"},
{"Names.java": r'''
public class Names {
    public static String snakeToCamel(String s) {
        StringBuilder sb = new StringBuilder();
        boolean up = false;
        for (char c : s.toCharArray()) {
            if (c == '_') { up = sb.length() > 0; continue; }
            sb.append(up ? Character.toUpperCase(c) : c);
            up = false;
        }
        return sb.toString();
    }
    public static String camelToSnake(String s) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (Character.isUpperCase(c) && i > 0) sb.append('_');
            sb.append(Character.toLowerCase(c));
        }
        return sb.toString();
    }
}'''}, r'''
eq("userAccountId", Names.snakeToCamel("user_account_id"), "s2c"); eq("aB", Names.snakeToCamel("__a__b_"), "underscores"); eq("", Names.snakeToCamel("___"), "only underscores");
eq("user_account_id", Names.camelToSnake("userAccountId"), "c2s"); eq("a_b_c", Names.camelToSnake("aBC"), "caps"); eq("x", Names.camelToSnake("X"), "first");
''')

add("impl-collatz-steps", "easy", "Implement `Collatz.steps(long n)`: number of steps to reach 1 (n even -> n/2, odd -> 3n+1). steps(1)=0. Throw IllegalArgumentException if n < 1.",
{"Collatz.java": f"public class Collatz {{ public static int steps(long n) {{ {U} }} }}"},
{"Collatz.java": r'''
public class Collatz {
    public static int steps(long n) {
        if (n < 1) throw new IllegalArgumentException("n < 1");
        int s = 0;
        while (n != 1) { n = (n % 2 == 0) ? n / 2 : 3 * n + 1; s++; }
        return s;
    }
}'''}, r'''
eq(0, Collatz.steps(1), "1"); eq(1, Collatz.steps(2), "2"); eq(8, Collatz.steps(6), "6"); eq(111, Collatz.steps(27), "27");
thrown(IllegalArgumentException.class, () -> Collatz.steps(0), "0");
''')

add("impl-sieve", "medium", "Implement `Sieve.primesUpTo(int n)` returning `List<Integer>` of all primes <= n in increasing order using a sieve (must handle n = 2_000_000 quickly). n < 2 gives an empty list.",
{"Sieve.java": f"import java.util.*;\npublic class Sieve {{ public static List<Integer> primesUpTo(int n) {{ {U} }} }}"},
{"Sieve.java": r'''
import java.util.*;
public class Sieve {
    public static List<Integer> primesUpTo(int n) {
        List<Integer> out = new ArrayList<>();
        if (n < 2) return out;
        boolean[] comp = new boolean[n + 1];
        for (int i = 2; i <= n; i++) {
            if (comp[i]) continue;
            out.add(i);
            for (long j = (long) i * i; j <= n; j += i) comp[(int) j] = true;
        }
        return out;
    }
}'''}, r'''
eq(List.of(2,3,5,7,11,13), Sieve.primesUpTo(13), "13"); eq(List.of(), Sieve.primesUpTo(1), "1"); eq(List.of(2), Sieve.primesUpTo(2), "2");
eq(148933, Sieve.primesUpTo(2000000).size(), "count to 2M");
''')

add("impl-binary-conversion", "easy", "Implement `Bin.toBinary(int n)` (non-negative n; 0 -> \"0\") and `Bin.fromBinary(String)` (throw NumberFormatException for empty strings or characters other than 0/1). Do not use Integer.toBinaryString/parseInt.",
{"Bin.java": f"public class Bin {{ public static String toBinary(int n) {{ {U} }} public static int fromBinary(String s) {{ {U} }} }}"},
{"Bin.java": r'''
public class Bin {
    public static String toBinary(int n) {
        if (n < 0) throw new IllegalArgumentException("negative");
        if (n == 0) return "0";
        StringBuilder sb = new StringBuilder();
        while (n > 0) { sb.append(n & 1); n >>= 1; }
        return sb.reverse().toString();
    }
    public static int fromBinary(String s) {
        if (s.isEmpty()) throw new NumberFormatException("empty");
        int v = 0;
        for (char c : s.toCharArray()) {
            if (c != '0' && c != '1') throw new NumberFormatException("bad char " + c);
            v = v * 2 + (c - '0');
        }
        return v;
    }
}'''}, r'''
eq("0", Bin.toBinary(0), "0"); eq("1010", Bin.toBinary(10), "10"); eq("11111111", Bin.toBinary(255), "255");
eq(10, Bin.fromBinary("1010"), "from"); eq(5, Bin.fromBinary("0101"), "leading zero");
thrown(NumberFormatException.class, () -> Bin.fromBinary(""), "empty"); thrown(NumberFormatException.class, () -> Bin.fromBinary("102"), "bad");
''')

add("impl-rotate-array", "easy", "Implement `Rot.rotate(int[] a, int k)` rotating the array right by k positions in place (k may be negative or larger than length; empty array is fine).",
{"Rot.java": f"public class Rot {{ public static void rotate(int[] a, int k) {{ {U} }} }}"},
{"Rot.java": r'''
public class Rot {
    public static void rotate(int[] a, int k) {
        int n = a.length;
        if (n == 0) return;
        k = ((k % n) + n) % n;
        rev(a, 0, n - 1); rev(a, 0, k - 1); rev(a, k, n - 1);
    }
    private static void rev(int[] a, int i, int j) { while (i < j) { int t = a[i]; a[i++] = a[j]; a[j--] = t; } }
}'''}, r'''
int[] a = {1,2,3,4,5}; Rot.rotate(a, 2); eq(new int[]{4,5,1,2,3}, a, "2");
a = new int[]{1,2,3,4,5}; Rot.rotate(a, -1); eq(new int[]{2,3,4,5,1}, a, "-1");
a = new int[]{1,2,3}; Rot.rotate(a, 7); eq(new int[]{3,1,2}, a, "7");
a = new int[]{}; Rot.rotate(a, 3); eq(new int[]{}, a, "empty");
''')

add("impl-remove-duplicates-sorted", "easy", "Implement `Dedup.unique(List<Integer> xs)` returning a new list with duplicates removed, keeping first occurrences in original order. Input must not be modified.",
{"Dedup.java": f"import java.util.*;\npublic class Dedup {{ public static List<Integer> unique(List<Integer> xs) {{ {U} }} }}"},
{"Dedup.java": r'''
import java.util.*;
public class Dedup {
    public static List<Integer> unique(List<Integer> xs) { return new ArrayList<>(new LinkedHashSet<>(xs)); }
}'''}, r'''
List<Integer> in = new ArrayList<>(List.of(3,1,3,2,1)); eq(List.of(3,1,2), Dedup.unique(in), "dedup"); eq(5, in.size(), "input unchanged");
eq(List.of(), Dedup.unique(List.of()), "empty");
''')

add("impl-stack-min", "medium", "Implement `MinStack` with push(int), pop() (returns the int), top(), min() — all O(1). pop/top/min on an empty stack throw `java.util.NoSuchElementException`.",
{"MinStack.java": f"public class MinStack {{ public void push(int x) {{ {U} }} public int pop() {{ {U} }} public int top() {{ {U} }} public int min() {{ {U} }} }}"},
{"MinStack.java": r'''
import java.util.*;
public class MinStack {
    private final Deque<int[]> st = new ArrayDeque<>();
    public void push(int x) { st.push(new int[]{x, st.isEmpty() ? x : Math.min(x, st.peek()[1])}); }
    public int pop() { if (st.isEmpty()) throw new NoSuchElementException(); return st.pop()[0]; }
    public int top() { if (st.isEmpty()) throw new NoSuchElementException(); return st.peek()[0]; }
    public int min() { if (st.isEmpty()) throw new NoSuchElementException(); return st.peek()[1]; }
}'''}, r'''
MinStack s = new MinStack(); s.push(5); s.push(2); s.push(7);
eq(2, s.min(), "min"); eq(7, s.top(), "top"); eq(7, s.pop(), "pop"); eq(2, s.pop(), "pop2"); eq(5, s.min(), "min after pops");
s.pop(); thrown(java.util.NoSuchElementException.class, () -> s.min(), "empty min"); thrown(java.util.NoSuchElementException.class, () -> s.pop(), "empty pop");
''')

add("impl-queue-two-stacks", "medium", "Implement a generic `TwoStackQueue<T>` (FIFO) with enqueue(T), dequeue() (throws NoSuchElementException when empty), peek(), size(), isEmpty(). Use two stacks internally with amortized O(1).",
{"TwoStackQueue.java": f"public class TwoStackQueue<T> {{ public void enqueue(T t) {{ {U} }} public T dequeue() {{ {U} }} public T peek() {{ {U} }} public int size() {{ {U} }} public boolean isEmpty() {{ {U} }} }}"},
{"TwoStackQueue.java": r'''
import java.util.*;
public class TwoStackQueue<T> {
    private final Deque<T> in = new ArrayDeque<>(), out = new ArrayDeque<>();
    public void enqueue(T t) { in.push(t); }
    private void shift() { if (out.isEmpty()) while (!in.isEmpty()) out.push(in.pop()); }
    public T dequeue() { shift(); if (out.isEmpty()) throw new NoSuchElementException(); return out.pop(); }
    public T peek() { shift(); if (out.isEmpty()) throw new NoSuchElementException(); return out.peek(); }
    public int size() { return in.size() + out.size(); }
    public boolean isEmpty() { return size() == 0; }
}'''}, r'''
TwoStackQueue<Integer> q = new TwoStackQueue<>();
ok(q.isEmpty(), "empty"); q.enqueue(1); q.enqueue(2); eq(1, q.dequeue(), "1"); q.enqueue(3);
eq(2, q.peek(), "peek"); eq(2, q.size(), "size"); eq(2, q.dequeue(), "2"); eq(3, q.dequeue(), "3");
thrown(java.util.NoSuchElementException.class, () -> q.dequeue(), "empty dequeue");
''')

add("impl-linked-list-reverse", "medium", "Implement a singly linked `IntList` with add(int) (append), toList() (java.util.List<Integer>), reverse() (in place), and removeAll(int value) removing every node with that value.",
{"IntList.java": f"import java.util.*;\npublic class IntList {{ public void add(int v) {{ {U} }} public List<Integer> toList() {{ {U} }} public void reverse() {{ {U} }} public void removeAll(int v) {{ {U} }} }}"},
{"IntList.java": r'''
import java.util.*;
public class IntList {
    private static class N { int v; N next; N(int v) { this.v = v; } }
    private N head, tail;
    public void add(int v) { N n = new N(v); if (head == null) head = tail = n; else { tail.next = n; tail = n; } }
    public List<Integer> toList() { List<Integer> l = new ArrayList<>(); for (N n = head; n != null; n = n.next) l.add(n.v); return l; }
    public void reverse() {
        N prev = null, cur = head; tail = head;
        while (cur != null) { N nx = cur.next; cur.next = prev; prev = cur; cur = nx; }
        head = prev;
    }
    public void removeAll(int v) {
        N dummy = new N(0); dummy.next = head; N p = dummy;
        while (p.next != null) { if (p.next.v == v) p.next = p.next.next; else p = p.next; }
        head = dummy.next; tail = null;
        for (N n = head; n != null; n = n.next) tail = n;
    }
}'''}, r'''
IntList l = new IntList(); for (int x : new int[]{1,2,3,2,4}) l.add(x);
l.reverse(); eq(List.of(4,2,3,2,1), l.toList(), "reverse");
l.add(9); eq(List.of(4,2,3,2,1,9), l.toList(), "append after reverse");
l.removeAll(2); eq(List.of(4,3,1,9), l.toList(), "remove all");
l.removeAll(4); l.removeAll(9); l.add(5); eq(List.of(3,1,5), l.toList(), "head/tail removal then add");
IntList e = new IntList(); e.reverse(); e.removeAll(1); eq(List.of(), e.toList(), "empty");
''')

add("impl-bst", "medium", "Implement `Bst<T extends Comparable<T>>` with insert(T) (ignores duplicates), contains(T), size(), inOrder() returning List<T>, and min()/max() throwing NoSuchElementException when empty.",
{"Bst.java": f"import java.util.*;\npublic class Bst<T extends Comparable<T>> {{ public void insert(T t) {{ {U} }} public boolean contains(T t) {{ {U} }} public int size() {{ {U} }} public List<T> inOrder() {{ {U} }} public T min() {{ {U} }} public T max() {{ {U} }} }}"},
{"Bst.java": r'''
import java.util.*;
public class Bst<T extends Comparable<T>> {
    private class N { T v; N l, r; N(T v) { this.v = v; } }
    private N root; private int size;
    public void insert(T t) {
        if (root == null) { root = new N(t); size++; return; }
        N n = root;
        while (true) {
            int c = t.compareTo(n.v);
            if (c == 0) return;
            if (c < 0) { if (n.l == null) { n.l = new N(t); size++; return; } n = n.l; }
            else { if (n.r == null) { n.r = new N(t); size++; return; } n = n.r; }
        }
    }
    public boolean contains(T t) {
        N n = root;
        while (n != null) { int c = t.compareTo(n.v); if (c == 0) return true; n = c < 0 ? n.l : n.r; }
        return false;
    }
    public int size() { return size; }
    public List<T> inOrder() { List<T> out = new ArrayList<>(); walk(root, out); return out; }
    private void walk(N n, List<T> out) { if (n == null) return; walk(n.l, out); out.add(n.v); walk(n.r, out); }
    public T min() { if (root == null) throw new NoSuchElementException(); N n = root; while (n.l != null) n = n.l; return n.v; }
    public T max() { if (root == null) throw new NoSuchElementException(); N n = root; while (n.r != null) n = n.r; return n.v; }
}'''}, r'''
Bst<Integer> t = new Bst<>();
for (int x : new int[]{5,3,8,1,4,5,9}) t.insert(x);
eq(6, t.size(), "size"); eq(List.of(1,3,4,5,8,9), t.inOrder(), "inorder"); ok(t.contains(4) && !t.contains(7), "contains");
eq(1, t.min(), "min"); eq(9, t.max(), "max");
thrown(java.util.NoSuchElementException.class, () -> new Bst<String>().min(), "empty min");
Bst<String> s = new Bst<>(); s.insert("b"); s.insert("a"); eq(List.of("a","b"), s.inOrder(), "strings");
''')

add("impl-min-heap", "medium", "Implement `IntMinHeap` (array-backed binary heap) with add(int), peek(), poll(), size(), isEmpty(). peek/poll on empty throw NoSuchElementException. Do not use PriorityQueue.",
{"IntMinHeap.java": f"public class IntMinHeap {{ public void add(int x) {{ {U} }} public int peek() {{ {U} }} public int poll() {{ {U} }} public int size() {{ {U} }} public boolean isEmpty() {{ {U} }} }}"},
{"IntMinHeap.java": r'''
import java.util.*;
public class IntMinHeap {
    private int[] a = new int[4]; private int n;
    public void add(int x) {
        if (n == a.length) a = Arrays.copyOf(a, n * 2);
        a[n] = x; int i = n++;
        while (i > 0 && a[(i - 1) / 2] > a[i]) { int p = (i - 1) / 2; int t = a[p]; a[p] = a[i]; a[i] = t; i = p; }
    }
    public int peek() { if (n == 0) throw new NoSuchElementException(); return a[0]; }
    public int poll() {
        if (n == 0) throw new NoSuchElementException();
        int top = a[0]; a[0] = a[--n]; int i = 0;
        while (true) {
            int l = 2 * i + 1, r = l + 1, m = i;
            if (l < n && a[l] < a[m]) m = l;
            if (r < n && a[r] < a[m]) m = r;
            if (m == i) break;
            int t = a[m]; a[m] = a[i]; a[i] = t; i = m;
        }
        return top;
    }
    public int size() { return n; }
    public boolean isEmpty() { return n == 0; }
}'''}, r'''
IntMinHeap h = new IntMinHeap(); int[] in = {9,4,7,1,8,1,3,-5,100,0};
for (int x : in) h.add(x);
eq(-5, h.peek(), "peek"); eq(10, h.size(), "size");
int[] out = new int[in.length]; for (int i = 0; i < out.length; i++) out[i] = h.poll();
int[] sorted = in.clone(); java.util.Arrays.sort(sorted); eq(sorted, out, "heap sort");
ok(h.isEmpty(), "empty"); thrown(java.util.NoSuchElementException.class, () -> h.poll(), "poll empty");
''')

add("impl-hashmap-open", "hard", "Implement `SimpleMap<K,V>`, a hash map using separate chaining with your own bucket array (no java.util.HashMap/Map classes as storage) and resizing at load factor 0.75. Methods: put(K,V) returns previous value or null, get(K) (null if absent), remove(K) returns old value or null, containsKey(K), size(). Null keys are allowed.",
{"SimpleMap.java": f"public class SimpleMap<K, V> {{ public V put(K k, V v) {{ {U} }} public V get(K k) {{ {U} }} public V remove(K k) {{ {U} }} public boolean containsKey(K k) {{ {U} }} public int size() {{ {U} }} }}"},
{"SimpleMap.java": r'''
public class SimpleMap<K, V> {
    private static class E<K, V> { final K k; V v; E<K, V> next; E(K k, V v, E<K, V> n) { this.k = k; this.v = v; next = n; } }
    @SuppressWarnings("unchecked") private E<K, V>[] tab = (E<K, V>[]) new E[4];
    private int size;
    private static int h(Object k) { return k == null ? 0 : (k.hashCode() & 0x7fffffff); }
    private E<K, V> find(K k) {
        for (E<K, V> e = tab[h(k) % tab.length]; e != null; e = e.next) if (java.util.Objects.equals(e.k, k)) return e;
        return null;
    }
    public V put(K k, V v) {
        E<K, V> e = find(k);
        if (e != null) { V old = e.v; e.v = v; return old; }
        if ((size + 1) > tab.length * 0.75) resize();
        int i = h(k) % tab.length;
        tab[i] = new E<>(k, v, tab[i]); size++;
        return null;
    }
    @SuppressWarnings("unchecked") private void resize() {
        E<K, V>[] old = tab; tab = (E<K, V>[]) new E[old.length * 2];
        for (E<K, V> e : old) while (e != null) { E<K, V> nx = e.next; int i = h(e.k) % tab.length; e.next = tab[i]; tab[i] = e; e = nx; }
    }
    public V get(K k) { E<K, V> e = find(k); return e == null ? null : e.v; }
    public boolean containsKey(K k) { return find(k) != null; }
    public V remove(K k) {
        int i = h(k) % tab.length; E<K, V> prev = null;
        for (E<K, V> e = tab[i]; e != null; prev = e, e = e.next) {
            if (java.util.Objects.equals(e.k, k)) { if (prev == null) tab[i] = e.next; else prev.next = e.next; size--; return e.v; }
        }
        return null;
    }
    public int size() { return size; }
}'''}, r'''
SimpleMap<String,Integer> m = new SimpleMap<>();
ok(m.put("a", 1) == null, "first put"); eq(1, m.put("a", 2), "replace"); eq(2, m.get("a"), "get"); ok(m.get("zz") == null, "miss");
for (int i = 0; i < 1000; i++) m.put("k" + i, i);
eq(1001, m.size(), "size"); for (int i = 0; i < 1000; i++) eq(i, m.get("k" + i), "k" + i);
eq(5, m.remove("k5"), "remove"); ok(!m.containsKey("k5"), "removed"); ok(m.remove("k5") == null, "remove again"); eq(1000, m.size(), "size after");
m.put(null, 7); eq(7, m.get(null), "null key"); ok(m.containsKey(null), "null contains");
''')

add("impl-trie", "medium", "Implement `Trie` with insert(String), contains(String) (whole-word), startsWith(String prefix), and `List<String> withPrefix(String prefix)` returning all inserted words with that prefix in alphabetical order.",
{"Trie.java": f"import java.util.*;\npublic class Trie {{ public void insert(String w) {{ {U} }} public boolean contains(String w) {{ {U} }} public boolean startsWith(String p) {{ {U} }} public List<String> withPrefix(String p) {{ {U} }} }}"},
{"Trie.java": r'''
import java.util.*;
public class Trie {
    private static class N { TreeMap<Character, N> kids = new TreeMap<>(); boolean end; }
    private final N root = new N();
    public void insert(String w) { N n = root; for (char c : w.toCharArray()) n = n.kids.computeIfAbsent(c, k -> new N()); n.end = true; }
    private N find(String p) { N n = root; for (char c : p.toCharArray()) { n = n.kids.get(c); if (n == null) return null; } return n; }
    public boolean contains(String w) { N n = find(w); return n != null && n.end; }
    public boolean startsWith(String p) { return find(p) != null; }
    public List<String> withPrefix(String p) {
        List<String> out = new ArrayList<>(); N n = find(p);
        if (n != null) collect(n, new StringBuilder(p), out);
        return out;
    }
    private void collect(N n, StringBuilder sb, List<String> out) {
        if (n.end) out.add(sb.toString());
        for (Map.Entry<Character, N> e : n.kids.entrySet()) { sb.append(e.getKey()); collect(e.getValue(), sb, out); sb.setLength(sb.length() - 1); }
    }
}'''}, r'''
Trie t = new Trie(); for (String w : new String[]{"car","cart","care","dog","cat"}) t.insert(w);
ok(t.contains("car") && !t.contains("ca"), "contains"); ok(t.startsWith("ca") && !t.startsWith("x"), "prefix");
eq(List.of("car","care","cart","cat"), t.withPrefix("ca"), "withPrefix"); eq(List.of(), t.withPrefix("z"), "none");
eq(5, t.withPrefix("").size(), "all");
''')

add("impl-lru-linkedhashmap", "medium", "Implement `Lru<K,V>` with a capacity: get(K) (returns null if absent; marks as most recently used), put(K,V) (evicts the least recently used entry when over capacity), size(), and `List<K> keysOldestFirst()`.",
{"Lru.java": f"import java.util.*;\npublic class Lru<K, V> {{ public Lru(int cap) {{ }} public V get(K k) {{ {U} }} public void put(K k, V v) {{ {U} }} public int size() {{ {U} }} public List<K> keysOldestFirst() {{ {U} }} }}"},
{"Lru.java": r'''
import java.util.*;
public class Lru<K, V> {
    private final LinkedHashMap<K, V> m;
    public Lru(int cap) {
        m = new LinkedHashMap<>(16, 0.75f, true) { protected boolean removeEldestEntry(Map.Entry<K, V> e) { return size() > cap; } };
    }
    public V get(K k) { return m.get(k); }
    public void put(K k, V v) { m.put(k, v); }
    public int size() { return m.size(); }
    public List<K> keysOldestFirst() { return new ArrayList<>(m.keySet()); }
}'''}, r'''
Lru<Integer,String> c = new Lru<>(3); c.put(1,"a"); c.put(2,"b"); c.put(3,"c"); c.get(1); c.put(4,"d");
eq(List.of(3,1,4), c.keysOldestFirst(), "order"); ok(c.get(2) == null, "evicted"); eq(3, c.size(), "size");
c.put(3, "C"); eq(List.of(1,4,3), c.keysOldestFirst(), "put refreshes"); eq("C", c.get(3), "value");
''')

add("impl-generic-pair-swap", "easy", "Implement generic immutable `Pair<A,B>` with getFirst(), getSecond(), `Pair<B,A> swap()`, static `of(A,B)`, plus equals/hashCode/toString in the form \"(first, second)\".",
{"Pair.java": f"public class Pair<A, B> {{ public static <A, B> Pair<A, B> of(A a, B b) {{ {U} }} public A getFirst() {{ {U} }} public B getSecond() {{ {U} }} public Pair<B, A> swap() {{ {U} }} }}"},
{"Pair.java": r'''
import java.util.Objects;
public class Pair<A, B> {
    private final A a; private final B b;
    private Pair(A a, B b) { this.a = a; this.b = b; }
    public static <A, B> Pair<A, B> of(A a, B b) { return new Pair<>(a, b); }
    public A getFirst() { return a; }
    public B getSecond() { return b; }
    public Pair<B, A> swap() { return new Pair<>(b, a); }
    @Override public boolean equals(Object o) { return o instanceof Pair<?, ?> p && Objects.equals(a, p.a) && Objects.equals(b, p.b); }
    @Override public int hashCode() { return Objects.hash(a, b); }
    @Override public String toString() { return "(" + a + ", " + b + ")"; }
}'''}, r'''
Pair<String,Integer> p = Pair.of("x", 1);
eq("x", p.getFirst(), "first"); eq(1, p.getSecond(), "second"); eq(Pair.of(1, "x"), p.swap(), "swap"); eq("(x, 1)", p.toString(), "toString");
eq(Pair.of("x", 1).hashCode(), p.hashCode(), "hash"); ok(!p.equals(Pair.of("x", 2)), "neq"); eq("(null, null)", Pair.of(null, null).toString(), "null");
''')

add("impl-stream-grouping", "medium", "Implement `Emp.avgSalaryByDept(List<Emp> emps)` returning `Map<String, Double>` (dept -> average salary) iterating in alphabetical dept order, and `Emp.topEarners(List<Emp>, int n)` returning names of the n highest-paid employees, highest first (ties by name). `Emp` is a record `Emp(String name, String dept, double salary)`. Use streams if you like.",
{"Emp.java": f"import java.util.*;\npublic record Emp(String name, String dept, double salary) {{ public static Map<String, Double> avgSalaryByDept(List<Emp> e) {{ {U} }} public static List<String> topEarners(List<Emp> e, int n) {{ {U} }} }}"},
{"Emp.java": r'''
import java.util.*;
import java.util.stream.*;
public record Emp(String name, String dept, double salary) {
    public static Map<String, Double> avgSalaryByDept(List<Emp> e) {
        return e.stream().collect(Collectors.groupingBy(Emp::dept, TreeMap::new, Collectors.averagingDouble(Emp::salary)));
    }
    public static List<String> topEarners(List<Emp> e, int n) {
        return e.stream().sorted(Comparator.comparingDouble(Emp::salary).reversed().thenComparing(Emp::name)).limit(n).map(Emp::name).collect(Collectors.toList());
    }
}'''}, r'''
List<Emp> es = List.of(new Emp("ann","eng",100), new Emp("bob","eng",80), new Emp("cy","ops",60), new Emp("di","ops",100), new Emp("ed","hr",50));
Map<String,Double> m = Emp.avgSalaryByDept(es);
eq(List.of("eng","hr","ops"), new ArrayList<>(m.keySet()), "order"); eq(90.0, m.get("eng"), "eng"); eq(80.0, m.get("ops"), "ops");
eq(List.of("ann","di","bob"), Emp.topEarners(es, 3), "top3"); eq(List.of(), Emp.topEarners(es, 0), "top0"); eq(5, Emp.topEarners(es, 10).size(), "top10");
''')

add("impl-sealed-expr-eval", "hard", "Implement an expression evaluator `Eval.eval(String)` for + - * / on integers (as long) with parentheses, unary minus, and spaces. Standard precedence; division truncates toward zero. Throw IllegalArgumentException on malformed input and ArithmeticException on division by zero.",
{"Eval.java": f"public class Eval {{ public static long eval(String s) {{ {U} }} }}"},
{"Eval.java": r'''
public class Eval {
    private final String s; private int p;
    private Eval(String s) { this.s = s; }
    public static long eval(String s) {
        Eval e = new Eval(s); long v = e.expr(); e.ws();
        if (e.p != s.length()) throw new IllegalArgumentException("unexpected '" + s.charAt(e.p) + "'");
        return v;
    }
    private void ws() { while (p < s.length() && s.charAt(p) == ' ') p++; }
    private long expr() {
        long v = term();
        while (true) { ws(); if (p < s.length() && s.charAt(p) == '+') { p++; v += term(); } else if (p < s.length() && s.charAt(p) == '-') { p++; v -= term(); } else return v; }
    }
    private long term() {
        long v = unary();
        while (true) {
            ws();
            if (p < s.length() && s.charAt(p) == '*') { p++; v *= unary(); }
            else if (p < s.length() && s.charAt(p) == '/') { p++; long d = unary(); if (d == 0) throw new ArithmeticException("/ by zero"); v /= d; }
            else return v;
        }
    }
    private long unary() { ws(); if (p < s.length() && s.charAt(p) == '-') { p++; return -unary(); } return atom(); }
    private long atom() {
        ws();
        if (p >= s.length()) throw new IllegalArgumentException("unexpected end");
        char c = s.charAt(p);
        if (c == '(') { p++; long v = expr(); ws(); if (p >= s.length() || s.charAt(p) != ')') throw new IllegalArgumentException("missing )"); p++; return v; }
        if (!Character.isDigit(c)) throw new IllegalArgumentException("unexpected '" + c + "'");
        long v = 0; while (p < s.length() && Character.isDigit(s.charAt(p))) v = v * 10 + (s.charAt(p++) - '0');
        return v;
    }
}'''}, r'''
eq(7L, Eval.eval("1 + 2 * 3"), "prec"); eq(9L, Eval.eval("(1+2)*3"), "parens"); eq(-5L, Eval.eval("-(2+3)"), "unary");
eq(3L, Eval.eval("7 / 2"), "div"); eq(-3L, Eval.eval("-7 / 2"), "div neg"); eq(4L, Eval.eval("10 - 3 - 3"), "left assoc"); eq(2L, Eval.eval("--2"), "double neg");
eq(5L, Eval.eval("  5  "), "spaces");
thrown(ArithmeticException.class, () -> Eval.eval("1/0"), "div0");
thrown(IllegalArgumentException.class, () -> Eval.eval("1 +"), "trailing op"); thrown(IllegalArgumentException.class, () -> Eval.eval("(1"), "unclosed");
thrown(IllegalArgumentException.class, () -> Eval.eval("1 2"), "junk"); thrown(IllegalArgumentException.class, () -> Eval.eval(""), "empty");
''', visible='Eval.eval("1 + 2 * 3") == 7')

add("impl-rpn", "medium", "Implement `Rpn.eval(String)` evaluating a space-separated reverse-Polish expression with ints and + - * / (integer division). Throw IllegalArgumentException for unknown tokens, stack underflow or leftover operands; ArithmeticException for division by zero.",
{"Rpn.java": f"public class Rpn {{ public static int eval(String s) {{ {U} }} }}"},
{"Rpn.java": r'''
import java.util.*;
public class Rpn {
    public static int eval(String s) {
        Deque<Integer> st = new ArrayDeque<>();
        for (String t : s.trim().split("\\s+")) {
            if (t.isEmpty()) continue;
            if (t.length() == 1 && "+-*/".contains(t)) {
                if (st.size() < 2) throw new IllegalArgumentException("underflow");
                int b = st.pop(), a = st.pop();
                switch (t.charAt(0)) {
                    case '+': st.push(a + b); break;
                    case '-': st.push(a - b); break;
                    case '*': st.push(a * b); break;
                    default: if (b == 0) throw new ArithmeticException("/ by zero"); st.push(a / b);
                }
            } else {
                try { st.push(Integer.parseInt(t)); } catch (NumberFormatException e) { throw new IllegalArgumentException("bad token " + t); }
            }
        }
        if (st.size() != 1) throw new IllegalArgumentException("operands left: " + st.size());
        return st.pop();
    }
}'''}, r'''
eq(14, Rpn.eval("5 1 2 + 4 * + 3 -") + 0, "classic");
eq(-3, Rpn.eval("-3"), "single neg"); eq(3, Rpn.eval("7 2 /"), "int div"); eq(-1, Rpn.eval("1 2 -"), "order");
thrown(IllegalArgumentException.class, () -> Rpn.eval("1 +"), "underflow"); thrown(IllegalArgumentException.class, () -> Rpn.eval("1 2"), "leftover");
thrown(IllegalArgumentException.class, () -> Rpn.eval("1 x +"), "bad token"); thrown(ArithmeticException.class, () -> Rpn.eval("1 0 /"), "div0");
thrown(IllegalArgumentException.class, () -> Rpn.eval(""), "empty");
''')

add("impl-matrix-spiral", "medium", "Implement `Spiral.order(int[][] m)` returning `List<Integer>` of the matrix elements in clockwise spiral order starting at the top-left. Works for non-square and empty matrices.",
{"Spiral.java": f"import java.util.*;\npublic class Spiral {{ public static List<Integer> order(int[][] m) {{ {U} }} }}"},
{"Spiral.java": r'''
import java.util.*;
public class Spiral {
    public static List<Integer> order(int[][] m) {
        List<Integer> out = new ArrayList<>();
        if (m.length == 0 || m[0].length == 0) return out;
        int t = 0, b = m.length - 1, l = 0, r = m[0].length - 1;
        while (t <= b && l <= r) {
            for (int j = l; j <= r; j++) out.add(m[t][j]);
            t++;
            for (int i = t; i <= b; i++) out.add(m[i][r]);
            r--;
            if (t <= b) { for (int j = r; j >= l; j--) out.add(m[b][j]); b--; }
            if (l <= r) { for (int i = b; i >= t; i--) out.add(m[i][l]); l++; }
        }
        return out;
    }
}'''}, r'''
eq(List.of(1,2,3,6,9,8,7,4,5), Spiral.order(new int[][]{{1,2,3},{4,5,6},{7,8,9}}), "3x3");
eq(List.of(1,2,3,4,8,12,11,10,9,5,6,7), Spiral.order(new int[][]{{1,2,3,4},{5,6,7,8},{9,10,11,12}}), "3x4");
eq(List.of(1,2,3), Spiral.order(new int[][]{{1,2,3}}), "row"); eq(List.of(1,2,3), Spiral.order(new int[][]{{1},{2},{3}}), "col"); eq(List.of(), Spiral.order(new int[0][0]), "empty");
''')

add("impl-n-queens-count", "hard", "Implement `Queens.count(int n)`: the number of ways to place n non-attacking queens on an n x n board (n >= 1). count(8) = 92.",
{"Queens.java": f"public class Queens {{ public static int count(int n) {{ {U} }} }}"},
{"Queens.java": r'''
public class Queens {
    public static int count(int n) { return go(n, 0, 0, 0, 0); }
    private static int go(int n, int row, int cols, int d1, int d2) {
        if (row == n) return 1;
        int c = 0;
        for (int col = 0; col < n; col++) {
            int a = 1 << col, b = 1 << (row + col), d = 1 << (row - col + n);
            if ((cols & a) != 0 || (d1 & b) != 0 || (d2 & d) != 0) continue;
            c += go(n, row + 1, cols | a, d1 | b, d2 | d);
        }
        return c;
    }
}'''}, r'''
eq(1, Queens.count(1), "1"); eq(0, Queens.count(2), "2"); eq(0, Queens.count(3), "3"); eq(2, Queens.count(4), "4"); eq(10, Queens.count(5), "5"); eq(92, Queens.count(8), "8"); eq(724, Queens.count(10), "10");
''')

add("impl-permutations", "medium", "Implement `Perms.of(List<Integer> xs)` returning all permutations as `List<List<Integer>>` in lexicographic-by-position order (the order produced by choosing elements left-to-right from the remaining ones). Empty input gives one empty permutation.",
{"Perms.java": f"import java.util.*;\npublic class Perms {{ public static List<List<Integer>> of(List<Integer> xs) {{ {U} }} }}"},
{"Perms.java": r'''
import java.util.*;
public class Perms {
    public static List<List<Integer>> of(List<Integer> xs) {
        List<List<Integer>> out = new ArrayList<>();
        go(new ArrayList<>(xs), new ArrayList<>(), out);
        return out;
    }
    private static void go(List<Integer> rest, List<Integer> cur, List<List<Integer>> out) {
        if (rest.isEmpty()) { out.add(new ArrayList<>(cur)); return; }
        for (int i = 0; i < rest.size(); i++) {
            int x = rest.remove(i); cur.add(x);
            go(rest, cur, out);
            cur.remove(cur.size() - 1); rest.add(i, x);
        }
    }
}'''}, r'''
eq(List.of(List.of(1,2,3), List.of(1,3,2), List.of(2,1,3), List.of(2,3,1), List.of(3,1,2), List.of(3,2,1)), Perms.of(List.of(1,2,3)), "123");
eq(List.of(List.of()), Perms.of(List.of()), "empty"); eq(24, Perms.of(List.of(1,2,3,4)).size(), "24");
''')

add("impl-subsets-sum", "medium", "Implement `Subsets.countWithSum(int[] a, int target)`: number of subsets (by index, including the empty subset when target is 0) whose elements sum to target. Elements may be negative or zero (n <= 20).",
{"Subsets.java": f"public class Subsets {{ public static int countWithSum(int[] a, int target) {{ {U} }} }}"},
{"Subsets.java": r'''
public class Subsets {
    public static int countWithSum(int[] a, int target) { return go(a, 0, target); }
    private static int go(int[] a, int i, int rem) {
        if (i == a.length) return rem == 0 ? 1 : 0;
        return go(a, i + 1, rem) + go(a, i + 1, rem - a[i]);
    }
}'''}, r'''
eq(1, Subsets.countWithSum(new int[]{}, 0), "empty zero"); eq(0, Subsets.countWithSum(new int[]{}, 1), "empty one");
eq(2, Subsets.countWithSum(new int[]{1,2,3}, 3), "1,2,3"); eq(4, Subsets.countWithSum(new int[]{0,0}, 0), "zeros");
eq(2, Subsets.countWithSum(new int[]{-1,1}, 0) , "neg"); eq(3, Subsets.countWithSum(new int[]{1,1,1}, 1), "dups");
''')

add("impl-edit-distance", "medium", "Implement `Edit.distance(String a, String b)`: Levenshtein distance (insert, delete, substitute each cost 1).",
{"Edit.java": f"public class Edit {{ public static int distance(String a, String b) {{ {U} }} }}"},
{"Edit.java": r'''
public class Edit {
    public static int distance(String a, String b) {
        int[] prev = new int[b.length() + 1], cur = new int[b.length() + 1];
        for (int j = 0; j <= b.length(); j++) prev[j] = j;
        for (int i = 1; i <= a.length(); i++) {
            cur[0] = i;
            for (int j = 1; j <= b.length(); j++)
                cur[j] = Math.min(Math.min(cur[j - 1], prev[j]) + 1, prev[j - 1] + (a.charAt(i - 1) == b.charAt(j - 1) ? 0 : 1));
            int[] t = prev; prev = cur; cur = t;
        }
        return prev[b.length()];
    }
}'''}, r'''
eq(3, Edit.distance("kitten", "sitting"), "classic"); eq(0, Edit.distance("", ""), "both empty"); eq(4, Edit.distance("", "abcd"), "from empty");
eq(0, Edit.distance("same", "same"), "same"); eq(1, Edit.distance("ab", "b"), "delete"); eq(3, Edit.distance("sunday", "saturday"), "sunday");
''')

add("impl-lcs", "medium", "Implement `Lcs.of(String a, String b)` returning one longest common subsequence string (when several exist, any is fine but its length must be maximal and it must be a subsequence of both).",
{"Lcs.java": f"public class Lcs {{ public static String of(String a, String b) {{ {U} }} }}"},
{"Lcs.java": r'''
public class Lcs {
    public static String of(String a, String b) {
        int[][] d = new int[a.length() + 1][b.length() + 1];
        for (int i = a.length() - 1; i >= 0; i--)
            for (int j = b.length() - 1; j >= 0; j--)
                d[i][j] = a.charAt(i) == b.charAt(j) ? d[i + 1][j + 1] + 1 : Math.max(d[i + 1][j], d[i][j + 1]);
        StringBuilder sb = new StringBuilder();
        int i = 0, j = 0;
        while (i < a.length() && j < b.length()) {
            if (a.charAt(i) == b.charAt(j)) { sb.append(a.charAt(i)); i++; j++; }
            else if (d[i + 1][j] >= d[i][j + 1]) i++; else j++;
        }
        return sb.toString();
    }
}'''}, r'''
String[][] cases = {{"ABCBDAB","BDCABA"}, {"abc","def"}, {"","x"}, {"abcdef","abcdef"}, {"AGGTAB","GXTXAYB"}};
int[] want = {4, 0, 0, 6, 4};
for (int i = 0; i < cases.length; i++) {
    String r = Lcs.of(cases[i][0], cases[i][1]);
    eq(want[i], r.length(), "length " + i);
    ok(isSub(r, cases[i][0]) && isSub(r, cases[i][1]), "subsequence " + i);
}
''', helpers=r'''
    static boolean isSub(String s, String t) { int j = 0; for (int i = 0; i < t.length() && j < s.length(); i++) if (t.charAt(i) == s.charAt(j)) j++; return j == s.length(); }
''')

add("impl-coin-change", "medium", "Implement `Coins.minCoins(int[] coins, int amount)`: fewest coins summing to amount (unlimited supply), or -1 if impossible. amount 0 -> 0.",
{"Coins.java": f"public class Coins {{ public static int minCoins(int[] coins, int amount) {{ {U} }} }}"},
{"Coins.java": r'''
import java.util.*;
public class Coins {
    public static int minCoins(int[] coins, int amount) {
        int[] dp = new int[amount + 1]; Arrays.fill(dp, Integer.MAX_VALUE); dp[0] = 0;
        for (int a = 1; a <= amount; a++)
            for (int c : coins) if (c > 0 && c <= a && dp[a - c] != Integer.MAX_VALUE) dp[a] = Math.min(dp[a], dp[a - c] + 1);
        return dp[amount] == Integer.MAX_VALUE ? -1 : dp[amount];
    }
}'''}, r'''
eq(3, Coins.minCoins(new int[]{1,2,5}, 11), "11"); eq(-1, Coins.minCoins(new int[]{2}, 3), "impossible"); eq(0, Coins.minCoins(new int[]{1}, 0), "zero");
eq(2, Coins.minCoins(new int[]{1,3,4}, 6), "greedy fails"); eq(100, Coins.minCoins(new int[]{1}, 100), "ones");
''')

add("impl-knapsack", "hard", "Implement `Knap.best(int[] weights, int[] values, int cap)`: maximum total value of a 0/1 knapsack.",
{"Knap.java": f"public class Knap {{ public static int best(int[] w, int[] v, int cap) {{ {U} }} }}"},
{"Knap.java": r'''
public class Knap {
    public static int best(int[] w, int[] v, int cap) {
        int[] dp = new int[cap + 1];
        for (int i = 0; i < w.length; i++)
            for (int c = cap; c >= w[i]; c--) dp[c] = Math.max(dp[c], dp[c - w[i]] + v[i]);
        return dp[cap];
    }
}'''}, r'''
eq(220, Knap.best(new int[]{10,20,30}, new int[]{60,100,120}, 50), "classic"); eq(0, Knap.best(new int[]{5}, new int[]{10}, 4), "too heavy");
eq(0, Knap.best(new int[]{}, new int[]{}, 10), "none"); eq(10, Knap.best(new int[]{5}, new int[]{10}, 5), "exact"); eq(10, Knap.best(new int[]{1,1}, new int[]{5,5}, 2), "two");
eq(5, Knap.best(new int[]{1,1}, new int[]{5,5}, 1), "no reuse");
''')

add("impl-lis", "hard", "Implement `Lis.length(int[] a)`: length of the longest strictly increasing subsequence, in O(n log n) (n up to 200000).",
{"Lis.java": f"public class Lis {{ public static int length(int[] a) {{ {U} }} }}"},
{"Lis.java": r'''
public class Lis {
    public static int length(int[] a) {
        int[] t = new int[a.length]; int n = 0;
        for (int x : a) {
            int lo = 0, hi = n;
            while (lo < hi) { int m = (lo + hi) >>> 1; if (t[m] < x) lo = m + 1; else hi = m; }
            t[lo] = x; if (lo == n) n++;
        }
        return n;
    }
}'''}, r'''
eq(4, Lis.length(new int[]{10,9,2,5,3,7,101,18}), "classic"); eq(0, Lis.length(new int[]{}), "empty"); eq(1, Lis.length(new int[]{5,5,5}), "equal"); eq(1, Lis.length(new int[]{3,2,1}), "desc");
int[] big = new int[200000]; for (int i = 0; i < big.length; i++) big[i] = i; eq(200000, Lis.length(big), "big");
''')

add("impl-union-find", "medium", "Implement `UnionFind(int n)` with union(a,b) (returns true if they were in different sets), connected(a,b), find(a), and components().",
{"UnionFind.java": f"public class UnionFind {{ public UnionFind(int n) {{ }} public boolean union(int a, int b) {{ {U} }} public boolean connected(int a, int b) {{ {U} }} public int find(int a) {{ {U} }} public int components() {{ {U} }} }}"},
{"UnionFind.java": r'''
public class UnionFind {
    private final int[] p, sz; private int comps;
    public UnionFind(int n) { p = new int[n]; sz = new int[n]; comps = n; for (int i = 0; i < n; i++) { p[i] = i; sz[i] = 1; } }
    public int find(int a) { while (p[a] != a) { p[a] = p[p[a]]; a = p[a]; } return a; }
    public boolean union(int a, int b) {
        int x = find(a), y = find(b); if (x == y) return false;
        if (sz[x] < sz[y]) { int t = x; x = y; y = t; }
        p[y] = x; sz[x] += sz[y]; comps--; return true;
    }
    public boolean connected(int a, int b) { return find(a) == find(b); }
    public int components() { return comps; }
}'''}, r'''
UnionFind u = new UnionFind(6); eq(6, u.components(), "initial");
ok(u.union(0,1), "u01"); ok(u.union(1,2), "u12"); ok(!u.union(0,2), "already"); ok(u.connected(0,2), "conn"); ok(!u.connected(0,3), "not conn");
eq(4, u.components(), "comps"); u.union(3,4); u.union(4,5); u.union(2,5); eq(1, u.components(), "all");
UnionFind big = new UnionFind(100000); for (int i = 1; i < 100000; i++) big.union(i - 1, i); eq(1, big.components(), "chain");
''')

add("impl-graph-components", "medium", "Implement `Graphs.components(int n, int[][] edges)` returning the number of connected components of an undirected graph with nodes 0..n-1, and `Graphs.hasPath(int n, int[][] edges, int from, int to)`.",
{"Graphs.java": f"public class Graphs {{ public static int components(int n, int[][] e) {{ {U} }} public static boolean hasPath(int n, int[][] e, int a, int b) {{ {U} }} }}"},
{"Graphs.java": r'''
import java.util.*;
public class Graphs {
    private static List<List<Integer>> adj(int n, int[][] e) {
        List<List<Integer>> g = new ArrayList<>(); for (int i = 0; i < n; i++) g.add(new ArrayList<>());
        for (int[] x : e) { g.get(x[0]).add(x[1]); g.get(x[1]).add(x[0]); } return g;
    }
    private static void dfs(List<List<Integer>> g, int s, boolean[] seen) {
        Deque<Integer> st = new ArrayDeque<>(); st.push(s); seen[s] = true;
        while (!st.isEmpty()) { int u = st.pop(); for (int v : g.get(u)) if (!seen[v]) { seen[v] = true; st.push(v); } }
    }
    public static int components(int n, int[][] e) {
        List<List<Integer>> g = adj(n, e); boolean[] seen = new boolean[n]; int c = 0;
        for (int i = 0; i < n; i++) if (!seen[i]) { c++; dfs(g, i, seen); }
        return c;
    }
    public static boolean hasPath(int n, int[][] e, int a, int b) { boolean[] seen = new boolean[n]; dfs(adj(n, e), a, seen); return seen[b]; }
}'''}, r'''
int[][] e = {{0,1},{1,2},{3,4}};
eq(3, Graphs.components(6, e), "3 comps"); eq(0, Graphs.components(0, new int[0][0]), "none"); eq(4, Graphs.components(4, new int[0][0]), "isolated");
ok(Graphs.hasPath(6, e, 0, 2), "path"); ok(!Graphs.hasPath(6, e, 0, 4), "no path"); ok(Graphs.hasPath(6, e, 5, 5), "self");
''')

add("impl-lru-ttl-cache", "hard", "Implement `TtlCache<K,V>` that takes a `java.util.function.LongSupplier clock` (milliseconds) in its constructor along with a ttlMillis. put(k,v) stores the value; get(k) returns it if now - putTime < ttl, else removes it and returns null; size() counts only unexpired entries.",
{"TtlCache.java": f"import java.util.function.LongSupplier;\npublic class TtlCache<K, V> {{ public TtlCache(LongSupplier clock, long ttlMillis) {{ }} public void put(K k, V v) {{ {U} }} public V get(K k) {{ {U} }} public int size() {{ {U} }} }}"},
{"TtlCache.java": r'''
import java.util.*;
import java.util.function.LongSupplier;
public class TtlCache<K, V> {
    private final LongSupplier clock; private final long ttl;
    private final Map<K, Object[]> m = new HashMap<>();
    public TtlCache(LongSupplier clock, long ttlMillis) { this.clock = clock; this.ttl = ttlMillis; }
    public void put(K k, V v) { m.put(k, new Object[]{v, clock.getAsLong()}); }
    @SuppressWarnings("unchecked") public V get(K k) {
        Object[] e = m.get(k); if (e == null) return null;
        if (clock.getAsLong() - (Long) e[1] >= ttl) { m.remove(k); return null; }
        return (V) e[0];
    }
    public int size() { long now = clock.getAsLong(); m.values().removeIf(e -> now - (Long) e[1] >= ttl); return m.size(); }
}'''}, r'''
long[] now = {1000}; TtlCache<String,Integer> c = new TtlCache<>(() -> now[0], 100);
c.put("a", 1); now[0] = 1050; c.put("b", 2); eq(1, c.get("a"), "a alive"); eq(2, c.size(), "two");
now[0] = 1100; ok(c.get("a") == null, "a expired at ttl boundary"); eq(2, c.get("b"), "b alive"); eq(1, c.size(), "one");
now[0] = 1200; ok(c.get("b") == null, "b expired"); eq(0, c.size(), "none");
c.put("a", 5); eq(5, c.get("a"), "re-put");
''')

add("impl-rate-limiter", "hard", "Implement `RateLimiter(LongSupplier clock, int maxPerWindow, long windowMillis)` with `boolean allow()`: sliding-window log — allow() returns true and records the call if fewer than maxPerWindow calls were allowed in the last windowMillis (a call at time t counts for (t, t+window], i.e. it stops counting once now - t >= window); otherwise returns false and records nothing.",
{"RateLimiter.java": f"import java.util.function.LongSupplier;\npublic class RateLimiter {{ public RateLimiter(LongSupplier clock, int max, long window) {{ }} public boolean allow() {{ {U} }} }}"},
{"RateLimiter.java": r'''
import java.util.*;
import java.util.function.LongSupplier;
public class RateLimiter {
    private final LongSupplier clock; private final int max; private final long window;
    private final Deque<Long> log = new ArrayDeque<>();
    public RateLimiter(LongSupplier clock, int max, long window) { this.clock = clock; this.max = max; this.window = window; }
    public boolean allow() {
        long now = clock.getAsLong();
        while (!log.isEmpty() && now - log.peekFirst() >= window) log.pollFirst();
        if (log.size() >= max) return false;
        log.addLast(now); return true;
    }
}'''}, r'''
long[] t = {0}; RateLimiter r = new RateLimiter(() -> t[0], 3, 1000);
ok(r.allow() && r.allow() && r.allow(), "first three"); ok(!r.allow(), "fourth denied");
t[0] = 999; ok(!r.allow(), "still in window");
t[0] = 1000; ok(r.allow() && r.allow() && r.allow(), "all expired at exactly window"); ok(!r.allow(), "full again");
t[0] = 2000; ok(r.allow() && r.allow(), "refill");
''')

add("impl-text-wrap", "medium", "Implement `Wrap.wrap(String text, int width)` returning `List<String>` of lines no longer than width, breaking only at spaces (greedy). Words longer than width are placed on their own line unbroken. Collapse multiple spaces; no empty lines for empty text (returns empty list).",
{"Wrap.java": f"import java.util.*;\npublic class Wrap {{ public static List<String> wrap(String text, int width) {{ {U} }} }}"},
{"Wrap.java": r'''
import java.util.*;
public class Wrap {
    public static List<String> wrap(String text, int width) {
        List<String> out = new ArrayList<>(); StringBuilder cur = new StringBuilder();
        for (String w : text.trim().split("\\s+")) {
            if (w.isEmpty()) continue;
            if (cur.length() == 0) cur.append(w);
            else if (cur.length() + 1 + w.length() <= width) cur.append(' ').append(w);
            else { out.add(cur.toString()); cur.setLength(0); cur.append(w); }
        }
        if (cur.length() > 0) out.add(cur.toString());
        return out;
    }
}'''}, r'''
eq(List.of("the quick", "brown fox", "jumps"), Wrap.wrap("the quick brown fox jumps", 10), "basic");
eq(List.of("a", "extraordinarily", "b"), Wrap.wrap("a extraordinarily b", 5), "long word");
eq(List.of(), Wrap.wrap("   ", 10), "blank"); eq(List.of("a b"), Wrap.wrap("a    b", 3), "collapse");
''')

add("impl-parse-kv-config", "medium", "Implement `Config.parse(String text)` returning `Map<String,String>` (insertion order) from lines `key = value`. Trim whitespace; ignore blank lines and lines starting with '#'; a later duplicate key overrides the earlier one but keeps its original position; throw IllegalArgumentException (message containing the 1-based line number) for a non-blank non-comment line without '='. Values may contain '='.",
{"Config.java": f"import java.util.*;\npublic class Config {{ public static Map<String,String> parse(String text) {{ {U} }} }}"},
{"Config.java": r'''
import java.util.*;
public class Config {
    public static Map<String,String> parse(String text) {
        Map<String,String> m = new LinkedHashMap<>();
        String[] lines = text.split("\n", -1);
        for (int i = 0; i < lines.length; i++) {
            String l = lines[i].trim();
            if (l.isEmpty() || l.startsWith("#")) continue;
            int eq = l.indexOf('=');
            if (eq < 0) throw new IllegalArgumentException("line " + (i + 1) + ": missing '='");
            m.put(l.substring(0, eq).trim(), l.substring(eq + 1).trim());
        }
        return m;
    }
}'''}, r'''
Map<String,String> m = Config.parse("# c\na = 1\n\n b=x=y \nc = z\na = 2\n");
eq(List.of("a","b","c"), new ArrayList<>(m.keySet()), "order"); eq("2", m.get("a"), "override"); eq("x=y", m.get("b"), "value with ="); eq(0, Config.parse("").size(), "empty");
try { Config.parse("a=1\n\nbroken"); fail("expected exception"); } catch (IllegalArgumentException e) { ok(e.getMessage().contains("3"), "line number in message: " + e.getMessage()); }
''')

add("impl-roman-to-int", "easy", "Implement `RomanParse.parse(String)` converting a valid Roman numeral (I V X L C D M, with subtractive forms) to int. Throw IllegalArgumentException for empty strings or illegal characters.",
{"RomanParse.java": f"public class RomanParse {{ public static int parse(String s) {{ {U} }} }}"},
{"RomanParse.java": r'''
public class RomanParse {
    private static int val(char c) {
        switch (c) { case 'I': return 1; case 'V': return 5; case 'X': return 10; case 'L': return 50; case 'C': return 100; case 'D': return 500; case 'M': return 1000; }
        throw new IllegalArgumentException("bad char " + c);
    }
    public static int parse(String s) {
        if (s.isEmpty()) throw new IllegalArgumentException("empty");
        int t = 0;
        for (int i = 0; i < s.length(); i++) {
            int v = val(s.charAt(i));
            if (i + 1 < s.length() && v < val(s.charAt(i + 1))) t -= v; else t += v;
        }
        return t;
    }
}'''}, r'''
eq(4, RomanParse.parse("IV"), "IV"); eq(1994, RomanParse.parse("MCMXCIV"), "1994"); eq(58, RomanParse.parse("LVIII"), "58"); eq(3999, RomanParse.parse("MMMCMXCIX"), "3999");
thrown(IllegalArgumentException.class, () -> RomanParse.parse(""), "empty"); thrown(IllegalArgumentException.class, () -> RomanParse.parse("ABC"), "bad");
''')

add("impl-valid-ipv4", "easy", "Implement `Ip.isValidIpv4(String s)`: exactly four dot-separated decimal parts, each 0-255, no leading zeros (except \"0\" itself), digits only, no spaces.",
{"Ip.java": f"public class Ip {{ public static boolean isValidIpv4(String s) {{ {U} }} }}"},
{"Ip.java": r'''
public class Ip {
    public static boolean isValidIpv4(String s) {
        String[] p = s.split("\\.", -1);
        if (p.length != 4) return false;
        for (String x : p) {
            if (x.isEmpty() || x.length() > 3) return false;
            for (char c : x.toCharArray()) if (c < '0' || c > '9') return false;
            if (x.length() > 1 && x.charAt(0) == '0') return false;
            if (Integer.parseInt(x) > 255) return false;
        }
        return true;
    }
}'''}, r'''
ok(Ip.isValidIpv4("192.168.0.1"), "ok"); ok(Ip.isValidIpv4("0.0.0.0"), "zeros"); ok(Ip.isValidIpv4("255.255.255.255"), "max");
ok(!Ip.isValidIpv4("256.1.1.1"), "256"); ok(!Ip.isValidIpv4("1.2.3"), "three"); ok(!Ip.isValidIpv4("1.2.3.4.5"), "five"); ok(!Ip.isValidIpv4("01.2.3.4"), "leading zero");
ok(!Ip.isValidIpv4("1.2.3."), "trailing dot"); ok(!Ip.isValidIpv4("a.b.c.d"), "letters"); ok(!Ip.isValidIpv4(" 1.2.3.4"), "space"); ok(!Ip.isValidIpv4("-1.2.3.4"), "neg");
''')

add("impl-bank-with-exceptions", "medium", "Implement `Bank` with a checked custom exception `InsufficientFundsException extends Exception` (in its own file; has `long shortfall()`), and `Bank` methods: open(String id, long initial) (IllegalArgumentException on duplicate id or negative initial), balance(String id) (NoSuchElementException if unknown), transfer(String from, String to, long amt) throws InsufficientFundsException (amt must be > 0 else IllegalArgumentException; atomic: nothing changes on failure).",
{"Bank.java": f"public class Bank {{ public void open(String id, long initial) {{ {U} }} public long balance(String id) {{ {U} }} public void transfer(String from, String to, long amt) throws InsufficientFundsException {{ {U} }} }}",
 "InsufficientFundsException.java": f"public class InsufficientFundsException extends Exception {{ public InsufficientFundsException(long shortfall) {{ }} public long shortfall() {{ {U} }} }}"},
{"Bank.java": r'''
import java.util.*;
public class Bank {
    private final Map<String, Long> acc = new HashMap<>();
    public void open(String id, long initial) {
        if (initial < 0 || acc.containsKey(id)) throw new IllegalArgumentException("cannot open " + id);
        acc.put(id, initial);
    }
    public long balance(String id) { Long b = acc.get(id); if (b == null) throw new NoSuchElementException(id); return b; }
    public void transfer(String from, String to, long amt) throws InsufficientFundsException {
        if (amt <= 0) throw new IllegalArgumentException("amount");
        long fb = balance(from); balance(to);
        if (fb < amt) throw new InsufficientFundsException(amt - fb);
        acc.put(from, fb - amt); acc.put(to, acc.get(to) + amt);
    }
}''', "InsufficientFundsException.java": r'''
public class InsufficientFundsException extends Exception {
    private final long shortfall;
    public InsufficientFundsException(long shortfall) { super("short by " + shortfall); this.shortfall = shortfall; }
    public long shortfall() { return shortfall; }
}'''}, r'''
Bank b = new Bank(); b.open("a", 100); b.open("b", 5);
thrown(IllegalArgumentException.class, () -> b.open("a", 1), "dup"); thrown(IllegalArgumentException.class, () -> b.open("c", -1), "neg initial");
b.transfer("a", "b", 30); eq(70L, b.balance("a"), "a"); eq(35L, b.balance("b"), "b");
try { b.transfer("b", "a", 50); fail("should throw"); } catch (InsufficientFundsException e) { eq(15L, e.shortfall(), "shortfall"); }
eq(35L, b.balance("b"), "atomic b"); eq(70L, b.balance("a"), "atomic a");
thrown(java.util.NoSuchElementException.class, () -> b.balance("zz"), "unknown");
thrown(java.util.NoSuchElementException.class, () -> { try { b.transfer("a", "zz", 1); } catch (InsufficientFundsException e) { throw new AssertionError(e); } }, "unknown dest");
eq(70L, b.balance("a"), "unchanged after unknown dest");
thrown(IllegalArgumentException.class, () -> { try { b.transfer("a", "b", 0); } catch (InsufficientFundsException e) { throw new AssertionError(e); } }, "zero amount");
''')

add("impl-interface-plugins", "medium", "Given the `Plugin` interface (already in the files), implement `PluginRegistry` with register(Plugin) (IllegalArgumentException on duplicate name), `String run(String name, String input)` (NoSuchElementException for unknown), and `String pipeline(List<String> names, String input)` feeding each plugin's output to the next.",
{"Plugin.java": "public interface Plugin { String name(); String apply(String input); }",
 "PluginRegistry.java": f"import java.util.*;\npublic class PluginRegistry {{ public void register(Plugin p) {{ {U} }} public String run(String name, String in) {{ {U} }} public String pipeline(List<String> names, String in) {{ {U} }} }}"},
{"Plugin.java": "public interface Plugin { String name(); String apply(String input); }",
 "PluginRegistry.java": r'''
import java.util.*;
public class PluginRegistry {
    private final Map<String, Plugin> m = new LinkedHashMap<>();
    public void register(Plugin p) { if (m.putIfAbsent(p.name(), p) != null) throw new IllegalArgumentException("duplicate " + p.name()); }
    public String run(String name, String in) { Plugin p = m.get(name); if (p == null) throw new NoSuchElementException(name); return p.apply(in); }
    public String pipeline(List<String> names, String in) { String cur = in; for (String n : names) cur = run(n, cur); return cur; }
}'''}, r'''
PluginRegistry r = new PluginRegistry();
r.register(new Plugin() { public String name() { return "upper"; } public String apply(String s) { return s.toUpperCase(); } });
r.register(new Plugin() { public String name() { return "excl"; } public String apply(String s) { return s + "!"; } });
eq("HI", r.run("upper", "hi"), "run"); eq("HI!", r.pipeline(List.of("upper", "excl"), "hi"), "pipeline"); eq("hi", r.pipeline(List.of(), "hi"), "empty pipeline");
thrown(IllegalArgumentException.class, () -> r.register(new Plugin() { public String name() { return "upper"; } public String apply(String s) { return s; } }), "dup");
thrown(java.util.NoSuchElementException.class, () -> r.run("nope", "x"), "unknown");
''')

add("impl-iterator-range", "medium", "Implement `Ranges.range(int start, int endExclusive, int step)` returning an `Iterable<Integer>` that lazily yields start, start+step, ... while < endExclusive (step > 0; for step < 0 it counts down while > endExclusive; step == 0 throws IllegalArgumentException at call time). Iterator.next() past the end throws NoSuchElementException.",
{"Ranges.java": f"public class Ranges {{ public static Iterable<Integer> range(int start, int endExclusive, int step) {{ {U} }} }}"},
{"Ranges.java": r'''
import java.util.*;
public class Ranges {
    public static Iterable<Integer> range(int start, int end, int step) {
        if (step == 0) throw new IllegalArgumentException("step 0");
        return () -> new Iterator<Integer>() {
            long cur = start;
            public boolean hasNext() { return step > 0 ? cur < end : cur > end; }
            public Integer next() { if (!hasNext()) throw new NoSuchElementException(); int v = (int) cur; cur += step; return v; }
        };
    }
}'''}, r'''
List<Integer> l = new ArrayList<>(); for (int x : Ranges.range(0, 10, 3)) l.add(x); eq(List.of(0,3,6,9), l, "up");
l.clear(); for (int x : Ranges.range(5, 0, -2)) l.add(x); eq(List.of(5,3,1), l, "down");
l.clear(); for (int x : Ranges.range(3, 3, 1)) l.add(x); eq(List.of(), l, "empty");
thrown(IllegalArgumentException.class, () -> Ranges.range(0, 5, 0), "step 0");
java.util.Iterator<Integer> it = Ranges.range(0, 1, 1).iterator(); it.next(); thrown(java.util.NoSuchElementException.class, () -> it.next(), "past end");
l.clear(); for (int x : Ranges.range(Integer.MAX_VALUE - 1, Integer.MAX_VALUE, 5)) l.add(x); eq(List.of(Integer.MAX_VALUE - 1), l, "no overflow");
''')

add("impl-immutable-money-record", "medium", "Implement record `Money(long cents, String currency)` with a compact constructor rejecting null/blank currency (IllegalArgumentException), `plus(Money)` and `minus(Money)` (IllegalArgumentException for mismatched currency), `times(int)`, and `toString()` like \"USD 12.34\" (negative: \"USD -0.05\").",
{"Money.java": f"public record Money(long cents, String currency) {{ public Money plus(Money o) {{ {U} }} public Money minus(Money o) {{ {U} }} public Money times(int k) {{ {U} }} }}"},
{"Money.java": r'''
public record Money(long cents, String currency) {
    public Money {
        if (currency == null || currency.isBlank()) throw new IllegalArgumentException("currency");
    }
    private void same(Money o) { if (!currency.equals(o.currency)) throw new IllegalArgumentException("currency mismatch"); }
    public Money plus(Money o) { same(o); return new Money(cents + o.cents, currency); }
    public Money minus(Money o) { same(o); return new Money(cents - o.cents, currency); }
    public Money times(int k) { return new Money(cents * k, currency); }
    @Override public String toString() {
        long a = Math.abs(cents);
        return currency + " " + (cents < 0 ? "-" : "") + (a / 100) + "." + String.format("%02d", a % 100);
    }
}'''}, r'''
Money a = new Money(1234, "USD");
eq("USD 12.34", a.toString(), "toString"); eq("USD -0.05", new Money(-5, "USD").toString(), "negative"); eq("EUR 0.00", new Money(0, "EUR").toString(), "zero");
eq(new Money(1300, "USD"), a.plus(new Money(66, "USD")), "plus"); eq(new Money(1200, "USD"), a.minus(new Money(34, "USD")), "minus"); eq(new Money(3702, "USD"), a.times(3), "times");
thrown(IllegalArgumentException.class, () -> a.plus(new Money(1, "EUR")), "mismatch"); thrown(IllegalArgumentException.class, () -> new Money(1, " "), "blank"); thrown(IllegalArgumentException.class, () -> new Money(1, null), "null");
''')

add("impl-bit-counting", "easy", "Implement `Bits.popCount(int)` (number of set bits; do not use Integer.bitCount), `Bits.isPowerOfTwo(int)` (positive powers only), and `Bits.reverse(int)` (reverse the 32 bits).",
{"Bits.java": f"public class Bits {{ public static int popCount(int x) {{ {U} }} public static boolean isPowerOfTwo(int x) {{ {U} }} public static int reverse(int x) {{ {U} }} }}"},
{"Bits.java": r'''
public class Bits {
    public static int popCount(int x) { int c = 0; while (x != 0) { x &= x - 1; c++; } return c; }
    public static boolean isPowerOfTwo(int x) { return x > 0 && (x & (x - 1)) == 0; }
    public static int reverse(int x) { int r = 0; for (int i = 0; i < 32; i++) { r = (r << 1) | (x & 1); x >>>= 1; } return r; }
}'''}, r'''
eq(0, Bits.popCount(0), "0"); eq(32, Bits.popCount(-1), "-1"); eq(3, Bits.popCount(0b10101), "21"); eq(1, Bits.popCount(Integer.MIN_VALUE), "min");
ok(Bits.isPowerOfTwo(1) && Bits.isPowerOfTwo(1024) && Bits.isPowerOfTwo(1 << 30), "pow2"); ok(!Bits.isPowerOfTwo(0) && !Bits.isPowerOfTwo(-8) && !Bits.isPowerOfTwo(12) && !Bits.isPowerOfTwo(Integer.MIN_VALUE), "not");
eq(Integer.MIN_VALUE, Bits.reverse(1), "rev 1"); eq(1, Bits.reverse(Integer.MIN_VALUE), "rev min"); eq(0xF0000000, Bits.reverse(0xF), "rev F"); eq(Integer.reverse(123456789), Bits.reverse(123456789), "rev big");
''')

add("impl-big-number-add", "medium", "Implement `BigAdd.add(String a, String b)` adding two non-negative decimal integers of arbitrary length given as strings (no BigInteger/BigDecimal). Result has no leading zeros (\"0\" for zero).",
{"BigAdd.java": f"public class BigAdd {{ public static String add(String a, String b) {{ {U} }} }}"},
{"BigAdd.java": r'''
public class BigAdd {
    public static String add(String a, String b) {
        StringBuilder sb = new StringBuilder();
        int i = a.length() - 1, j = b.length() - 1, carry = 0;
        while (i >= 0 || j >= 0 || carry > 0) {
            int s = carry + (i >= 0 ? a.charAt(i--) - '0' : 0) + (j >= 0 ? b.charAt(j--) - '0' : 0);
            sb.append((char) ('0' + s % 10)); carry = s / 10;
        }
        int end = sb.length();
        while (end > 1 && sb.charAt(end - 1) == '0') end--;
        sb.setLength(end);
        return sb.length() == 0 ? "0" : sb.reverse().toString();
    }
}'''}, r'''
eq("579", BigAdd.add("123", "456"), "simple"); eq("1000", BigAdd.add("999", "1"), "carry"); eq("0", BigAdd.add("0", "0"), "zeros"); eq("0", BigAdd.add("", ""), "empty");
eq("100000000000000000000", BigAdd.add("99999999999999999999", "1"), "20 digits"); eq("12", BigAdd.add("0012", "0"), "leading zeros"); eq("300", BigAdd.add("100", "200"), "no trailing strip");
''')
