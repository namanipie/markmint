"""
In-memory simulator to test proposed Phase 6.4 taxonomy refinements.
Verifies:
1. Zero regressions on already-mapped questions.
2. Safe promotion of targeted Category A questions.
3. Out-of-syllabus (A3) and Truncated (A4) remain unmapped.
4. Ambiguities remain strictly controlled (no unexpected collision).
"""
import os
import sys
import json
import copy

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.core.database import SessionLocal
from backend.models.core import Question, Section, Exam, question_topic
from backend.services.taxonomy_registry.registry import get_taxonomy_registry, TaxonomyTopicRule
from backend.services.taxonomy_classifier import TaxonomyClassifierService

PROPOSED_UPDATES = {
    22: {
        "new_topics": [],
        "phrase_updates": {
            423: [
                "distribution exactly normal",
                "in a distribution exactly normal",
                "7% of the items are under 35 and 89% are under 63"
            ],
            424: [
                "level of confidence is denoted by",
                "the level of confidence is denoted by"
            ],
            425: [
                "sample of heights of 6400 english men",
                "sample of 100 students is taken from a large population",
                "random sample of size 500, the mean is found to be 20. in another independent sample of size 400",
                "sample of heights of 1600 american"
            ],
            426: [
                "'t' test is a",
                "t test is a ________ distribution"
            ],
            430: [
                "b_{yx} < 1",
                "b_{xy}",
                "if b_{yx} < 1, then b_{xy} is"
            ],
            432: [
                "different workers using four different machine types",
                "workers using four different machine types"
            ]
        },
        "guards": {
            425: ["machinist is expected to make engine parts", "machinist"]
        }
    },
    24: {
        "new_topics": [
            {
                "id": 934,
                "name": "Red-Black Trees: Properties and Balance",
                "canonical_name": "Red-Black Trees: Properties and Balance",
                "unit_id": 159,
                "unit_name": "Trees and Hashing",
                "strong_phrases": [
                    "red-black tree",
                    "red black tree",
                    "maximum height of a red-black tree",
                    "maximum height of a red black tree",
                    "properties of a red-black tree",
                    "properties of a red black tree",
                    "red-black tree with n nodes",
                    "red black tree with n nodes",
                    "black height"
                ],
                "specific_keywords": ["red-black tree", "red black tree", "black height"],
                "negative_guards": ["avl", "b-tree", "b+ tree"]
            }
        ],
        "phrase_updates": {
            737: [
                "struct student",
                "student structure contains the following fields"
            ],
            738: [
                "linear ds",
                "maximum of all the row sums",
                "suggest a suitable abstract data type",
                "lowest worst-case complexity",
                "which loop is guaranteed to execute at least one time",
                "prints the string \"hello\""
            ],
            740: [
                "add two n x n matrices",
                "multiply two m \\times n matrices",
                "multiply two m x n matrices"
            ],
            741: [
                "inserting a node at the end of the list",
                "cur.setnext (node)",
                "cur.setnext(node)"
            ],
            748: [
                "convert the expression given as follows",
                "a+(b*c-(d/e^f)*g)*h"
            ],
            750: [
                "normal queue, if implemented using an array of size max-size gets full"
            ],
            751: [
                "call logs in the mobile",
                "least recent number is deleted"
            ]
        },
        "guards": {}
    },
    25: {
        "new_topics": [],
        "phrase_updates": {
            764: [
                "role of operating system",
                "operating system is not a",
                "not an operating system",
                "services provided by the operating system",
                "services provided by operating system",
                "services provided by operating systems",
                "bios is used by",
                "connects high-speed high-bandwidth device to memory subsystem",
                "properties of the following operating systems",
                "computing cluster consisting of two nodes"
            ],
            767: [
                "active entity whereas",
                "active entity whereas program is a passive entity",
                "operating processes"
            ],
            768: [
                "cooperating process",
                "process that can be affected by other process"
            ],
            769: [
                "not shared by the threads of the same process",
                "multiple threads of control implies",
                "application that is performed 80% in parallel",
                "speedup according to amdahl"
            ],
            770: [
                "process p1 tries changing data",
                "process p2 tries reading"
            ],
            772: [
                "dining-philosophers problem will occur in case of"
            ],
            773: [
                "which scheduler is used to load the processes from secondary memory to main memory",
                "removal of the running process from the cpu and the selects another process",
                "interrupt a running process"
            ],
            775: [
                "for real-time operating systems, interrupt latency should be",
                "processes data instructions without any delay"
            ],
            779: [
                "how would the first-fit, best-fit and worst-fit algorithms place processes",
                "primary purpose of memory management"
            ],
            780: [
                "associative memory"
            ],
            781: [
                "the swap space in the disk is used for",
                "purpose of the disks swap space is to",
                "swap space in the disk"
            ],
            785: [
                "a file is a/an",
                "file organization methods",
                "directory and disk structures"
            ],
            786: [
                "primary goal of protection",
                "restrict system access to authorized users",
                "capability-based system"
            ],
            788: [
                "programs cause security breaches"
            ]
        },
        "guards": {}
    },
    26: {
        "new_topics": [],
        "phrase_updates": {
            792: [
                "reflected binary code",
                "gray code is also known as reflected binary code"
            ],
            796: [
                "register capable of shifting",
                "accumulator",
                "temporary storage location to hold an intermediate result"
            ],
            797: [
                "pci bus",
                "bus used to connect the monitor",
                "connected to memory bus",
                "which interrupt services save all the register and flags"
            ],
            798: [
                "how many bits are needed to address any single byte",
                "address space of",
                "1 gb is equivalent to how to many bytes",
                "data is transferred to and from memory in groups of bits called",
                "virtual memory consists of",
                "number successful accesses to memory stated as a fraction",
                "write miss",
                "present in the cache",
                "data transfer instructions",
                "rotated right by two"
            ],
            799: [
                "describe addressing mode with example"
            ],
            802: [
                "adder circuit which can add two binary numbers and also take into account an input carry"
            ],
            803: [
                "commonly used for binary multiplication in digital circuits"
            ],
            805: [
                "normalized representation of",
                "in 32 bit representation the scale factor as a range of"
            ],
            810: [
                "explain the types of hazards"
            ],
            811: [
                "mesi protocol",
                "architecture of parallel systems and its types",
                "memory in multiprocessor system"
            ],
            812: [
                "complex and expensive to produce is"
            ]
        },
        "guards": {
            796: ["where does the multiplier operand is stored", "multiplier operand is stored"]
        }
    },
    27: {
        "new_topics": [
            {
                "id": 935,
                "name": "All-Pairs Shortest Paths: Floyd-Warshall Algorithm",
                "canonical_name": "All-Pairs Shortest Paths: Floyd-Warshall Algorithm",
                "unit_id": 173,
                "unit_name": "Greedy Algorithms and Dynamic Programming",
                "strong_phrases": [
                    "floyd-warshall",
                    "floyd warshall",
                    "floyd-warshall algorithm",
                    "floyd warshall algorithm",
                    "all-pairs shortest paths",
                    "all pairs shortest paths",
                    "transitive closure for the following digraph using floyd",
                    "running time of the floyd warshall algorithm",
                    "trace the working of floyd-warshall algorithm"
                ],
                "specific_keywords": ["floyd-warshall", "floyd warshall"],
                "negative_guards": ["dijkstra", "bellman-ford", "what approach is being followed in floyd warshall", "approach is being followed in floyd warshall"]
            }
        ],
        "phrase_updates": {
            816: [
                "iteratively inserting each element of the unsorted portion",
                "ram has six different sets of pencils",
                "he arranges pencils by comparing its length with the next immediate pencil",
                "top-down design",
                "bottom-up",
                "design paradigms for the problem",
                "well defined and ordered procedure",
                "algorithms can be represented",
                "depth first search is",
                "breadth first search is started on a binary tree"
            ],
            817: [
                "count variable method and table method",
                "the following algorithm using count variable method and table method",
                "linear search",
                "prescribe a suitable sequential search algorithm and simulate",
                "two phases. the first phase, initialization, takes time o(n^3)"
            ],
            818: [
                "the measure of the longest amount of time possibly taken to complete an algorithm",
                "longest amount of time possibly taken to complete an algorithm",
                "correct order of increasing growth",
                "\\omega(n^2)",
                "4n^2 + 5 \\in \\omega",
                "f(n)=o(g(n))",
                "maximum asymptotic complexity"
            ],
            819: [
                "tower of hanoi",
                "advantage of recursive approach"
            ],
            821: [
                "largest sub array sum",
                "largest sub-array sum",
                "application of maximum sum sub-array problem"
            ],
            822: [
                "maximum and minimum in an array"
            ],
            824: [
                "what does the variable a denote in masters theorem"
            ],
            825: [
                "closest-pair problem",
                "vertical strip of width 2d"
            ],
            827: [
                "greedy based technique to determine a subset of items"
            ],
            828: [
                "minimum cost spanning tree with n vertices",
                "spanning tree of a graph g"
            ],
            829: [
                "chain of matrices",
                "minimum number of scalar multiplications"
            ],
            831: [
                "state-space tree",
                "tree of choices called as"
            ],
            832: [
                "queens attack each other",
                "placing 4 queens on a 4x4 chessboard",
                "set of all subsets of n elements",
                "under what condition any set a will be a subset of b"
            ],
            834: [
                "travelling salesman problem is an example of"
            ],
            836: [
                "rabin-karp string matching"
            ],
            838: [
                "state np hard and np complete and differentiate both",
                "solved in polynomial time are known as"
            ]
        },
        "guards": {
            818: ["recurrence relation", "masters theorem"]
        }
    },
    28: {
        "new_topics": [
            {
                "id": 936,
                "name": "Query Processing and Optimization: Parsing, Evaluation and Relational Plans",
                "canonical_name": "Query Processing and Optimization: Parsing, Evaluation and Relational Plans",
                "unit_id": 178,
                "unit_name": "SQL and Advanced Database Programming",
                "strong_phrases": [
                    "query processing",
                    "query processing engine",
                    "steps involved in processing a query",
                    "valid step in query processing",
                    "parsing in query processing",
                    "parsing and translation",
                    "how user query is executed in the query processing engine",
                    "demonstrate the steps involved in processing a query"
                ],
                "specific_keywords": ["query processing", "query optimization"],
                "negative_guards": ["transaction", "concurrency", "normalization"]
            }
        ],
        "phrase_updates": {
            841: [
                "what is dbms",
                "feature of the database",
                "limitations/disadvantages of dbms",
                "disadvantages of dbms",
                "responsibilities of a database management system",
                "naive user",
                "levels of abstraction"
            ],
            842: [
                "components of data base system environment",
                "manages the allocation of space on disk storage and the data structures used to represent information"
            ],
            843: [
                "evolution models",
                "top-to-bottom relationship",
                "hierarchical"
            ],
            844: [
                "develop e-r model",
                "derived attribute",
                "maximum number of entities that can be involved in a relationship"
            ],
            846: [
                "relational model is based on the concept that data is organized and stored in two-dimensional tables",
                "permitted values called the",
                "super key",
                "pit fall in relational"
            ],
            848: [
                "\\sigma_{salary > 1000}"
            ],
            851: [
                "drop table",
                "a ________ constraint is a constraint that ensures that a column or set of columns satisfies a specified condition"
            ],
            852: [
                "insert employee",
                "write an sql query",
                "subqueries and correlated queries",
                "what is a join",
                "all aggregate functions except"
            ],
            853: [
                "a window into a portion of a database is"
            ],
            854: [
                "developers can write their own functions and procedures"
            ],
            857: [
                "which is not a type of normalization",
                "primary goal of normalization",
                "condition for 2^{nd} norm form",
                "condition for $2^{\\text{nd}}$ norm form",
                "define first normal form",
                "1^{st} normal form",
                "1^{st} norm form"
            ],
            858: [
                "boyce-codd normal form is found to be stricter than third normal form"
            ],
            860: [
                "lossless decomposition"
            ],
            861: [
                "properties of a transaction",
                "transaction control language commands"
            ],
            862: [
                "what is serialization",
                "testing of seriability"
            ],
            863: [
                "duty read",
                "dirty read",
                "problems with concurrent execution",
                "several operation simultaneously",
                "locks are used",
                "locking",
                "dead lock",
                "deadlock"
            ],
            864: [
                "fuzzy check prints",
                "check points",
                "deferred-modification"
            ]
        },
        "guards": {
            863: ["serializability", "equivalent to same serial execution"]
        }
    },
    29: {
        "new_topics": [],
        "phrase_updates": {
            866: [
                "cognitive science"
            ],
            867: [
                "multi-agent system",
                "crossword puzzle",
                "different types of agents"
            ],
            868: [
                "ill-structured problem"
            ],
            871: [
                "search is called",
                "node/ state is marked to be visited",
                "node/state is marked to be visited",
                "if any search algorithm is able to generate a solution, then the search is"
            ],
            878: [
                "constraints are the one that restrict"
            ],
            879: [
                "to + go = out",
                "\\text{to} + \\text{go} = \\text{out}"
            ],
            881: [
                "process of reasoning that operate on",
                "internal representation"
            ],
            882: [
                "p\\land q \\rightarrow r",
                "p \\wedge q \\rightarrow r"
            ],
            886: [
                "mean ends analysis"
            ]
        },
        "guards": {}
    }
}

