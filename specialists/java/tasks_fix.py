from lib import fix
T = []
def add(*a, **k): T.append(fix(*a, **k))

add("fix-binsearch-overflow", "easy", "binarySearch returns -1 or loops forever on some inputs (e.g. searching the last element, or large arrays).",
{"Bin.java": r'''
public class Bin {
    /** Index of target in sorted array, or -1. */
    public static int search(int[] a, int target) {
        int lo = 0, hi = a.length - 1;
        while (lo <= hi) {
            int mid = lo + (hi - lo) / 2;
            if (a[mid] == target) return mid;
            if (a[mid] < target) lo = mid + 1; else hi = mid - 1;
        }
        return -1;
    }
}'''}, [("Bin.java", "lo <= hi", "lo < hi")],
r'''
eq(0, Bin.search(new int[]{5}, 5), "single");
eq(4, Bin.search(new int[]{1,3,5,7,9}, 9), "last");
eq(0, Bin.search(new int[]{1,3,5,7,9}, 1), "first");
eq(2, Bin.search(new int[]{1,3,5,7,9}, 5), "mid");
eq(-1, Bin.search(new int[]{1,3,5,7,9}, 4), "missing");
eq(-1, Bin.search(new int[]{}, 4), "empty");
''', "Bin.java")

add("fix-reverse-words", "easy", "reverseWords drops the first word and keeps wrong spacing.",
{"Words.java": r'''
public class Words {
    public static String reverseWords(String s) {
        String[] parts = s.trim().split("\\s+");
        StringBuilder sb = new StringBuilder();
        for (int i = parts.length - 1; i >= 0; i--) {
            sb.append(parts[i]);
            if (i > 0) sb.append(' ');
        }
        return sb.toString();
    }
}'''}, [("Words.java", "i >= 0", "i > 0")],
r'''
eq("c b a", Words.reverseWords("a b c"), "basic");
eq("world hello", Words.reverseWords("  hello    world "), "spaces");
eq("x", Words.reverseWords("x"), "single");
eq("", Words.reverseWords("   "), "blank");
''', "Words.java")

add("fix-is-palindrome", "easy", "isPalindrome says 'A man, a plan, a canal: Panama' is not a palindrome, and crashes on empty input.",
{"Pal.java": r'''
public class Pal {
    public static boolean isPalindrome(String s) {
        StringBuilder b = new StringBuilder();
        for (char c : s.toCharArray()) if (Character.isLetterOrDigit(c)) b.append(Character.toLowerCase(c));
        String t = b.toString();
        int i = 0, j = t.length() - 1;
        while (i < j) { if (t.charAt(i++) != t.charAt(j--)) return false; }
        return true;
    }
}'''}, [("Pal.java", "b.append(Character.toLowerCase(c))", "b.append(c)")],
r'''
ok(Pal.isPalindrome("A man, a plan, a canal: Panama"), "panama");
ok(Pal.isPalindrome(""), "empty");
ok(!Pal.isPalindrome("race a car"), "not");
ok(Pal.isPalindrome("Aa"), "case");
''', "Pal.java")

add("fix-fizzbuzz-order", "easy", "fizzBuzz prints 'Fizz' for multiples of 15 instead of 'FizzBuzz'.",
{"FizzBuzz.java": r'''
import java.util.*;
public class FizzBuzz {
    public static List<String> run(int n) {
        List<String> out = new ArrayList<>();
        for (int i = 1; i <= n; i++) {
            if (i % 15 == 0) out.add("FizzBuzz");
            else if (i % 3 == 0) out.add("Fizz");
            else if (i % 5 == 0) out.add("Buzz");
            else out.add(String.valueOf(i));
        }
        return out;
    }
}'''}, [("FizzBuzz.java", '''            if (i % 15 == 0) out.add("FizzBuzz");
            else if (i % 3 == 0) out.add("Fizz");''', '''            if (i % 3 == 0) out.add("Fizz");
            else if (i % 15 == 0) out.add("FizzBuzz");''')],
r'''
eq(java.util.List.of("1","2","Fizz","4","Buzz","Fizz","7","8","Fizz","Buzz","11","Fizz","13","14","FizzBuzz"), FizzBuzz.run(15), "15");
eq(0, FizzBuzz.run(0).size(), "zero");
''', "FizzBuzz.java")

add("fix-string-equals", "easy", "Registry.has returns false for names that are definitely registered (compares strings with ==).",
{"Registry.java": r'''
import java.util.*;
public class Registry {
    private final List<String> names = new ArrayList<>();
    public void add(String n) { names.add(n); }
    public boolean has(String n) {
        for (String s : names) if (s.equals(n)) return true;
        return false;
    }
}'''}, [("Registry.java", "s.equals(n)", "s == n")],
r'''
Registry r = new Registry();
r.add(new String("alice")); r.add("bob");
ok(r.has(new String("alice")), "alice");
ok(r.has(new StringBuilder("bo").append("b").toString()), "bob");
ok(!r.has("carol"), "carol");
''', "Registry.java")

add("fix-integer-cache", "medium", "Counter.sameCount returns false for equal counts above 127.",
{"Counter.java": r'''
import java.util.*;
public class Counter {
    private final Map<String, Integer> counts = new HashMap<>();
    public void inc(String k) { counts.merge(k, 1, Integer::sum); }
    public int get(String k) { return counts.getOrDefault(k, 0); }
    public boolean sameCount(String a, String b) {
        return counts.getOrDefault(a, 0).equals(counts.getOrDefault(b, 0));
    }
}'''}, [("Counter.java", "counts.getOrDefault(a, 0).equals(counts.getOrDefault(b, 0))", "counts.getOrDefault(a, 0) == counts.getOrDefault(b, 0)")],
r'''
Counter c = new Counter();
for (int i = 0; i < 300; i++) { c.inc("a"); c.inc("b"); }
ok(c.sameCount("a", "b"), "300 vs 300");
c.inc("a");
ok(!c.sameCount("a", "b"), "301 vs 300");
ok(c.sameCount("x", "y"), "both missing");
eq(301, c.get("a"), "get");
''', "Counter.java")

add("fix-concurrent-modification", "medium", "removeNegatives throws ConcurrentModificationException.",
{"Clean.java": r'''
import java.util.*;
public class Clean {
    public static void removeNegatives(List<Integer> xs) {
        Iterator<Integer> it = xs.iterator();
        while (it.hasNext()) if (it.next() < 0) it.remove();
    }
}'''}, [("Clean.java", "Iterator<Integer> it = xs.iterator();\n        while (it.hasNext()) if (it.next() < 0) it.remove();", "for (Integer x : xs) if (x < 0) xs.remove(x);")],
r'''
List<Integer> l = new ArrayList<>(List.of(1, -2, -3, 4, -5, 6));
Clean.removeNegatives(l);
eq(List.of(1, 4, 6), l, "mixed");
List<Integer> m = new ArrayList<>(List.of(-1, -1, -1));
Clean.removeNegatives(m);
eq(0, m.size(), "all neg");
''', "Clean.java")

