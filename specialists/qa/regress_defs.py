"""Regression-test tasks: REGRESS[task_id] = [dict(mut=<1-based hand mutant that is the bug>, report=..., test=..., diff=?)].
The planted bug is hand mutant `mut`; `test` is the reference minimal regression test (fails on buggy, passes on fixed)."""

R = {}


def add(tid, mut, report, test, diff=None):
    d = dict(mut=mut, report=report, test=test)
    if diff:
        d["diff"] = diff
    R.setdefault(tid, []).append(d)


add("qa_slugify", 3, "slugify('hello world', max_len=6) returns 'hello-' (with a trailing dash). A slug must never end with '-', even after truncation.",
    "from slug import slugify\nassert slugify('hello world', max_len=6) == 'hello'\n", "easy")
add("qa_rle", 3, "rle_decode('12x') returns 'xx' (2 chars) instead of twelve x characters: only the last digit of a multi-digit count is used.",
    "from rle import rle_decode\nassert rle_decode('12x') == 'x' * 12\n", "easy")
add("qa_title_case", 2, "title_case('what to do in') gives 'What to Do in'. The last word must always be capitalised, even when it is a small word like 'in'.",
    "from titles import title_case\nassert title_case('what to do in') == 'What to Do In'\n", "easy")
add("qa_parse_duration", 3, "parse_duration('1h1h') returns 7200 but repeated units should raise ValueError ('units must appear at most once').",
    "from duration import parse_duration\ntry:\n    parse_duration('1h1h')\nexcept ValueError:\n    pass\nelse:\n    raise AssertionError('repeated unit accepted')\n")
add("qa_bisect", 2, "upper_bound([1, 2, 2, 2, 5], 2) returns 1, the same as lower_bound. It should return 4, the index after the last 2.",
    "from bsearch import upper_bound\nassert upper_bound([1, 2, 2, 2, 5], 2) == 4\n", "easy")
add("qa_dedupe", 1, "dedupe([1, 2, 1]) returns [2, 1]. The docs say the first occurrence is kept and the order preserved, so [1, 2] is expected.",
    "from dedupe import dedupe\nassert dedupe([1, 2, 1]) == [1, 2]\n", "easy")
add("qa_moving_avg", 1, "moving_average([1, 2, 3, 4, 5], 2) returns only 3 averages; the last window (4, 5) is missing. Expected [1.5, 2.5, 3.5, 4.5].",
    "from smooth import moving_average\nassert moving_average([1, 2, 3, 4, 5], 2) == [1.5, 2.5, 3.5, 4.5]\n", "easy")
add("qa_primes", 6, "is_prime(9) and is_prime(4) return True. Perfect squares of primes are being reported as prime.",
    "from nt import is_prime\nassert is_prime(9) is False\nassert is_prime(4) is False\n", "easy")
add("qa_luhn", 1, "luhn_valid('79927398713') returns False although it is the standard valid Luhn example.",
    "from luhn import luhn_valid\nassert luhn_valid('79927398713') is True\n", "easy")
add("qa_ipv4", 1, "is_ipv4('255.255.255.255') returns False. 255 is a valid octet value.",
    "from ipv4 import is_ipv4\nassert is_ipv4('255.255.255.255') is True\n", "easy")
add("qa_brackets", 3, "first_mismatch('a(b(c') returns 3 but should point at the OLDEST unclosed opener, index 1.",
    "from brackets import first_mismatch\nassert first_mismatch('a(b(c') == 1\n")
add("qa_hex_color", 1, "parse_hex_color('#f80') raises ValueError('bad length'). The 3-digit short form must expand to (255, 136, 0).",
    "from color import parse_hex_color\nassert parse_hex_color('#f80') == (255, 136, 0)\n", "easy")
add("qa_ring_buffer", 1, "After appending 1, 2, 3, 4 to RingBuffer(3), to_list() returns [4, 2, 3]. The oldest item should have been overwritten and the order kept: [2, 3, 4].",
    "from ring import RingBuffer\nr = RingBuffer(3)\nfor i in (1, 2, 3, 4):\n    r.append(i)\nassert r.to_list() == [2, 3, 4]\n")
add("qa_min_stack", 1, "MinStack: push(2), push(2), pop() and then min() raises IndexError although one 2 is still on the stack.",
    "from minstack import MinStack\ns = MinStack()\ns.push(2)\ns.push(2)\ns.pop()\nassert s.min() == 2\n")
add("qa_union_find", 3, "UnionFind.union(1, 0) returns True after 0 and 1 were already united. It must return False when nothing changes.",
    "from dsu import UnionFind\nu = UnionFind(3)\nassert u.union(0, 1) is True\nassert u.union(1, 0) is False\nassert u.count() == 2\n", "easy")
add("qa_intervals", 1, "merge_intervals([(1, 3), (3, 5)]) returns two intervals. Touching closed intervals should be merged into (1, 5).",
    "from intervals import merge_intervals\nassert merge_intervals([(1, 3), (3, 5)]) == [(1, 5)]\n", "easy")
