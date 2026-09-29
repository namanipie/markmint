"""
Regression tests for Phase 6: Second-Year Taxonomy & Classifier Refinements.
Verifies MCQ distractor isolation, course-specific disambiguations, and corpus invariants.
"""
import pytest
from backend.services.taxonomy_classifier import (
    TaxonomyClassifierService,
    TaxonomyTopicRule,
    ClassificationProposal,
)
from backend.services.taxonomy_registry.registry import get_taxonomy_registry
from backend.core.database import SessionLocal
from backend.models.core import Question, Section, Exam, question_topic, QuestionFamilyMembership, QuestionFamily, Course


# ==============================================================================
# 1. MCQ DISTRACTOR ISOLATION TESTS
# ==============================================================================

def test_mcq_distractor_isolation_positive_in_stem():
    """Verify that a negative guard in options does NOT reject a positive match in stem."""
    rule_stack = TaxonomyTopicRule(
        topic_id=1, topic_name="Stack ADT", unit_id=1, unit_name="Unit 1",
        strong_phrases=["lifo order"],
        specific_keywords=["stack adt"],
        negative_guards=["queue"]
    )
    rule_queue = TaxonomyTopicRule(
        topic_id=2, topic_name="Queue ADT", unit_id=1, unit_name="Unit 1",
        strong_phrases=["fifo order"],
        specific_keywords=["queue adt"],
        negative_guards=["stack"]
    )

    classifier = TaxonomyClassifierService([rule_stack, rule_queue], isolate_mcq_distractors=True)

    # Case 1: Stack question with 'queue' as a distractor option
    q1 = "Which data structure operates in lifo order? (A) Queue (B) Array (C) Tree"
    p1 = classifier.classify(101, q1)
    assert p1.confidence == "HIGH"
    assert p1.topic_id == 1
    assert p1.topic_name == "Stack ADT"

    # Case 2: Queue question with 'stack' as a distractor option
    q2 = "Which data structure follows fifo order? (A) Stack (B) Graph (C) Hash"
    p2 = classifier.classify(102, q2)
    assert p2.confidence == "HIGH"
    assert p2.topic_id == 2
    assert p2.topic_name == "Queue ADT"


def test_mcq_distractor_isolation_negative_in_stem():
    """Verify that a negative guard matching in stem DOES properly reject the rule."""
    rule_stack = TaxonomyTopicRule(
        topic_id=1, topic_name="Stack ADT", unit_id=1, unit_name="Unit 1",
        strong_phrases=["lifo order"],
        specific_keywords=["stack adt"],
        negative_guards=["queue"]
    )
    classifier = TaxonomyClassifierService([rule_stack], isolate_mcq_distractors=True)

    # Guard 'queue' is in the stem of the question
    q = "Can a queue implement lifo order? (A) Yes (B) No"
    p = classifier.classify(103, q)
    assert p.confidence == "UNMAPPED"
    assert p.method == "GUARDRAIL_REJECTED"


def test_mcq_distractor_isolation_positive_only_in_options():
    """Verify that if positive signal is only in options, negative guard still rejects."""
    rule_queue = TaxonomyTopicRule(
        topic_id=2, topic_name="Queue ADT", unit_id=1, unit_name="Unit 1",
        strong_phrases=["queue adt"],
        specific_keywords=["queue"],
        negative_guards=["stack"]
    )
    classifier = TaxonomyClassifierService([rule_queue], isolate_mcq_distractors=True)

    # 'queue' is only in option (A), and 'stack' is in option (B)
    q = "Which is linear? (A) Queue (B) Stack (C) Tree"
    p = classifier.classify(104, q)
    # Since positive keyword is in options, distractor isolation does not grant a waiver
    assert p.confidence == "UNMAPPED"
    assert p.method == "GUARDRAIL_REJECTED"


# ==============================================================================
# 2. COURSE-SPECIFIC DISAMBIGUATION & REFINEMENT TESTS
# ==============================================================================