add("fix-list-remove-int", "medium", "Inventory.removeItemId(7) removes the element at index 7 instead of the element whose value is 7 (or throws).",
{"Inventory.java": r'''
import java.util.*;
public class Inventory {
    private final List<Integer> ids = new ArrayList<>();
    public void add(int id) { ids.add(id); }
    public boolean removeItemId(int id) { return ids.remove(Integer.valueOf(id)); }
    public List<Integer> all() { return ids; }
}'''}, [("Inventory.java", "return ids.remove(Integer.valueOf(id));", "ids.remove(id); return true;")],
r'''
Inventory inv = new Inventory();
inv.add(10); inv.add(7); inv.add(30);
ok(inv.removeItemId(7), "removed 7");
eq(List.of(10, 30), inv.all(), "after");
ok(!inv.removeItemId(99), "99 not present");
eq(List.of(10, 30), inv.all(), "unchanged");
''', "Inventory.java")

add("fix-substring-bounds", "easy", "truncate(\"hello\", 10) throws StringIndexOutOfBoundsException; also the ellipsis should count toward the limit.",
{"Trunc.java": r'''
public class Trunc {
    /** If s is longer than max, cut so that result (with trailing "...") is exactly max chars. max >= 3. */
    public static String truncate(String s, int max) {
        if (s.length() <= max) return s;
        return s.substring(0, max - 3) + "...";
    }
}'''}, [("Trunc.java", '''        if (s.length() <= max) return s;
        return s.substring(0, max - 3) + "...";''', '''        return s.substring(0, max) + "...";''')],
r'''
eq("hello", Trunc.truncate("hello", 10), "short");
eq("hello", Trunc.truncate("hello", 5), "exact");
eq("he...", Trunc.truncate("hello world", 5), "cut");
eq(10, Trunc.truncate("abcdefghijklmnop", 10).length(), "len");
''', "Trunc.java")

add("fix-average-int-division", "easy", "average() of {1,2} returns 1.0 instead of 1.5.",
{"Stats.java": r'''
public class Stats {
    public static double average(int[] xs) {
        if (xs.length == 0) return 0.0;
        long sum = 0;
        for (int x : xs) sum += x;
        return (double) sum / xs.length;
    }
}'''}, [("Stats.java", "return (double) sum / xs.length;", "return sum / xs.length;")],
r'''
eq(1.5, Stats.average(new int[]{1, 2}), "1.5");
eq(0.0, Stats.average(new int[]{}), "empty");
eq(2.0, Stats.average(new int[]{2, 2, 2}), "twos");
eq((double) Integer.MAX_VALUE, Stats.average(new int[]{Integer.MAX_VALUE, Integer.MAX_VALUE, Integer.MAX_VALUE, Integer.MAX_VALUE}), "no overflow");
''', "Stats.java")

add("fix-overflow-factorial", "medium", "factorial(20) is wrong (negative) and factorial(21) should throw ArithmeticException rather than silently overflow.",
{"Fact.java": r'''
public class Fact {
    public static long factorial(int n) {
        if (n < 0) throw new IllegalArgumentException("negative");
        long r = 1;
        for (int i = 2; i <= n; i++) r = Math.multiplyExact(r, (long) i);
        return r;
    }
}'''}, [("Fact.java", "r = Math.multiplyExact(r, (long) i);", "r = r * (int) i;")],
r'''
eq(1L, Fact.factorial(0), "0");
eq(120L, Fact.factorial(5), "5");
eq(2432902008176640000L, Fact.factorial(20), "20");
thrown(ArithmeticException.class, () -> Fact.factorial(21), "21");
thrown(IllegalArgumentException.class, () -> Fact.factorial(-1), "neg");
''', "Fact.java")

add("fix-merge-sorted", "medium", "merge() loses the tail of the longer array.",
{"Merge.java": r'''
public class Merge {
    public static int[] merge(int[] a, int[] b) {
        int[] r = new int[a.length + b.length];
        int i = 0, j = 0, k = 0;
        while (i < a.length && j < b.length) r[k++] = a[i] <= b[j] ? a[i++] : b[j++];
        while (i < a.length) r[k++] = a[i++];
        while (j < b.length) r[k++] = b[j++];
        return r;
    }
}'''}, [("Merge.java", "        while (i < a.length) r[k++] = a[i++];\n        while (j < b.length) r[k++] = b[j++];\n", "")],
r'''
eq(new int[]{1,2,3,4,5,6}, Merge.merge(new int[]{1,3,5}, new int[]{2,4,6}), "interleave");
eq(new int[]{1,2,3,9,10}, Merge.merge(new int[]{1,2,3}, new int[]{9,10}), "tail b");
eq(new int[]{1,2,3}, Merge.merge(new int[]{}, new int[]{1,2,3}), "empty a");
eq(new int[]{1,1,2,2}, Merge.merge(new int[]{1,2}, new int[]{1,2}), "dups");
''', "Merge.java")

add("fix-equals-hashcode", "medium", "Equal Point objects do not collapse in a HashSet: equals is right but hashCode is inconsistent.",
{"Point.java": r'''
import java.util.Objects;
public final class Point {
    private final int x, y;
    public Point(int x, int y) { this.x = x; this.y = y; }
    public int x() { return x; }
    public int y() { return y; }
    @Override public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof Point)) return false;
        Point p = (Point) o;
        return x == p.x && y == p.y;
    }
    @Override public int hashCode() { return Objects.hash(x, y); }
}'''}, [("Point.java", "return Objects.hash(x, y);", "return System.identityHashCode(this);")],
r'''
java.util.Set<Point> s = new java.util.HashSet<>();
s.add(new Point(1, 2)); s.add(new Point(1, 2)); s.add(new Point(2, 1));
eq(2, s.size(), "set size");
eq(new Point(3, 4).hashCode(), new Point(3, 4).hashCode(), "hash");
ok(s.contains(new Point(2, 1)), "contains");
''', "Point.java")

add("fix-compareto-overflow", "medium", "Sorting Version objects gives wrong order for large version numbers (compareTo uses subtraction).",
{"Version.java": r'''
public class Version implements Comparable<Version> {
    final int major, minor;
    public Version(int major, int minor) { this.major = major; this.minor = minor; }
    @Override public int compareTo(Version o) {
        int c = Integer.compare(major, o.major);
        return c != 0 ? c : Integer.compare(minor, o.minor);
    }
}'''}, [("Version.java", '''        int c = Integer.compare(major, o.major);
        return c != 0 ? c : Integer.compare(minor, o.minor);''', '''        int c = major - o.major;
        return c != 0 ? c : minor - o.minor;''')],
r'''
ok(new Version(Integer.MAX_VALUE, 0).compareTo(new Version(-5, 0)) > 0, "big vs negative");
ok(new Version(1, 2).compareTo(new Version(1, 10)) < 0, "minor");
ok(new Version(2, 0).compareTo(new Version(2, 0)) == 0, "equal");
ok(new Version(0, Integer.MIN_VALUE).compareTo(new Version(0, 5)) < 0, "min minor");
''', "Version.java")

