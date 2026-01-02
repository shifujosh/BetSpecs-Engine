# BetSpecs: Deterministic RAG & Real-Time Ingestion

> **Note:** Source code is proprietary. This repository demonstrates the verification architecture.

BetSpecs is a real-time analytics engine that solves the "hallucination problem" in LLMs when dealing with numerical sports data. It operates as a specialized **Swarm Agent** within the **[JACQ Ecosystem](https://github.com/shifujosh/JACQ-Architecture)**.

It introduces a **Verification Layer**—inspired by high-frequency trading pipelines (see [Market-Data-Pipeline-Ref](https://github.com/shifujosh/Market-Data-Pipeline-Ref-))—that forces LLM outputs to pass a deterministic truth check against raw SQL data.

## The Verification Flow

```mermaid
flowchart LR
    Stream[Real-Time Data Stream] -->|Ingest| Norm[Normalization Layer]
    Norm -->|Structured Data| DB[(SQL Ground Truth)]
    
    User[User Query] -->|Intent| LLM[LLM Inference]
    LLM -->|Retrieval| DB
    
    subgraph "Trust Layer"
        LLM -->|Draft Output| Verifier[Verification Agent]
        DB -->|Cross-Reference| Verifier
        Verifier -->|Pass/Fail| Final[Client UI]
    end
```

## Key Innovations

### 1. Vector Anchors
We do not feed raw stats to the LLM context blindly. We use "Anchor Embeddings" to retrieve only the relevant game state rows, reducing context window noise.

### 2. Deterministic Logic Gates
The **Verification Agent** is not an LLM. It is a logic engine that parses the LLM's JSON output and queries the SQL database directly. 
- If `LLM says "Player scored 30"` AND `DB says "Player scored 20"` -> **REJECT & REGENERATE**.

### 3. Real-Time Ingestion
Data is normalized from multiple firehose providers (Sportradar, Genius) and normalized into a unified schema within sub-milliseconds.