def test_course_24_dsa_refinements():
    """Test Data Structures and Algorithms rule refinements."""
    registry = get_taxonomy_registry()
    rules = registry.get_topic_rules(24)
    classifier = TaxonomyClassifierService(rules)

    # Stack operation sequence
    q_stack = "The following sequence of operations is performed on stack: PUSH (30), PUSH (40), POP (A) 40,30"
    p_stack = classifier.classify(201, q_stack)
    assert p_stack.topic_name == "Stack ADT and Operations"
    assert p_stack.confidence == "HIGH"

    # Queue operation
    q_queue = "In Queues, we can insert an element at rear end and delete an element at front end"
    p_queue = classifier.classify(202, q_queue)
    assert p_queue.topic_name == "Queue ADT and Operations"

    # AVL Tree balance factor
    q_avl = "Select the correct definition for balancing factor of a tree (A) Difference between left subtree and right subtree"
    p_avl = classifier.classify(203, q_avl)
    assert p_avl.topic_name == "AVL Trees and Rotations"


def test_course_25_os_refinements():
    """Test Operating Systems CPU scheduling disambiguation and paging/disk refinements."""
    registry = get_taxonomy_registry()
    rules = registry.get_topic_rules(25)
    classifier = TaxonomyClassifierService(rules)

    # Specific scheduling algorithm should map to CPU Scheduling Algorithms, not criteria
    q_sched = "FCFS Scheduling Algorithm is (A) Preemptive Scheduling (B) Non Preemptive Scheduling"
    p_sched = classifier.classify(301, q_sched)
    assert p_sched.topic_name == "CPU Scheduling Algorithms"

    # General criteria without algorithm name maps to Criteria and Dispatcher
    q_crit = "Explain CPU scheduling criteria including turnaround time and waiting time with dispatcher latency"
    p_crit = classifier.classify(302, q_crit)
    assert p_crit.topic_name == "CPU Scheduling Criteria and Dispatcher"

    # Disk scheduling request with cylinders
    q_disk = "Suppose, a disk has 400 cylinders numbered 0 to 399. The driver is currently serving request at cylinder 143"
    p_disk = classifier.classify(303, q_disk)
    assert p_disk.topic_name == "Disk Scheduling Algorithms and RAID"


def test_course_27_daa_refinements():
    """Test Design and Analysis of Algorithms complexity vs algorithm disambiguation."""
    registry = get_taxonomy_registry()
    rules = registry.get_topic_rules(27)
    classifier = TaxonomyClassifierService(rules)

    # Time complexity of binary search maps to Binary Search, NOT generic complexity analysis
    q_bs = "What is the time complexity of the binary search algorithm? (A) O(n) (B) O(log n)"
    p_bs = classifier.classify(401, q_bs)
    assert p_bs.topic_name == "Binary Search and Maximum Subarray Problem"

    # Time complexity of recurrence tree maps to Recursion Tree
    q_rec = "Deduce the time complexity of a given relation using Recursion Tree method"
    p_rec = classifier.classify(402, q_rec)
    assert p_rec.topic_name == "Recursion Tree Method and Mathematical Induction"

    # NP-complete Hamiltonian cycle
    q_np = "Show that the Hamiltonian-cycle decision problem is NP complete [8]"
    p_np = classifier.classify(403, q_np)
    assert p_np.topic_name == "NP-Completeness and NP-Hardness"


def test_course_28_dbms_refinements():
    """Test DBMS definition, ER model, and SQL refinements."""
    registry = get_taxonomy_registry()
    rules = registry.get_topic_rules(28)
    classifier = TaxonomyClassifierService(rules)

    # Database definition
    q_db = "Database is a (A) Collection of inter related data (B) Collection of binary data"
    p_db = classifier.classify(501, q_db)
    assert p_db.topic_name == "Database System Concepts and Architecture"

    # SQL function TO_DATE
    q_sql = "Converts the string in a given format in to oracle data format (A) TO_DATE"
    p_sql = classifier.classify(502, q_sql)
    assert p_sql.topic_name == "SQL Queries (DML), Joins and Nested Subqueries"


