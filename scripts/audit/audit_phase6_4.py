"""
Phase 6.4 Comprehensive True Taxonomy Gap Validation Script.
Analyzes every single one of the 222 Category A questions against the official syllabus
and current taxonomy definitions.
Classifies each into A1, A2, A3, A4, or A5.
"""
import os
import sys
import json
import re
from collections import defaultdict, Counter

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.core.database import SessionLocal
from backend.models.core import Question, Section, Exam, Topic, Unit, Course
from backend.services.taxonomy_registry.registry import get_taxonomy_registry
from backend.services.taxonomy_classifier import TaxonomyClassifierService

def run_phase6_4_audit():
    db = SessionLocal()
    registry = get_taxonomy_registry()

    report_path = os.path.join(BASE_DIR, "data", "s3_s4", "phase6_3_audit_report.json")
    with open(report_path, encoding="utf-8") as f:
        data = json.load(f)

    cat_a_raw = [q for q in data["unmapped_questions"] if q["diagnostic_category"] == "A"]
    print(f"Total Category A questions loaded: {len(cat_a_raw)}")

    # Load full DB objects for metadata
    q_ids = [q["question_id"] for q in cat_a_raw]
    db_questions = (
        db.query(Question)
        .join(Section, Question.section_id == Section.id)
        .join(Exam, Section.exam_id == Exam.id)
        .filter(Question.id.in_(q_ids))
        .all()
    )
    q_map = {q.id: q for q in db_questions}

    detailed_results = []
    category_counts = Counter()
    by_course_counts = defaultdict(Counter)

    for item in cat_a_raw:
        qid = item["question_id"]
        cid = item["course_id"]
        text = item["original_text"]
        norm_text = text.lower()
        q_obj = q_map.get(qid)
        exam = q_obj.section.exam if q_obj else None
        stem, opts = TaxonomyClassifierService.split_stem_and_options(text)

        cat = "A2"
        target_tid = None
        target_name = None
        unit_id = None
        unit_name = None
        justification = ""

        # Check for A4: Insufficiently informative, truncated, or exam metadata
        if len(text.strip()) < 15 or "or alternative for q" in norm_text:
            cat = "A4"
            justification = "Exam header or incomplete question text missing actionable problem statement"
        elif "choose the correct statement from the following" in norm_text and not opts and len(text.strip()) < 55:
            cat = "A4"
            justification = "Truncated MCQ question missing choices and context"

        # Check Course 22 (Probability & Statistics)
        elif cid == 22:
            if any(k in norm_text for k in ["estimator", "estimation is of two types", "cramer-rao", "unbiased estimator", "bias of an estimator"]):
                cat = "A3"
                justification = "Estimation Theory (Point/Interval Estimation, Cramer-Rao) is part of Advanced Statistics/Inference, out-of-syllabus for 21MAB202T (Testing of Hypothesis focus)"
            elif "simple sample of heights of 6400 english men" in norm_text or "sample of 100 students" in norm_text or "sample of size 500, the mean is found to be 20" in norm_text:
                cat = "A2"
                target_tid = 425
                target_name = "Large Sample Tests: Z-Test for Means and Proportions"
                unit_id = 45
                unit_name = "Testing of Hypothesis"
                justification = "Large sample test for single mean or difference of means (Z-test) with n >= 30"
            elif "'t' test" in norm_text:
                cat = "A2"
                target_tid = 426
                target_name = "Small Sample Tests: Student's t-Test"
                unit_id = 45
                unit_name = "Testing of Hypothesis"
                justification = "Direct test of Student's t-test distribution properties"
            elif "distribution exactly normal" in norm_text:
                cat = "A2"
                target_tid = 423
                target_name = "Normal Distribution and Standard Normal Curves"
                unit_id = 44
                unit_name = "Standard Probability Distributions"
                justification = "Normal distribution probability calculation for mean and standard deviation"
            elif "b_{yx}" in text or "b_{xy}" in text:
                cat = "A2"
                target_tid = 430
                target_name = "Lines of Regression and Regression Equations"
                unit_id = 46
                unit_name = "Correlation, Regression, and Design of Experiments"
                justification = "Mathematical relationship between regression coefficients byx and bxy"
            elif "five men differ with respect to mean productivity" in norm_text and "four different machine types" in norm_text:
                cat = "A2"
                target_tid = 432
                target_name = "Two-Way Analysis of Variance (ANOVA)"
                unit_id = 46
                unit_name = "Correlation, Regression, and Design of Experiments"
                justification = "Two-factor ANOVA testing workers and machine types"
            elif "level of confidence" in norm_text or "confidence is denoted by" in norm_text:
                cat = "A2"
                target_tid = 424
                target_name = "Null Hypothesis, Alternative Hypothesis, and Errors in Testing"
                unit_id = 45
                unit_name = "Testing of Hypothesis"
                justification = "Significance level and confidence level in hypothesis testing"
            elif "two random samples of tobacco" in norm_text:
                cat = "A3"  # Ambiguous between small sample t and F test
                justification = "Tests equality of two normal populations without specifying mean or variance test"
            else:
                cat = "A3"
                justification = "Advanced inference concept outside standard 5-unit syllabus"

        # Check Course 24 (DSA)
        elif cid == 24:
            if "red-black tree" in norm_text:
                cat = "A1"
                target_name = "Red-Black Trees: Properties and Balance"
                unit_id = 160
                unit_name = "Trees and Hashing"
                justification = "Red-Black balanced search tree properties and height bounds (Unit 4 balanced tree syllabus concept)"
            elif "convert the expression given as follows" in norm_text or "a+(b*c-(d/e^f)*g)*h" in norm_text:
                cat = "A2"
                target_tid = 753
                target_name = "Stack Applications: Infix to Postfix, Evaluation, and Balancing Symbols"
                unit_id = 159
                unit_name = "Stack and Queue"
                justification = "Infix expression conversion using stack application"
            elif "customer support ticket system" in norm_text and "insert at the beginning" in norm_text and "delete the last ticket" in norm_text:
                cat = "A2"
                target_tid = 755
                target_name = "Circular Queue and Deque"
                unit_id = 159
                unit_name = "Stack and Queue"
                justification = "Double-ended queue (Deque) ADT application allowing insertion/deletion at both ends"
            elif "call logs in the mobile" in norm_text and "least recent number is deleted" in norm_text:
                cat = "A2"
                target_tid = 755
                target_name = "Circular Queue and Deque"
                unit_id = 159
                unit_name = "Stack and Queue"
                justification = "Fixed-size circular FIFO queue simulation for recent call logs"
            elif "normal queue, if implemented using an array of size max-size gets full when" in norm_text:
                cat = "A2"
                target_tid = 754
                target_name = "Queue ADT and Array/Linked Implementation"
                unit_id = 159
                unit_name = "Stack and Queue"
                justification = "Queue array boundary conditions for overflow check"
            elif "struct student" in norm_text:
                cat = "A2"
                target_tid = 747
                target_name = "Structures, Pointers, and Dynamic Memory Allocation in C"
                unit_id = 157
                unit_name = "Introduction"
                justification = "C programming structures, pointers, and arrow operator usage"
            elif "add two n x n matrices" in norm_text or "multiply two m \\times n matrices" in norm_text:
                cat = "A2"
                target_tid = 747
                target_name = "Structures, Pointers, and Dynamic Memory Allocation in C"
                unit_id = 157
                unit_name = "Introduction"
                justification = "Matrix operations and 2D arrays in C"
            elif "maximum of all the row sums" in norm_text:
                cat = "A2"
                target_tid = 748
                target_name = "Data Structure Definition, Types, ADT, and Operations"
                unit_id = 157
                unit_name = "Introduction"
                justification = "2D array operations and array data structure limitations"
            elif "linear ds" in norm_text:
                cat = "A2"
                target_tid = 748
                target_name = "Data Structure Definition, Types, ADT, and Operations"
                unit_id = 157
                unit_name = "Introduction"
                justification = "Classification of linear vs non-linear data structures"
            elif "situation is usually called" in norm_text and "overflow" in norm_text:
                cat = "A2"
                target_tid = 748
                target_name = "Data Structure Definition, Types, ADT, and Operations"
                unit_id = 157
                unit_name = "Introduction"
                justification = "Underflow and overflow conditions in data structure operations"
            elif "inserting a node at the end of the list" in norm_text or "cur.setnext (node)" in norm_text:
                cat = "A2"
                target_tid = 750
                target_name = "List ADT and Operations: Array, Cursor, and Linked Implementations"
                unit_id = 158
                unit_name = "List Structure"
                justification = "Linked list node insertion operation"
            elif "which loop is guaranteed to execute at least one time" in norm_text or "prints the string \"hello\"" in norm_text:
                cat = "A2"
                target_tid = 746
                target_name = "C Programming Refresher: Structures and Primitive Types"
                unit_id = 157
                unit_name = "Introduction"
                justification = "C language control structures and looping primitives"
            elif "keys 2, 4, 13, 5, 26, 7, 19, 21, 9 are to be sorted" in norm_text:
                cat = "A2"
                target_tid = 748
                target_name = "Data Structure Definition, Types, ADT, and Operations"
                unit_id = 157
                unit_name = "Introduction"
                justification = "Data structure selection and trade-off comparison for sorting"
            elif "lowest worst-case complexity" in norm_text:
                cat = "A2"
                target_tid = 748
                target_name = "Data Structure Definition, Types, ADT, and Operations"
                unit_id = 157
                unit_name = "Introduction"
                justification = "Complexity trade-offs in data structures"
            else:
                cat = "A3"
                justification = "Out-of-syllabus programming problem"

        # Check Course 25 (OS)
        elif cid == 25:
            if "role of operating system" in norm_text or "operating system is not a" in norm_text or "not an operating system" in norm_text or "bios is used by" in norm_text or "connects high-speed high-bandwidth device to memory subsystem" in norm_text:
                cat = "A2"
                target_tid = 763
                target_name = "Computer-System Architecture and Operating-System Structure"
                unit_id = 161
                unit_name = "Introduction and Operating-System Structures"
                justification = "Computer system organization, buses, BIOS, and OS definition"
            elif "services provided by operating system" in norm_text or "services provided by operating systems" in norm_text:
                cat = "A2"
                target_tid = 764
                target_name = "Operating System Services and User Interfaces"
                unit_id = 161
                unit_name = "Introduction and Operating-System Structures"
                justification = "Operating system services and system interface capabilities"
            elif "properties of the following operating systems" in norm_text and ("batch" in norm_text or "distributed" in norm_text):
                cat = "A2"
                target_tid = 763
                target_name = "Computer-System Architecture and Operating-System Structure"
                unit_id = 161
                unit_name = "Introduction and Operating-System Structures"
                justification = "Types of operating systems: batch, time-sharing, parallel, distributed"
            elif "active entity whereas" in norm_text and "passive entity" in norm_text:
                cat = "A2"
                target_tid = 767
                target_name = "Process Concept and Process Control Block"
                unit_id = 162
                unit_name = "Process Management, Threads and Synchronization"
                justification = "Process vs program active vs passive entity definition"
            elif "operating processes" in norm_text:
                cat = "A2"
                target_tid = 767
                target_name = "Process Concept and Process Control Block"
                unit_id = 162
                unit_name = "Process Management, Threads and Synchronization"
                justification = "Process concepts and advantages of multi-process operations"
            elif "not shared by the threads of the same process" in norm_text or "multiple threads of control implies" in norm_text or "amdahl" in norm_text or ("application that is performed 80% in parallel" in norm_text):
                cat = "A2"
                target_tid = 769
                target_name = "Multithreading Models and Threading Issues"
                unit_id = 162
                unit_name = "Process Management, Threads and Synchronization"
                justification = "Thread stack vs shared address space and Amdahl's Law speedup in multicore"
            elif "cooperating process" in norm_text or "process that can be affected by other process" in norm_text:
                cat = "A2"
                target_tid = 768
                target_name = "Interprocess Communication and Client-Server"
                unit_id = 162
                unit_name = "Process Management, Threads and Synchronization"
                justification = "Independent vs cooperating processes in IPC"
            elif "dining-philosophers problem will occur in case of" in norm_text:
                cat = "A2"
                target_tid = 772
                target_name = "Classical Synchronization Problems"
                unit_id = 162
                unit_name = "Process Management, Threads and Synchronization"
                justification = "Classical Dining Philosophers synchronization problem instances"
            elif "which scheduler is used to load the processes from secondary memory to main memory" in norm_text:
                cat = "A2"
                target_tid = 773
                target_name = "Basic CPU Scheduling Concepts and Scheduling Criteria"
                unit_id = 163
                unit_name = "CPU Scheduling and Deadlocks"
                justification = "Long-term vs short-term process scheduling roles"
            elif "removal of the running process from the cpu and the selects another process" in norm_text:
                cat = "A2"
                target_tid = 773
                target_name = "Basic CPU Scheduling Concepts and Scheduling Criteria"
                unit_id = 163
                unit_name = "CPU Scheduling and Deadlocks"
                justification = "Dispatcher and CPU scheduler mechanism for context switching"
            elif "interrupt a running process" in norm_text:
                cat = "A2"
                target_tid = 773
                target_name = "Basic CPU Scheduling Concepts and Scheduling Criteria"
                unit_id = 163
                unit_name = "CPU Scheduling and Deadlocks"
                justification = "Preemption and interrupt handling during process execution"
            elif "for real-time operating systems, interrupt latency should be" in norm_text or "processes data instructions without any delay" in norm_text:
                cat = "A2"
                target_tid = 775
                target_name = "Real-Time and Multiprocessor Scheduling"
                unit_id = 163
                unit_name = "CPU Scheduling and Deadlocks"
                justification = "Real-time operating systems interrupt latency and deadline scheduling"
            elif "swap space" in norm_text or "swap-space" in norm_text:
                cat = "A2"
                target_tid = 786
                target_name = "RAID Structure and Swap-Space Management"
                unit_id = 164
                unit_name = "Memory Management and Storage"
                justification = "Swap-space management on secondary storage"
            elif "how would the first-fit, best-fit and worst-fit algorithms place processes" in norm_text:
                cat = "A2"
                target_tid = 779
                target_name = "Main Memory and Contiguous Memory Allocation"
                unit_id = 164
                unit_name = "Memory Management and Storage"
                justification = "Contiguous memory allocation partition allocation simulation"
            elif "primary purpose of memory management" in norm_text:
                cat = "A2"
                target_tid = 779
                target_name = "Main Memory and Contiguous Memory Allocation"
                unit_id = 164
                unit_name = "Memory Management and Storage"
                justification = "Memory management allocation and address binding goals"
            elif "associative memory" in norm_text:
                cat = "A2"
                target_tid = 780
                target_name = "Paging, Segmentation and TLB"
                unit_id = 164
                unit_name = "Memory Management and Storage"
                justification = "Associative memory / TLB hardware for address translation"
            elif "a file is a/an" in norm_text or "file organization methods" in norm_text:
                cat = "A2"
                target_tid = 787
                target_name = "File Concept and Access Methods"
                unit_id = 165
                unit_name = "File Systems and Security"
                justification = "Abstract file data types and file access organizations"
            elif "directory and disk structures" in norm_text:
                cat = "A2"
                target_tid = 788
                target_name = "Directory and Disk Structure, File System Mounting and Sharing"
                unit_id = 165
                unit_name = "File Systems and Security"
                justification = "Single-level, two-level, and tree-structured directory architectures"
            elif "primary goal of protection" in norm_text or "restrict system access to authorized users" in norm_text or "capability-based system" in norm_text:
                cat = "A2"
                target_tid = 789
                target_name = "Protection Goals, Principles, and Domain of Protection"
                unit_id = 165
                unit_name = "File Systems and Security"
                justification = "Protection goals, domain of protection, and access control policies"
            elif "programs cause security breaches" in norm_text:
                cat = "A2"
                target_tid = 789
                target_name = "Protection Goals, Principles, and Domain of Protection"
                unit_id = 165
                unit_name = "File Systems and Security"
                justification = "Program threats, buffer overflow, and security breaches"
            elif "process p1 tries changing data" in norm_text and "process p2 tries reading" in norm_text:
                cat = "A2"
                target_tid = 770
                target_name = "Critical-Section Problem and Peterson's Solution"
                unit_id = 162
                unit_name = "Process Management, Threads and Synchronization"
                justification = "Race conditions and concurrent memory consistency requirements"
            elif "computing cluster consisting of two nodes" in norm_text:
                cat = "A2"
                target_tid = 763
                target_name = "Computer-System Architecture and Operating-System Structure"
                unit_id = 161
                unit_name = "Introduction and Operating-System Structures"
                justification = "Clustered systems architecture and storage sharing models"
            else:
                cat = "A3"
                justification = "General OS concept not cleanly bound to a single unit"

        # Check Course 26 (COA)
        elif cid == 26:
            if "reflected binary code" in norm_text:
                cat = "A2"
                target_tid = 792
                target_name = "Binary Codes and Parity"
                unit_id = 166
                unit_name = "Introduction to Number System and Logic Gates"
                justification = "Gray code is also known as reflected binary code"
            elif "adder circuit which can add two binary numbers and also take into account an input carry" in norm_text:
                cat = "A2"
                target_tid = 802
                target_name = "Adders: Half, Full, Carry Lookahead and Fast Adders"
                unit_id = 168
                unit_name = "Design of Arithmetic and Logic Unit (ALU)"
                justification = "Full adder circuit definition with carry input"
            elif "commonly used for binary multiplication in digital circuits" in norm_text:
                cat = "A2"
                target_tid = 803
                target_name = "Multipliers: Signed, Unsigned, Fast and Carry Save Multipliers"
                unit_id = 168
                unit_name = "Design of Arithmetic and Logic Unit (ALU)"
                justification = "Binary multiplication algorithms in hardware"
            elif "shift register" in norm_text or "register capable of shifting" in norm_text or "accumulator" in norm_text or "temporary storage location to hold an intermediate result" in norm_text:
                cat = "A2"
                target_tid = 796
                target_name = "Functional Units and Operational Concepts of a Computer"
                unit_id = 167
                unit_name = "Basic Structure of Computers and Architecture"
                justification = "Processor internal registers (Accumulator, Shift register)"
            elif "pci bus" in norm_text or "bus used to connect the monitor" in norm_text or "connected to memory bus" in norm_text:
                cat = "A2"
                target_tid = 797
                target_name = "Bus Structures and Memory Performance"
                unit_id = 167
                unit_name = "Basic Structure of Computers and Architecture"
                justification = "Bus structures, memory buses, and peripheral interconnects"
            elif "how many bits are needed to address any single byte" in norm_text or "address space of" in norm_text or "1 gb is equivalent to how to many bytes" in norm_text or "data is transferred to and from memory in groups of bits called" in norm_text:
                cat = "A2"
                target_tid = 798
                target_name = "Memory Addresses, Operations and Memory Hierarchy"
                unit_id = 167
                unit_name = "Basic Structure of Computers and Architecture"
                justification = "Memory addressing calculations, address bus widths, word size"
            elif "virtual memory consists of" in norm_text:
                cat = "A2"
                target_tid = 798
                target_name = "Memory Addresses, Operations and Memory Hierarchy"
                unit_id = 167
                unit_name = "Basic Structure of Computers and Architecture"
                justification = "Memory hierarchy and virtual memory structure"
            elif "number successful accesses to memory stated as a fraction" in norm_text or "write miss" in norm_text or "present in the cache" in norm_text:
                cat = "A2"
                target_tid = 798
                target_name = "Memory Addresses, Operations and Memory Hierarchy"
                unit_id = 167
                unit_name = "Basic Structure of Computers and Architecture"
                justification = "Cache memory hit rate, miss rate, and write policies"
            elif "data transfer instructions" in norm_text and "data manipulation instructions" in norm_text:
                cat = "A2"
                target_tid = 799
                target_name = "Instructions, Instruction Sequencing and Assembly Language"
                unit_id = 167
                unit_name = "Basic Structure of Computers and Architecture"
                justification = "Instruction types: data transfer, data manipulation, arithmetic"
            elif "rotated right by two" in norm_text:
                cat = "A2"
                target_tid = 799
                target_name = "Instructions, Instruction Sequencing and Assembly Language"
                unit_id = 167
                unit_name = "Basic Structure of Computers and Architecture"
                justification = "Bit-level rotate and shift instruction operations"
            elif "describe addressing mode with example" in norm_text:
                cat = "A2"
                target_tid = 800
                target_name = "Addressing Modes and Implementation"
                unit_id = 167
                unit_name = "Basic Structure of Computers and Architecture"
                justification = "Addressing modes definitions and examples"
            elif "normalized representation of" in norm_text or "in 32 bit representation the scale factor as a range of" in norm_text:
                cat = "A2"
                target_tid = 805
                target_name = "IEEE 754 Floating Point Representation and Operations"
                unit_id = 168
                unit_name = "Design of Arithmetic and Logic Unit (ALU)"
                justification = "IEEE 754 single-precision floating point normalized formats"
            elif "explain the types of hazards" in norm_text:
                cat = "A2"
                target_tid = 810
                target_name = "Pipeline Hazards: Data, Instruction and Control Hazards"
                unit_id = 169
                unit_name = "Control Unit and Pipelining"
                justification = "Instruction pipeline hazards classification"
            elif "complex and expensive to produce is" in norm_text and "cisc" in norm_text:
                cat = "A2"
                target_tid = 812
                target_name = "ARM Processor Architecture and CPU Cores"
                unit_id = 170
                unit_name = "Parallelism and ARM Processor"
                justification = "RISC vs CISC architectural principles"
            elif "mesi protocol" in norm_text or "architecture of parallel systems and its types" in norm_text or "memory in multiprocessor system" in norm_text:
                cat = "A2"
                target_tid = 811
                target_name = "Parallel Processing and Flynn's Classification"
                unit_id = 170
                unit_name = "Parallelism and ARM Processor"
                justification = "Multiprocessor cache coherence (MESI) and parallel systems"
            elif "which interrupt services save all the register and flags" in norm_text:
                cat = "A2"
                target_tid = 797
                target_name = "Bus Structures and Memory Performance"
                unit_id = 167
                unit_name = "Basic Structure of Computers and Architecture"
                justification = "Interrupt handling and context saving"
            else:
                cat = "A3"
                justification = "Out-of-syllabus COA question"

        # Check Course 27 (DAA)
        elif cid == 27:
            if "floyd-warshall" in norm_text or "floyd warshall" in norm_text:
                cat = "A1"
                target_name = "All-Pairs Shortest Paths: Floyd-Warshall Algorithm"
                unit_id = 173
                unit_name = "Greedy Algorithms and Dynamic Programming"
                justification = "Floyd-Warshall all-pairs shortest paths dynamic programming algorithm (canonical CLRS/SRMIST syllabus topic missing from taxonomy)"
            elif "insertion sort" in norm_text or "iteratively inserting each element of the unsorted portion" in norm_text:
                cat = "A2"
                target_tid = 816
                target_name = "Algorithm Design Paradigms and Loop Invariants (Insertion Sort)"
                unit_id = 171
                unit_name = "Introduction to Algorithm Design and Asymptotic Analysis"
                justification = "Insertion sort algorithm, passes, and loop invariant analysis"
            elif "correct order of increasing growth" in norm_text or "\\omega(n^2)" in norm_text or "4n^2 + 5 \\in \\omega" in norm_text or "f(n)=o(g(n))" in norm_text or "maximum asymptotic complexity" in norm_text:
                cat = "A2"
                target_tid = 818
                target_name = "Asymptotic Notations and Growth Functions"
                unit_id = 171
                unit_name = "Introduction to Algorithm Design and Asymptotic Analysis"
                justification = "Asymptotic notation bounds (Big-O, Omega, Theta) and growth ordering"
            elif "what does the variable a denote in masters theorem" in norm_text:
                cat = "A2"
                target_tid = 824
                target_name = "Master Theorem and Recurrence Proofs"
                unit_id = 172
                unit_name = "Divide and Conquer Paradigms"
                justification = "Master theorem recurrence parameters"
            elif "closest-pair problem" in norm_text or "vertical strip of width 2d" in norm_text:
                cat = "A2"
                target_tid = 825
                target_name = "Geometric Algorithms: Closest Pair and Convex Hull"
                unit_id = 172
                unit_name = "Divide and Conquer Paradigms"
                justification = "Divide-and-conquer closest pair of points 2D geometric algorithm"
            elif "maximum and minimum in an array" in norm_text or "maximum and minimum elements" in norm_text:
                cat = "A2"
                target_tid = 822
                target_name = "Merge Sort, Quick Sort and Order Statistics"
                unit_id = 172
                unit_name = "Divide and Conquer Paradigms"
                justification = "Simultaneous minimum and maximum comparison bounds in divide-and-conquer"
            elif "linear search" in norm_text:
                cat = "A2"
                target_tid = 817
                target_name = "Time and Space Complexity Analysis"
                unit_id = 171
                unit_name = "Introduction to Algorithm Design and Asymptotic Analysis"
                justification = "Best and worst-case comparison counts in linear scan search"
            elif "largest sub array sum" in norm_text or "largest sub-array sum" in norm_text:
                cat = "A2"
                target_tid = 821
                target_name = "Binary Search and Maximum Subarray Problem"
                unit_id = 172
                unit_name = "Divide and Conquer Paradigms"
                justification = "Maximum subarray problem instance calculation"
            elif "chain of matrices" in norm_text or "minimum number of scalar multiplications" in norm_text:
                cat = "A2"
                target_tid = 829
                target_name = "Dynamic Programming: 0/1 Knapsack and Matrix Chain Multiplication"
                unit_id = 173
                unit_name = "Greedy Algorithms and Dynamic Programming"
                justification = "Matrix chain multiplication scalar multiplication cost calculation"
            elif "greedy based technique to determine a subset of items" in norm_text:
                cat = "A2"
                target_tid = 827
                target_name = "Fractional Knapsack and Activity Selection"
                unit_id = 173
                unit_name = "Greedy Algorithms and Dynamic Programming"
                justification = "Greedy knapsack problem formulation"
            elif "minimum cost spanning tree with n vertices" in norm_text or "spanning tree of a graph g" in norm_text:
                cat = "A2"
                target_tid = 828
                target_name = "Minimum Spanning Trees: Kruskal and Prim"
                unit_id = 173
                unit_name = "Greedy Algorithms and Dynamic Programming"
                justification = "Minimum spanning tree tree-edge invariants (N-1 edges)"
            elif "state-space tree" in norm_text or "tree of choices called as" in norm_text:
                cat = "A2"
                target_tid = 831
                target_name = "State Space Trees and Backtracking Principles"
                unit_id = 174
                unit_name = "Backtracking and Branch and Bound"
                justification = "State space tree definition in backtracking"
            elif "queens attack each other" in norm_text or "placing 4 queens on a 4x4 chessboard" in norm_text:
                cat = "A2"
                target_tid = 832
                target_name = "N-Queens and Sum of Subsets Problems"
                unit_id = 174
                unit_name = "Backtracking and Branch and Bound"
                justification = "N-Queens constraint rules and 4-queens solution counting"
            elif "state np hard and np complete and differentiate both" in norm_text or "solved in polynomial time are known as" in norm_text:
                cat = "A2"
                target_tid = 838
                target_name = "NP-Completeness and NP-Hardness"
                unit_id = 175
                unit_name = "Randomized Algorithms and NP-Completeness"
                justification = "NP-Complete vs NP-Hard definitions and tractable polynomial classes"
            elif "rabin-karp string matching" in norm_text:
                cat = "A2"
                target_tid = 836
                target_name = "Randomized Algorithms: Quicksort and String Matching"
                unit_id = 175
                unit_name = "Randomized Algorithms and NP-Completeness"
                justification = "Rabin-Karp string matching hash calculation and spurious hits"
            elif "travelling salesman problem is an example of" in norm_text:
                cat = "A2"
                target_tid = 834
                target_name = "Branch and Bound Search Strategies"
                unit_id = 174
                unit_name = "Backtracking and Branch and Bound"
                justification = "Travelling salesman problem algorithmic classification"
            elif "depth first search is" in norm_text or "breadth first and depth first search" in norm_text or "breadth first search is started on a binary tree" in norm_text:
                cat = "A2"
                target_tid = 816
                target_name = "Algorithm Design Paradigms and Loop Invariants (Insertion Sort)"
                unit_id = 171
                unit_name = "Introduction to Algorithm Design and Asymptotic Analysis"
                justification = "Graph and tree traversal algorithm properties"
            elif "top-down design" in norm_text or "bottom-up" in norm_text or "design paradigms for the problem" in norm_text or "well defined and ordered procedure" in norm_text or "algorithms can be represented" in norm_text:
                cat = "A2"
                target_tid = 816
                target_name = "Algorithm Design Paradigms and Loop Invariants (Insertion Sort)"
                unit_id = 171
                unit_name = "Introduction to Algorithm Design and Asymptotic Analysis"
                justification = "Algorithm fundamentals and design paradigm principles"
            elif "tower of hanoi" in norm_text or "advantage of recursive approach" in norm_text:
                cat = "A2"
                target_tid = 819
                target_name = "Recurrence Relations and Substitution Method"
                unit_id = 171
                unit_name = "Introduction to Algorithm Design and Asymptotic Analysis"
                justification = "Recursion vs iteration and recursive recurrence problems"
            elif "two phases. the first phase, initialization, takes time o(n^3)" in norm_text:
                cat = "A2"
                target_tid = 817
                target_name = "Time and Space Complexity Analysis"
                unit_id = 171
                unit_name = "Introduction to Algorithm Design and Asymptotic Analysis"
                justification = "Composite algorithm time complexity analysis"
            elif "max heap" in norm_text:
                cat = "A3"
                justification = "Heap data structure property, primarily DSA syllabus"
            elif "set of all subsets of n elements" in norm_text or "under what condition any set a will be a subset of b" in norm_text:
                cat = "A2"
                target_tid = 832
                target_name = "N-Queens and Sum of Subsets Problems"
                unit_id = 174
                unit_name = "Backtracking and Branch and Bound"
                justification = "Subset properties relevant to Sum of Subsets state space explosion"
            else:
                cat = "A3"
                justification = "Out-of-syllabus algorithmic problem"

        # Check Course 28 (DBMS)
        elif cid == 28:
            if "query processing" in norm_text or "query processing engine" in norm_text or "processing a query" in norm_text:
                cat = "A1"
                target_name = "Query Processing and Optimization: Parsing, Evaluation and Relational Plans"
                unit_id = 178
                unit_name = "SQL and Advanced Database Programming"
                justification = "Query processing architecture, query tree parsing, query optimization and execution (Silberschatz Ch 12/13, missing from taxonomy)"
            elif "what is dbms" in norm_text or "feature of the database" in norm_text or "limitations/disadvantages of dbms" in norm_text or "responsibilities of a database management system" in norm_text or "naive user" in norm_text or "levels of abstraction" in norm_text:
                cat = "A2"
                target_tid = 841
                target_name = "Database System Concepts and Architecture"
                unit_id = 176
                unit_name = "Introduction and Conceptual Data Modeling"
                justification = "Database fundamentals, user types, schema abstraction levels, and DBMS responsibilities"
            elif "components of data base system environment" in norm_text or "manages the allocation of space on disk storage and the data structures used to represent information" in norm_text:
                cat = "A2"
                target_tid = 842
                target_name = "Data Independence and DBMS Components"
                unit_id = 176
                unit_name = "Introduction and Conceptual Data Modeling"
                justification = "DBMS internal components (Storage manager, buffer manager, query processor)"
            elif "evolution models" in norm_text or "top-to-bottom relationship" in norm_text or "hierarchical" in norm_text:
                cat = "A2"
                target_tid = 843
                target_name = "Data Models and Schemas"
                unit_id = 176
                unit_name = "Introduction and Conceptual Data Modeling"
                justification = "Database models: Hierarchical, Network, Relational"
            elif "develop e-r model" in norm_text or "derived attribute" in norm_text or "maximum number of entities that can be involved in a relationship" in norm_text:
                cat = "A2"
                target_tid = 844
                target_name = "Entity Relationship (ER) Model and Diagrams"
                unit_id = 176
                unit_name = "Introduction and Conceptual Data Modeling"
                justification = "ER diagram modeling, attribute types, relationship cardinality"
            elif "relational model is based on the concept that data is organized and stored in two-dimensional tables" in norm_text or "permitted values called the" in norm_text or "super key" in norm_text or "pit fall in relational" in norm_text:
                cat = "A2"
                target_tid = 846
                target_name = "Relational Model Concepts and Integrity Constraints"
                unit_id = 177
                unit_name = "Relational Data Model and Relational Languages"
                justification = "Relational concepts: Domains, relations, candidate keys, primary keys, super keys"
            elif "\\sigma_{salary > 1000}" in text:
                cat = "A2"
                target_tid = 848
                target_name = "Relational Algebra: Selection, Projection and Set Operations"
                unit_id = 177
                unit_name = "Relational Data Model and Relational Languages"
                justification = "Relational algebra selection operator notation"
            elif "drop table" in norm_text or "check constraint" in norm_text:
                cat = "A2"
                target_tid = 851
                target_name = "SQL Data Definition (DDL) and Integrity Constraints"
                unit_id = 178
                unit_name = "SQL and Advanced Database Programming"
                justification = "SQL DDL commands and column check constraints"
            elif "insert employee" in norm_text or "write an sql query" in norm_text or "subqueries and correlated queries" in norm_text or "what is a join" in norm_text or "all aggregate functions except" in norm_text:
                cat = "A2"
                target_tid = 852
                target_name = "SQL Queries (DML), Joins and Nested Subqueries"
                unit_id = 178
                unit_name = "SQL and Advanced Database Programming"
                justification = "SQL DML statements, subqueries, joins, and aggregate functions"
            elif "a window into a portion of a database is" in norm_text:
                cat = "A2"
                target_tid = 853
                target_name = "SQL Views, Set Operations and Assertions"
                unit_id = 178
                unit_name = "SQL and Advanced Database Programming"
                justification = "SQL view concept definition"
            elif "developers can write their own functions and procedures" in norm_text:
                cat = "A2"
                target_tid = 854
                target_name = "PL/SQL Programming: Blocks, Procedures and Functions"
                unit_id = 178
                unit_name = "SQL and Advanced Database Programming"
                justification = "Stored procedures and functions creation in PL/SQL"
            elif "which is not a type of normalization" in norm_text or "primary goal of normalization" in norm_text or "condition for 2^{nd} norm form" in norm_text or "define first normal form" in norm_text or "1^{st} normal form" in norm_text or "1^{st} norm form" in norm_text:
                cat = "A2"
                target_tid = 857
                target_name = "First Normal Form (1NF) and Second Normal Form (2NF)"
                unit_id = 179
                unit_name = "Database Design Theory and Normalization"
                justification = "First and Second normal forms definitions, goals, and conditions"
            elif "boyce-codd normal form is found to be stricter than third normal form" in norm_text:
                cat = "A2"
                target_tid = 858
                target_name = "Third Normal Form (3NF) and Boyce-Codd Normal Form (BCNF)"
                unit_id = 179
                unit_name = "Database Design Theory and Normalization"
                justification = "Comparison of 3NF vs BCNF rigor"
            elif "lossless decomposition" in norm_text:
                cat = "A2"
                target_tid = 860
                target_name = "Join Dependencies, Fifth Normal Form (5NF) and Lossless Decomposition"
                unit_id = 179
                unit_name = "Database Design Theory and Normalization"
                justification = "Lossless join decomposition analysis"
            elif "properties of a transaction" in norm_text or "transaction control language commands" in norm_text:
                cat = "A2"
                target_tid = 861
                target_name = "Transaction Concepts and ACID Properties"
                unit_id = 180
                unit_name = "Transaction Management, Concurrency Control and Storage"
                justification = "Transaction ACID properties and transaction control commands"
            elif "what is serialization" in norm_text or "testing of seriability" in norm_text:
                cat = "A2"
                target_tid = 862
                target_name = "Serializability and Schedule Types"
                unit_id = 180
                unit_name = "Transaction Management, Concurrency Control and Storage"
                justification = "Schedule serializability testing methods"
            elif "duty read" in norm_text or "dirty read" in norm_text or "problems with concurrent execution" in norm_text or "several operation simultaneously" in norm_text or "locks are used" in norm_text or "locking" in norm_text or "dead lock" in norm_text or "deadlock" in norm_text:
                cat = "A2"
                target_tid = 863
                target_name = "Concurrency Control and Locking Protocols"
                unit_id = 180
                unit_name = "Transaction Management, Concurrency Control and Storage"
                justification = "Concurrency control anomalies, lock-based protocols, and deadlock in transactions"
            elif "fuzzy check prints" in norm_text or "check points" in norm_text or "deferred-modification" in norm_text:
                cat = "A2"
                target_tid = 864
                target_name = "Timestamp Protocols and Database Recovery Techniques"
                unit_id = 180
                unit_name = "Transaction Management, Concurrency Control and Storage"
                justification = "Checkpoints, fuzzy checkpoints, and deferred modification recovery"
            else:
                cat = "A3"
                justification = "Out-of-syllabus database question"

        # Check Course 29 (AI)
        elif cid == 29:
            if "multi-agent system" in norm_text:
                cat = "A2"
                target_tid = 867
                target_name = "Agent Types and Multi-Agent Environments"
                unit_id = 181
                unit_name = "Introduction and Intelligent Agents"
                justification = "Multi-agent systems and real-world cooperative agent environments"
            elif "mean ends analysis" in norm_text:
                cat = "A2"
                target_tid = 884
                target_name = "Classical Planning: STRIPS and Planning as State-Space Search"
                unit_id = 184
                unit_name = "Planning and Constraint Satisfaction"
                justification = "Means-Ends analysis problem solving in classical planning"
            elif "ill-structured problem" in norm_text:
                cat = "A2"
                target_tid = 868
                target_name = "Problem Formulation, State Spaces and Search Problems"
                unit_id = 181
                unit_name = "Introduction and Intelligent Agents"
                justification = "Well-structured vs ill-structured problem formulation"
            elif "cognitive science" in norm_text:
                cat = "A2"
                target_tid = 866
                target_name = "Foundations and Historical Evolution of AI"
                unit_id = 181
                unit_name = "Introduction and Intelligent Agents"
                justification = "Cognitive science and psychological foundations of AI"
            elif "crossword puzzle" in norm_text:
                cat = "A2"
                target_tid = 867
                target_name = "Agent Types and Multi-Agent Environments"
                unit_id = 181
                unit_name = "Introduction and Intelligent Agents"
                justification = "Task environments classification (Static vs dynamic, deterministic)"
            elif "search is called" in norm_text and "complete" in norm_text:
                cat = "A2"
                target_tid = 869
                target_name = "Uninformed Search Strategies: BFS, DFS, and Uniform Cost Search"
                unit_id = 182
                unit_name = "Uninformed and Informed Search Strategies"
                justification = "Search algorithm completeness evaluation criteria"
            elif "node/ state is marked to be visited" in norm_text or "node/state is marked to be visited" in norm_text:
                cat = "A2"
                target_tid = 869
                target_name = "Uninformed Search Strategies: BFS, DFS, and Uniform Cost Search"
                unit_id = 182
                unit_name = "Uninformed and Informed Search Strategies"
                justification = "Visited state tracking and graph search node exploration"
            elif "constraints are the one that restrict" in norm_text:
                cat = "A2"
                target_tid = 874
                target_name = "Constraint Satisfaction Problems Formulation and Propagation"
                unit_id = 182
                unit_name = "Uninformed and Informed Search Strategies"
                justification = "Constraint satisfaction formulation principles"
            elif "to + go = out" in norm_text:
                cat = "A2"
                target_tid = 875
                target_name = "CSP Solving: Backtracking and Arc Consistency"
                unit_id = 182
                unit_name = "Uninformed and Informed Search Strategies"
                justification = "Cryptarithmetic puzzle instance solving via CSP backtracking"
            elif "process of reasoning that operate on" in norm_text and "internal" in norm_text:
                cat = "A2"
                target_tid = 878
                target_name = "Knowledge Representation: Ontological Engineering and Categories"
                unit_id = 183
                unit_name = "Knowledge Representation and Logic"
                justification = "Internal representation of knowledge in reasoning agents"
            elif "different types of agents" in norm_text:
                cat = "A2"
                target_tid = 867
                target_name = "Agent Types and Multi-Agent Environments"
                unit_id = 181
                unit_name = "Introduction and Intelligent Agents"
                justification = "Agent architectures: reflex, model-based, goal-based, utility-based"
            elif "p\\land q \\rightarrow r" in norm_text or "p \\wedge q \\rightarrow r" in norm_text:
                cat = "A2"
                target_tid = 876
                target_name = "Propositional Logic: Syntax, Semantics, and Equivalence"
                unit_id = 183
                unit_name = "Knowledge Representation and Logic"
                justification = "Propositional logic logical equivalences"
            elif "extraction of meaningful information that is previously unknown" in norm_text:
                cat = "A2"
                target_tid = 887
                target_name = "Learning from Observations and Inductive Learning"
                unit_id = 185
                unit_name = "Learning and Expert Systems"
                justification = "Knowledge discovery and inductive machine learning concepts"
            else:
                cat = "A3"
                justification = "Out-of-syllabus AI question"

        # Record detailed result
        detailed_results.append({
            "question_id": qid,
            "course_id": cid,
            "course_name": item["course_name"],
            "semester": item.get("semester"),
            "year": item.get("exam_year"),
            "exam_id": item.get("exam_id"),
            "assessment_type": item.get("assessment_type"),
            "family_id": item.get("family_id"),
            "original_text": text,
            "category": cat,
            "target_topic_id": target_tid,
            "target_topic_name": target_name,
            "syllabus_unit_id": unit_id,
            "syllabus_unit_name": unit_name,
            "justification": justification
        })

        category_counts[cat] += 1
        by_course_counts[cid][cat] += 1

    summary = {
        "total_category_a": len(cat_a_raw),
        "breakdown": dict(category_counts),
        "by_course": {cid: dict(counts) for cid, counts in by_course_counts.items()}
    }

    out_file = os.path.join(BASE_DIR, "data", "s3_s4", "phase6_4_gap_analysis.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "questions": detailed_results}, f, indent=2)

    print("\n" + "="*80)
    print("PHASE 6.4 CATEGORY A FORENSIC CLASSIFICATION SUMMARY")
    print("="*80)
    print(f"Total Category A questions evaluated: {len(cat_a_raw)}")
    for cat, cnt in sorted(category_counts.items()):
        print(f"  Category {cat}: {cnt} ({cnt/len(cat_a_raw)*100:.1f}%)")

    print("\nBy Course Breakdown:")
    for cid in sorted(by_course_counts.keys()):
        counts = by_course_counts[cid]
        cname = [q["course_name"] for q in cat_a_raw if q["course_id"] == cid][0]
        print(f"  Course {cid} ({cname}): Total {sum(counts.values())} -> " + ", ".join(f"{k}:{v}" for k, v in sorted(counts.items())))

if __name__ == "__main__":
    run_phase6_4_audit()
