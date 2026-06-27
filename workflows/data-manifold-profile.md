---
description: Profile a dataset's intrinsic mathematical properties and produce structured architectural guidance.
---
# /data-manifold-profile — Dataset Manifold Profiling

Measure geometric/spectral properties of dataset to derive architectural constraints and identify open questions.

## Prerequisites
- User dataset path, format, description.
- Task type: classification, regression, generation, other.
- Adjacency list if graph data.

---

## Phase 1: Environment Setup

// turbo
```bash
uv pip install scikit-dimension numpy scipy matplotlib seaborn
```

If graph:
// turbo
```bash
uv pip install networkx
```

If persistent homology requested (optional, small data):
// turbo
```bash
uv pip install ripser persim
```

---

## Phase 2: Data Loading and Sanity Check
1. Load dataset.
2. Report stats: sample count (N), ambient dimensions (m), data type, NaNs, value ranges.
3. Skip/subsample persistent homology if N > 100,000.
4. Note sequence axis order if sequential.

---

## Phase 3: Reliable Measurements
Run 4 scalable analyses. Write single Python script, save results to JSON.

### 3.1 Intrinsic Dimension (MLE — Levina-Bickel)
```python
from skdim.id import MLE
import numpy as np

estimator = MLE()
estimator.fit(X)  # X is (N, m) array
d_intrinsic = estimator.dimension_
```
- Report median + std for k=5, 10, 20, 50. Flag unstable if std/median > 30%.
- Compare d_intrinsic to m.

### 3.2 PCA Explained Variance
```python
from sklearn.decomposition import PCA
# For large data, use randomized PCA
pca = PCA(n_components=min(m, 100), svd_solver='randomized', random_state=42)
pca.fit(X)
cumulative_var = np.cumsum(pca.explained_variance_ratio_)
d_pca_95 = np.searchsorted(cumulative_var, 0.95) + 1
d_pca_99 = np.searchsorted(cumulative_var, 0.99) + 1
```
- Report d at 95% and 99% variance.
- Plot and save explained variance curve. Report elbow if sharp.

### 3.3 Spectral / Frequency Analysis
Tabular/image:
```python
from scipy.fft import fft, fftfreq
# Compute FFT along each feature axis, report power spectrum
```
Sequential:
```python
# Compute power spectral density
from scipy.signal import welch
freqs, psd = welch(signal, fs=sampling_rate)
# Report: fraction of energy in low-freq (<10% bandwidth) vs high-freq (>50% bandwidth)
```
- Flag high-frequency-dominant if high-freq ratio > 30%.
- Flag smooth if high-freq ratio < 5%.

### 3.4 Graph Spectral Gap (if graph)
```python
import networkx as nx
from scipy.sparse.linalg import eigsh

L_norm = nx.normalized_laplacian_matrix(G).astype(float)
eigenvalues = eigsh(L_norm, k=min(10, L_norm.shape[0]-1), which='SM', return_eigenvectors=False)
eigenvalues_sorted = np.sort(eigenvalues)
lambda_2 = eigenvalues_sorted[1]  # spectral gap
```
- Report λ₂ and λ_max.
- λ₂ < 0.1: flag over-squashing risk.
- λ₂ > 0.5: flag deep GNN over-smoothing risk.

---

## Phase 4: Optional — Persistent Homology (Small Data Only)
Gate: N ≤ 10,000. If larger, subsample to 5,000 and flag as approximate.
```python
from ripser import ripser
from persim import plot_diagrams

result = ripser(X_sample, maxdim=2, thresh=2.0)
diagrams = result['dgms']

betti_0 = len(diagrams[0]) - 1  # subtract infinite bar
betti_1 = len([p for p in diagrams[1] if p[1] - p[0] > persistence_threshold])
betti_2 = len([p for p in diagrams[2] if p[1] - p[0] > persistence_threshold]) if len(diagrams) > 2 else 0
```
- Report Betti numbers (β₀, β₁, β₂) at H₁ median persistence.
- Save diagram.

---

## Phase 5: Structured Report
Write markdown artifact with exactly three sections.

### Section 1: Hard Architectural Constraints

| Measurement | Condition | Architectural Constraint |
|---|---|---|
| d_intrinsic ≪ m | d/m < 0.1 | Network MUST have bottleneck layers. Hidden width should reflect d, not m. Autoencoder-style compression is mathematically justified. |
| d_intrinsic ≈ m | d/m > 0.5 | Data does not lie on a low-dimensional manifold. No strong compression — wide layers needed. |
| PCA elbow is sharp | 95% variance in <10% of components | Linear subspace dominates. First layers can use linear projection without information loss. |
| PCA elbow is gradual | 95% variance requires >50% of components | Non-linear manifold. Linear projections lose information. Need non-linear encoder. |
| High-frequency energy > 30% | — | Network needs multi-scale architecture or positional encoding. Standard networks will suffer spectral bias — slow to learn high-freq patterns. |
| Low-frequency energy > 95% | — | Simple/shallow architecture may suffice. Data is smooth. |
| λ₂ < 0.1 (graph) | — | GNN will suffer over-squashing. MUST use graph rewiring, virtual nodes, or attention-based aggregation for long-range dependencies. |
| λ₂ > 0.5 (graph) | — | Deep GNN (>4 layers) will over-smooth. Limit depth or add residual connections. |
| β₁ > 0 (if measured) | — | Data manifold has holes. Network MUST use non-homeomorphic activations (ReLU, not tanh). Depth ≥ O(Σβ_k) is a theoretical lower bound. |
| β₀ > num_classes | — | Data has more connected components than classes. Network needs enough capacity to merge components — wider hidden layers. |

### Section 2: Open Questions (Domain inputs needed)
1. **Symmetry group G:** translation, rotation, permutation, mirror?
2. **Causality / sequential ordering:** does shuffling features/tokens destroy meaning?
3. **Optimal depth vs trainability:** empirical check required.
4. **Interaction order:** requires 1-WL or k-WL GNN?

### Section 3: Measurement Caveats
List skipped, subsampled, unstable, or inapplicable measurements.

---

## Phase 6: Summary Table

```
| Property              | Value          | Confidence | Architectural Implication          |
|-----------------------|----------------|------------|------------------------------------|
| Ambient dim (m)       | ...            | Exact      | ...                                |
| Intrinsic dim (d)     | ...            | High/Med   | ...                                |
| PCA 95% dim           | ...            | Exact      | ...                                |
| High-freq ratio       | ...            | High       | ...                                |
| Spectral gap (λ₂)     | ...            | High/N/A   | ...                                |
| β₀                    | ...            | Approx/N/A | ...                                |
| β₁                    | ...            | Approx/N/A | ...                                |
| Symmetry group (G)    | UNKNOWN        | —          | Requires domain input              |
| Interaction order     | UNKNOWN        | —          | Requires domain input              |
```

---

## Rules
1. Do not guess answers to open questions. Ask.
2. Explain skipped measurements in Section 3.
3. Recommend structural features (e.g. skip connections), not named architectures (e.g. ResNet).
4. Set random seeds for reproducibility.
5. Save plots and JSON data to `<project_dir>/.gtd/data-profile/`.