def test_course_22_prob_refinements():
    """Test Probability and Statistics distribution and hypothesis testing refinements."""
    registry = get_taxonomy_registry()
    rules = registry.get_topic_rules(22)
    classifier = TaxonomyClassifierService(rules)

    # Binomial distribution with parameters
    q_bin = "The mean of a binomial distribution is 20 and the standard deviation is 4 then the parameters are"
    p_bin = classifier.classify(601, q_bin)
    assert p_bin.topic_name == "Binomial Distribution"

    # Level of significance
    q_hyp = "The value set for alpha is known as (A) The level of rejection (B) The level of significance"
    p_hyp = classifier.classify(602, q_hyp)
    assert p_hyp.topic_name == "Null Hypothesis, Alternative Hypothesis, and Errors in Testing"


# ==============================================================================
# 3. CORPUS & INVARIANT INTEGRITY TESTS
# ==============================================================================

def test_second_year_mapping_coverage_threshold():
    """Verify that second-year corpus topic mapping coverage meets or exceeds 74%."""
    db = SessionLocal()
    try:
        second_year_cids = [22, 24, 25, 26, 27, 28, 29, 30, 31]
        total_sy_q = (
            db.query(Question)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id.in_(second_year_cids))
            .count()
        )
        mapped_sy_q = (
            db.query(Question)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .join(question_topic, Question.id == question_topic.c.question_id)
            .filter(Exam.course_id.in_(second_year_cids))
            .distinct()
            .count()
        )
        assert total_sy_q == 1911
        assert mapped_sy_q >= 1620
        coverage_pct = mapped_sy_q / total_sy_q * 100
        assert coverage_pct >= 85.0, f"Expected >= 85% coverage, got {coverage_pct:.2f}%"
    finally:
        db.close()


def test_question_family_membership_invariants():
    """Verify that QuestionFamily 1:1 membership and zero orphan invariant hold."""
    db = SessionLocal()
    try:
        total_questions = db.query(Question).count()
        total_memberships = db.query(QuestionFamilyMembership).count()
        unique_member_questions = db.query(QuestionFamilyMembership.question_id).distinct().count()

        assert total_questions == total_memberships
        assert total_questions == unique_member_questions

        # Orphan questions check
        orphaned = (
            db.query(Question)
            .outerjoin(QuestionFamilyMembership, Question.id == QuestionFamilyMembership.question_id)
            .filter(QuestionFamilyMembership.id == None)
            .count()
        )
        assert orphaned == 0

        # Course isolation check for second-year questions
        second_year_cids = [22, 24, 25, 26, 27, 28, 29, 30, 31]
        mismatched_qf = (
            db.query(QuestionFamilyMembership)
            .join(QuestionFamily, QuestionFamilyMembership.family_id == QuestionFamily.id)
            .join(Question, QuestionFamilyMembership.question_id == Question.id)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .join(Course, Exam.course_id == Course.id)
            .filter(Exam.course_id.in_(second_year_cids))
            .filter(QuestionFamily.subject != Course.name)
            .count()
        )
        assert mismatched_qf == 0
    finally:
        db.close()


# ==============================================================================
# 4. PHASE 6.2 CATEGORY C DISAMBIGUATION REGRESSION TESTS
# ==============================================================================

