from FOL.fol_builder import build_fol_kb
from FOL.grounding import ground_kb
from FOL.cnf_converter import convert_kb_to_cnf


class KnowledgeBase:
    def __init__(self, puzzle=None):
        self.facts = set()
        self.rules = []
        self.clauses = []

        if puzzle is not None:
            self.build_from_puzzle(puzzle)

    # -------------------------
    # Main builder
    # -------------------------

    def build_from_puzzle(self, puzzle):
        facts, rules = build_fol_kb(puzzle)
        facts, rules = ground_kb(facts, rules)
        clauses = convert_kb_to_cnf(rules)

        self.add_facts(facts)
        self.add_rules(rules)
        self.add_clauses(clauses)

    # -------------------------
    # Add methods
    # -------------------------

    def add_fact(self, fact):
        self.facts.add(fact)

    def add_facts(self, facts):
        self.facts.update(facts)

    def add_rule(self, rule):
        self.rules.append(rule)

    def add_rules(self, rules):
        self.rules.extend(rules)

    def add_clause(self, clause):
        self.clauses.append(clause)

    def add_clauses(self, clauses):
        self.clauses.extend(clauses)

    # -------------------------
    # Access
    # -------------------------

    def get_facts(self):
        return list(self.facts)

    def get_rules(self):
        return self.rules

    def get_clauses(self):
        return self.clauses

    # -------------------------
    # Debug
    # -------------------------

    def print_summary(self):
        print("Knowledge Base Summary:")
        print(f"Facts: {len(self.facts)}")
        print(f"Rules: {len(self.rules)}")
        print(f"Clauses: {len(self.clauses)}")