add("qa_priority_queue", 2, "Items with equal priority come out in reverse insertion order. The docs promise first-in first-out for ties.",
    "from pq import PriorityQueue\nq = PriorityQueue()\nq.push('x', 1)\nq.push('y', 1)\nassert q.pop() == 'x'\n")
add("qa_split_bill", 1, "split_cents(100, 3) returns [34, 34, 33]; the parts sum to 101 cents. Expected [34, 33, 33].",
    "from splitting import split_cents\nassert split_cents(100, 3) == [34, 33, 33]\n", "easy")
add("qa_add_months", 2, "add_months(date(2024, 1, 31), 1) crashes with 'day is out of range for month'. It should clamp to Feb 29.",
    "from datetime import date\nfrom months import add_months\nassert add_months(date(2024, 1, 31), 1) == date(2024, 2, 29)\n")
add("qa_age", 1, "age_on(date(2000, 5, 15), date(2024, 5, 15)) returns 23 on the person's 24th birthday itself.",
    "from datetime import date\nfrom age import age_on\nassert age_on(date(2000, 5, 15), date(2024, 5, 15)) == 24\n", "easy")
add("qa_token_bucket", 1, "A TokenBucket(2, 1) that was idle for 100 seconds lets 3 requests through at once. The bucket may never hold more than `capacity` tokens.",
    "from bucket import TokenBucket\nb = TokenBucket(2, 1)\nb.allow(0)\nb.allow(0)\nassert [b.allow(100) for _ in range(3)] == [True, True, False]\n")
add("qa_sliding_window", 1, "SlidingWindowLimiter(1, 5): an event at t=0 is still counted at t=5, so allow(5) is refused. The window is (now - window, now], so the t=0 event has expired by t=5.",
    "from window import SlidingWindowLimiter\ns = SlidingWindowLimiter(1, 5)\nassert s.allow(0) is True\nassert s.allow(5) is True\n")
add("qa_ttl_cache", 1, "A TTLCache entry set at t=0 with ttl=10 is still returned at t=10. It should be expired exactly at set_time + ttl.",
    "from ttl import TTLCache\nc = TTLCache(10)\nc.set('a', 1, 0)\nassert c.get('a', 10) is None\n")
add("qa_retry_backoff", 1, "backoff_delays(3) returns three delays [1.0, 2.0, 4.0]; with 3 attempts there are only 2 waits between them.",
    "from retry import backoff_delays\nassert backoff_delays(3) == [1.0, 2.0]\n", "easy")
add("qa_order_fsm", 1, "A shipped order can still be cancelled (state becomes 'cancelled'). Only 'new' and 'paid' orders may be cancelled; shipped must raise InvalidTransition.",
    "from order import Order, InvalidTransition\no = Order()\no.pay()\no.ship()\ntry:\n    o.cancel()\nexcept InvalidTransition:\n    pass\nelse:\n    raise AssertionError('cancel after ship allowed')\nassert o.state == 'shipped'\n")
add("qa_mf_cart", 2, "bulk_discount(10, 100) gives 50 cents (the 5% tier) instead of 100 cents (the 10% tier): exactly 10 items must already get 10%.",
    "from pricing import bulk_discount\nassert bulk_discount(10, 100) == 100\n")
add("qa_mf_inventory", 2, "Inventory.remove('apple', 10) with exactly 10 apples in stock raises OutOfStock. Removing exactly what is on hand must work.",
    "from items import Item\nfrom stock import Inventory\ninv = Inventory()\ninv.add_item(Item('apple', 50), 10)\ninv.remove('apple', 10)\nassert inv.quantity('apple') == 0\n")
add("qa_deep_merge", 3, "deep_merge returns nested dicts that alias the first argument: changing result['n']['x'] later also changes the original input dict.",
    "from dicts import deep_merge\na = {'n': {'x': 1}}\nr = deep_merge(a, {})\nr['n']['x'] = 99\nassert a == {'n': {'x': 1}}\n")
add("qa_paginate", 4, "paginate(list(range(10)), 3, 4) raises ValueError('page out of range') for the last page. Page 3 of 3 must be allowed.",
    "from paging import paginate\nr = paginate(list(range(10)), 3, 4)\nassert r['items'] == [8, 9]\n", "easy")
add("qa_stats", 5, "mode([1, 1, 2, 2]) returns 2. When several values tie for most common, the smallest must be returned (1).",
    "from descstats import mode\nassert mode([1, 1, 2, 2]) == 1\n", "easy")
add("qa_base_convert", 3, "to_base(0, 2) returns an empty string instead of '0'.",
    "from baseconv import to_base\nassert to_base(0, 2) == '0'\n", "easy")
add("qa_mutable_default", 1, "add_tag('a') followed by add_tag('b') returns ['a', 'b'] the second time: state leaks between independent calls.",
    "from tags import add_tag\nadd_tag('a')\nassert add_tag('b') == ['b']\n")
add("qa_env_parser", 3, "parse_env('A=\"x y\"') returns the value with the quotes still in it ('\"x y\"'). Quotes around a value must be removed.",
    "from envfile import parse_env\nassert parse_env('A=\"x y\"') == {'A': 'x y'}\n", "easy")

REGRESS = R