def test_phase6_2_course_28_dbms_category_c():
    """Verify Phase 6.2 Category C disambiguations for DBMS."""
    registry = get_taxonomy_registry()
    rules = registry.get_topic_rules(28)
    classifier = TaxonomyClassifierService(rules, isolate_mcq_distractors=True)

    # Topic 845 Extended ER vs Topic 844 Basic ER
    q_eer = "Draw an extended ER diagram where entity set person is classified as student and employee"
    p_eer = classifier.classify(701, q_eer)
    assert p_eer.topic_name == "Extended ER (EER) Features: Specialization and Generalization"

    # Topic 848 Relational Algebra vs Topic 852 SQL
    q_ra = "Relational algebra is a procedural language whereas relational algebra is extended version of SQL"
    p_ra = classifier.classify(702, q_ra)
    assert p_ra.topic_name == "Relational Algebra: Selection, Projection and Set Operations"

    # Topic 856 Closure of FD vs Topic 861 3NF/BCNF
    q_fd = "Refers to the set of all functional dependencies that can be inferred from the given set of dependencies"
    p_fd = classifier.classify(703, q_fd)
    assert p_fd.topic_name == "Functional Dependencies and Armstrong's Axioms"


def test_phase6_2_course_27_daa_category_c():
    """Verify Phase 6.2 Category C disambiguations for DAA."""
    registry = get_taxonomy_registry()
    rules = registry.get_topic_rules(27)
    classifier = TaxonomyClassifierService(rules, isolate_mcq_distractors=True)

    # Topic 820 Recursion tree
    q_rt = "Draw the recursion tree for T(n) = 4T(n/2) + cn and determine the overall asymptotic running time"
    p_rt = classifier.classify(801, q_rt)
    assert p_rt.topic_name == "Recursion Tree Method and Mathematical Induction"

    # Topic 825 Convex Hull vs Generic Divide and Conquer
    q_ch = "Give an O(n log n) divide and conquer algorithm that solves the convex hull problem"
    p_ch = classifier.classify(802, q_ch)
    assert p_ch.topic_name == "Geometric Algorithms: Closest Pair and Convex Hull"

    # Topic 830 Optimal BST vs Generic DP
    q_obst = "Illustrate the concept of optimal binary search tree using dynamic programming"
    p_obst = classifier.classify(803, q_obst)
    assert p_obst.topic_name == "Longest Common Subsequence and Optimal Binary Search Trees"

    # Topic 832 N-Queens / Subset Sum vs Generic Backtracking
    q_ss = "Apply backtracking method to solve the following instance of the subset sum problem"
    p_ss = classifier.classify(804, q_ss)
    assert p_ss.topic_name == "N-Queens and Sum of Subsets Problems"

    # Topic 836 Randomized Quicksort
    q_rq = "Which of the following is not true about randomized quicksort? (A) Pivot chosen uniformly at random"
    p_rq = classifier.classify(805, q_rq)
    assert p_rq.topic_name == "Randomized Algorithms: Quicksort and String Matching"


def test_phase6_2_course_25_os_category_c():
    """Verify Phase 6.2 Category C disambiguations for OS."""
    registry = get_taxonomy_registry()
    rules = registry.get_topic_rules(25)
    classifier = TaxonomyClassifierService(rules, isolate_mcq_distractors=True)

    # Wait system call
    q_wait = "Which system call is used by the parent process to wait for the child process to complete? (A) wait (B) fork"
    p_wait = classifier.classify(901, q_wait)
    assert p_wait.topic_name == "System Calls and OS Interface"

    # Ready queue
    q_rq = "Where are placed the list of processes that are prepared to be executed and waiting: ready queue"
    p_rq = classifier.classify(902, q_rq)
    assert p_rq.topic_name == "Process Concept and Process Control Block"

    # Deadlock necessary conditions vs sync
    q_dl = "Which of the following is not a necessary condition for a deadlock to occur? (A) Mutual exclusion (B) Hold and wait"
    p_dl = classifier.classify(903, q_dl)
    assert p_dl.topic_name == "Deadlock Characterization and Resource Allocation Graph"

    # Thrashing vs general paging
    q_thr = "What is thrashing in the context of virtual memory management?"
    p_thr = classifier.classify(904, q_thr)
    assert p_thr.topic_name == "Thrashing and Frame Allocation"