add("fix-stack-pop", "easy", "ArrayStack.pop returns the wrong element and size() never shrinks.",
{"ArrayStack.java": r'''
import java.util.*;
public class ArrayStack<T> {
    private Object[] data = new Object[2];
    private int size;
    public void push(T t) {
        if (size == data.length) data = Arrays.copyOf(data, size * 2);
        data[size++] = t;
    }
    @SuppressWarnings("unchecked")
    public T pop() {
        if (size == 0) throw new NoSuchElementException("empty");
        T t = (T) data[--size];
        data[size] = null;
        return t;
    }
    public int size() { return size; }
    public boolean isEmpty() { return size == 0; }
}'''}, [("ArrayStack.java", "T t = (T) data[--size];", "T t = (T) data[size - 1];")],
r'''
ArrayStack<String> s = new ArrayStack<>();
s.push("a"); s.push("b"); s.push("c");
eq("c", s.pop(), "pop c");
eq(2, s.size(), "size");
eq("b", s.pop(), "pop b"); eq("a", s.pop(), "pop a");
ok(s.isEmpty(), "empty");
thrown(java.util.NoSuchElementException.class, () -> s.pop(), "empty pop");
''', "ArrayStack.java")

add("fix-queue-wraparound", "hard", "RingQueue loses/duplicates elements after the head wraps around the internal array.",
{"RingQueue.java": r'''
public class RingQueue {
    private final int[] buf;
    private int head = 0, size = 0;
    public RingQueue(int cap) { buf = new int[cap]; }
    public boolean offer(int v) {
        if (size == buf.length) return false;
        buf[(head + size) % buf.length] = v;
        size++;
        return true;
    }
    public int poll() {
        if (size == 0) throw new IllegalStateException("empty");
        int v = buf[head];
        head = (head + 1) % buf.length;
        size--;
        return v;
    }
    public int size() { return size; }
}'''}, [("RingQueue.java", "buf[(head + size) % buf.length] = v;", "buf[(head + size) % (buf.length + 1 > size ? size + 1 : buf.length)] = v;")],
r'''
RingQueue q = new RingQueue(3);
ok(q.offer(1) && q.offer(2) && q.offer(3), "fill");
ok(!q.offer(4), "full");
eq(1, q.poll(), "p1"); eq(2, q.poll(), "p2");
ok(q.offer(4) && q.offer(5), "wrap offers");
eq(3, q.poll(), "p3"); eq(4, q.poll(), "p4"); eq(5, q.poll(), "p5");
eq(0, q.size(), "size");
thrown(IllegalStateException.class, () -> q.poll(), "empty");
for (int round = 0; round < 10; round++) { q.offer(round); q.offer(round + 100); eq(round, q.poll(), "r" + round); eq(round + 100, q.poll(), "r2" + round); }
''', "RingQueue.java")

add("fix-lru-order", "hard", "LRUCache evicts the most recently used entry instead of the least recently used, and get() does not refresh recency.",
{"LRUCache.java": r'''
import java.util.*;
public class LRUCache<K, V> {
    private final int cap;
    private final LinkedHashMap<K, V> map = new LinkedHashMap<>();
    public LRUCache(int cap) { this.cap = cap; }
    public V get(K k) {
        if (!map.containsKey(k)) return null;
        V v = map.remove(k);
        map.put(k, v);
        return v;
    }
    public void put(K k, V v) {
        map.remove(k);
        map.put(k, v);
        if (map.size() > cap) {
            K eldest = map.keySet().iterator().next();
            map.remove(eldest);
        }
    }
    public int size() { return map.size(); }
    public boolean containsKey(K k) { return map.containsKey(k); }
}'''}, [("LRUCache.java", '''        V v = map.remove(k);
        map.put(k, v);
        return v;''', '''        return map.get(k);'''), ("LRUCache.java", "K eldest = map.keySet().iterator().next();", "K eldest = k;")],
r'''
LRUCache<String, Integer> c = new LRUCache<>(2);
c.put("a", 1); c.put("b", 2);
eq(1, c.get("a"), "get a");
c.put("c", 3);
ok(!c.containsKey("b"), "b evicted");
ok(c.containsKey("a") && c.containsKey("c"), "a,c kept");
c.put("a", 10); c.put("d", 4);
ok(!c.containsKey("c"), "c evicted");
eq(10, c.get("a"), "a updated");
eq(2, c.size(), "size");
ok(c.get("zzz") == null, "miss");
''', "LRUCache.java")

add("fix-gcd-negative", "easy", "gcd(-12, 18) returns -6 and lcm of zero crashes.",
{"MathUtil.java": r'''
public class MathUtil {
    public static int gcd(int a, int b) {
        a = Math.abs(a); b = Math.abs(b);
        while (b != 0) { int t = a % b; a = b; b = t; }
        return a;
    }
    public static int lcm(int a, int b) {
        if (a == 0 || b == 0) return 0;
        return Math.abs(a / gcd(a, b) * b);
    }
}'''}, [("MathUtil.java", "a = Math.abs(a); b = Math.abs(b);", ""), ("MathUtil.java", "        if (a == 0 || b == 0) return 0;\n", "")],
r'''
eq(6, MathUtil.gcd(-12, 18), "neg");
eq(6, MathUtil.gcd(12, -18), "neg2");
eq(5, MathUtil.gcd(0, 5), "zero");
eq(12, MathUtil.lcm(4, 6), "lcm");
eq(0, MathUtil.lcm(0, 6), "lcm zero");
eq(12, MathUtil.lcm(-4, 6), "lcm neg");
''', "MathUtil.java")

add("fix-isprime-sqrt", "easy", "isPrime reports 4 and 9 as prime, and 2 as not prime.",
{"Primes.java": r'''
public class Primes {
    public static boolean isPrime(int n) {
        if (n < 2) return false;
        for (int i = 2; (long) i * i <= n; i++) if (n % i == 0) return false;
        return true;
    }
}'''}, [("Primes.java", "(long) i * i <= n", "i * i < n")],
r'''
ok(Primes.isPrime(2), "2"); ok(Primes.isPrime(3), "3"); ok(!Primes.isPrime(4), "4"); ok(!Primes.isPrime(9), "9");
ok(Primes.isPrime(97), "97"); ok(!Primes.isPrime(1), "1"); ok(!Primes.isPrime(0), "0"); ok(!Primes.isPrime(-7), "-7");
ok(Primes.isPrime(2147483647), "maxint");
''', "Primes.java")

add("fix-char-count", "easy", "countVowels ignores uppercase vowels.",
{"Vowels.java": r'''
public class Vowels {
    public static int countVowels(String s) {
        int n = 0;
        for (char c : s.toLowerCase().toCharArray()) if ("aeiou".indexOf(c) >= 0) n++;
        return n;
    }
}'''}, [("Vowels.java", "s.toLowerCase().toCharArray()", "s.toCharArray()")],
r'''
eq(5, Vowels.countVowels("Education"), "Education");
eq(0, Vowels.countVowels("rhythm"), "none");
eq(2, Vowels.countVowels("AEz"), "upper");
''', "Vowels.java")

