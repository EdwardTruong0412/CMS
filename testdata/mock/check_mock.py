import json, re, sys, unicodedata, datetime
d = sys.argv[1]
deps = [x["name"] for x in json.load(open(f"{d}/departments.json"))]
poss = [x["name"] for x in json.load(open(f"{d}/positions.json"))]
emps = json.load(open(f"{d}/employees.json"))
def fold(s):
    s = s.replace("đ", "d").replace("Đ", "D")
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").lower()
errs = []
def ok(c, m):
    if not c: errs.append(m)
ok(len(emps) == 50, "50 employees")
ok(len(deps) <= 20 and len(poss) <= 20, "capacity 20/20")
for lst, n in ((deps, "dept"), (poss, "pos")):
    ok(len({x.strip().lower() for x in lst}) == len(lst), f"{n} unique")
    for x in lst: ok(1 <= len(x.strip()) <= 100, f"{n} length {x}")
keys = {"employee_code","full_name","work_email","phone","department","position","start_date","status"}
for e in emps:
    ok(set(e) == keys, f"8 fields {e['employee_code']}")
    ok(re.fullmatch(r"[A-Za-z0-9-]{1,20}", e["employee_code"]) is not None, f"code {e}")
    ok(1 <= len(e["full_name"]) <= 100 and e["full_name"] == e["full_name"].strip(), f"name {e}")
    em = e["work_email"]
    ok(len(em) <= 254 and " " not in em and em.count("@") == 1 and em.split("@")[0] and "." in em.split("@")[1], f"email {em}")
    ok(em.endswith("@example.test"), f"reserved domain {em}")
    ok(e["phone"] is None or re.fullmatch(r"\+?\d{8,15}", e["phone"]) is not None, f"phone {e['phone']}")
    datetime.date.fromisoformat(e["start_date"])
    ok(e["department"] in deps and e["position"] in poss, f"org {e}")
    ok(e["status"] in ("active", "inactive"), "status")
for k in ("employee_code", "work_email"):
    ok(len({e[k].lower() for e in emps}) == 50, f"{k} unique ci")
# search test points (EMP-AC17, EMP-AC20): match on name, code, email
def hits(q):
    q = fold(q)
    return [e["full_name"] for e in emps if q in fold(e["full_name"]) or q in e["employee_code"].lower() or q in e["work_email"].lower()]
ok(hits("001") == ["Nguyễn Thị Hồng Ánh"], f"001 -> {hits('001')}")
for q, name in (("do", "Đỗ Đức Dũng"), ("duc", "Đỗ Đức Dũng"), ("vuong", "Trần Quốc Vượng")):
    ok(hits(q) == [name], f"{q} -> {hits(q)}")
ng = [e["full_name"] for e in emps if "Nguyễn" in e["full_name"]]
ok(hits("nguyen") == ng and hits("NGUYỄN") == ng, "nguyen fold")
for n in ("Nguyễn Thị Hồng Ánh", "Đỗ Đức Dũng", "Trần Quốc Vượng"):
    ok(n in [e["full_name"] for e in emps], f"EMP-AC19 value {n}")
ok(not any(e["work_email"].lower() == "a.nguyen@example.test" for e in emps), "a.nguyen kept free for tests")
tl = [e for e in emps if e["position"] == "Trợ lý"]
ok(len(tl) == 3 and sum(e["status"] == "inactive" for e in tl) == 1, "ORG-AC07 test point: Trợ lý 3 employees, 1 inactive")
ok("Phòng Kế toán" in deps and "Phòng Nhân sự" in deps and "Kế toán trưởng" in poss, "ORG test values present")
print("inactive:", sum(e["status"] == "inactive" for e in emps), "no phone:", sum(e["phone"] is None for e in emps), "Nguyễn:", len(ng))
print("FAIL\n" + "\n".join(errs) if errs else "PASS")
sys.exit(1 if errs else 0)