def test_phase6_2_course_26_coa_category_c():
    """Verify Phase 6.2 Category C disambiguations for COA."""
    registry = get_taxonomy_registry()
    rules = registry.get_topic_rules(26)
    classifier = TaxonomyClassifierService(rules, isolate_mcq_distractors=True)

    # Booth's algorithm with distractors
    q_booth = "Booth's algorithm is applied on _____________ (A) Decimal numbers (B) Binary numbers (C) Octal"
    p_booth = classifier.classify(1001, q_booth)
    assert p_booth.topic_name == "Multiplication Algorithms and Booth's Multiplier"

    # RTN abbreviation
    q_rtn = "RTN stands for (A) Register Transmission Notation (B) Register Transfer Notation"
    p_rtn = classifier.classify(1002, q_rtn)
    assert p_rtn.topic_name == "Instructions and Instruction Sequencing"

    # Microprogrammed control unit
    q_mcu = "Illustrate the micro-programmed control unit(MCU) with a neat diagram and how instructions are fetched"
    p_mcu = classifier.classify(1003, q_mcu)
    assert p_mcu.topic_name == "Micro-programmed Control Unit Design"

    # ARM ISA
    q_arm = "Which instruction set architecture is typically used in ARM processors [1]"
    p_arm = classifier.classify(1004, q_arm)
    assert p_arm.topic_name == "ARM Processor Architecture and CPU Cores"


def test_phase6_2_course_22_prob_category_c():
    """Verify Phase 6.2 Category C disambiguations for Probability."""
    registry = get_taxonomy_registry()
    rules = registry.get_topic_rules(22)
    classifier = TaxonomyClassifierService(rules, isolate_mcq_distractors=True)

    # Uniform distribution
    q_unif = "Let X be a uniformly distributed random variable over (0, 1) then the moment generating function"
    p_unif = classifier.classify(1101, q_unif)
    assert p_unif.topic_name == "Uniform and Exponential Distributions"

    # Type error examiner question
    q_err = "A failing student is passed by an examiner it is an example of (A) Type I error (B) Type II error"
    p_err = classifier.classify(1102, q_err)
    assert p_err.topic_name == "Null Hypothesis, Alternative Hypothesis, and Errors in Testing"

    # Control chart for variables vs attributes
    q_cc = "Control chart for variable is (A) s-chart (B) p-chart (C) np-chart (D) c-chart"
    p_cc = classifier.classify(1103, q_cc)
    assert p_cc.topic_name == "Control Charts for Variables: Range (R) and Standard Deviation (s) Charts"


def test_phase6_2_course_24_dsa_category_c():
    """Verify Phase 6.2 Category C disambiguations for DSA."""
    registry = get_taxonomy_registry()
    rules = registry.get_topic_rules(24)
    classifier = TaxonomyClassifierService(rules, isolate_mcq_distractors=True)

    # Josephus circular list
    q_jos = "Explain the Josephus Problem. Describe how a Circular Linked List can be used to solve it"
    p_jos = classifier.classify(1201, q_jos)
    assert p_jos.topic_name == "Sparse Matrix and Josephus Problem"

    # Stack peek with distractor
    q_peek = "The ___________ operation displays the topmost value but will not delete it from the stack. (A) Peek (B) Enqueue"
    p_peek = classifier.classify(1202, q_peek)
    assert p_peek.topic_name == "Stack ADT and Operations"

    # Deque
    q_deq = "A data structure in which elements can be inserted or deleted at / from both ends but not in the middle"
    p_deq = classifier.classify(1203, q_deq)
    assert p_deq.topic_name == "Circular Queue and Deque"

    # Hash collision separate chaining
    q_sc = "Compute the contents of a hash table of 5 entries using separate chaining method"
    p_sc = classifier.classify(1204, q_sc)
    assert p_sc.topic_name == "Collision Resolution Techniques"