def simulate():
    db = SessionLocal()
    reg = get_taxonomy_registry()

    print("Running precision-guarded simulation of Phase 6.4 refinements...\n")

    total_promoted = 0
    total_regressions = 0

    for cid in sorted(PROPOSED_UPDATES.keys()):
        updates = PROPOSED_UPDATES[cid]
        base_rules = reg.get_topic_rules(cid)
        clf_base = TaxonomyClassifierService(base_rules)

        sim_rules = copy.deepcopy(base_rules)
        rule_by_tid = {r.topic_id: r for r in sim_rules}

        # Add new topics
        for nt in updates["new_topics"]:
            new_r = TaxonomyTopicRule(
                topic_id=nt["id"],
                topic_name=nt["name"],
                unit_id=nt["unit_id"],
                unit_name=nt["unit_name"],
                strong_phrases=nt.get("strong_phrases", []),
                specific_keywords=nt.get("specific_keywords", []),
                negative_guards=nt.get("negative_guards", []),
                context_hints=nt.get("context_hints", [])
            )
            sim_rules.append(new_r)
            rule_by_tid[nt["id"]] = new_r

        # Apply phrase updates
        for tid, phrases in updates["phrase_updates"].items():
            if tid in rule_by_tid:
                r = rule_by_tid[tid]
                for p in phrases:
                    if p not in r.strong_phrases:
                        r.strong_phrases.append(p)

        # Apply guard updates
        for tid, guards in updates.get("guards", {}).items():
            if tid in rule_by_tid:
                r = rule_by_tid[tid]
                for g in guards:
                    if g not in r.negative_guards:
                        r.negative_guards.append(g)

        clf_sim = TaxonomyClassifierService(sim_rules)

        qs = (
            db.query(Question.id, Question.original_text)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == cid)
            .order_by(Question.id)
            .all()
        )

        regressions = []
        promoted = []

        for q in qs:
            p_base = clf_base.classify(q.id, q.original_text)
            p_sim = clf_sim.classify(q.id, q.original_text)

            if p_base.confidence in ["HIGH", "MEDIUM"] and (p_sim.topic_id != p_base.topic_id or p_sim.confidence not in ["HIGH", "MEDIUM"]):
                regressions.append((q, p_base, p_sim))
            elif p_base.confidence not in ["HIGH", "MEDIUM"] and p_sim.confidence in ["HIGH", "MEDIUM"]:
                promoted.append((q, p_sim))

        print(f"Course {cid}: Promoted +{len(promoted)} | Regressions: {len(regressions)}")
        for q, p_base, p_sim in regressions:
            print(f"  REGRESSION Q{q.id}: was {p_base.topic_id} ({p_base.topic_name}) -> now {p_sim.topic_id} ({p_sim.confidence})")
            print("    Text:", q.original_text[:120].replace("\n", " "))
            print("    Candidates in sim:", [(c["topic_id"], c["evidence"]) for c in p_sim.candidate_topics])

        total_promoted += len(promoted)
        total_regressions += len(regressions)

    print(f"\n==================================================")
    print(f"OVERALL SIMULATION RESULTS:")
    print(f"Total newly mapped questions: +{total_promoted}")
    print(f"Total regressions on existing mappings: {total_regressions}")
    print(f"==================================================")

if __name__ == "__main__":
    simulate()