add("fix-caesar-wrap", "medium", "Caesar shift breaks for letters near the end of the alphabet and for negative shifts.",
{"Caesar.java": r'''
public class Caesar {
    public static String shift(String s, int k) {
        k = ((k % 26) + 26) % 26;
        StringBuilder sb = new StringBuilder();
        for (char c : s.toCharArray()) {
            if (c >= 'a' && c <= 'z') sb.append((char) ('a' + (c - 'a' + k) % 26));
            else if (c >= 'A' && c <= 'Z') sb.append((char) ('A' + (c - 'A' + k) % 26));
            else sb.append(c);
        }
        return sb.toString();
    }
}'''}, [("Caesar.java", "k = ((k % 26) + 26) % 26;", "k = k % 26;"), ("Caesar.java", "('a' + (c - 'a' + k) % 26)", "(c + k)")],
r'''
eq("Khoor, Zruog!", Caesar.shift("Hello, World!", 3), "hello");
eq("abc", Caesar.shift("xyz", 3), "wrap");
eq("xyz", Caesar.shift("abc", -3), "neg");
eq("abc", Caesar.shift("abc", 26), "full");
eq("bcd", Caesar.shift("abc", 53), "big");
''', "Caesar.java")

add("fix-anagram-groups", "medium", "groupAnagrams merges unrelated words because the key is wrong, and the input order is not preserved.",
{"Anagrams.java": r'''
import java.util.*;
public class Anagrams {
    public static List<List<String>> group(List<String> words) {
        Map<String, List<String>> m = new LinkedHashMap<>();
        for (String w : words) {
            char[] cs = w.toCharArray();
            Arrays.sort(cs);
            m.computeIfAbsent(new String(cs), k -> new ArrayList<>()).add(w);
        }
        return new ArrayList<>(m.values());
    }
}'''}, [("Anagrams.java", "Arrays.sort(cs);\n            m.computeIfAbsent(new String(cs)", "m.computeIfAbsent(String.valueOf(cs.length)")],
r'''
eq(List.of(List.of("eat","tea","ate"), List.of("tan","nat"), List.of("bat")), Anagrams.group(List.of("eat","tan","tea","bat","nat","ate")), "classic");
eq(List.of(), Anagrams.group(List.of()), "empty");
eq(List.of(List.of("ab"), List.of("cd")), Anagrams.group(List.of("ab","cd")), "same length different");
''', "Anagrams.java")

add("fix-optional-orelse", "medium", "findUser(\"nobody\") throws NullPointerException instead of returning Optional.empty().",
{"Users.java": r'''
import java.util.*;
public class Users {
    private final Map<String, String> emails = new HashMap<>();
    public void put(String name, String email) { emails.put(name, email); }
    public Optional<String> findEmail(String name) { return Optional.ofNullable(emails.get(name)).map(String::toLowerCase); }
}'''}, [("Users.java", "Optional.ofNullable(emails.get(name)).map(String::toLowerCase)", "Optional.of(emails.get(name).toLowerCase())")],
r'''
Users u = new Users(); u.put("ann", "ANN@X.COM");
eq(Optional.of("ann@x.com"), u.findEmail("ann"), "found");
eq(Optional.empty(), u.findEmail("nobody"), "missing");
''', "Users.java")

add("fix-stream-distinct-sorted", "medium", "topWords returns duplicates and sorts ascending; it must return the n most frequent distinct words (ties broken alphabetically).",
{"Top.java": r'''
import java.util.*;
import java.util.stream.*;
public class Top {
    public static List<String> topWords(List<String> words, int n) {
        Map<String, Long> freq = words.stream().collect(Collectors.groupingBy(w -> w, Collectors.counting()));
        return freq.entrySet().stream()
            .sorted(Map.Entry.<String, Long>comparingByValue().reversed().thenComparing(Map.Entry.comparingByKey()))
            .limit(n).map(Map.Entry::getKey).collect(Collectors.toList());
    }
}'''}, [("Top.java", "Map.Entry.<String, Long>comparingByValue().reversed().thenComparing(Map.Entry.comparingByKey())", "Map.Entry.<String, Long>comparingByValue()")],
r'''
eq(List.of("a", "b"), Top.topWords(List.of("b","a","a","c","b","a"), 2), "top2");
eq(List.of("x", "y", "z"), Top.topWords(List.of("z","y","x"), 5), "ties alphabetical, n larger than distinct");
eq(List.of(), Top.topWords(List.of(), 3), "empty");
''', "Top.java")

add("fix-date-leap", "medium", "isLeap(2000) is false although 2000 is a leap year (century years divisible by 400 are leap years).",
{"Cal.java": r'''
public class Cal {
    public static boolean isLeap(int y) { return (y % 4 == 0 && y % 100 != 0) || y % 400 == 0; }
    public static int daysInMonth(int y, int m) {
        switch (m) {
            case 2: return isLeap(y) ? 29 : 28;
            case 4: case 6: case 9: case 11: return 30;
            default:
                if (m < 1 || m > 12) throw new IllegalArgumentException("month " + m);
                return 31;
        }
    }
}'''}, [("Cal.java", "(y % 4 == 0 && y % 100 != 0) || y % 400 == 0", "y % 4 == 0 && y % 100 != 0")],
r'''
ok(Cal.isLeap(2000), "2000"); ok(!Cal.isLeap(1900), "1900"); ok(Cal.isLeap(2024), "2024"); ok(!Cal.isLeap(2100), "2100");
eq(29, Cal.daysInMonth(2000, 2), "feb 2000"); eq(28, Cal.daysInMonth(2023, 2), "feb 2023");
eq(30, Cal.daysInMonth(2023, 4), "apr"); eq(31, Cal.daysInMonth(2023, 12), "dec");
thrown(IllegalArgumentException.class, () -> Cal.daysInMonth(2023, 13), "bad month");
''', "Cal.java")

add("fix-matrix-transpose", "medium", "transpose() of a non-square matrix throws ArrayIndexOutOfBounds (dimensions swapped).",
{"Mat.java": r'''
public class Mat {
    public static int[][] transpose(int[][] m) {
        if (m.length == 0) return new int[0][0];
        int[][] t = new int[m[0].length][m.length];
        for (int i = 0; i < m.length; i++)
            for (int j = 0; j < m[0].length; j++) t[j][i] = m[i][j];
        return t;
    }
}'''}, [("Mat.java", "new int[m[0].length][m.length]", "new int[m.length][m[0].length]")],
r'''
eq(new int[][]{{1,4},{2,5},{3,6}}, Mat.transpose(new int[][]{{1,2,3},{4,5,6}}), "2x3");
eq(new int[][]{{1,3},{2,4}}, Mat.transpose(new int[][]{{1,2},{3,4}}), "2x2");
eq(new int[0][0], Mat.transpose(new int[0][0]), "empty");
''', "Mat.java")