def test_phase6_2_course_29_ai_category_c():
    """Verify Phase 6.2 Category C disambiguations for AI."""
    registry = get_taxonomy_registry()
    rules = registry.get_topic_rules(29)
    classifier = TaxonomyClassifierService(rules, isolate_mcq_distractors=True)

    # Water jug toy problem
    q_wj = "Given two water jugs with capacities X and Y litres. Initially, both the jugs are empty"
    p_wj = classifier.classify(1301, q_wj)
    assert p_wj.topic_name == "Toy Problems: 8-Puzzle, Water Jug and Missionaries-Cannibals"

    # CSP classification
    q_csp = "Which of the following mentioned problems are not constraint satisfaction problems? (A) N-queens (B) Cryptarithmetic"
    p_csp = classifier.classify(1302, q_csp)
    assert p_csp.topic_name == "Constraint Satisfaction Problems Formulation and Propagation"

    # Expert system architecture
    q_es = "18. What is the architecture of o fan expert system primarily concerned with? (A) Identifying planning problems (B) Designing machine learning models"
    p_es = classifier.classify(1303, q_es)
    assert p_es.topic_name == "Architecture of Expert Systems and Inference Engine"


def test_phase6_3_os_disambiguations():
    """Verify Phase 6.3 Operating Systems false ambiguity resolutions."""
    registry = get_taxonomy_registry()
    rules = registry.get_topic_rules(25)
    classifier = TaxonomyClassifierService(rules)

    # Q9056: Compaction definition
    q_comp = "9. What is compaction? (A) Technique for overcoming internal fragmentation (B) Technique for overcoming external fragmentation (C) Technique for overcoming fatal error (D) Technique for overcoming page fault [1]"
    p_comp = classifier.classify(9056, q_comp)
    assert p_comp.confidence == "HIGH"
    assert p_comp.topic_id == 779
    assert p_comp.topic_name == "Main Memory and Contiguous Memory Allocation"

    # Q9060: Virtual memory definition
    q_vm = "13. abstracts main memory into an extremely large, uniform array of storage, separating logical memory as viewed by the user from physical memory (A) Virtual memory (B) Main memory (C) Paging (D) Page table [1]"
    p_vm = classifier.classify(9060, q_vm)
    assert p_vm.confidence == "HIGH"
    assert p_vm.topic_id == 781
    assert p_vm.topic_name == "Virtual Memory and Demand Paging"

    # Q9093: Hardware implementation of mutual exclusion (Test and Set)
    q_hw = "9. The hardware implementation which provides mutual exclusion is _____ [1] A. Counting semaphore B. Binary semaphore C. Test and set lock D. Scheduling algorithm"
    p_hw = classifier.classify(9093, q_hw)
    assert p_hw.confidence == "HIGH"
    assert p_hw.topic_id == 770
    assert p_hw.topic_name == "Critical-Section Problem and Peterson's Solution"

    # Q9164: Thrashing definition
    q_thr = "15. The situation where the processor spends most of its time in swapping process pieces rather than execution instruction is called ________. (A) Paging (B) The principle of locality (C) Thrashing (D) Swapping [1]"
    p_thr = classifier.classify(9164, q_thr)
    assert p_thr.confidence == "HIGH"
    assert p_thr.topic_id == 783
    assert p_thr.topic_name == "Thrashing and Frame Allocation"


def test_phase6_3_coa_disambiguations():
    """Verify Phase 6.3 COA false ambiguity resolutions."""
    registry = get_taxonomy_registry()
    rules = registry.get_topic_rules(26)
    classifier = TaxonomyClassifierService(rules)

    # Q8349: ARM processor control unit design
    q_arm = "20. __________ method is used to design the control unit of ARM processor. (A) Hardwired (B) Microprogrammed (C) State machine (D) Combinational circuit [1]"
    p_arm = classifier.classify(8349, q_arm)
    assert p_arm.confidence == "HIGH"
    assert p_arm.topic_id == 812
    assert p_arm.topic_name == "ARM Processor Architecture and CPU Cores"


