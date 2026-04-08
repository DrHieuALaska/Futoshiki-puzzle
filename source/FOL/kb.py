from FOL.fol_builder import build_fol_facts, build_fol_rules
from FOL.grounding import ground_to_clauses


class KnowledgeBase:
    def __init__(self, puzzle=None):
        self.facts = set()
        self.fol_rules = []
        self.clauses = []

        if puzzle is not None:
            self.build_from_puzzle(puzzle)

    # -------------------------
    # Main builder
    # -------------------------

    def build_from_puzzle(self, puzzle):
        facts = build_fol_facts(puzzle)
        fol_rules = build_fol_rules(puzzle)
        
        ## Grounding
        ground_clauses  = ground_to_clauses(facts, fol_rules, puzzle.N)

        self.add_facts(facts)
        self.add_fol_rules(fol_rules)
        self.add_clauses(ground_clauses)

    # -------------------------
    # Add methods
    # -------------------------

    def add_fact(self, fact):
        self.facts.add(fact)

    def add_facts(self, facts):
        self.facts.update(facts)

    def add_fol_rule(self, fol_rule):
        self.fol_rules.append(fol_rule)

    def add_fol_rules(self, fol_rules):
        self.fol_rules.extend(fol_rules)

    def add_clause(self, clause):
        self.clauses.append(clause)

    def add_clauses(self, clauses):
        self.clauses.extend(clauses)

    # -------------------------
    # Access
    # -------------------------

    def get_facts(self):
        return list(self.facts)

    def get_clauses(self):
        return self.clauses
    
    def get_fol_rules(self):
        return self.fol_rules

    # -------------------------
    # Debug
    # -------------------------

    def print_summary(self):
        print("Knowledge Base Summary:")
        print(f"Facts: {len(self.facts)}")
        print(f"FOL Rules: {len(self.fol_rules)}")
        print(f"Clauses: {len(self.clauses)}")