add("fix-flatten-nested", "hard", "flatten skips nested lists deeper than one level.",
{"Flat.java": r'''
import java.util.*;
public class Flat {
    public static List<Object> flatten(List<?> in) {
        List<Object> out = new ArrayList<>();
        for (Object o : in) {
            if (o instanceof List) out.addAll(flatten((List<?>) o));
            else out.add(o);
        }
        return out;
    }
}'''}, [("Flat.java", "out.addAll(flatten((List<?>) o));", "out.addAll((List<?>) o);")],
r'''
eq(List.of(1, 2, 3, 4, 5), Flat.flatten(List.of(1, List.of(2, List.of(3, List.of(4))), 5)), "deep");
eq(List.of(), Flat.flatten(List.of(List.of(), List.of(List.of()))), "empty nests");
eq(List.of("a"), Flat.flatten(List.of("a")), "flat");
''', "Flat.java")

add("fix-bank-withdraw", "medium", "Account.withdraw allows overdraft and does not reject negative amounts; failed withdrawals must leave the balance unchanged.",
{"Account.java": r'''
public class Account {
    private long balance;
    public Account(long initial) { this.balance = initial; }
    public void deposit(long amt) {
        if (amt <= 0) throw new IllegalArgumentException("amount must be positive");
        balance += amt;
    }
    public void withdraw(long amt) {
        if (amt <= 0) throw new IllegalArgumentException("amount must be positive");
        if (amt > balance) throw new IllegalStateException("insufficient funds");
        balance -= amt;
    }
    public long balance() { return balance; }
}'''}, [("Account.java", '''        if (amt <= 0) throw new IllegalArgumentException("amount must be positive");
        if (amt > balance) throw new IllegalStateException("insufficient funds");
        balance -= amt;''', '''        balance -= amt;''')],
r'''
Account a = new Account(100);
a.withdraw(40); eq(60L, a.balance(), "after withdraw");
thrown(IllegalStateException.class, () -> a.withdraw(61), "overdraft");
eq(60L, a.balance(), "unchanged");
thrown(IllegalArgumentException.class, () -> a.withdraw(-5), "neg");
thrown(IllegalArgumentException.class, () -> a.deposit(0), "zero deposit");
a.withdraw(60); eq(0L, a.balance(), "exact");
''', "Account.java")

add("fix-parse-csv-quotes", "hard", "parseLine splits on commas inside quoted fields and keeps the quotes; also trailing empty field is lost.",
{"Csv.java": r'''
import java.util.*;
public class Csv {
    public static List<String> parseLine(String line) {
        List<String> out = new ArrayList<>();
        StringBuilder cur = new StringBuilder();
        boolean inQ = false;
        for (int i = 0; i < line.length(); i++) {
            char c = line.charAt(i);
            if (inQ) {
                if (c == '"') {
                    if (i + 1 < line.length() && line.charAt(i + 1) == '"') { cur.append('"'); i++; }
                    else inQ = false;
                } else cur.append(c);
            } else if (c == '"') inQ = true;
            else if (c == ',') { out.add(cur.toString()); cur.setLength(0); }
            else cur.append(c);
        }
        out.add(cur.toString());
        return out;
    }
}'''}, [("Csv.java", "        out.add(cur.toString());\n        return out;", "        if (cur.length() > 0) out.add(cur.toString());\n        return out;"), ("Csv.java", "} else cur.append(c);\n            } else if (c == '\"') inQ = true;", "} else cur.append(c);\n            } else if (c == '\"') cur.append(c);")],
r'''
eq(List.of("a", "b", "c"), Csv.parseLine("a,b,c"), "plain");
eq(List.of("a", "b,c", "d"), Csv.parseLine("a,\"b,c\",d"), "quoted comma");
eq(List.of("say \"hi\"", "x"), Csv.parseLine("\"say \"\"hi\"\"\",x"), "escaped quote");
eq(List.of("a", ""), Csv.parseLine("a,"), "trailing empty");
eq(List.of(""), Csv.parseLine(""), "empty line");
''', "Csv.java")

add("fix-binary-tree-height", "medium", "height() of a single node is 1 but should be 0 per the doc (edges), and empty tree should be -1.",
{"Tree.java": r'''
public class Tree {
    static class Node { int v; Node l, r; Node(int v) { this.v = v; } }
    Node root;
    public void insert(int v) { root = ins(root, v); }
    private Node ins(Node n, int v) {
        if (n == null) return new Node(v);
        if (v < n.v) n.l = ins(n.l, v); else if (v > n.v) n.r = ins(n.r, v);
        return n;
    }
    /** Height in edges. Empty tree = -1, single node = 0. */
    public int height() { return h(root); }
    private int h(Node n) { return n == null ? -1 : 1 + Math.max(h(n.l), h(n.r)); }
}'''}, [("Tree.java", "return n == null ? -1 : 1 + Math.max(h(n.l), h(n.r));", "return n == null ? 0 : 1 + Math.max(h(n.l), h(n.r));")],
r'''
Tree t = new Tree();
eq(-1, t.height(), "empty");
t.insert(5); eq(0, t.height(), "one");
t.insert(3); t.insert(8); eq(1, t.height(), "balanced");
t.insert(9); t.insert(10); eq(3, t.height(), "right chain");
''', "Tree.java")

add("fix-topo-sort-cycle", "hard", "topoSort returns a partial order silently when the graph has a cycle; it must throw IllegalStateException. It also misses nodes with no edges.",
{"Topo.java": r'''
import java.util.*;
public class Topo {
    /** nodes 0..n-1, edges[i] = {from, to}. Returns a topological order; throws IllegalStateException on cycle. */
    public static List<Integer> sort(int n, int[][] edges) {
        List<List<Integer>> g = new ArrayList<>();
        int[] indeg = new int[n];
        for (int i = 0; i < n; i++) g.add(new ArrayList<>());
        for (int[] e : edges) { g.get(e[0]).add(e[1]); indeg[e[1]]++; }
        Deque<Integer> q = new ArrayDeque<>();
        for (int i = 0; i < n; i++) if (indeg[i] == 0) q.add(i);
        List<Integer> out = new ArrayList<>();
        while (!q.isEmpty()) {
            int u = q.poll();
            out.add(u);
            for (int v : g.get(u)) if (--indeg[v] == 0) q.add(v);
        }
        if (out.size() != n) throw new IllegalStateException("cycle");
        return out;
    }
}'''}, [("Topo.java", '        if (out.size() != n) throw new IllegalStateException("cycle");\n', ""), ("Topo.java", "for (int i = 0; i < n; i++) if (indeg[i] == 0) q.add(i);", "for (int[] e : edges) if (indeg[e[0]] == 0 && !q.contains(e[0])) q.add(e[0]);")],
r'''
eq(List.of(0, 1, 2, 3), Topo.sort(4, new int[][]{{0,1},{1,2},{2,3}}), "chain");
List<Integer> o = Topo.sort(5, new int[][]{{0,1},{0,2},{1,3},{2,3}});
ok(o.size() == 5 && o.indexOf(0) < o.indexOf(1) && o.indexOf(1) < o.indexOf(3) && o.indexOf(2) < o.indexOf(3), "diamond + isolated node 4: " + o);
thrown(IllegalStateException.class, () -> Topo.sort(3, new int[][]{{0,1},{1,2},{2,1}}), "cycle");
eq(3, Topo.sort(3, new int[][]{}).size(), "no edges");
''', "Topo.java")

