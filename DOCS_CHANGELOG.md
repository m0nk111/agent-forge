# Documentation Changelog

Track changes to documentation files in the Agent-Forge project.

---

## 2025-10-13

### BM25 Hybrid Search Documentation Suite

**Created**:
- `docs/BM25_HYBRID_SEARCH.md` - Complete technical documentation
  - BM25 algorithm explanation with mathematical formulas
  - Client-side implementation details (bm25-encoder.ts)
  - Architecture diagrams showing insert and search flows
  - Code examples in TypeScript and Python
  - Performance benchmarks and comparisons
  - Troubleshooting guide for common issues
  - Why client-side vs server-side approach

**Updated**:
- `docs/CLAUDE_CONTEXT_STATUS.md`
  - Added "Production Ready" status with hybrid search
  - Documented BM25 encoder implementation overview
  - Explained auto-fit feature for vocabulary building
  - Added test results showing 606 entities indexed
  - Updated workflow diagrams for hybrid search
  
- `docs/CLAUDE_CONTEXT_INTEGRATION.md`
  - Updated architecture diagram for BM25 integration
  - Added "BM25 Hybrid Search" section with detailed explanation
  - Documented why client-side generation was chosen
  - Updated prerequisites and components sections
  - Added hybrid search usage examples
  
- `docs/README.md`
  - Added "Technical Deep-Dives" section
  - Listed new BM25 documentation with descriptions
  - Highlighted key innovation (client-side BM25)
  - Added production status indicator

**Context**:
- Fixed Milvus BM25 server-side function issues
- Implemented client-side BM25 sparse vector generation
- Enabled hybrid search (dense + sparse vectors)
- RRF reranking for optimal results
- Auto-fit encoder from collection data

**Impact**:
- Complete technical reference for BM25 implementation
- Troubleshooting guide for future issues
- Architecture documentation for maintenance
- Examples for developers integrating hybrid search