def test_phase6_3_daa_disambiguations():
    """Verify Phase 6.3 DAA false ambiguity resolutions."""
    registry = get_taxonomy_registry()
    rules = registry.get_topic_rules(27)
    classifier = TaxonomyClassifierService(rules)

    # Q8619: Substitution method definition
    q_sub = "3. Which method for solving recurrence relations involves making an educated guess for the solution and then using mathematical induction to prove its correctness? (A) Recursion Tree Method (B) Master Theorem (C) Substitution Method (D) Iteration Method [1]"
    p_sub = classifier.classify(8619, q_sub)
    assert p_sub.confidence == "HIGH"
    assert p_sub.topic_id == 819
    assert p_sub.topic_name == "Recurrence Relations and Substitution Method"

    # Q8537: State space tree search
    q_sst = "17. Which search is used in back tracking to traverse the state space tree? [1] A. Breadth first search B. Depth first search C. Nearest neighbour first D. Binary search tree"
    p_sst = classifier.classify(8537, q_sst)
    assert p_sst.confidence == "HIGH"
    assert p_sst.topic_id == 831
    assert p_sst.topic_name == "State Space Trees and Backtracking Principles"

    # Q8631: Branch and bound bounding function for TSP
    q_bb = "15. When applying Branch and Bound algorithms to the Traveling Salesman Problem (TSP), what is the primary role of the bounding function? (A) To determine the exact cost (B) Upper bound (C) Lower bound (D) Hamiltonian circuit"
    p_bb = classifier.classify(8631, q_bb)
    assert p_bb.confidence == "HIGH"
    assert p_bb.topic_id == 834
    assert p_bb.topic_name == "Branch and Bound Search Strategies"

    # Q8507: Randomized quicksort
    q_rq1 = "18. Which of the following is incorrect about randomized quicksort? (A) It has the same time complexity (B) It has the same space complexity as standard quicksort (C) It is an in-place sorting (D) It cannot have a time complexity algorithm of O(n^2) in any case [1]"
    p_rq1 = classifier.classify(8507, q_rq1)
    assert p_rq1.confidence == "HIGH"
    assert p_rq1.topic_id == 836
    assert p_rq1.topic_name == "Randomized Algorithms: Quicksort and String Matching"

    # Q8655: Randomized quicksort
    q_rq2 = "7. Which of the following is NOT true about randomized quicksort? (A) Its time complexity matches that of standard quicksort (B) It is an in-place sorting algorithm (C) Its space complexity is greater than standard quicksort (D) Its worst-case time complexity could still be $O(n^2)$ [1]"
    p_rq2 = classifier.classify(8655, q_rq2)
    assert p_rq2.confidence == "HIGH"
    assert p_rq2.topic_id == 836
    assert p_rq2.topic_name == "Randomized Algorithms: Quicksort and String Matching"

    # Q8666: NP-hard problem classification
    q_nph = "18. Which of the following problems is classified as NP-hard? (A) Sorting an array (B) Solving a system of linear equations (C) Traveling Salesman Problem (TSP) (D) Finding the minimum spanning tree [1]"
    p_nph = classifier.classify(8666, q_nph)
    assert p_nph.confidence == "HIGH"
    assert p_nph.topic_id == 838
    assert p_nph.topic_name == "NP-Completeness and NP-Hardness"

    # Q8474: Not an NP-hard problem
    q_not_nph = "17. Which of the following is known to be not an NP-Hard Problem? (A) Vertex Cover Problem (B) 0/1 Knapsack Problem (C) Maximal Independent Set Problem (D) Travelling Salesman Problem [1]"
    p_not_nph = classifier.classify(8474, q_not_nph)
    assert p_not_nph.confidence == "HIGH"
    assert p_not_nph.topic_id == 838
    assert p_not_nph.topic_name == "NP-Completeness and NP-Hardness"

    # Q8700: Polynomial time reduction
    q_ptr = "20. We wish to show that a problem B is NP-complete. Which of the following facts is sufficient to establish this. (A) There is a polynomial time reduction from B to SAT (B) There is a polynomial time reduction from SAT to B [1]"
    p_ptr = classifier.classify(8700, q_ptr)
    assert p_ptr.confidence == "HIGH"
    assert p_ptr.topic_id == 839
    assert p_ptr.topic_name == "Polynomial-Time Reductions"