add("fix-dijkstra-visited", "hard", "shortest path distances are wrong when a shorter route is discovered later (stale queue entries are processed).",
{"Dijkstra.java": r'''
import java.util.*;
public class Dijkstra {
    public static int[] dist(int n, int[][] edges, int src) {
        List<List<int[]>> g = new ArrayList<>();
        for (int i = 0; i < n; i++) g.add(new ArrayList<>());
        for (int[] e : edges) g.get(e[0]).add(new int[]{e[1], e[2]});
        int[] d = new int[n];
        Arrays.fill(d, Integer.MAX_VALUE);
        d[src] = 0;
        PriorityQueue<int[]> pq = new PriorityQueue<>((a, b) -> Integer.compare(a[1], b[1]));
        pq.add(new int[]{src, 0});
        while (!pq.isEmpty()) {
            int[] cur = pq.poll();
            if (cur[1] > d[cur[0]]) continue;
            for (int[] e : g.get(cur[0])) {
                int nd = cur[1] + e[1];
                if (nd < d[e[0]]) { d[e[0]] = nd; pq.add(new int[]{e[0], nd}); }
            }
        }
        return d;
    }
}'''}, [("Dijkstra.java", "                if (nd < d[e[0]]) {", "                if (d[e[0]] == Integer.MAX_VALUE) {")],
r'''
int[][] e = {{0,1,10},{0,2,3},{2,1,4},{1,3,2},{2,3,20}};
eq(new int[]{0, 7, 3, 9}, Dijkstra.dist(4, e, 0), "classic");
eq(new int[]{0, Integer.MAX_VALUE}, Dijkstra.dist(2, new int[][]{}, 0), "unreachable");
''', "Dijkstra.java")

add("fix-bfs-grid-visited", "hard", "shortestPath on a grid takes exponential time / returns wrong values because cells are not marked visited when enqueued.",
{"Grid.java": r'''
import java.util.*;
public class Grid {
    /** '#' is wall. Returns min steps from (0,0) to bottom-right with 4-neighbour moves, or -1. */
    public static int shortestPath(String[] g) {
        int R = g.length, C = g[0].length();
        if (g[0].charAt(0) == '#' || g[R-1].charAt(C-1) == '#') return -1;
        int[][] dist = new int[R][C];
        for (int[] row : dist) Arrays.fill(row, -1);
        Deque<int[]> q = new ArrayDeque<>();
        q.add(new int[]{0, 0}); dist[0][0] = 0;
        int[] dr = {1,-1,0,0}, dc = {0,0,1,-1};
        while (!q.isEmpty()) {
            int[] p = q.poll();
            for (int k = 0; k < 4; k++) {
                int r = p[0] + dr[k], c = p[1] + dc[k];
                if (r < 0 || c < 0 || r >= R || c >= C || g[r].charAt(c) == '#' || dist[r][c] != -1) continue;
                dist[r][c] = dist[p[0]][p[1]] + 1;
                q.add(new int[]{r, c});
            }
        }
        return dist[R-1][C-1];
    }
}'''}, [("Grid.java", "|| dist[r][c] != -1) continue;", "|| (r == 0 && c == 0)) continue;")],
r'''
eq(4, Grid.shortestPath(new String[]{"...", "...", "..."}), "open 3x3");
eq(-1, Grid.shortestPath(new String[]{".#.", "###", "..."}), "blocked");
eq(0, Grid.shortestPath(new String[]{"."}), "single");
String[] big = new String[12]; for (int i = 0; i < 12; i++) big[i] = ".".repeat(12);
eq(22, Grid.shortestPath(big), "12x12 open");
''', "Grid.java")

add("fix-interval-merge", "hard", "mergeIntervals does not sort its input and fails to merge fully contained intervals.",
{"Intervals.java": r'''
import java.util.*;
public class Intervals {
    public static int[][] merge(int[][] in) {
        int[][] a = in.clone();
        Arrays.sort(a, (x, y) -> Integer.compare(x[0], y[0]));
        List<int[]> out = new ArrayList<>();
        for (int[] iv : a) {
            if (out.isEmpty() || out.get(out.size() - 1)[1] < iv[0]) out.add(new int[]{iv[0], iv[1]});
            else out.get(out.size() - 1)[1] = Math.max(out.get(out.size() - 1)[1], iv[1]);
        }
        return out.toArray(new int[0][]);
    }
}'''}, [("Intervals.java", "Arrays.sort(a, (x, y) -> Integer.compare(x[0], y[0]));", ""), ("Intervals.java", "= Math.max(out.get(out.size() - 1)[1], iv[1]);", "= iv[1];")],
r'''
eq(new int[][]{{1,6},{8,10},{15,18}}, Intervals.merge(new int[][]{{8,10},{1,3},{2,6},{15,18}}), "unsorted");
eq(new int[][]{{1,10}}, Intervals.merge(new int[][]{{1,10},{2,3},{4,5}}), "contained");
eq(new int[][]{{1,5}}, Intervals.merge(new int[][]{{1,4},{4,5}}), "touching");
eq(new int[0][0], Intervals.merge(new int[0][0]), "empty");
''', "Intervals.java")

add("fix-two-sum-self", "medium", "twoSum can use the same element twice and returns indices in the wrong order.",
{"TwoSum.java": r'''
import java.util.*;
public class TwoSum {
    /** Indices {i, j}, i < j, with a[i] + a[j] == target; null if none. */
    public static int[] find(int[] a, int target) {
        Map<Integer, Integer> seen = new HashMap<>();
        for (int j = 0; j < a.length; j++) {
            Integer i = seen.get(target - a[j]);
            if (i != null) return new int[]{i, j};
            seen.put(a[j], j);
        }
        return null;
    }
}'''}, [("TwoSum.java", '''            Integer i = seen.get(target - a[j]);
            if (i != null) return new int[]{i, j};
            seen.put(a[j], j);''', '''            seen.put(a[j], j);
            Integer i = seen.get(target - a[j]);
            if (i != null) return new int[]{j, i};''')],
r'''
eq(new int[]{0, 1}, TwoSum.find(new int[]{2, 7, 11, 15}, 9), "basic");
eq(new int[]{1, 2}, TwoSum.find(new int[]{3, 2, 4}, 6), "no self reuse");
eq(new int[]{0, 1}, TwoSum.find(new int[]{3, 3}, 6), "dups");
ok(TwoSum.find(new int[]{1, 2}, 10) == null, "none");
''', "TwoSum.java")

add("fix-max-subarray", "medium", "maxSubarray returns 0 for all-negative arrays instead of the largest (least negative) element.",
{"Kadane.java": r'''
public class Kadane {
    public static int maxSubarray(int[] a) {
        if (a.length == 0) throw new IllegalArgumentException("empty");
        int best = a[0], cur = a[0];
        for (int i = 1; i < a.length; i++) {
            cur = Math.max(a[i], cur + a[i]);
            best = Math.max(best, cur);
        }
        return best;
    }
}'''}, [("Kadane.java", "int best = a[0], cur = a[0];", "int best = 0, cur = 0;")],
r'''
eq(6, Kadane.maxSubarray(new int[]{-2,1,-3,4,-1,2,1,-5,4}), "classic");
eq(-1, Kadane.maxSubarray(new int[]{-3,-1,-2}), "all negative");
eq(5, Kadane.maxSubarray(new int[]{5}), "single");
thrown(IllegalArgumentException.class, () -> Kadane.maxSubarray(new int[]{}), "empty");
''', "Kadane.java")

