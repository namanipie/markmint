"""
Taxonomy classification rules for Course 6: Fundamental Of Economics (FOE) (18MSS101T / 21MGH101T).
Derived directly from the official SRM IST Economics Syllabus, Question Bank, and course decks.

Unit 1 (id=6):  Introduction to Economics and Consumer Behaviour (Topics 160-163)
Unit 2 (id=62): Demand, Supply, and Market Equilibrium (Topics 164-167)
Unit 3 (id=63): Production and Cost Analysis (Topics 168-171)
Unit 4 (id=64): Market Structures and Pricing (Topics 172-175)
Unit 5 (id=65): Money, Banking, and Macroeconomic Aggregates (Topics 176-179)
"""
from typing import List
from backend.services.taxonomy_classifier import TaxonomyTopicRule

FOE_TAXONOMY_RULES: List[TaxonomyTopicRule] = [
    # -------------------------------------------------------------
    # UNIT 1: INTRODUCTION TO ECONOMICS AND CONSUMER BEHAVIOUR
    # -------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=160,
        topic_name="Definitions, Nature, and Scope of Economics",
        unit_id=6,
        unit_name="Introduction to Economics and Consumer Behaviour",
        strong_phrases=[
            "nature of economics", "definitions of economics", "fundamentals of economics",
            "father of modern economics", "adam smith", "lionel robbins", "alfred marshall",
            "relationship between ends and scarce means", "wealth and its distribution",
            "nature of scarcity", "subject matter of economics"
        ],
        specific_keywords=["adam smith", "lionel robbins", "alfred marshall"],
        negative_guards=["indifference curve", "elasticity", "monopoly", "oligopoly"]
    ),
    TaxonomyTopicRule(
        topic_id=161,
        topic_name="Microeconomics, Macroeconomics, and Central Economic Problems",
        unit_id=6,
        unit_name="Introduction to Economics and Consumer Behaviour",
        strong_phrases=[
            "micro economics", "macro economics", "microeconomics", "macroeconomics",
            "central problem of every economy", "scarcity of economic resources",
            "economic resources are limited", "positive economics", "normative economics"
        ],
        specific_keywords=["microeconomics", "micro economics", "macroeconomics", "macro economics"],
        negative_guards=["indifference curve", "elasticity", "monopoly"]
    ),
    TaxonomyTopicRule(
        topic_id=162,
        topic_name="Cardinal Utility Analysis and Law of Diminishing Marginal Utility",
        unit_id=6,
        unit_name="Introduction to Economics and Consumer Behaviour",
        strong_phrases=[
            "law of diminishing marginal utility", "diminishing marginal utility",
            "equi-marginal utility", "total utility decreases", "marginal utility decreases",
            "utility analysis helps to explain", "cardinal utility", "marginal utility",
            "utility from goods", "marginal utility theories"
        ],
        specific_keywords=["marginal utility", "equi-marginal utility", "utility from goods"],
        negative_guards=["indifference curve", "elasticity of supply"]
    ),
    TaxonomyTopicRule(
        topic_id=163,
        topic_name="Consumer Preferences and Indifference Curve Analysis",
        unit_id=6,
        unit_name="Introduction to Economics and Consumer Behaviour",
        strong_phrases=[
            "indifference curve analysis", "indifference curve", "indifference curves",
            "slope of the indifference curve", "farther the indifference curve from the origin",
            "consumer preferences and choices", "marginal rate of substitution"
        ],
        specific_keywords=["indifference curve", "indifference curves"],
        negative_guards=["monopoly", "oligopoly", "national income"]
    ),

    # -------------------------------------------------------------
    # UNIT 2: DEMAND, SUPPLY, AND MARKET EQUILIBRIUM
    # -------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=164,
        topic_name="Theory of Demand, Law of Demand, and Demand Elasticity",
        unit_id=62,
        unit_name="Demand, Supply, and Market Equilibrium",
        strong_phrases=[
            "law of demand", "demand theory", "elasticity of demand", "price elasticity",
            "negative relationship between price and quantity demanded",
            "demand curve", "elastic demand", "inelastic demand", "unitary elasticity",
            "durable goods tend to have an elastic demand", "demand schedule"
        ],
        specific_keywords=["law of demand", "elasticity of demand", "demand curve"],
        negative_guards=["cross elasticity", "income elasticity", "supply curve", "law of supply"]
    ),
    TaxonomyTopicRule(
        topic_id=165,
        topic_name="Income Elasticity and Cross Elasticity of Demand",
        unit_id=62,
        unit_name="Demand, Supply, and Market Equilibrium",
        strong_phrases=[
            "income elasticity", "cross elasticity", "cross-price elasticity",
            "income and substitution effects", "inferior goods have negative income elasticity",
            "substitute goods have positive cross elasticity"
        ],
        specific_keywords=["cross elasticity", "income elasticity"],
        negative_guards=["supply", "monopoly"]
    ),
    TaxonomyTopicRule(
        topic_id=166,
        topic_name="Theory of Supply, Law of Supply, and Elasticity of Supply",
        unit_id=62,
        unit_name="Demand, Supply, and Market Equilibrium",
        strong_phrases=[
            "law of supply", "elasticity of supply", "supply curve",
            "factors that influence supply", "supply is a desired quantity",
            "when the price of goods or services is low, the supply is"
        ],
        specific_keywords=["law of supply", "elasticity of supply", "supply curve"],
        negative_guards=["indifference curve", "monopoly"]
    ),
    TaxonomyTopicRule(
        topic_id=167,
        topic_name="Market Equilibrium and Consumer Surplus",
        unit_id=62,
        unit_name="Demand, Supply, and Market Equilibrium",
        strong_phrases=[
            "market equilibrium of a commodity", "market equilibrium", "equilibrium price",
            "consumer equilibrium", "consumer surplus", "intersection of market demand and supply",
            "balancing of demand and supply"
        ],
        specific_keywords=["consumer surplus", "equilibrium price"],
        negative_guards=["monopolistic competition", "monopoly", "national income"]
    ),

    # -------------------------------------------------------------
    # UNIT 3: PRODUCTION AND COST ANALYSIS
    # -------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=168,
        topic_name="Factors of Production and Short-Run Production Function",
        unit_id=63,
        unit_name="Production and Cost Analysis",
        strong_phrases=[
            "factors of production", "production function describes", "production function",
            "transformation of input into output", "capital in economics",
            "land, labor, capital", "define production"
        ],
        specific_keywords=["factors of production", "production function"],
        negative_guards=["variable proportions", "returns to scale", "monopoly"]
    ),
    TaxonomyTopicRule(
        topic_id=169,
        topic_name="Law of Variable Proportions and Returns to Scale",
        unit_id=63,
        unit_name="Production and Cost Analysis",
        strong_phrases=[
            "law of variable proportions", "variable proportions", "returns to scale",
            "increasing returns to scale", "diminishing returns to scale",
            "law of diminishing returns"
        ],
        specific_keywords=["variable proportions", "returns to scale"],
        negative_guards=["monopoly", "oligopoly", "banking"]
    ),
    TaxonomyTopicRule(
        topic_id=170,
        topic_name="Cost Analysis: Short-Run and Long-Run Cost Curves",
        unit_id=63,
        unit_name="Production and Cost Analysis",
        strong_phrases=[
            "cost concept", "basic premise of cost concept", "marginal cost",
            "average cost", "total cost of producing one more unit",
            "fixed cost and variable cost", "short run cost curves", "long run cost curves"
        ],
        specific_keywords=["marginal cost", "average cost", "cost concept"],
        negative_guards=["monopoly", "oligopoly", "national income"]
    ),
    TaxonomyTopicRule(
        topic_id=171,
        topic_name="Revenue Concepts, Cost Minimization, and Profit Maximization",
        unit_id=63,
        unit_name="Production and Cost Analysis",
        strong_phrases=[
            "profit maximization in a firm", "profit maximization", "cost minimization",
            "marginal revenue and marginal cost interact", "total revenue, average revenue",
            "equilibrium of the firm", "revenue is directly influenced by"
        ],
        specific_keywords=["profit maximization", "cost minimization", "marginal revenue"],
        negative_guards=["monopoly", "oligopoly", "banking"]
    ),

    # -------------------------------------------------------------
    # UNIT 4: MARKET STRUCTURES AND PRICING
    # -------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=172,
        topic_name="Perfect Competition: Features and Equilibrium Analysis",
        unit_id=64,
        unit_name="Market Structures and Pricing",
        strong_phrases=[
            "perfect competition", "perfectly competitive market", "perfectly competitive firm",
            "all firms produce identical products", "firm is a price taker",
            "features of perfect competition"
        ],
        specific_keywords=["perfect competition", "perfectly competitive"],
        negative_guards=["monopoly", "monopolistic", "oligopoly"]
    ),
    TaxonomyTopicRule(
        topic_id=173,
        topic_name="Monopoly: Characteristics, Pricing, and Price Discrimination",
        unit_id=64,
        unit_name="Market Structures and Pricing",
        strong_phrases=[
            "price determination under monopoly", "price discrimination under monopoly",
            "price discrimination", "single seller in monopoly", "monopoly market",
            "barriers to entry in monopoly", "what is monopoly"
        ],
        specific_keywords=["monopoly", "price discrimination"],
        negative_guards=["monopolistic", "perfect competition", "oligopoly"]
    ),
    TaxonomyTopicRule(
        topic_id=174,
        topic_name="Monopolistic Competition: Product Differentiation and Equilibrium",
        unit_id=64,
        unit_name="Market Structures and Pricing",
        strong_phrases=[
            "monopolistic competition", "monopolistically competitive",
            "product differentiation in monopolistic competition", "product differentiation",
            "equilibrium under monopolistic competition", "difference between perfect and monopolistic"
        ],
        specific_keywords=["monopolistic competition", "product differentiation"],
        negative_guards=["oligopoly", "banking"]
    ),
    TaxonomyTopicRule(
        topic_id=175,
        topic_name="Oligopoly: Characteristics, Cartels, and Price Rigidity",
        unit_id=64,
        unit_name="Market Structures and Pricing",
        strong_phrases=[
            "oligopoly", "kinked demand curve", "cartels in oligopoly",
            "few large firms dominate the market", "price rigidity in oligopoly",
            "interdependence of firms in oligopoly"
        ],
        specific_keywords=["oligopoly", "kinked demand curve", "cartels"],
        negative_guards=["perfect competition", "banking"]
    ),

    # -------------------------------------------------------------
    # UNIT 5: MONEY, BANKING, AND MACROECONOMIC AGGREGATES
    # -------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=176,
        topic_name="Money: Functions, Evolution, and Quantity Theory",
        unit_id=65,
        unit_name="Money, Banking, and Macroeconomic Aggregates",
        strong_phrases=[
            "primary function of money", "functions of money", "medium of exchange",
            "store of value", "unit of account", "demand for money", "money supply towards indian economy",
            "influence of money supply"
        ],
        specific_keywords=["functions of money", "medium of exchange", "unit of account"],
        negative_guards=["inflation", "deflation", "banking", "national income"]
    ),
    TaxonomyTopicRule(
        topic_id=177,
        topic_name="Commercial Banking, Credit Creation, and Central Bank Monetary Policy",
        unit_id=65,
        unit_name="Money, Banking, and Macroeconomic Aggregates",
        strong_phrases=[
            "rbi monetary policy", "monetary policy", "central bank", "commercial banks",
            "credit creation by commercial banks", "liquid assets and their liabilities",
            "current account deposits", "what is monetary policy", "lower interest rates"
        ],
        specific_keywords=["monetary policy", "commercial banks", "central bank"],
        negative_guards=["monopoly", "oligopoly"]
    ),
    TaxonomyTopicRule(
        topic_id=178,
        topic_name="Inflation, Deflation, and Business Cycles",
        unit_id=65,
        unit_name="Money, Banking, and Macroeconomic Aggregates",
        strong_phrases=[
            "what is inflation", "inflation", "deflation", "business cycle",
            "persistent increase in the general price level", "phase of business cycle",
            "recession and depression"
        ],
        specific_keywords=["inflation", "deflation", "business cycle"],
        negative_guards=["monopoly", "elasticity"]
    ),
    TaxonomyTopicRule(
        topic_id=179,
        topic_name="National Income Accounting and Balance of Payments",
        unit_id=65,
        unit_name="Money, Banking, and Macroeconomic Aggregates",
        strong_phrases=[
            "calculating national income", "national income", "gross domestic product",
            "gnp", "nnp", "gdp", "balance of payments", "bop", "two sectoral economy",
            "calculate the gross domestic product in india"
        ],
        specific_keywords=["national income", "gross domestic product", "gnp", "nnp", "gdp", "bop"],
        negative_guards=["monopoly", "oligopoly", "elasticity"]
    ),
]
