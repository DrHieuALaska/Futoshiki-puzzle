from FOL.fol_builder import build_fol_facts, build_fol_grounded_rules, build_fol_symbolic_rules
from FOL.grounding import ground_kb
from FOL.cnf_converter import convert_kb_to_cnf


class KnowledgeBase:
    def __init__(self, puzzle=None):
        self.facts = set()
        self.grounded_rules = []
        self.symbolic_rules = []
        self.clauses = []

        if puzzle is not None:
            self.build_from_puzzle(puzzle)

    # -------------------------
    # Main builder
    # -------------------------

    def build_from_puzzle(self, puzzle):
        facts = build_fol_facts(puzzle)
        grounded_rules = build_fol_grounded_rules(puzzle)
        symbolic_rules = build_fol_symbolic_rules(puzzle)
        clauses = convert_kb_to_cnf(grounded_rules)

        self.add_facts(facts)
        self.add_grounded_rules(grounded_rules)
        self.add_symbolic_rules(symbolic_rules)
        self.add_clauses(clauses)

    # -------------------------
    # Add methods
    # -------------------------

    def add_fact(self, fact):
        self.facts.add(fact)

    def add_facts(self, facts):
        self.facts.update(facts)

    # Only add grounded rules to KB — symbolic rules are for inference engine to use as templates
    def add_grounded_rule(self, grounded_rule):
        self.grounded_rules.append(grounded_rule)

    def add_grounded_rules(self, grounded_rules):
        self.grounded_rules.extend(grounded_rules)

    def add_symbolic_rule(self, symbolic_rule):
        self.symbolic_rules.append(symbolic_rule)

    def add_symbolic_rules(self, symbolic_rules):
        self.symbolic_rules.extend(symbolic_rules)

    def add_clause(self, clause):
        self.clauses.append(clause)

    def add_clauses(self, clauses):
        self.clauses.extend(clauses)

    # -------------------------
    # Access
    # -------------------------

    def get_facts(self):
        return list(self.facts)

    def get_grounded_rules(self):
        return self.grounded_rules

    def get_clauses(self):
        return self.clauses
    
    def get_symbolic_rules(self):
        return self.symbolic_rules

    # -------------------------
    # Debug
    # -------------------------

    def print_summary(self):
        print("Knowledge Base Summary:")
        print(f"Facts: {len(self.facts)}")
        print(f"Grounded Rules: {len(self.grounded_rules)}")
        print(f"Symbolic Rules: {len(self.symbolic_rules)}")
        print(f"Clauses: {len(self.clauses)}")