add("fix-roman-numerals", "medium", "toRoman(4) gives IIII and toRoman(1994) is wrong; subtractive forms are missing.",
{"Roman.java": r'''
public class Roman {
    private static final int[] V = {1000,900,500,400,100,90,50,40,10,9,5,4,1};
    private static final String[] S = {"M","CM","D","CD","C","XC","L","XL","X","IX","V","IV","I"};
    public static String toRoman(int n) {
        if (n < 1 || n > 3999) throw new IllegalArgumentException("range");
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < V.length; i++) while (n >= V[i]) { sb.append(S[i]); n -= V[i]; }
        return sb.toString();
    }
}'''}, [("Roman.java", '{1000,900,500,400,100,90,50,40,10,9,5,4,1}', '{1000,500,100,50,10,5,1}'), ("Roman.java", '{"M","CM","D","CD","C","XC","L","XL","X","IX","V","IV","I"}', '{"M","D","C","L","X","V","I"}')],
r'''
eq("IV", Roman.toRoman(4), "4"); eq("IX", Roman.toRoman(9), "9"); eq("MCMXCIV", Roman.toRoman(1994), "1994");
eq("MMMCMXCIX", Roman.toRoman(3999), "3999"); eq("I", Roman.toRoman(1), "1");
thrown(IllegalArgumentException.class, () -> Roman.toRoman(0), "0");
thrown(IllegalArgumentException.class, () -> Roman.toRoman(4000), "4000");
''', "Roman.java")

add("fix-thread-safe-counter", "hard", "SafeCounter loses increments under concurrent use.",
{"SafeCounter.java": r'''
public class SafeCounter {
    private int n;
    public synchronized void inc() { n++; }
    public synchronized int get() { return n; }
}'''}, [("SafeCounter.java", "public synchronized void inc()", "public void inc()")],
r'''
SafeCounter c = new SafeCounter();
Thread[] ts = new Thread[8];
for (int i = 0; i < ts.length; i++) { ts[i] = new Thread(() -> { for (int k = 0; k < 200000; k++) c.inc(); }); ts[i].start(); }
for (Thread t : ts) t.join();
eq(1600000, c.get(), "no lost updates");
''', "SafeCounter.java")

add("fix-record-validation", "easy", "Range(5, 1) should be rejected with IllegalArgumentException; contains() must be inclusive on both ends.",
{"Range.java": r'''
public record Range(int lo, int hi) {
    public Range {
        if (lo > hi) throw new IllegalArgumentException("lo > hi");
    }
    public boolean contains(int x) { return x >= lo && x <= hi; }
    public int length() { return hi - lo; }
}'''}, [("Range.java", '        if (lo > hi) throw new IllegalArgumentException("lo > hi");\n', ""), ("Range.java", "x >= lo && x <= hi", "x > lo && x < hi")],
r'''
thrown(IllegalArgumentException.class, () -> new Range(5, 1), "invalid");
Range r = new Range(2, 5);
ok(r.contains(2) && r.contains(5) && r.contains(3), "inclusive");
ok(!r.contains(1) && !r.contains(6), "outside");
eq(3, r.length(), "length");
eq(new Range(1, 2), new Range(1, 2), "equals");
''', "Range.java")

add("fix-enum-switch-fallthrough", "easy", "Light.next() maps GREEN to RED instead of YELLOW (missing return/ break semantic).",
{"Light.java": r'''
public enum Light {
    RED, GREEN, YELLOW;
    public Light next() {
        switch (this) {
            case RED: return GREEN;
            case GREEN: return YELLOW;
            default: return RED;
        }
    }
    public int seconds() {
        return switch (this) { case RED -> 30; case GREEN -> 25; case YELLOW -> 5; };
    }
}'''}, [("Light.java", "case GREEN: return YELLOW;\n            default: return RED;", "case GREEN: return RED;\n            default: return GREEN;"), ("Light.java", "case YELLOW -> 5;", "case YELLOW -> 25;")],
r'''
eq(Light.GREEN, Light.RED.next(), "red"); eq(Light.YELLOW, Light.GREEN.next(), "green"); eq(Light.RED, Light.YELLOW.next(), "yellow");
eq(5, Light.YELLOW.seconds(), "yellow secs"); eq(30, Light.RED.seconds(), "red secs");
''', "Light.java")

add("fix-try-finally-return", "hard", "readAll should always close the resource exactly once even when parse fails, and must propagate the original exception, not a secondary one from close().",
{"Res.java": r'''
public class Res implements AutoCloseable {
    public static int opened = 0, closed = 0;
    private final String data;
    public Res(String data) { this.data = data; opened++; }
    public int parse() {
        if (data.isEmpty()) throw new IllegalArgumentException("empty data");
        return Integer.parseInt(data);
    }
    @Override public void close() { closed++; }
    public static int readAll(String s) {
        try (Res r = new Res(s)) {
            return r.parse();
        }
    }
}'''}, [("Res.java", '''        try (Res r = new Res(s)) {
            return r.parse();
        }''', '''        Res r = new Res(s);
        int v = r.parse();
        r.close();
        return v;''')],
r'''
eq(42, Res.readAll("42"), "ok");
thrown(IllegalArgumentException.class, () -> Res.readAll(""), "empty");
thrown(NumberFormatException.class, () -> Res.readAll("x"), "nan");
eq(Res.opened, Res.closed, "all closed");
''', "Res.java")

add("fix-generic-max", "medium", "max() returns the minimum for lists and fails on empty list with NPE instead of NoSuchElementException.",
{"Gen.java": r'''
import java.util.*;
public class Gen {
    public static <T extends Comparable<? super T>> T max(Collection<? extends T> c) {
        Iterator<? extends T> it = c.iterator();
        if (!it.hasNext()) throw new NoSuchElementException("empty");
        T best = it.next();
        while (it.hasNext()) { T x = it.next(); if (x.compareTo(best) > 0) best = x; }
        return best;
    }
}'''}, [("Gen.java", "if (x.compareTo(best) > 0) best = x;", "if (x.compareTo(best) < 0) best = x;"), ("Gen.java", '        if (!it.hasNext()) throw new NoSuchElementException("empty");\n', "")],
r'''
eq(9, Gen.max(List.of(3, 9, 2)), "ints");
eq("pear", Gen.max(Set.of("apple", "pear", "fig")), "strings");
thrown(NoSuchElementException.class, () -> Gen.max(new ArrayList<Integer>()), "empty");
''', "Gen.java")

