"""
Generates the authoritative declarative taxonomy definition for Course 1:
Calculus and Linear Algebra (21MAB101T).
"""

import json
import os

CALCULUS_DATA = {
    "schema_version": "1.0",
    "taxonomy_version": "1.0.0",
    "course": {
        "id": 1,
        "name": "Calculus and Linear Algebra",
        "canonical_code": "21MAB101T",
        "code": "SEM1-CALC",
        "regulation_year": 2021,
        "department": "Mathematics"
    },
    "provenance": {
        "source_document": "SRMIST B.Tech Regulation 2021 Curriculum & Syllabus - 21MAB101T Calculus and Linear Algebra",
        "regulation": "2021",
        "approved_by": "Academic Council SRMIST",
        "notes": "Authoritative syllabus covering Matrices, Differential Equations, Partial Derivatives, Sequences and Series, and Multiple Integrals."
    },
    "units": [
        {
            "id": 13,
            "number": 1,
            "name": "Matrices and Linear Algebra",
            "topics": [
                {
                    "id": 1,
                    "name": "Eigenvalues and Eigenvectors",
                    "canonical_name": "Eigenvalues and Eigenvectors",
                    "aliases": ["Eigen values", "Eigen vectors", "Characteristic roots"],
                    "strong_phrases": [
                        "eigenvalues and eigenvectors",
                        "eigen values and eigen vectors",
                        "eigen values of the matrix",
                        "eigenvalues of the matrix",
                        "find the eigenvalues",
                        "find the eigen values",
                        "eigen values of a",
                        "eigenvalues of a",
                        "characteristic roots",
                        "characteristic equation of the matrix"
                    ],
                    "specific_keywords": [
                        "eigenvalue", "eigenvalues", "eigen value", "eigen values", "eigenvector", "eigenvectors"
                    ],
                    "negative_guards": ["cayley-hamilton", "quadratic form", "canonical form"],
                    "context_hints": ["matrix", "linear algebra"]
                },
                {
                    "id": 2,
                    "name": "Matrix Operations",
                    "canonical_name": "Matrix Operations",
                    "aliases": ["Matrix Algebra", "Rank of Matrix", "Orthogonal Matrix"],
                    "strong_phrases": [
                        "orthogonal matrix",
                        "symmetric matrix",
                        "skew symmetric matrix",
                        "rank of the matrix",
                        "inverse of the matrix",
                        "adjoint of the matrix",
                        "trace of the matrix"
                    ],
                    "specific_keywords": [
                        "orthogonal matrix", "rank of matrix", "matrix operations"
                    ],
                    "negative_guards": ["eigenvalue", "eigenvalues", "cayley-hamilton", "quadratic form"],
                    "context_hints": ["matrices", "linear algebra"]
                },
                {
                    "id": 3,
                    "name": "Linear Systems",
                    "canonical_name": "Linear Systems",
                    "aliases": ["System of Linear Equations", "Cramer's Rule", "Gaussian Elimination"],
                    "strong_phrases": [
                        "system of linear equations",
                        "consistency of system of equations",
                        "cramer's rule",
                        "gaussian elimination",
                        "gauss elimination method",
                        "gauss-jordan",
                        "homogeneous system of equations",
                        "non-homogeneous system"
                    ],
                    "specific_keywords": [
                        "cramer s rule", "gauss elimination", "system of equations"
                    ],
                    "negative_guards": ["quadratic form", "eigenvalue"],
                    "context_hints": ["linear equations", "linear algebra"]
                },
                {
                    "id": 32,
                    "name": "Cayley-Hamilton Theorem",
                    "canonical_name": "Cayley-Hamilton Theorem",
                    "aliases": ["Cayley Hamilton Theorem", "Cayley-Hamilton"],
                    "strong_phrases": [
                        "cayley-hamilton theorem",
                        "cayley hamilton theorem",
                        "verify cayley-hamilton",
                        "verify cayley hamilton",
                        "using cayley-hamilton",
                        "using cayley hamilton"
                    ],
                    "specific_keywords": [
                        "cayley-hamilton", "cayley hamilton"
                    ],
                    "negative_guards": [],
                    "context_hints": ["matrices", "linear algebra"]
                },
                {
                    "id": 33,
                    "name": "Quadratic Forms",
                    "canonical_name": "Quadratic Forms",
                    "aliases": ["Reduction to Canonical Form", "Nature of Quadratic Form", "Index and Signature"],
                    "strong_phrases": [
                        "quadratic form",
                        "reduction of quadratic form",
                        "canonical form of the quadratic form",
                        "nature of the quadratic form",
                        "positive definite",
                        "negative definite",
                        "index and signature of the quadratic form",
                        "rank, signature, and nature",
                        "rank signature and nature"
                    ],
                    "specific_keywords": [
                        "quadratic form", "canonical form", "positive definite", "negative definite", "indefinite quadratic"
                    ],
                    "negative_guards": ["cayley-hamilton"],
                    "context_hints": ["matrices", "linear algebra"]
                }
            ]
        },
        {
            "id": 14,
            "number": 2,
            "name": "Ordinary Differential Equations",
            "topics": [
                {
                    "id": 4,
                    "name": "First-Order ODE",
                    "canonical_name": "First-Order ODE",
                    "aliases": ["Exact Differential Equations", "Linear First-Order ODE", "Integrating Factor"],
                    "strong_phrases": [
                        "exact differential equation",
                        "integrating factor",
                        "bernoulli's equation",
                        "bernoulli equation",
                        "linear differential equation of first order",
                        "first order differential equation",
                        "separable variables"
                    ],
                    "specific_keywords": [
                        "integrating factor", "exact differential", "bernoulli equation"
                    ],
                    "negative_guards": ["second order", "d^2", "particular integral", "auxiliary equation"],
                    "context_hints": ["differential equations", "ode"]
                },
                {
                    "id": 5,
                    "name": "Second-Order ODE",
                    "canonical_name": "Second-Order ODE",
                    "aliases": ["Higher Order ODE", "Constant Coefficients ODE", "Particular Integral"],
                    "strong_phrases": [
                        "particular integral",
                        "complementary function",
                        "auxiliary equation",
                        "variation of parameters",
                        "method of variation of parameters",
                        "cauchy's linear equation",
                        "legendre's linear equation",
                        "second order differential equation",
                        "d^2 +", "d^2 -"
                    ],
                    "specific_keywords": [
                        "particular integral", "complementary function", "variation of parameters", "auxiliary equation"
                    ],
                    "negative_guards": ["partial differential", "pde"],
                    "context_hints": ["differential equations", "ode"]
                },
                {
                    "id": 6,
                    "name": "ODE Solutions",
                    "canonical_name": "ODE Solutions",
                    "aliases": ["Wronskian", "Linearly Independent Solutions", "Initial Value Problems"],
                    "strong_phrases": [
                        "wronskian",
                        "linearly independent solutions of",
                        "initial value problem for ode",
                        "boundary value problem"
                    ],
                    "specific_keywords": [
                        "wronskian", "linearly independent solution"
                    ],
                    "negative_guards": ["pde"],
                    "context_hints": ["differential equations", "solutions"]
                }
            ]
        },
        {
            "id": 15,
            "number": 3,
            "name": "Partial Differential Equations",
            "topics": [
                {
                    "id": 7,
                    "name": "PDE Classification",
                    "canonical_name": "PDE Classification",
                    "aliases": ["Formation of PDE", "Lagrange's Linear Equation"],
                    "strong_phrases": [
                        "partial differential equation",
                        "formation of pde",
                        "lagrange's linear equation",
                        "charpit's method",
                        "order and degree of pde",
                        "quasi-linear pde"
                    ],
                    "specific_keywords": [
                        "formation of pde", "lagrange s linear", "charpit s method", "pde classification"
                    ],
                    "negative_guards": ["ordinary differential equation"],
                    "context_hints": ["pde", "calculus"]
                },
                {
                    "id": 8,
                    "name": "Separation of Variables",
                    "canonical_name": "Separation of Variables",
                    "aliases": ["Method of Separation of Variables", "Wave Equation", "Heat Equation"],
                    "strong_phrases": [
                        "method of separation of variables",
                        "one dimensional wave equation",
                        "one dimensional heat equation",
                        "two dimensional laplace equation",
                        "separation of variables"
                    ],
                    "specific_keywords": [
                        "separation of variables", "wave equation", "heat equation"
                    ],
                    "negative_guards": [],
                    "context_hints": ["pde", "boundary conditions"]
                }
            ]
        },
        {
            "id": 16,
            "number": 4,
            "name": "Laplace Transforms",
            "topics": [
                {
                    "id": 9,
                    "name": "Laplace Transform Tables",
                    "canonical_name": "Laplace Transform Tables",
                    "aliases": ["Laplace Transforms of Elementary Functions", "First Shifting Theorem"],
                    "strong_phrases": [
                        "laplace transform of",
                        "find the laplace transform",
                        "first shifting property",
                        "second shifting property",
                        "transforms of derivatives",
                        "transforms of integrals",
                        "laplace transform tables"
                    ],
                    "specific_keywords": [
                        "laplace transform", "laplace transforms"
                    ],
                    "negative_guards": ["inverse laplace", "convolution theorem"],
                    "context_hints": ["transform calculus"]
                },
                {
                    "id": 10,
                    "name": "Inverse Laplace Transforms",
                    "canonical_name": "Inverse Laplace Transforms",
                    "aliases": ["Inverse Transforms", "Convolution Theorem"],
                    "strong_phrases": [
                        "inverse laplace transform",
                        "find the inverse laplace",
                        "convolution theorem",
                        "using convolution theorem",
                        "partial fractions in laplace",
                        "solve differential equation using laplace"
                    ],
                    "specific_keywords": [
                        "inverse laplace", "convolution theorem"
                    ],
                    "negative_guards": [],
                    "context_hints": ["transform calculus"]
                }
            ]
        },
        {
            "id": 17,
            "number": 5,
            "name": "Sequence and Series",
            "topics": [
                {
                    "id": 11,
                    "name": "Convergence Tests",
                    "canonical_name": "Convergence Tests",
                    "aliases": ["Convergence of Series", "Ratio Test", "Comparison Test", "D'Alembert's Test"],
                    "strong_phrases": [
                        "test the convergence of the series",
                        "convergence of the series",
                        "test for convergence",
                        "d'alembert's ratio test",
                        "ratio test",
                        "comparison test",
                        "cauchy's root test",
                        "rabee's test",
                        "integral test for series",
                        "alternating series",
                        "leibnitz's test",
                        "absolutely convergent",
                        "conditionally convergent",
                        "monotonically decreasing sequence",
                        "convergent or divergent"
                    ],
                    "specific_keywords": [
                        "convergence of series", "ratio test", "comparison test", "cauchy s root test",
                        "leibnitz s test", "conditionally convergent", "absolutely convergent",
                        "convergent sequence"
                    ],
                    "negative_guards": ["fourier series", "taylor series", "maclaurin series", "power series"],
                    "context_hints": ["series", "calculus"]
                },
                {
                    "id": 12,
                    "name": "Power Series",
                    "canonical_name": "Power Series",
                    "aliases": ["Radius of Convergence", "Interval of Convergence"],
                    "strong_phrases": [
                        "power series",
                        "radius of convergence",
                        "interval of convergence",
                        "series \\sum x^n",
                        "power series expansion"
                    ],
                    "specific_keywords": [
                        "power series", "radius of convergence", "interval of convergence"
                    ],
                    "negative_guards": ["fourier series"],
                    "context_hints": ["series", "analysis"]
                },
                {
                    "id": 13,
                    "name": "Fourier Series",
                    "canonical_name": "Fourier Series",
                    "aliases": ["Half-Range Fourier Series", "Harmonic Analysis"],
                    "strong_phrases": [
                        "fourier series",
                        "fourier coefficients",
                        "half range sine series",
                        "half range cosine series",
                        "dirichlet's conditions",
                        "parseval's identity",
                        "harmonic analysis"
                    ],
                    "specific_keywords": [
                        "fourier series", "half range sine", "half range cosine", "dirichlet s conditions"
                    ],
                    "negative_guards": [],
                    "context_hints": ["series", "fourier"]
                },
                {
                    "id": 35,
                    "name": "Taylor Series",
                    "canonical_name": "Taylor Series",
                    "aliases": ["Maclaurin Series", "Taylor Expansion"],
                    "strong_phrases": [
                        "taylor's series",
                        "taylor's theorem",
                        "taylor series",
                        "taylor expansion",
                        "maclaurin's series",
                        "maclaurin series",
                        "maclaurin expansion",
                        "expand f x y in powers of"
                    ],
                    "specific_keywords": [
                        "taylor series", "taylor s theorem", "maclaurin series", "maclaurin s series"
                    ],
                    "negative_guards": ["fourier series"],
                    "context_hints": ["series", "calculus"]
                }
            ]
        },
        {
            "id": 18,
            "number": 6,
            "name": "Functions of Several Variables",
            "topics": [
                {
                    "id": 14,
                    "name": "Partial Derivatives",
                    "canonical_name": "Partial Derivatives",
                    "aliases": ["Euler's Theorem for Homogeneous Functions", "Jacobian", "Total Derivative", "Curvature"],
                    "strong_phrases": [
                        "euler's theorem for homogeneous",
                        "euler's theorem",
                        "euler theorem",
                        "jacobian",
                        "total derivative",
                        "partial differentiation",
                        "partial derivatives",
                        "find dy dx if",
                        "radius of curvature",
                        "center of curvature",
                        "envelope of family of curves",
                        "envelope of the family"
                    ],
                    "specific_keywords": [
                        "euler s theorem", "jacobian", "total derivative", "radius of curvature", "envelope of the family"
                    ],
                    "negative_guards": ["maxima and minima", "lagrange multiplier", "stationary point"],
                    "context_hints": ["multivariable calculus"]
                },
                {
                    "id": 15,
                    "name": "Gradient",
                    "canonical_name": "Gradient",
                    "aliases": ["Gradient of Scalar Field", "Unit Normal Vector"],
                    "strong_phrases": [
                        "gradient of the scalar function",
                        "gradient of phi",
                        "unit normal vector to the surface",
                        "unit normal to the surface",
                        "normal derivative"
                    ],
                    "specific_keywords": [
                        "unit normal to the surface", "unit normal vector"
                    ],
                    "negative_guards": ["directional derivative", "divergence", "curl"],
                    "context_hints": ["vector differential calculus"]
                },
                {
                    "id": 16,
                    "name": "Directional Derivatives",
                    "canonical_name": "Directional Derivatives",
                    "aliases": ["Directional Derivative"],
                    "strong_phrases": [
                        "directional derivative of",
                        "directional derivative",
                        "maximum directional derivative"
                    ],
                    "specific_keywords": [
                        "directional derivative", "directional derivatives"
                    ],
                    "negative_guards": [],
                    "context_hints": ["vector differential calculus"]
                },
                {
                    "id": 34,
                    "name": "Extrema and Optimization",
                    "canonical_name": "Extrema and Optimization",
                    "aliases": ["Maxima and Minima", "Lagrange Multipliers", "Saddle Point"],
                    "strong_phrases": [
                        "maxima and minima",
                        "maximum and minimum values",
                        "lagrange's multiplier method",
                        "lagrange's multipliers",
                        "lagrange multiplier",
                        "saddle point",
                        "stationary point",
                        "rt - s^2",
                        "box of maximum capacity",
                        "box of maximum volume",
                        "rectangular box of maximum"
                    ],
                    "specific_keywords": [
                        "lagrange multiplier", "lagrange s multiplier", "maxima and minima", "stationary point", "saddle point"
                    ],
                    "negative_guards": [],
                    "context_hints": ["multivariable calculus", "optimization"]
                }
            ]
        },
        {
            "id": 19,
            "number": 7,
            "name": "Multiple Integrals",
            "topics": [
                {
                    "id": 17,
                    "name": "Double Integrals",
                    "canonical_name": "Double Integrals",
                    "aliases": ["Change of Order of Integration", "Beta and Gamma Functions", "Area using Double Integrals"],
                    "strong_phrases": [
                        "double integral",
                        "double integrals",
                        "change the order of integration",
                        "change of order of integration",
                        "area enclosed by the curves",
                        "beta and gamma functions",
                        "gamma function",
                        "beta function",
                        "gamma n + 1",
                        "beta m, n"
                    ],
                    "specific_keywords": [
                        "double integral", "double integrals", "gamma function", "beta function"
                    ],
                    "negative_guards": ["triple integral"],
                    "context_hints": ["multiple integrals", "calculus"]
                },
                {
                    "id": 18,
                    "name": "Triple Integrals",
                    "canonical_name": "Triple Integrals",
                    "aliases": ["Volume using Triple Integrals", "Cylindrical Coordinates"],
                    "strong_phrases": [
                        "triple integral",
                        "triple integrals",
                        "volume of tetrahedron using triple",
                        "volume enclosed by using triple integral"
                    ],
                    "specific_keywords": [
                        "triple integral", "triple integrals"
                    ],
                    "negative_guards": [],
                    "context_hints": ["multiple integrals", "calculus"]
                },
                {
                    "id": 19,
                    "name": "Change of Variables",
                    "canonical_name": "Change of Variables",
                    "aliases": ["Cartesian to Polar Coordinates", "Spherical Polar Coordinates"],
                    "strong_phrases": [
                        "change of variables in double integral",
                        "transforming to polar coordinates",
                        "spherical polar coordinates",
                        "cylindrical polar coordinates"
                    ],
                    "specific_keywords": [
                        "change of variables in double", "polar coordinates in double"
                    ],
                    "negative_guards": [],
                    "context_hints": ["multiple integrals", "calculus"]
                }
            ]
        },
        {
            "id": 25,
            "number": 8,
            "name": "Vector Calculus",
            "topics": [
                {
                    "id": 36,
                    "name": "Vector Calculus",
                    "canonical_name": "Vector Calculus",
                    "aliases": ["Green's Theorem", "Stokes' Theorem", "Gauss Divergence Theorem", "Solenoidal and Irrotational"],
                    "strong_phrases": [
                        "green's theorem",
                        "stokes' theorem",
                        "stokes theorem",
                        "gauss divergence theorem",
                        "divergence theorem",
                        "solenoidal vector",
                        "irrotational vector",
                        "scalar potential",
                        "work done by a force vector"
                    ],
                    "specific_keywords": [
                        "green s theorem", "stokes theorem", "gauss divergence theorem", "solenoidal", "irrotational"
                    ],
                    "negative_guards": [],
                    "context_hints": ["vector integration"]
                }
            ]
        },
        {
            "id": 26,
            "number": 9,
            "name": "Complex Analysis",
            "topics": [
                {
                    "id": 37,
                    "name": "Complex Variables and Analytic Functions",
                    "canonical_name": "Complex Variables and Analytic Functions",
                    "aliases": ["Cauchy-Riemann Equations", "Harmonic Function", "Milne-Thomson Method"],
                    "strong_phrases": [
                        "analytic function",
                        "cauchy-riemann equations",
                        "cauchy riemann equations",
                        "c-r equations",
                        "harmonic conjugate",
                        "harmonic function",
                        "milne-thomson method",
                        "milne thomson method"
                    ],
                    "specific_keywords": [
                        "analytic function", "cauchy-riemann", "cauchy riemann", "harmonic conjugate", "milne-thomson"
                    ],
                    "negative_guards": ["conformal mapping", "residue", "laurent series"],
                    "context_hints": ["complex variables", "complex analysis"]
                },
                {
                    "id": 38,
                    "name": "Conformal Mapping",
                    "canonical_name": "Conformal Mapping",
                    "aliases": ["Bilinear Transformation", "Möbius Transformation"],
                    "strong_phrases": [
                        "conformal mapping",
                        "bilinear transformation",
                        "cross ratio",
                        "mobius transformation",
                        "transformation w ="
                    ],
                    "specific_keywords": [
                        "conformal mapping", "bilinear transformation"
                    ],
                    "negative_guards": [],
                    "context_hints": ["complex analysis", "mapping"]
                },
                {
                    "id": 39,
                    "name": "Residues and Laurent Series",
                    "canonical_name": "Residues and Laurent Series",
                    "aliases": ["Cauchy's Integral Theorem", "Residue Theorem", "Poles and Singularities"],
                    "strong_phrases": [
                        "cauchy's integral formula",
                        "cauchy's integral theorem",
                        "cauchy's residue theorem",
                        "residue of f(z)",
                        "residue at the pole",
                        "laurent's series",
                        "laurent series",
                        "taylor and laurent series",
                        "singularities of f(z)"
                    ],
                    "specific_keywords": [
                        "cauchy s integral formula", "cauchy s residue theorem", "residue theorem", "laurent series"
                    ],
                    "negative_guards": [],
                    "context_hints": ["complex analysis", "contour integration"]
                }
            ]
        }
    ]
}

target_path = os.path.join(
    os.path.dirname(__file__), "..", "..", "backend", "services", "taxonomy_registry", "definitions", "course_01_calculus.json"
)
with open(target_path, "w", encoding="utf-8") as f:
    json.dump(CALCULUS_DATA, f, indent=2)

print(f"Successfully generated {target_path}")
