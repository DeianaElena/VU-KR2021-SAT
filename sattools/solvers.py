from copy import deepcopy
from typing import Iterable, List, Set, Tuple

import numpy as np

from .utils import CNFtype, flatten_list


class Solver:
    def __init__(self, cnf: CNFtype, verbose=False) -> None:
        self.cnf = cnf
        self.verbose = verbose

        self.literals = self.determine_literals(cnf)
        self.satisfied = False
        self.solution: List[int] = []

    def solve(self) -> None:
        """Kick off solving algorithm"""
        self.satisfied = self.start()

        if self.verbose:
            if self.satisfied:
                print("Satisfied")
            else:
                print("Cannot satisfied")

    def start(self) -> bool:
        # IMPORTANT: Implement this function in subclass
        raise NotImplementedError

    def set_solution(self, solution: Iterable[int]):
        """Set the solution"""
        self.solution = list(solution)

    @staticmethod
    def determine_literals(cnf: CNFtype) -> Set[int]:
        """Determine all unique literals"""
        return set(np.unique(flatten_list(cnf)))

    @classmethod
    def determine_pure_literals(cls, cnf: CNFtype) -> Set[int]:
        """Determine all pure literals"""
        unique_literals = cls.determine_literals(cnf)
        # Keep a set of literals when their negation isn't present
        # FYI: { } does a set comprehension
        pure_literals = {ul for ul in unique_literals if -ul not in unique_literals}

        return pure_literals

    @staticmethod
    def determine_unit_clauses(cnf: CNFtype) -> Set[int]:
        """Return the unit clauses in a cnf"""
        # Count the amount of literals in every clause
        clause_lenghts = np.fromiter(map(len, cnf), dtype=np.int_)
        # Keep clauses with count == 1
        literals = np.array(cnf, dtype=np.object_)[clause_lenghts == 1]
        # Literals in now an array with lists of single clauses, flatten this
        literals = set(flatten_list(literals))

        return literals

    @classmethod
    def remove_literal(cls, cnf: CNFtype, literal: int):
        # Copy the original to not overwrite any references
        cnf = deepcopy(cnf)
        # Remove clauses with literal
        cnf = cls.remove_clauses_with_literal(cnf, literal)
        # Shorten clauses with negated literal
        cnf = cls.shorten_clauses_with_literal(cnf, -literal)

        return cnf

    @staticmethod
    def remove_clauses_with_literal(cnf: CNFtype, literal: int):
        """Remove clauses from the cnf with the given literal"""
        return [clause for clause in cnf if literal not in clause]

    @staticmethod
    def shorten_clauses_with_literal(cnf: CNFtype, literal: int):
        """Shorten clauses from cnf with given literal"""
        return [[c for c in clause if c != literal] for clause in cnf]

    # NOTE: This doesn't implement the tautology rule
    @classmethod
    def simplify(cls, cnf: CNFtype) -> Tuple[CNFtype, Set[int]]:
        """Remove unit clauses and pure literals, return new cnf and removed literals"""
        # Determine unit clauses
        unit_clauses = cls.determine_unit_clauses(cnf)
        # Determine pure literals
        pure_literals = cls.determine_pure_literals(cnf)

        remove_literals = unit_clauses | pure_literals

        # Remove pure literals from cnf
        for literal in remove_literals:
            cnf = cls.remove_literal(cnf, literal)

        return cnf, remove_literals


class DPLL(Solver):
    def __init__(self, cnf: CNFtype, verbose=False) -> None:
        super().__init__(cnf, verbose)

        # Allows keeping count of backtracks and recursions
        self.backtrack_count = 0
        self.recursion_count = 0

    def start(self) -> bool:
        return self.backtrack(self.cnf, partial_assignment=set())

    def backtrack(self, cnf: CNFtype, partial_assignment: Set[int],) -> bool:
        # Print some information every so often
        if self.verbose and self.recursion_count % 10 == 0:
            info_strings = [
                f"{self.recursion_count = }",  # amount of function recursions
                f"{self.backtrack_count = }",  # amount of backtracks
                f"{len(partial_assignment) = }",  # amount of assignments
                f"{len(cnf) = }",  # length of unsolved cnf
            ]
            print(", ".join(info_strings))

        # Increase recursion count
        self.recursion_count += 1

        # Copy partial assignments so parent doesn't get overwritten when changed
        partial_assignment = deepcopy(partial_assignment)

        # Simplify cnf
        cnf, removed_literals = self.simplify(cnf)
        # Add removed literals from simplification
        partial_assignment = partial_assignment | removed_literals

        # Finish if cnf contains no clauses: satisfied
        if len(cnf) == 0:
            self.set_solution(partial_assignment)
            return True

        # Stop if cnf contains empty clauses: unsatisfied
        if np.isin(0, np.fromiter(map(len, cnf), dtype=np.int_)):
            # Keep the count of backtracks
            self.backtrack_count += 1
            return False

        # Pick a random literal without considering those already in partial assignment
        literal = int(np.random.choice(list(self.literals - partial_assignment)))

        # Try negation of the picked literal
        satisfied = self.backtrack(
            self.remove_literal(cnf, -literal), partial_assignment | set([-literal])
        )

        if not satisfied:
            # Try non-negated picked value
            satisfied = self.backtrack(
                self.remove_literal(cnf, literal), partial_assignment | set([literal])
            )

        return satisfied