add("fix-wordcount-case-punct", "medium", "wordFrequency counts 'The' and 'the,' as different words and counts empty tokens.",
{"WordFreq.java": r'''
import java.util.*;
public class WordFreq {
    public static Map<String, Integer> count(String text) {
        Map<String, Integer> m = new TreeMap<>();
        for (String w : text.toLowerCase().split("[^a-z']+")) {
            if (w.isEmpty()) continue;
            m.merge(w, 1, Integer::sum);
        }
        return m;
    }
}'''}, [("WordFreq.java", 'text.toLowerCase().split("[^a-z\']+")', 'text.split(" ")'), ("WordFreq.java", "            if (w.isEmpty()) continue;\n", "")],
r'''
eq(Map.of("the", 3, "cat", 1, "sat", 1), WordFreq.count("The cat, the... sat; THE"), "mixed");
eq(Map.of("don't", 2), WordFreq.count("Don't don't"), "apostrophe");
eq(0, WordFreq.count("  ,, ").size(), "no words");
''', "WordFreq.java")

add("fix-multi-shape-area", "medium", "Total area is wrong: Circle.area uses diameter, and Rect.perimeter is missing a factor.",
{"Shape.java": r'''
public interface Shape { double area(); double perimeter(); }
''', "Circle.java": r'''
public class Circle implements Shape {
    private final double r;
    public Circle(double r) { this.r = r; }
    public double area() { return Math.PI * r * r; }
    public double perimeter() { return 2 * Math.PI * r; }
}''', "Rect.java": r'''
public class Rect implements Shape {
    private final double w, h;
    public Rect(double w, double h) { this.w = w; this.h = h; }
    public double area() { return w * h; }
    public double perimeter() { return 2 * (w + h); }
}''', "Shapes.java": r'''
import java.util.List;
public class Shapes {
    public static double totalArea(List<? extends Shape> s) { double t = 0; for (Shape x : s) t += x.area(); return t; }
}'''}, [("Circle.java", "Math.PI * r * r", "Math.PI * 2 * r * r"), ("Rect.java", "2 * (w + h)", "w + h")],
r'''
eq(Math.PI, new Circle(1).area(), "circle area");
eq(12.0, new Rect(3, 4).area(), "rect area");
eq(14.0, new Rect(3, 4).perimeter(), "rect perimeter");
eq(12.0 + Math.PI, Shapes.totalArea(java.util.List.of(new Rect(3, 4), new Circle(1))), "total");
''', "Circle.java")

add("fix-multi-event-bus", "hard", "EventBus delivers events to unsubscribed listeners and calls listeners in reverse subscription order. Also one throwing listener must not stop delivery to the others.",
{"Listener.java": r'''
public interface Listener { void on(String event); }
''', "EventBus.java": r'''
import java.util.*;
public class EventBus {
    private final Map<String, List<Listener>> subs = new HashMap<>();
    public void subscribe(String topic, Listener l) { subs.computeIfAbsent(topic, k -> new ArrayList<>()).add(l); }
    public void unsubscribe(String topic, Listener l) {
        List<Listener> ls = subs.get(topic);
        if (ls != null) ls.remove(l);
    }
    public int publish(String topic, String event) {
        int delivered = 0;
        for (Listener l : new ArrayList<>(subs.getOrDefault(topic, List.of()))) {
            try { l.on(event); delivered++; } catch (RuntimeException e) { /* isolate */ }
        }
        return delivered;
    }
}'''}, [("EventBus.java", "        if (ls != null) ls.remove(l);\n", ""), ("EventBus.java", "try { l.on(event); delivered++; } catch (RuntimeException e) { /* isolate */ }", "l.on(event); delivered++;")],
r'''
EventBus b = new EventBus();
List<String> log = new ArrayList<>();
Listener a = e -> log.add("a:" + e), bad = e -> { throw new RuntimeException("boom"); }, c = e -> log.add("c:" + e);
b.subscribe("t", a); b.subscribe("t", bad); b.subscribe("t", c);
eq(2, b.publish("t", "1"), "delivered count");
eq(List.of("a:1", "c:1"), log, "order and isolation");
b.unsubscribe("t", a);
b.publish("t", "2");
eq(List.of("a:1", "c:1", "c:2"), log, "after unsubscribe");
eq(0, b.publish("none", "x"), "no topic");
''', "EventBus.java")

add("fix-multi-inventory-total", "medium", "Order.total() ignores quantity and applies the discount to the wrong base; discounts are percentages.",
{"Item.java": r'''
public record Item(String name, long priceCents, int qty) {}
''', "Order.java": r'''
import java.util.*;
public class Order {
    private final List<Item> items = new ArrayList<>();
    public void add(Item i) { items.add(i); }
    /** total in cents after percentage discount (0-100), rounded down. */
    public long total(int discountPercent) {
        long sum = 0;
        for (Item i : items) sum += i.priceCents() * i.qty();
        return sum * (100 - discountPercent) / 100;
    }
}'''}, [("Order.java", "i.priceCents() * i.qty()", "i.priceCents()"), ("Order.java", "sum * (100 - discountPercent) / 100", "sum - discountPercent")],
r'''
Order o = new Order();
o.add(new Item("pen", 150, 4)); o.add(new Item("book", 1999, 1));
eq(2599L, o.total(0), "no discount");
eq(2339L, o.total(10), "10%");
eq(0L, o.total(100), "100%");
eq(0L, new Order().total(50), "empty");
''', "Order.java")

add("fix-multi-matrix-class", "medium", "Matrix.multiply uses wrong index order, and equals ignores content.",
{"Matrix.java": r'''
import java.util.Arrays;
public final class Matrix {
    private final int[][] a;
    public Matrix(int[][] a) { this.a = a; }
    public int rows() { return a.length; }
    public int cols() { return a[0].length; }
    public int get(int i, int j) { return a[i][j]; }
    public Matrix multiply(Matrix o) {
        if (cols() != o.rows()) throw new IllegalArgumentException("dim mismatch");
        int[][] r = new int[rows()][o.cols()];
        for (int i = 0; i < rows(); i++)
            for (int j = 0; j < o.cols(); j++)
                for (int k = 0; k < cols(); k++) r[i][j] += a[i][k] * o.a[k][j];
        return new Matrix(r);
    }
    @Override public boolean equals(Object x) { return x instanceof Matrix && Arrays.deepEquals(a, ((Matrix) x).a); }
    @Override public int hashCode() { return Arrays.deepHashCode(a); }
}'''}, [("Matrix.java", "r[i][j] += a[i][k] * o.a[k][j];", "r[i][j] += a[k][i] * o.a[j][k];"), ("Matrix.java", "x instanceof Matrix && Arrays.deepEquals(a, ((Matrix) x).a)", "x instanceof Matrix && rows() == ((Matrix) x).rows()")],
r'''
Matrix a = new Matrix(new int[][]{{1,2,3},{4,5,6}}), b = new Matrix(new int[][]{{7,8},{9,10},{11,12}});
eq(new Matrix(new int[][]{{58,64},{139,154}}), a.multiply(b), "2x3 * 3x2");
ok(!new Matrix(new int[][]{{1}}).equals(new Matrix(new int[][]{{2}})), "not equal");
thrown(IllegalArgumentException.class, () -> a.multiply(a), "mismatch");
''', "Matrix.java")