def test_phase6_3_ambiguous_correct_retention():
    """Verify that true multi-topic comparison and composite questions correctly remain AMBIGUOUS."""
    registry = get_taxonomy_registry()

    # Course 22: Q10110 (discrete distribution + CDF composite)
    rules_22 = registry.get_topic_rules(22)
    clf_22 = TaxonomyClassifierService(rules_22)
    q_cdf_comp = "21. a.. A random variable X has the following distribution. Find: (i) the value of 'k' (ii) the cumulative distribution function (CDF)"
    p_cdf_comp = clf_22.classify(10110, q_cdf_comp)
    assert p_cdf_comp.confidence == "AMBIGUOUS"

    # Course 22: Q10120 (binomial fit + chi-square goodness of fit)
    q_fit_comp = "26. Fit a binomial distribution for the following data and also test the goodness of fit."
    p_fit_comp = clf_22.classify(10120, q_fit_comp)
    assert p_fit_comp.confidence == "AMBIGUOUS"

    # Course 26: Q8382 (BCD addition + 2's complement)
    rules_26 = registry.get_topic_rules(26)
    clf_26 = TaxonomyClassifierService(rules_26)
    q_subq = "21. Answer the following subquestions: a. Perform BCD Addition for 984+599. ii. Perform using 1's and 2's complement method."
    p_subq = clf_26.classify(8382, q_subq)
    assert p_subq.confidence == "AMBIGUOUS"

    # Course 27: Q8563 (cross-paradigm dynamic programming selection)
    rules_27 = registry.get_topic_rules(27)
    clf_27 = TaxonomyClassifierService(rules_27)
    q_cross_dp = "11. Which of the following can be solved using dynamic programming? (A) Merge sort (B) Binary search (C) Longest common subsequence (D) Quick sort [1]"
    p_cross_dp = clf_27.classify(8563, q_cross_dp)
    assert p_cross_dp.confidence == "AMBIGUOUS"

    # Course 27: Q8660 (cross-paradigm problems cannot be solved using backtracking)
    q_cross_bt = "12. Which of the following problems cannot be solved using backtracking? (A) N-Queens Problem (B) Knapsack Problem (C) Longest Common Subsequence (D) Hamiltonian Circuit [1]"
    p_cross_bt = clf_27.classify(8660, q_cross_bt)
    assert p_cross_bt.confidence == "AMBIGUOUS"

    # Course 27: Q8677 (composite NP-complete + Rabin-Karp)
    q_comp_np_rk = "25. Discuss about NP, NP- Hard and NP-Complete in detailed with examples. a. Discuss NP. b. Write Rabin Karp algorithm."
    p_comp_np_rk = clf_27.classify(8677, q_comp_np_rk)
    assert p_comp_np_rk.confidence == "AMBIGUOUS"

    # Course 27: Q8694 (cross-paradigm problems cannot be solved by backtracking)
    q_cross_bt2 = "14. Which of the problems cannot be solved by backtracking method? (A) n-queen problem (B) Subset sum problem (C) Hamiltonian circuit problem (D) Traveling salesman problem [1]"
    p_cross_bt2 = clf_27.classify(8694, q_cross_bt2)
    assert p_cross_bt2.confidence == "AMBIGUOUS"


